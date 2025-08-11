"""Document-related Pydantic schemas.

This module provides schemas for document management, file uploads,
processing status, and document search operations.
All fields have an explicit 'description' argument.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from .base import BaseModelSchema, BaseSchema
from .common import BaseResponse, SearchParams


class DocumentResponse(BaseSchema):
    """Schema for document response data."""

    id: int = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type/extension")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    status: str = Field(..., description="Processing status")
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
                "id": "4b40c3d9-208c-49ed-bd96-31c0b971e318",
                "title": "Machine Learning Guide",
                "filename": "ml_guide.pdf",
                "file_type": "pdf",
                "file_size": 2048576,
                "mime_type": "application/pdf",
                "status": "completed",
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
                "document_ids": ["4b40c3d9-208c-49ed-bd96-31c0b971e318"],
                "file_types": ["pdf", "docx"],
            }
        }
    }


class DocumentUploadResponse(BaseSchema):
    """Schema for document upload response with enhanced features."""

    document: DocumentResponse = Field(..., description="Uploaded document information")
    task_id: Optional[str] = Field(None, description="Background processing task ID")
    auto_processing: bool = Field(
        False, description="Whether auto-processing was enabled"
    )


class ProcessingStatusResponse(BaseSchema):
    """Enhanced schema for document processing status with background task information."""

    document_id: int = Field(..., description="Document ID")
    status: str = Field(..., description="Current processing status")
    chunk_count: int = Field(0, description="Number of chunks created")
    processing_time: Optional[float] = Field(
        None, description="Processing time in seconds"
    )
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Document creation time")

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

    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")


class DocumentSearchResponse(BaseResponse):
    """Response schema for document search."""

    results: List[DocumentChunkResponse] = Field(..., description="Search results")
    query: str = Field(..., description="Original search query")
    algorithm: str = Field(..., description="Search algorithm used")
    total_results: int = Field(..., description="Total number of results")
    search_time_ms: float = Field(..., description="Search time in milliseconds")


class BackgroundTaskResponse(BaseModel):
    """Response schema for background task operations."""

    message: str = Field(..., description="Status message")
    task_id: str = Field(..., description="Background task ID")
    document_id: str = Field(..., description="Document ID")
    status: str = Field(..., description="Task status")
    priority: Optional[int] = Field(None, description="Task priority")
    created_at: Optional[datetime] = Field(None, description="Task creation timestamp")


class ProcessingConfigRequest(BaseModel):
    """Request schema for processing configuration."""

    chunk_size: Optional[int] = Field(None, ge=100, le=4000, description="Chunk size")
    chunk_overlap: Optional[int] = Field(
        None, ge=0, le=1000, description="Chunk overlap"
    )
    enable_metadata_embedding: Optional[bool] = Field(
        None, description="Enable metadata embedding"
    )
    enable_text_preprocessing: Optional[bool] = Field(
        None, description="Enable text preprocessing"
    )
    normalize_unicode: Optional[bool] = Field(
        None, description="Enable unicode normalization"
    )
    remove_extra_whitespace: Optional[bool] = Field(
        None, description="Remove extra whitespace"
    )
    language_detection: Optional[bool] = Field(
        None, description="Enable language detection"
    )


class ProcessingConfigResponse(BaseModel):
    """Response schema for processing configuration."""

    message: str = Field(..., description="Status message")
    config: Dict[str, Any] = Field(
        ..., description="Processing configuration dictionary"
    )


class QueueStatusResponse(BaseResponse):
    """Response schema for document processing queue status."""

    queue_size: int = Field(..., description="Number of items in queue")
    active_tasks: int = Field(..., description="Number of currently active tasks")
    max_concurrent_tasks: int = Field(
        ..., description="Maximum concurrent tasks allowed"
    )
    completed_tasks: int = Field(..., description="Number of completed tasks")
    worker_running: bool = Field(
        ..., description="Whether the worker is currently running"
    )


class DocumentUserInfo(BaseModel):
    """User information for document responses."""

    username: str = Field(..., description="Username of the document owner")
    email: str = Field(..., description="Email of the document owner")


class DocumentSearchResult(BaseModel):
    """Individual document search result."""

    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    file_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    status: str = Field(..., description="Document processing status")
    created_at: str = Field(..., description="Document creation timestamp")
    updated_at: Optional[str] = Field(default=None, description="Last update timestamp")
    user: DocumentUserInfo = Field(..., description="Document owner information")
    error_message: Optional[str] = Field(
        default=None, description="Error message if processing failed"
    )


class DocumentSearchCriteria(BaseModel):
    """Search criteria used for the document search."""

    query: str = Field(..., description="Search query")
    file_types: Optional[str] = Field(default=None, description="File type filters")
    status_filter: Optional[str] = Field(default=None, description="Status filter")
    user_filter: Optional[str] = Field(default=None, description="User filter")
    date_from: Optional[str] = Field(default=None, description="Start date filter")
    date_to: Optional[str] = Field(default=None, description="End date filter")
    min_size: Optional[int] = Field(
        default=None, description="Minimum file size filter"
    )
    max_size: Optional[int] = Field(
        default=None, description="Maximum file size filter"
    )
    limit: int = Field(..., description="Maximum number of results")


class AdvancedSearchData(BaseModel):
    """Advanced document search results data."""

    results: List[DocumentSearchResult] = Field(
        default_factory=list, description="Search results"
    )
    total_found: int = Field(..., description="Total number of documents found")
    search_criteria: DocumentSearchCriteria = Field(
        ..., description="Search criteria used"
    )
    timestamp: str = Field(..., description="Search timestamp")


class DocumentStorageStats(BaseModel):
    """Document storage statistics."""

    total_size_bytes: int = Field(..., description="Total storage used in bytes")
    total_size_mb: float = Field(..., description="Total storage used in MB")
    avg_file_size_bytes: float = Field(..., description="Average file size in bytes")


class DocumentFileTypeStats(BaseModel):
    """File type statistics."""

    extension: str = Field(..., description="File extension")
    count: int = Field(..., description="Number of files with this extension")
    total_size: int = Field(..., description="Total size of files with this extension")


class DocumentTopUser(BaseModel):
    """Top document uploader information."""

    username: str = Field(..., description="Username")
    document_count: int = Field(..., description="Number of documents uploaded")
    total_size_bytes: int = Field(..., description="Total size of uploaded documents")


class DocumentProcessingStats(BaseModel):
    """Document processing statistics."""

    success_rate: float = Field(..., description="Processing success rate percentage")
    avg_processing_time_seconds: float = Field(
        ..., description="Average processing time in seconds"
    )
    total_processed: int = Field(..., description="Total number of processed documents")


class DocumentRecentActivity(BaseModel):
    """Recent document activity metrics."""

    uploads_last_7_days: int = Field(
        ..., description="Number of uploads in last 7 days"
    )
    processed_last_7_days: int = Field(
        ..., description="Number of processed documents in last 7 days"
    )


class DocumentStatisticsData(BaseModel):
    """Document statistics data model."""

    counts_by_status: Dict[str, int] = Field(
        default_factory=dict, description="Document counts by status"
    )
    total_documents: int = Field(..., description="Total number of documents")
    storage: DocumentStorageStats = Field(..., description="Storage usage statistics")
    file_types: List[DocumentFileTypeStats] = Field(
        default_factory=list, description="File type distribution"
    )
    processing: DocumentProcessingStats = Field(
        ..., description="Processing statistics"
    )
    recent_activity: DocumentRecentActivity = Field(
        ..., description="Recent activity metrics"
    )
    top_uploaders: List[DocumentTopUser] = Field(
        default_factory=list, description="Top document uploaders"
    )
    timestamp: str = Field(..., description="Statistics timestamp")


class CleanupPreviewItem(BaseModelSchema):
    """Document cleanup preview item."""

    id: str
    title: str
    status: str
    created_at: str
    file_size: int


class CleanupDryRunResponse(BaseModelSchema):
    """Document cleanup dry run results."""

    total_count: int
    preview: List[CleanupPreviewItem]
    total_size_bytes: int
    criteria: dict


class CleanupDeletedResponse(BaseModelSchema):
    """Document cleanup deletion results."""

    deleted_count: int
    deleted_size_bytes: int
    errors: List[str]
    criteria: dict


class BulkReprocessResponse(BaseModelSchema):
    """Bulk document reprocessing results."""

    reprocessed_count: int
    total_found: int
    errors: List[str]
    criteria: dict
