"""
Document-related Pydantic schemas.

This module provides schemas for document management, file uploads,
processing status, and document search operations.

Generated on: 2025-07-14 03:47:30 UTC
Current User: lllucius
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from .base import BaseSchema
from .common import BaseResponse, SearchParams


class DocumentResponse(BaseSchema):
    """Schema for document response data."""

    id: UUID = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type/extension")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    processing_status: str = Field(..., description="Processing status")
    owner_id: UUID = Field(..., description="Owner user ID")
    metainfo: Optional[Dict[str, Any]] = Field(None, description="Additional metainfo")
    chunk_count: int = Field(0, description="Number of chunks")
    created_at: datetime = Field(..., description="Upload timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,
        "json_encoders": {datetime: lambda v: v.isoformat()},
        "json_schema_extra": {
            "example": {
                "id": "4b40c3d9-208c-49ed-bd96-31c0b971e318",
                "title": "Machine Learning Guide",
                "filename": "ml_guide.pdf",
                "file_type": "pdf",
                "file_size": 2048576,
                "mime_type": "application/pdf",
                "processing_status": "completed",
                "owner_id": "4b40c3d9-208c-49ed-bd96-31c0b971e318",
                "metainfo": {"pages": 50, "language": "en"},
                "chunk_count": 25,
                "created_at": "2025-07-14T03:47:30Z",
                "updated_at": "2025-07-14T03:47:30Z",
            }
        },
    }


class DocumentUpdate(BaseSchema):
    """Schema for document updates."""

    title: Optional[str] = Field(
        None, min_length=1, max_length=500, description="New title"
    )
    metainfo: Optional[Dict[str, Any]] = Field(None, description="Updated metainfo")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Updated ML Guide",
                "metainfo": {"category": "AI/ML", "difficulty": "intermediate"},
            }
        }
    }


class DocumentChunkResponse(BaseSchema):
    """Schema for document chunk response data."""

    id: UUID = Field(..., description="Chunk ID")
    content: str = Field(..., description="Chunk text content")
    chunk_index: int = Field(..., description="Chunk index in document")
    start_char: int = Field(..., description="Start character position")
    end_char: int = Field(..., description="End character position")
    token_count: int = Field(..., description="Number of tokens")
    document_id: UUID = Field(..., description="Parent document ID")
    document_title: Optional[str] = Field(None, description="Document title")
    similarity_score: Optional[float] = Field(
        None, description="Similarity score (for search)"
    )
    metainfo: Optional[Dict[str, Any]] = Field(None, description="Additional metainfo")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = {
        "from_attributes": True,
        "json_encoders": {datetime: lambda v: v.isoformat()},
        "json_schema_extra": {
            "example": {
                "id": "4b40c3d9-208c-49ed-bd96-31c0b971e318",
                "content": "Machine learning is a subset of artificial intelligence...",
                "chunk_index": 0,
                "start_char": 0,
                "end_char": 500,
                "token_count": 120,
                "document_id": "4b40c3d9-208c-49ed-bd96-31c0b971e318",
                "document_title": "Machine Learning Guide",
                "similarity_score": 0.95,
                "metainfo": {"section": "introduction"},
                "created_at": "2025-07-14T03:47:30Z",
            }
        },
    }


class DocumentSearchRequest(SearchParams):
    """Schema for document search requests."""

    document_ids: Optional[List[UUID]] = Field(
        None, description="Specific document IDs to search"
    )
    file_types: Optional[List[str]] = Field(None, description="File types to include")

    @field_validator("file_types")
    @classmethod
    def validate_file_types(cls, v):
        """Validate file types."""
        if v:
            allowed_types = ["pdf", "docx", "txt", "md", "rtf"]
            invalid_types = [ft for ft in v if ft.lower() not in allowed_types]
            if invalid_types:
                raise ValueError(f"Invalid file types: {invalid_types}")
            return [ft.lower() for ft in v]
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "machine learning algorithms",
                "limit": 10,
                "threshold": 0.8,
                "algorithm": "hybrid",
                "document_ids": ["4b40c3d9-208c-49ed-bd96-31c0b971e318"],
                "file_types": ["pdf", "docx"],
            }
        }
    }


class DocumentUploadResponse(BaseResponse):
    """Schema for document upload response with enhanced features."""

    document: DocumentResponse = Field(..., description="Uploaded document information")
    task_id: Optional[str] = Field(None, description="Background processing task ID")
    auto_processing: bool = Field(
        False, description="Whether auto-processing was enabled"
    )


class ProcessingStatusResponse(BaseResponse):
    """Enhanced schema for document processing status with background task information."""

    document_id: UUID = Field(..., description="Document ID")
    status: str = Field(..., description="Current processing status")
    chunk_count: int = Field(0, description="Number of chunks created")
    processing_time: Optional[float] = Field(
        None, description="Processing time in seconds"
    )
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Document creation time")
    updated_at: datetime = Field(..., description="Document last update time")

    # Background task information
    task_id: Optional[str] = Field(None, description="Background task ID")
    task_status: Optional[str] = Field(None, description="Background task status")
    progress: Optional[float] = Field(None, description="Processing progress (0-1)")
    task_created_at: Optional[datetime] = Field(None, description="Task creation time")
    task_started_at: Optional[datetime] = Field(None, description="Task start time")
    task_error: Optional[str] = Field(None, description="Task error message")

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}


class DocumentListResponse(BaseResponse):
    """Response schema for document list."""

    documents: List[DocumentResponse] = Field([], description="List of documents")
    total: int = Field(0, description="Total number of documents")


class DocumentSearchResponse(BaseResponse):
    """Response schema for document search."""

    results: List[DocumentChunkResponse] = Field([], description="Search results")
    query: str = Field(..., description="Original search query")
    algorithm: str = Field(..., description="Search algorithm used")
    total_results: int = Field(0, description="Total number of results")
    search_time_ms: float = Field(0.0, description="Search time in milliseconds")


class BackgroundTaskResponse(BaseModel):
    """Response schema for background task operations."""

    message: str
    task_id: str
    document_id: str
    status: str
    priority: Optional[int] = None
    created_at: Optional[datetime] = None


class ProcessingConfigRequest(BaseModel):
    """Request schema for processing configuration."""

    chunk_size: Optional[int] = Field(None, ge=100, le=4000)
    chunk_overlap: Optional[int] = Field(None, ge=0, le=1000)
    enable_metadata_embedding: Optional[bool] = None
    enable_text_preprocessing: Optional[bool] = None
    normalize_unicode: Optional[bool] = None
    remove_extra_whitespace: Optional[bool] = None
    language_detection: Optional[bool] = None


class ProcessingConfigResponse(BaseModel):
    """Response schema for processing configuration."""

    message: str
    config: Dict[str, Any]
