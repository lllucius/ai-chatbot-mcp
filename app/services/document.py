"""
Document service for file processing and document management.

This service provides methods for document upload, processing, chunking,
embedding generation, and document lifecycle management.

Generated on: 2025-07-14 03:50:38 UTC
Current User: lllucius
"""

import os
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from ..models.document import Document, DocumentChunk
from ..schemas.document import DocumentUpdate
from ..services.embedding import EmbeddingService
from ..utils.file_processing import FileProcessor
from ..utils.text_processing import TextProcessor
from ..core.exceptions import NotFoundError, ValidationError, DocumentError
from ..config import settings

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Service for document management and processing.
    
    This service handles document upload, text extraction, chunking,
    embedding generation, and document lifecycle operations.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize document service.
        
        Args:
            db: Database session for document operations
        """
        self.db = db
        self.file_processor = FileProcessor()
        self.text_processor = TextProcessor(
            chunk_size=settings.default_chunk_size,
            chunk_overlap=settings.default_chunk_overlap
        )
        self.embedding_service = EmbeddingService(db)
    
    async def create_document(
        self,
        file: UploadFile,
        title: str,
        user_id: int
    ) -> Document:
        """
        Create a new document record and save file.
        
        Args:
            file: Uploaded file object
            title: Document title
            user_id: Owner user ID
            
        Returns:
            Document: Created document object
        """
        try:
            # Generate unique filename
            file_extension = file.filename.split('.')[-1].lower()
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = os.path.join(settings.upload_directory, unique_filename)
            
            # Ensure upload directory exists
            Path(settings.upload_directory).mkdir(parents=True, exist_ok=True)
            
            # Save file to disk
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Get file info
            file_info = self.file_processor.get_file_info(file_path)
            
            # Create document record
            document = Document(
                title=title,
                filename=file.filename,
                file_path=file_path,
                file_type=file_extension,
                file_size=len(content),
                mime_type=file_info.get("mime_type"),
                processing_status="pending",
                owner_id=user_id,
                metainfo={
                    "original_filename": file.filename,
                    "upload_info": file_info
                }
            )
            
            self.db.add(document)
            await self.db.commit()
            await self.db.refresh(document)
            
            logger.info(f"Document created: {document.id} ({document.filename})")
            return document
            
        except Exception as e:
            logger.error(f"Document creation failed: {e}")
            # Clean up file if it was saved
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            raise DocumentError(f"Document creation failed: {e}")
    
    async def start_processing(self, document_id: int) -> bool:
        """
        Start document processing (text extraction and chunking).
        
        Args:
            document_id: Document ID to process
            
        Returns:
            bool: True if processing started successfully
        """
        try:
            # Get document
            document = await self.get_document_by_id(document_id)
            if not document:
                raise NotFoundError("Document not found")
            
            # Update status
            document.processing_status = "processing"
            await self.db.commit()
            
            # Process in background (in production, use a task queue)
            await self._process_document(document)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start processing for document {document_id}: {e}")
            # Update status to failed
            if document:
                document.processing_status = "failed"
                await self.db.commit()
            return False
    
    async def _process_document(self, document: Document):
        """Process document: extract text, create chunks, generate embeddings."""
        try:
            logger.info(f"Starting processing for document {document.id}")
            
            # Extract text from file
            text_content = await self.file_processor.extract_text(
                document.file_path, 
                document.file_type
            )
            
            # Get text statistics
            text_stats = self.text_processor.get_text_statistics(text_content)
            
            # Create text chunks
            chunks = self.text_processor.create_chunks(
                text_content,
                metainfo={
                    "document_id": document.id,
                    "document_title": document.title
                }
            )
            
            logger.info(f"Created {len(chunks)} chunks for document {document.id}")
            
            # Process chunks and generate embeddings
            chunk_records = []
            for chunk in chunks:
                # Generate embedding
                embedding = await self.embedding_service.generate_embedding(chunk.content)
                
                # Create chunk record
                chunk_record = DocumentChunk(
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    start_char=chunk.start_char,
                    end_char=chunk.end_char,
                    token_count=self.embedding_service.openai_client.count_tokens(chunk.content),
                    embedding=embedding,
                    document_id=document.id,
                    metainfo=chunk.metainfo
                )
                
                chunk_records.append(chunk_record)
                self.db.add(chunk_record)
            
            # Update document metainfo and status
            document.metainfo = {
                **(document.metainfo or {}),
                "text_stats": text_stats,
                "processing_completed": True,
                "chunk_count": len(chunks)
            }
            document.processing_status = "completed"
            
            await self.db.commit()
            
            logger.info(f"Processing completed for document {document.id}")
            
        except Exception as e:
            logger.error(f"Document processing failed for {document.id}: {e}")
            document.processing_status = "failed"
            document.metainfo = {
                **(document.metainfo or {}),
                "processing_error": str(e)
            }
            await self.db.commit()
            raise
    
    async def get_document(self, document_id: int, user_id: int) -> Document:
        """
        Get document by ID with access control.
        
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
                and_(
                    Document.id == document_id,
                    Document.owner_id == user_id
                )
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
        file_type: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> Tuple[List[Document], int]:
        """
        List documents for a user with pagination and filtering.
        
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
            filters.append(Document.processing_status == status_filter)
        
        # Count total documents
        count_query = select(func.count(Document.id)).where(and_(*filters))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get documents with pagination
        query = (
            select(Document)
            .where(and_(*filters))
            .order_by(desc(Document.created_at))
            .offset((page - 1) * size)
            .limit(size)
        )
        
        result = await self.db.execute(query)
        documents = result.scalars().all()
        
        return list(documents), total
    
    async def update_document(
        self,
        document_id: int,
        request: DocumentUpdate,
        user_id: int
    ) -> Document:
        """
        Update document metainfo.
        
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
        """
        Delete document and all associated data.
        
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
    
    async def get_processing_status(self, document_id: int, user_id: int) -> Dict[str, Any]:
        """
        Get document processing status and progress.
        
        Args:
            document_id: Document ID
            user_id: User ID for access control
            
        Returns:
            dict: Processing status information
        """
        document = await self.get_document(document_id, user_id)
        
        # Count processed chunks
        chunks_result = await self.db.execute(
            select(func.count(DocumentChunk.id)).where(
                DocumentChunk.document_id == document_id
            )
        )
        chunks_processed = chunks_result.scalar() or 0
        
        # Estimate total chunks based on file size
        estimated_chunks = max(1, document.file_size // (settings.default_chunk_size * 4))
        
        # Calculate progress
        if document.processing_status == "completed":
            progress = 1.0
        elif document.processing_status == "processing":
            progress = min(0.9, chunks_processed / estimated_chunks)
        else:
            progress = 0.0
        
        return {
            "document_id": document_id,
            "status": document.processing_status,
            "progress": progress,
            "chunks_processed": chunks_processed,
            "total_chunks": estimated_chunks if document.processing_status != "completed" else chunks_processed,
            "error_message": document.metainfo.get("processing_error") if document.metainfo else None,
            "started_at": document.created_at,
            "completed_at": document.updated_at if document.processing_status == "completed" else None
        }
    
    async def reprocess_document(self, document_id: int, user_id: int) -> bool:
        """
        Reprocess document (re-extract text and regenerate chunks/embeddings).
        
        Args:
            document_id: Document ID
            user_id: User ID for access control
            
        Returns:
            bool: True if reprocessing started successfully
        """
        document = await self.get_document(document_id, user_id)
        
        if document.processing_status == "processing":
            raise ValidationError("Document is currently being processed")
        
        # Delete existing chunks
        await self.db.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        
        # Reset document status
        document.processing_status = "pending"
        document.metainfo = {
            **(document.metainfo or {}),
            "reprocessing": True
        }
        
        await self.db.commit()
        
        # Start processing
        return await self.start_processing(document_id)
    
    async def get_download_info(self, document_id: int, user_id: int) -> Tuple[str, str, str]:
        """
        Get document download information.
        
        Args:
            document_id: Document ID
            user_id: User ID for access control
            
        Returns:
            Tuple[str, str, str]: File path, filename, mime type
        """
        document = await self.get_document(document_id, user_id)
        
        if not os.path.exists(document.file_path):
            raise NotFoundError("Document file not found")
        
        return document.file_path, document.filename, document.mime_type or "application/octet-stream"