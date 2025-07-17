"""
Document-related Pydantic schemas.

This module provides schemas for document management, file uploads,
processing status, and document search operations.

Generated on: 2025-07-14 03:47:30 UTC
Current User: lllucius
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from .base import BaseSchema
from .common import BaseResponse, SearchParams


class DocumentResponse(BaseSchema):
    """Schema for document response data."""

    id: int = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type/extension")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    processing_status: str = Field(..., description="Processing status")
    owner_id: int = Field(..., description="Owner user ID")
    metainfo: Optional[Dict[str, Any]] = Field(None, description="Additional metainfo")
    chunk_count: int = Field(0, description="Number of chunks")
    created_at: datetime = Field(..., description="Upload timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,
        "json_encoders": {datetime: lambda v: v.isoformat()},
        "json_schema_extra": {
            "example": {
                "id": 1,
                "title": "Machine Learning Guide",
                "filename": "ml_guide.pdf",
                "file_type": "pdf",
                "file_size": 2048576,
                "mime_type": "application/pdf",
                "processing_status": "completed",
                "owner_id": 1,
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

    id: int = Field(..., description="Chunk ID")
    content: str = Field(..., description="Chunk text content")
    chunk_index: int = Field(..., description="Chunk index in document")
    start_char: int = Field(..., description="Start character position")
    end_char: int = Field(..., description="End character position")
    token_count: int = Field(..., description="Number of tokens")
    document_id: int = Field(..., description="Parent document ID")
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
                "id": 1,
                "content": "Machine learning is a subset of artificial intelligence...",
                "chunk_index": 0,
                "start_char": 0,
                "end_char": 500,
                "token_count": 120,
                "document_id": 1,
                "document_title": "Machine Learning Guide",
                "similarity_score": 0.95,
                "metainfo": {"section": "introduction"},
                "created_at": "2025-07-14T03:47:30Z",
            }
        },
    }


class DocumentSearchRequest(SearchParams):
    """Schema for document search requests."""

    document_ids: Optional[List[int]] = Field(
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
                "document_ids": [1, 2, 3],
                "file_types": ["pdf", "docx"],
            }
        }
    }


class DocumentUploadResponse(BaseResponse):
    """Schema for document upload response."""

    document: DocumentResponse = Field(..., description="Uploaded document information")
    processing_started: bool = Field(
        False, description="Whether processing has started"
    )
    estimated_completion: Optional[str] = Field(
        None, description="Estimated processing completion time"
    )


class ProcessingStatusResponse(BaseResponse):
    """Schema for document processing status."""

    document_id: int = Field(..., description="Document ID")
    status: str = Field(..., description="Current processing status")
    progress: float = Field(0.0, description="Processing progress (0-1)")
    chunks_processed: int = Field(0, description="Number of chunks processed")
    total_chunks: int = Field(0, description="Total chunks to process")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    started_at: Optional[datetime] = Field(None, description="Processing start time")
    completed_at: Optional[datetime] = Field(
        None, description="Processing completion time"
    )

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
