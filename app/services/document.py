"""Document service for comprehensive file processing and document management.

This service provides complete document lifecycle management including file upload,
content extraction, text processing, chunking, embedding generation, and search
integration with support for multiple file formats and robust error handling.
"""

import contextlib
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import UploadFile
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import DocumentError, NotFoundError, ValidationError
from app.models.document import Document, DocumentChunk, FileStatus
from app.services.background_processor import get_background_processor
from app.services.base import BaseService
from app.services.embedding import EmbeddingService
from app.utils.file_processing import FileProcessor
from app.utils.text_processing import TextProcessor
from shared.schemas.document import DocumentUpdate

logger = logging.getLogger(__name__)


class DocumentService(BaseService):
    """Service for comprehensive document management and processing workflows.

    This service extends BaseService to provide document-specific functionality
    including file upload handling, content extraction, text processing, chunking,
    embedding generation, and document lifecycle management with error recovery.
    """

    def __init__(self, db: AsyncSession):
        """Initialize document service with processing components.

        Args:
            db: Database session for document operations

        """
        super().__init__(db, "document_service")

        # Initialize processing components
        self.file_processor = FileProcessor()
        self.text_processor = TextProcessor(
            chunk_size=settings.default_chunk_size,
            chunk_overlap=settings.default_chunk_overlap,
        )
        self.embedding_service = EmbeddingService(db)

    async def create_document(
        self, file: UploadFile, title: str, user_id: int
    ) -> Document:
        """Create a new document record and initiate processing pipeline.

        This method handles the initial document creation phase including file
        validation, storage, and database record creation. The document is marked
        as "pending" for subsequent processing stages.

        Args:
            file: Uploaded file object with content and metadata
            title: Human-readable title for the document
            user_id: int of the document owner

        Returns:
            Document: Created document object with pending processing status

        Raises:
            ValidationError: If file validation fails (type, size, format)
            DocumentError: If file processing or storage fails
            Exception: If database operation fails

        Processing Steps:
        1. Validate file type and size against configured limits
        2. Generate secure unique filename to prevent conflicts
        3. Save file to configured upload directory
        4. Extract file metadata and technical information
        5. Create database record with pending status
        6. Log operation for monitoring and debugging

        Example:
            >>> with open("document.pdf", "rb") as f:
            ...     upload_file = UploadFile(filename="document.pdf", file=f)
            ...     doc = await document_service.create_document(upload_file, "My PDF", user_id)
            >>> print(f"Created document {doc.id} with status: {doc.status}")

        """
        operation = "create_document"
        self._log_operation_start(
            operation,
            filename=file.filename,
            title=title,
            user_id=str(user_id),
            mime_type=file.content_type,
        )

        try:
            await self._ensure_db_session()

            # Validate file before processing
            if not file.filename:
                raise ValidationError("Filename is required")

            # Use enhanced processor for format detection and validation
            try:
                # Save file temporarily for format detection
                temp_content = await file.read()
                await file.seek(0)  # Reset file pointer

                unique_filename = (
                    f"{uuid.uuid4()}.{file.filename.split('.')[-1].lower()}"
                )
                temp_path = os.path.join("/tmp", unique_filename)

                with open(temp_path, "wb") as temp_file:
                    temp_file.write(temp_content)

                # Simple file format detection using file extension and content
                import mimetypes

                import filetype

                kind = filetype.guess(temp_path)
                if kind is not None:
                    file_extension = f".{kind.extension}"
                    detected_mime_type = kind.mime
                else:
                    # Fallback to filename extension
                    file_extension = f".{file.filename.split('.')[-1].lower()}"
                    detected_mime_type, _ = mimetypes.guess_type(file.filename)
                os.unlink(temp_path)  # Clean up temp file

            except Exception as e:
                raise ValidationError(f"Unsupported file format: {e}")

            # Additional validation against allowed types
            allowed_extensions = (
                str(settings.allowed_file_types).split(",")
                if isinstance(settings.allowed_file_types, str)
                else settings.allowed_file_types
            )
            if file_extension.lstrip(".") not in allowed_extensions:
                raise ValidationError(f"File type '{file_extension}' not allowed")

            # Read file content for processing
            content = await file.read()
            if len(content) > settings.max_file_size:
                raise ValidationError(
                    f"File size exceeds maximum allowed ({settings.max_file_size} bytes)"
                )

            # Generate secure unique filename to prevent conflicts
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(settings.upload_directory, unique_filename)

            # Ensure upload directory exists
            Path(settings.upload_directory).mkdir(parents=True, exist_ok=True)

            # Save file to disk with error handling
            try:
                with open(file_path, "wb") as buffer:
                    buffer.write(content)
            except OSError as e:
                self.logger.error(
                    "File write failed", extra={"error": str(e), "file_path": file_path}
                )
                raise DocumentError(f"Failed to save file: {e}")

            # Extract file metadata and technical information
            try:
                file_info = self.file_processor.get_file_info(file_path)
            except Exception as e:
                # If metadata extraction fails, continue with basic info
                self.logger.warning(
                    "Metadata extraction failed", extra={"error": str(e)}
                )
                file_info = {"error": str(e)}

            # Create comprehensive document record
            document = Document(
                title=title,
                filename=file.filename,
                file_path=file_path,
                file_type=file_extension.lstrip("."),
                file_size=len(content),
                mime_type=detected_mime_type
                or file.content_type
                or file_info.get("mime_type"),
                status=FileStatus.PENDING,
                owner_id=user_id,
                metainfo={
                    "original_filename": file.filename,
                    "upload_info": file_info,
                    "processing_config": {
                        "chunk_size": settings.default_chunk_size,
                        "chunk_overlap": settings.default_chunk_overlap,
                    },
                },
            )

            self.db.add(document)
            await self.db.commit()
            await self.db.refresh(document)

            self._log_operation_success(
                operation,
                document_id=str(document.id),
                filename=file.filename,
                title=title,
                file_size=len(content),
                file_type=file_extension,
                user_id=str(user_id),
            )

            return document

        except (ValidationError, DocumentError):
            raise
        except Exception as e:
            self._log_operation_error(
                operation, e, filename=file.filename, title=title, user_id=str(user_id)
            )
            # Clean up file if it was created
            if "file_path" in locals() and os.path.exists(file_path):
                with contextlib.suppress(OSError):
                    os.unlink(file_path)
            await self.db.rollback()
            raise DocumentError(f"Document creation failed: {e}")

    async def start_processing(self, document_id: int, priority: int = 5) -> str:
        """Start background document processing (text extraction and chunking).

        Args:
            document_id: Document ID to process
            priority: Processing priority (lower = higher priority)

        Returns:
            str: Task ID for tracking background processing

        Raises:
            NotFoundError: If document not found
            ValidationError: If document is already processing

        """
        operation = "start_processing"

        try:
            await self._ensure_db_session()

            # Get document
            document = await self.get_document_by_id(document_id)
            if not document:
                raise NotFoundError("Document not found")

            if document.status == FileStatus.PROCESSING:
                raise ValidationError("Document is already being processed")

            if document.status == FileStatus.COMPLETED:
                raise ValidationError("Document has already been processed")

            # Get background processor
            background_processor = await get_background_processor()

            # Queue document for background processing
            task_id = await background_processor.queue_document_processing(
                document_id=document_id, priority=priority
            )

            self._log_operation_success(
                operation,
                document_id=str(document_id),
                task_id=task_id,
                priority=priority,
            )

            return task_id

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self._log_operation_error(operation, e, document_id=str(document_id))
            raise

    async def get_status(
        self, document_id: int, task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get document processing status including background task information.

        Args:
            document_id: Document ID
            task_id: Optional task ID for background processing

        Returns:
            Dict[str, Any]: Comprehensive processing status

        """
        try:
            await self._ensure_db_session()

            # Get document
            document = await self.get_document_by_id(document_id)
            if not document:
                raise NotFoundError("Document not found")

            # Get basic status
            status_info = {
                "document_id": str(document_id),
                "status": document.status,
                "chunk_count": document.chunk_count,
                "processing_time": document.processing_time,
                "error_message": document.error_message,
                "created_at": document.created_at,
                "updated_at": document.updated_at,
            }

            # Add background task information if available
            if task_id:
                background_processor = await get_background_processor()
                task_status = await background_processor.get_task_status(task_id)
                if task_status:
                    status_info.update(
                        {
                            "task_id": task_id,
                            "task_status": task_status["status"],
                            "progress": task_status["progress"],
                            "task_created_at": task_status.get("created_at"),
                            "task_started_at": task_status.get("started_at"),
                            "task_error": task_status.get("error_message"),
                        }
                    )

            return status_info

        except Exception as e:
            logger.error(
                f"Failed to get processing status for document {document_id}: {e}"
            )
            raise

    async def _process_document(self, document: Document):
        """Process document: extract text, create chunks, generate embeddings using unstructured."""
        try:
            logger.info(f"Starting processing for document {document.id}")

            # Extract structured chunks directly using unstructured
            chunks_data = await self.file_processor.extract_chunks(
                document.file_path,
                document.file_type,
                max_characters=settings.default_chunk_size,
            )

            logger.info(
                f"Extracted {len(chunks_data)} chunks for document {document.id}"
            )

            # Also extract full text for backward compatibility and statistics
            text_content = await self.file_processor.extract_text(
                document.file_path, document.file_type
            )

            # Get text statistics
            text_stats = self.text_processor.get_text_statistics(text_content)

            # Process chunks and generate embeddings
            chunk_records = []
            for i, chunk_data in enumerate(chunks_data):
                # Generate embedding for the chunk text
                embedding = await self.embedding_service.generate_embedding(
                    chunk_data["text"]
                )

                # Create chunk record with unstructured metadata
                chunk_record = DocumentChunk(
                    content=chunk_data["text"],
                    chunk_index=i,
                    start_offset=None,  # Unstructured doesn't provide character offsets in same way
                    end_offset=None,
                    token_count=self.embedding_service.openai_client.count_tokens(
                        chunk_data["text"]
                    ),
                    embedding=embedding,
                    document_id=document.id,
                    # Store unstructured metadata
                    **(
                        {"language": chunk_data["metadata"].get("language")}
                        if chunk_data.get("metadata", {}).get("language")
                        else {}
                    ),
                )

                chunk_records.append(chunk_record)
                self.db.add(chunk_record)

            # Update document with full text content and metadata
            document.content = text_content
            document.chunk_count = len(chunks_data)
            document.metainfo = {
                **(document.metainfo or {}),
                "text_stats": text_stats,
                "processing_completed": True,
                "chunk_count": len(chunks_data),
                "unstructured_processing": True,
                "chunks_metadata": [chunk.get("metadata", {}) for chunk in chunks_data],
            }
            document.status = FileStatus.COMPLETED

            await self.db.commit()

            logger.info(f"Processing completed for document {document.id}")

        except Exception as e:
            logger.error(f"Document processing failed for {document.id}: {e}")
            document.status = FileStatus.FAILED
            document.error_message = str(e)
            document.metainfo = {
                **(document.metainfo or {}),
                "processing_error": str(e),
                "unstructured_processing": False,
            }
            await self.db.commit()
            raise

    async def get_document(self, document_id: int, user_id: int) -> Document:
        """Get document by ID with access control.

        Args:
            document_id: Document ID
            user_id: User ID for access control

        Returns:
            Document: Document object

        Raises:
            NotFoundError: If document not found or access denied

        """
        result = await self.db.execute(
            select(Document).where(
                and_(Document.id == document_id, Document.owner_id == user_id)
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise NotFoundError("Document not found")

        return document

    async def get_document_by_id(self, document_id: int) -> Optional[Document]:
        """Get document by ID without access control (internal use)."""
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def list_documents(
        self,
        user_id: int,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        file_type: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> Tuple[List[Document], int]:
        """List documents for a user with pagination and filtering.

        Args:
            user_id: User ID
            page: Page number (1-based)
            size: Items per page
            file_type: Filter by file type
            status_filter: Filter by processing status

        Returns:
            Tuple[List[Document], int]: List of documents and total count

        """
        # Build filters
        filters = [Document.owner_id == user_id]

        if file_type:
            filters.append(Document.file_type == file_type.lower())

        if status_filter:
            filters.append(Document.status == status_filter)

        if search:
            # Use the base service search functionality
            return await self._search_entities(
                model=Document,
                search_fields=["title", "summary", "content"],
                search_term=search,
                additional_filters=filters,
                page=page,
                size=size,
            )
        else:
            return await self._list_with_filters(
                model=Document,
                filters=filters,
                page=page,
                size=size,
                order_by=Document.title,
            )

    async def update_document(
        self, document_id: int, request: DocumentUpdate, user_id: int
    ) -> Document:
        """Update document metainfo.

        Args:
            document_id: Document ID
            request: Update data
            user_id: User ID for access control

        Returns:
            Document: Updated document object

        """
        document = await self.get_document(document_id, user_id)

        # Update fields
        if request.title is not None:
            document.title = request.title

        if request.metainfo is not None:
            # Merge with existing metainfo
            existing_metainfo = document.metainfo or {}
            existing_metainfo.update(request.metainfo)
            document.metainfo = existing_metainfo

        await self.db.commit()
        await self.db.refresh(document)

        logger.info(f"Document updated: {document_id}")
        return document

    async def delete_document(self, document_id: int, user_id: int) -> bool:
        """Delete document and all associated data.

        Args:
            document_id: Document ID
            user_id: User ID for access control

        Returns:
            bool: True if deleted successfully

        """
        document = await self.get_document(document_id, user_id)

        # Delete file from disk
        try:
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
        except Exception as e:
            logger.warning(f"Failed to delete file {document.file_path}: {e}")

        # Delete database record (cascades to chunks)
        await self.db.delete(document)
        await self.db.commit()

        logger.info(f"Document deleted: {document_id}")
        return True

    async def reprocess_document(self, document_id: int, user_id: int) -> bool:
        """Reprocess document (re-extract text and regenerate chunks/embeddings).

        Args:
            document_id: Document ID
            user_id: User ID for access control

        Returns:
            bool: True if reprocessing started successfully

        """
        document = await self.get_document(document_id, user_id)

        if document.status == FileStatus.PROCESSING:
            raise ValidationError("Document is currently being processed")

        # Delete existing chunks
        await self.db.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )

        # Reset document status
        document.status = "pending"
        document.metainfo = {**(document.metainfo or {}), "reprocessing": True}

        await self.db.commit()

        # Start processing
        return await self.start_processing(document_id)

    async def get_download_info(
        self, document_id: int, user_id: int
    ) -> Tuple[str, str, str]:
        """Get document download information.

        Args:
            document_id: Document ID
            user_id: User ID for access control

        Returns:
            Tuple[str, str, str]: File path, filename, mime type

        """
        document = await self.get_document(document_id, user_id)

        if not os.path.exists(document.file_path):
            raise NotFoundError("Document file not found")

        return (
            document.file_path,
            document.filename,
            document.mime_type or "application/octet-stream",
        )
