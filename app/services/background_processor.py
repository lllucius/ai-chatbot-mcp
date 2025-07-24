"""
Background processing service for document processing and embedding generation.

This service provides asynchronous background processing capabilities for:
- Document text extraction and preprocessing
- Embedding generation for document chunks
- Progress tracking and status updates
- Error handling and retry mechanisms
- Queue management for processing tasks

Key Features:
- Async task processing with concurrency control
- Progress tracking and status updates
- Error handling with retry logic
- Memory-efficient processing of large documents
- Configurable processing parameters
- Comprehensive logging and monitoring

Current Date: 2025-01-20
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.document import Document, DocumentChunk, FileStatus
from ..services.embedding import EmbeddingService
from ..utils.file_processing import FileProcessor
from ..utils.text_processing import TextProcessor
from .base import BaseService

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Background task status enumeration."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingTask:
    """Represents a background processing task."""

    def __init__(
        self,
        task_id: str,
        document_id: UUID,
        task_type: str = "process_document",
        priority: int = 5,
        max_retries: int = 3,
        retry_delay: float = 5.0,
    ):
        self.task_id = task_id
        self.document_id = document_id
        self.task_type = task_type
        self.priority = priority
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retries = 0
        self.status = TaskStatus.QUEUED
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.progress = 0.0

    def __lt__(self, other):
        """Priority queue comparison (lower priority number = higher priority)."""
        return self.priority < other.priority


class BackgroundProcessor(BaseService):
    """
    Background processing service for document processing and embedding generation.

    This service manages asynchronous processing of documents including text extraction,
    chunking, preprocessing, and embedding generation. It provides progress tracking,
    error handling, and retry mechanisms for robust document processing.
    """

    def __init__(
        self,
        db: AsyncSession,
        max_concurrent_tasks: int = 3,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        Initialize the background processor.

        Args:
            db: Database session
            max_concurrent_tasks: Maximum number of concurrent processing tasks
            chunk_size: Default chunk size for text processing
            chunk_overlap: Default chunk overlap for text processing
        """
        super().__init__(db, "background_processor")
        self.max_concurrent_tasks = max_concurrent_tasks
        self.processing_semaphore = asyncio.Semaphore(max_concurrent_tasks)

        # Task management
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.active_tasks: Dict[str, ProcessingTask] = {}
        self.task_results: Dict[str, Dict[str, Any]] = {}

        # Processing components
        self.file_processor = FileProcessor()
        self.text_processor = TextProcessor(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        self.embedding_service = EmbeddingService(db)

        # Worker task
        self._worker_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

    async def start(self):
        """Start the background processing worker."""
        if self._worker_task is not None:
            logger.warning("Background processor already started")
            return

        self._shutdown_event.clear()
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("Background processor started")

    async def stop(self):
        """Stop the background processing worker."""
        if self._worker_task is None:
            return

        self._shutdown_event.set()

        # Cancel active tasks
        for task_id in list(self.active_tasks.keys()):
            await self.cancel_task(task_id)

        # Wait for worker to finish
        if self._worker_task:
            try:
                await asyncio.wait_for(self._worker_task, timeout=30.0)
            except asyncio.TimeoutError:
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass

        self._worker_task = None
        logger.info("Background processor stopped")

    async def queue_document_processing(
        self,
        document_id: UUID,
        priority: int = 5,
        processing_config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Queue a document for background processing.

        Args:
            document_id: Document ID to process
            priority: Task priority (lower = higher priority)
            processing_config: Optional processing configuration

        Returns:
            str: Task ID for tracking
        """
        task_id = str(uuid.uuid4())

        task = ProcessingTask(
            task_id=task_id,
            document_id=document_id,
            task_type="process_document",
            priority=priority,
        )

        await self.task_queue.put((priority, task))

        self._log_operation_start(
            "queue_document_processing",
            task_id=task_id,
            document_id=str(document_id),
            priority=priority,
        )

        return task_id

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a background task.

        Args:
            task_id: Task ID to check

        Returns:
            Optional[Dict[str, Any]]: Task status information or None if not found
        """
        task = self.active_tasks.get(task_id)
        if not task:
            # Check if task completed
            if task_id in self.task_results:
                result = self.task_results[task_id]
                return {
                    "task_id": task_id,
                    "status": result.get("status", TaskStatus.COMPLETED),
                    "progress": 1.0,
                    "error_message": result.get("error_message"),
                    "completed_at": result.get("completed_at"),
                }
            return None

        return {
            "task_id": task.task_id,
            "document_id": str(task.document_id),
            "status": task.status,
            "progress": task.progress,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "error_message": task.error_message,
            "retries": task.retries,
            "max_retries": task.max_retries,
        }

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a background task.

        Args:
            task_id: Task ID to cancel

        Returns:
            bool: True if task was cancelled, False if not found
        """
        task = self.active_tasks.get(task_id)
        if not task:
            return False

        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()

        # Remove from active tasks
        self.active_tasks.pop(task_id, None)

        logger.info(f"Task cancelled: {task_id}")
        return True

    async def _worker_loop(self):
        """Main worker loop for processing tasks."""
        logger.info("Background processor worker started")

        while not self._shutdown_event.is_set():
            try:
                # Wait for task or shutdown
                try:
                    # Use timeout to check shutdown periodically
                    _, task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Add to active tasks
                self.active_tasks[task.task_id] = task

                # Process task with concurrency control
                async with self.processing_semaphore:
                    await self._process_task(task)

            except Exception as e:
                logger.error(f"Worker loop error: {e}", exc_info=True)
                await asyncio.sleep(1.0)

        logger.info("Background processor worker stopped")

    async def _process_task(self, task: ProcessingTask):
        """
        Process a single task.

        Args:
            task: Task to process
        """
        operation = f"process_task_{task.task_type}"

        try:
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.utcnow()

            self._log_operation_start(
                operation,
                task_id=task.task_id,
                document_id=str(task.document_id),
                task_type=task.task_type,
            )

            if task.task_type == "process_document":
                await self._process_document_task(task)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.progress = 1.0

            # Store result
            self.task_results[task.task_id] = {
                "status": TaskStatus.COMPLETED,
                "completed_at": task.completed_at,
            }

            self._log_operation_success(
                operation,
                task_id=task.task_id,
                document_id=str(task.document_id),
                processing_time=time.time() - task.started_at.timestamp(),
            )

        except Exception as e:
            await self._handle_task_error(task, e)

        finally:
            # Remove from active tasks
            self.active_tasks.pop(task.task_id, None)

    async def _process_document_task(self, task: ProcessingTask):
        """
        Process a document processing task.

        Args:
            task: Document processing task
        """
        await self._ensure_db_session()

        # Get document
        result = await self.db.execute(
            select(Document).where(Document.id == task.document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise ValueError(f"Document not found: {task.document_id}")

        # Update document status
        await self.db.execute(
            update(Document)
            .where(Document.id == document.id)
            .values(status=FileStatus.PROCESSING)
        )
        await self.db.commit()

        start_time = time.time()

        try:
            # Step 1: Extract text (20% progress)
            task.progress = 0.1
            logger.info(f"Extracting text from document {document.id}")

            extracted_text = await self.file_processor.extract_text(
                document.file_path, document.file_type.value
            )

            task.progress = 0.2

            # Step 2: Get text statistics (30% progress)
            text_stats = self.text_processor.get_text_statistics(extracted_text)

            task.progress = 0.3

            # Step 3: Create chunks (40% progress)
            logger.info(f"Creating chunks for document {document.id}")

            chunks = self.text_processor.create_chunks(
                extracted_text,
                metainfo={
                    "document_id": str(document.id),
                    "document_title": document.title,
                    "language": text_stats.get("language"),
                },
            )

            task.progress = 0.4

            logger.info(f"Created {len(chunks)} chunks for document {document.id}")

            # Step 4: Generate embeddings and save chunks (40-90% progress)
            chunk_records = []
            progress_step = 0.5 / len(chunks) if chunks else 0

            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = await self.embedding_service.generate_embedding(
                    chunk.content
                )

                # Create chunk record
                chunk_record = DocumentChunk(
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    start_offset=chunk.start_char,
                    end_offset=chunk.end_char,
                    token_count=len(
                        chunk.content.split()
                    ),  # Simple word count approximation
                    embedding=embedding,
                    embedding_model=str(settings.openai_embedding_model),
                    language=text_stats.get("language"),
                    document_id=document.id,
                )

                chunk_records.append(chunk_record)
                self.db.add(chunk_record)

                # Update progress
                task.progress = 0.4 + (i + 1) * progress_step

                # Allow other tasks to run
                await asyncio.sleep(0)

            task.progress = 0.9

            # Step 5: Update document (90-100% progress)
            processing_time = time.time() - start_time

            # Update document with results
            await self.db.execute(
                update(Document)
                .where(Document.id == document.id)
                .values(
                    content=extracted_text,
                    status=FileStatus.COMPLETED,
                    chunk_count=len(chunks),
                    processing_time=processing_time,
                    metainfo={
                        **(document.metainfo or {}),
                        "text_stats": text_stats,
                        "processing_completed_at": datetime.utcnow().isoformat(),
                        "chunk_count": len(chunks),
                        "processing_config": {
                            "chunk_size": self.text_processor.chunk_size,
                            "chunk_overlap": self.text_processor.chunk_overlap,
                            "embedding_model": str(settings.openai_embedding_model),
                        },
                    },
                )
            )

            await self.db.commit()
            task.progress = 1.0

            logger.info(
                f"Document processing completed for {document.id}: "
                f"{len(chunks)} chunks, {processing_time:.2f}s"
            )

        except Exception as e:
            # Update document status to failed
            await self.db.execute(
                update(Document)
                .where(Document.id == document.id)
                .values(
                    status=FileStatus.FAILED,
                    error_message=str(e),
                    metainfo={
                        **(document.metainfo or {}),
                        "processing_error": str(e),
                        "processing_failed_at": datetime.utcnow().isoformat(),
                    },
                )
            )
            await self.db.commit()
            raise

    async def _handle_task_error(self, task: ProcessingTask, error: Exception):
        """
        Handle task processing error with retry logic.

        Args:
            task: Failed task
            error: Exception that occurred
        """
        task.retries += 1
        task.error_message = str(error)

        logger.error(
            f"Task {task.task_id} failed (attempt {task.retries}/{task.max_retries}): {error}"
        )

        if task.retries < task.max_retries:
            # Retry task
            task.status = TaskStatus.QUEUED
            task.progress = 0.0

            # Add back to queue with delay
            await asyncio.sleep(task.retry_delay)
            await self.task_queue.put((task.priority, task))

            logger.info(f"Task {task.task_id} requeued for retry")
        else:
            # Max retries reached
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()

            # Store failed result
            self.task_results[task.task_id] = {
                "status": TaskStatus.FAILED,
                "error_message": task.error_message,
                "completed_at": task.completed_at,
            }

            logger.error(
                f"Task {task.task_id} permanently failed after {task.retries} retries"
            )

    async def get_queue_status(self) -> Dict[str, Any]:
        """
        Get the current status of the task queue.

        Returns:
            Dict[str, Any]: Queue status information
        """
        return {
            "queue_size": self.task_queue.qsize(),
            "active_tasks": len(self.active_tasks),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "completed_tasks": len(self.task_results),
            "worker_running": self._worker_task is not None
            and not self._worker_task.done(),
        }

    async def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """
        Clean up old completed task results.

        Args:
            max_age_hours: Maximum age of completed tasks to keep (in hours)
        """
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)

        to_remove = []
        for task_id, result in self.task_results.items():
            completed_at = result.get("completed_at")
            if completed_at and completed_at.timestamp() < cutoff_time:
                to_remove.append(task_id)

        for task_id in to_remove:
            del self.task_results[task_id]

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old task results")


# Global background processor instance
_background_processor: Optional[BackgroundProcessor] = None


async def get_background_processor(db: AsyncSession) -> BackgroundProcessor:
    """
    Get the global background processor instance.

    Args:
        db: Database session

    Returns:
        BackgroundProcessor: Global processor instance
    """
    global _background_processor

    if _background_processor is None:
        _background_processor = BackgroundProcessor(db)
        await _background_processor.start()

    return _background_processor


async def shutdown_background_processor():
    """Shutdown the global background processor."""
    global _background_processor

    if _background_processor is not None:
        await _background_processor.stop()
        _background_processor = None
