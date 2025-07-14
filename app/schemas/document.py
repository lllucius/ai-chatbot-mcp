"""
Document-related Pydantic schemas for API requests and responses.

This module defines schemas for document operations using modern Pydantic V2,
completely separate from SQLAlchemy models.

Current Date and Time (UTC): 2025-07-14 05:03:11
Current User: lllucius
"""

import uuid
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .base import BaseModelSchema
from .common import BaseResponse, PaginationParams


class DocumentStatusEnum(str, Enum):
    """Document processing status enumeration for API."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class DocumentTypeEnum(str, Enum):
    """Document type enumeration for API."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    RTF = "rtf"
    HTML = "html"
    OTHER = "other"


class DocumentBase(BaseModel):
    """Base document schema with common fields."""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        validate_assignment=True,
        extra='ignore'
    )
    
    title: str = Field(
        max_length=500,
        description="Document title or filename"
    )
    filename: str = Field(
        max_length=255,
        description="Original filename"
    )
    content_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="MIME type of the document"
    )


class DocumentCreate(DocumentBase):
    """Schema for creating a new document."""
    pass


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        extra='ignore'
    )
    
    title: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Updated document title"
    )
    summary: Optional[str] = Field(
        default=None,
        description="Updated document summary"
    )
    status: Optional[DocumentStatusEnum] = Field(
        default=None,
        description="Updated processing status"
    )


class DocumentResponse(BaseModelSchema):
    """Schema for document API responses."""
    
    title: str = Field(description="Document title")
    filename: str = Field(description="Original filename")
    file_path: Optional[str] = Field(default=None, description="Path to stored file")
    content_type: Optional[str] = Field(default=None, description="MIME type")
    file_size: int = Field(description="File size in bytes")
    document_type: DocumentTypeEnum = Field(description="Type of document")
    status: DocumentStatusEnum = Field(description="Processing status")
    summary: Optional[str] = Field(default=None, description="AI-generated summary")
    chunk_count: int = Field(description="Number of text chunks")
    processing_time: Optional[float] = Field(default=None, description="Processing time in seconds")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    user_id: uuid.UUID = Field(description="ID of user who uploaded the document")


class DocumentChunkResponse(BaseModelSchema):
    """Schema for document chunk API responses."""
    
    content: str = Field(description="Text content of the chunk")
    chunk_index: int = Field(description="Index of this chunk within the document")
    start_offset: Optional[int] = Field(default=None, description="Starting character offset")
    end_offset: Optional[int] = Field(default=None, description="Ending character offset")
    token_count: Optional[int] = Field(default=None, description="Number of tokens")
    language: Optional[str] = Field(default=None, description="Detected language")
    document_id: uuid.UUID = Field(description="ID of the parent document")


class DocumentDetailResponse(BaseResponse):
    """Response schema for document detail endpoints."""
    
    document: DocumentResponse = Field(description="Document details")
    chunks: Optional[List[DocumentChunkResponse]] = Field(
        default=None,
        description="Document chunks (if requested)"
    )


class DocumentListResponse(BaseResponse):
    """Response schema for document list endpoints."""
    
    documents: List[DocumentResponse] = Field(description="List of documents")
    total_count: int = Field(description="Total number of documents")


class DocumentSearchParams(PaginationParams):
    """Search parameters for document queries."""
    
    title: Optional[str] = Field(
        default=None,
        description="Filter by title (partial match)"
    )
    filename: Optional[str] = Field(
        default=None,
        description="Filter by filename (partial match)"
    )
    content_type: Optional[str] = Field(
        default=None,
        description="Filter by content type"
    )
    document_type: Optional[DocumentTypeEnum] = Field(
        default=None,
        description="Filter by document type"
    )
    status: Optional[DocumentStatusEnum] = Field(
        default=None,
        description="Filter by processing status"
    )
    user_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Filter by user ID"
    )


class DocumentUploadResponse(BaseResponse):
    """Response schema for document upload endpoints."""
    
    document: DocumentResponse = Field(description="Uploaded document details")
    upload_url: Optional[str] = Field(default=None, description="URL where file was uploaded")


class DocumentProcessingResponse(BaseResponse):
    """Response schema for document processing endpoints."""
    
    document_id: uuid.UUID = Field(description="ID of the processed document")
    status: DocumentStatusEnum = Field(description="Processing status")
    chunks_created: int = Field(description="Number of chunks created")
    processing_time: float = Field(description="Processing time in seconds")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class DocumentStatsResponse(BaseModel):
    """Response schema for document statistics."""
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True
    )
    
    total_documents: int = Field(description="Total number of documents")
    documents_by_status: dict = Field(description="Document counts by status")
    documents_by_type: dict = Field(description="Document counts by type")
    total_size_bytes: int = Field(description="Total size of all documents")
    total_chunks: int = Field(description="Total number of chunks")
    documents_created_today: int = Field(description="Documents created today")
    documents_created_this_week: int = Field(description="Documents created this week")
    documents_created_this_month: int = Field(description="Documents created this month")
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="When statistics were last calculated"
    )
    
    def model_dump_json(self, **kwargs):
        """Custom JSON serialization with datetime handling."""
        data = self.model_dump(**kwargs)
        
        # Convert last_updated to ISO format string
        if 'last_updated' in data and data['last_updated'] is not None:
            if isinstance(data['last_updated'], datetime):
                data['last_updated'] = data['last_updated'].isoformat() + 'Z'
        
        import json
        return json.dumps(data)