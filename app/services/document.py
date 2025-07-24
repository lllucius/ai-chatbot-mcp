"Service layer for document business logic."

import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from fastapi import UploadFile
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from ..config import settings
from ..core.exceptions import DocumentError, NotFoundError, ValidationError
from ..models.document import Document, DocumentChunk, FileStatus
from ..schemas.document import DocumentUpdate
from ..services.background_processor import get_background_processor
from ..services.embedding import EmbeddingService
from ..utils.enhanced_document_processor import (
    DocumentProcessor as EnhancedDocumentProcessor,
)
from ..utils.file_processing import FileProcessor
from ..utils.text_processing import TextProcessor
from .base import BaseService

logger = logging.getLogger(__name__)


class DocumentService(BaseService):
    "Document service for business logic operations."

    def __init__(self, db: AsyncSession):
        "Initialize class instance."
        super().__init__(db, "document_service")
        self.file_processor = FileProcessor()
        self.enhanced_processor = EnhancedDocumentProcessor(config={})
        self.text_processor = TextProcessor(
            chunk_size=settings.default_chunk_size,
            chunk_overlap=settings.default_chunk_overlap,
        )
        self.embedding_service = EmbeddingService(db)

    async def create_document(
        self, file: UploadFile, title: str, user_id: UUID
    ) -> Document:
        "Create new document."
        operation = "create_document"
        self._log_operation_start(
            operation,
            filename=file.filename,
            title=title,
            user_id=str(user_id),
            content_type=file.content_type,
        )
        try:
            (await self._ensure_db_session())
            if not file.filename:
                raise ValidationError("Filename is required")
            try:
                temp_content = await file.read()
                (await file.seek(0))
                unique_filename = (
                    f"{uuid.uuid4()}.{file.filename.split('.')[(- 1)].lower()}"
                )
                temp_path = os.path.join("/tmp", unique_filename)
                with open(temp_path, "wb") as temp_file:
                    temp_file.write(temp_content)
                import mimetypes
                import filetype

                kind = filetype.guess(temp_path)
                if kind is not None:
                    file_extension = f".{kind.extension}"
                    detected_mime_type = kind.mime
                else:
                    file_extension = f".{file.filename.split('.')[(- 1)].lower()}"
                    (detected_mime_type, _) = mimetypes.guess_type(file.filename)
                os.unlink(temp_path)
            except Exception as e:
                raise ValidationError(f"Unsupported file format: {e}")
            allowed_extensions = (
                str(settings.allowed_file_types).split(",")
                if isinstance(settings.allowed_file_types, str)
                else settings.allowed_file_types
            )
            if file_extension.lstrip(".") not in allowed_extensions:
                raise ValidationError(f"File type '{file_extension}' not allowed")
            content = await file.read()
            if len(content) > settings.max_file_size:
                raise ValidationError(
                    f"File size exceeds maximum allowed ({settings.max_file_size} bytes)"
                )
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(settings.upload_directory, unique_filename)
            Path(settings.upload_directory).mkdir(parents=True, exist_ok=True)
            try:
                with open(file_path, "wb") as buffer:
                    buffer.write(content)
            except OSError as e:
                self.logger.error(
                    "File write failed", error=str(e), file_path=file_path
                )
                raise DocumentError(f"Failed to save file: {e}")
            try:
                file_info = self.file_processor.get_file_info(file_path)
            except Exception as e:
                self.logger.warning("Metadata extraction failed", error=str(e))
                file_info = {"error": str(e)}
            document = Document(
                title=title,
                filename=file.filename,
                file_path=file_path,
                file_type=file_extension.lstrip("."),
                file_size=len(content),
                content_type=(
                    detected_mime_type
                    or file.content_type
                    or file_info.get("mime_type")
                ),
                status=FileStatus.PENDING,
                owner_id=user_id,
                metainfo={
                    "original_filename": file.filename,
                    "detected_mime_type": detected_mime_type,
                    "upload_info": file_info,
                    "processing_config": {
                        "chunk_size": settings.default_chunk_size,
                        "chunk_overlap": settings.default_chunk_overlap,
                        "enhanced_processor": True,
                    },
                },
            )
            self.db.add(document)
            (await self.db.commit())
            (await self.db.refresh(document))
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
            if ("file_path" in locals()) and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except OSError:
                    pass
            (await self.db.rollback())
            raise
            (await self.db.refresh(document))
            logger.info(f"Document created: {document.id} ({document.filename})")
            return document
        except Exception as e:
            logger.error(f"Document creation failed: {e}")
            if ("file_path" in locals()) and os.path.exists(file_path):
                os.remove(file_path)
            raise DocumentError(f"Document creation failed: {e}")

    async def start_processing(self, document_id: UUID, priority: int = 5) -> str:
        "Start Processing operation."
        operation = "start_processing"
        try:
            (await self._ensure_db_session())
            document = await self.get_document_by_id(document_id)
            if not document:
                raise NotFoundError("Document not found")
            if document.status == FileStatus.PROCESSING:
                raise ValidationError("Document is already being processed")
            if document.status == FileStatus.COMPLETED:
                raise ValidationError("Document has already been processed")
            background_processor = await get_background_processor(self.db)
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

    async def get_processing_status(
        self, document_id: UUID, task_id: Optional[str] = None
    ) -> Dict[(str, Any)]:
        "Get processing status data."
        try:
            (await self._ensure_db_session())
            document = await self.get_document_by_id(document_id)
            if not document:
                raise NotFoundError("Document not found")
            status_info = {
                "document_id": str(document_id),
                "status": document.status,
                "chunk_count": document.chunk_count,
                "processing_time": document.processing_time,
                "error_message": document.error_message,
                "created_at": document.created_at,
                "updated_at": document.updated_at,
            }
            if task_id:
                background_processor = await get_background_processor(self.db)
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
        "Process Document operation."
        try:
            logger.info(f"Starting processing for document {document.id}")
            chunks_data = await self.file_processor.extract_chunks(
                document.file_path,
                document.file_type,
                max_characters=settings.default_chunk_size,
            )
            logger.info(
                f"Extracted {len(chunks_data)} chunks for document {document.id}"
            )
            text_content = await self.file_processor.extract_text(
                document.file_path, document.file_type
            )
            text_stats = self.text_processor.get_text_statistics(text_content)
            chunk_records = []
            for i, chunk_data in enumerate(chunks_data):
                embedding = await self.embedding_service.generate_embedding(
                    chunk_data["text"]
                )
                chunk_record = DocumentChunk(
                    content=chunk_data["text"],
                    chunk_index=i,
                    start_offset=None,
                    end_offset=None,
                    token_count=self.embedding_service.openai_client.count_tokens(
                        chunk_data["text"]
                    ),
                    embedding=embedding,
                    document_id=document.id,
                    **(
                        {"language": chunk_data["metadata"].get("language")}
                        if chunk_data.get("metadata", {}).get("language")
                        else {}
                    ),
                )
                chunk_records.append(chunk_record)
                self.db.add(chunk_record)
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
            (await self.db.commit())
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
            (await self.db.commit())
            raise

    async def get_document(self, document_id: UUID, user_id: UUID) -> Document:
        "Get document data."
        result = await self.db.execute(
            select(Document).where(
                and_((Document.id == document_id), (Document.owner_id == user_id))
            )
        )
        document = result.scalar_one_or_none()
        if not document:
            raise NotFoundError("Document not found")
        return document

    async def get_document_by_id(self, document_id: UUID) -> Optional[Document]:
        "Get document by id data."
        result = await self.db.execute(
            select(Document).where((Document.id == document_id))
        )
        return result.scalar_one_or_none()

    async def list_documents(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 20,
        file_type: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> Tuple[(List[Document], int)]:
        "List documents entries."
        filters = [Document.owner_id == user_id]
        if file_type:
            filters.append((Document.file_type == file_type.lower()))
        if status_filter:
            filters.append((Document.status == status_filter))
        count_query = select(func.count(Document.id)).where(and_(*filters))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        query = (
            select(Document)
            .where(and_(*filters))
            .order_by(desc(Document.created_at))
            .offset(((page - 1) * size))
            .limit(size)
        )
        result = await self.db.execute(query)
        documents = result.scalars().all()
        return (list(documents), total)

    async def update_document(
        self, document_id: UUID, request: DocumentUpdate, user_id: UUID
    ) -> Document:
        "Update existing document."
        document = await self.get_document(document_id, user_id)
        if request.title is not None:
            document.title = request.title
        if request.metainfo is not None:
            existing_metainfo = document.metainfo or {}
            existing_metainfo.update(request.metainfo)
            document.metainfo = existing_metainfo
        (await self.db.commit())
        (await self.db.refresh(document))
        logger.info(f"Document updated: {document_id}")
        return document

    async def delete_document(self, document_id: UUID, user_id: UUID) -> bool:
        "Delete document."
        document = await self.get_document(document_id, user_id)
        try:
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
        except Exception as e:
            logger.warning(f"Failed to delete file {document.file_path}: {e}")
        (await self.db.delete(document))
        (await self.db.commit())
        logger.info(f"Document deleted: {document_id}")
        return True

    async def get_status(self, document_id: UUID, user_id: UUID) -> Dict[(str, Any)]:
        "Get status data."
        document = await self.get_document(document_id, user_id)
        chunks_result = await self.db.execute(
            select(func.count(DocumentChunk.id)).where(
                (DocumentChunk.document_id == document_id)
            )
        )
        chunks_processed = chunks_result.scalar() or 0
        estimated_chunks = max(
            1, (document.file_size // (settings.default_chunk_size * 4))
        )
        if document.status == FileStatus.COMPLETED:
            progress = 1.0
        elif document.status == FileStatus.PROCESSING:
            progress = min(0.9, (chunks_processed / estimated_chunks))
        else:
            progress = 0.0
        return {
            "document_id": document_id,
            "status": document.status,
            "progress": progress,
            "chunks_processed": chunks_processed,
            "total_chunks": (
                estimated_chunks
                if (document.status != "completed")
                else chunks_processed
            ),
            "error_message": (
                document.metainfo.get("processing_error") if document.metainfo else None
            ),
            "started_at": document.created_at,
            "completed_at": (
                document.updated_at
                if (document.status == FileStatus.COMPLETED)
                else None
            ),
        }

    async def reprocess_document(self, document_id: UUID, user_id: UUID) -> bool:
        "Reprocess Document operation."
        document = await self.get_document(document_id, user_id)
        if document.status == FileStatus.PROCESSING:
            raise ValidationError("Document is currently being processed")
        (
            await self.db.execute(
                select(DocumentChunk).where((DocumentChunk.document_id == document_id))
            )
        )
        document.status = "pending"
        document.metainfo = {**(document.metainfo or {}), "reprocessing": True}
        (await self.db.commit())
        return await self.start_processing(document_id)

    async def get_download_info(
        self, document_id: UUID, user_id: UUID
    ) -> Tuple[(str, str, str)]:
        "Get download info data."
        document = await self.get_document(document_id, user_id)
        if not os.path.exists(document.file_path):
            raise NotFoundError("Document file not found")
        return (
            document.file_path,
            document.filename,
            (document.mime_type or "application/octet-stream"),
        )
