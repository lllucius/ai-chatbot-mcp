"""
Pydantic response schemas for document management API endpoints.

This module provides response models for all document-related endpoints that currently
return raw dictionaries, ensuring type safety and proper API documentation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .base import BaseModelSchema


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
    error_message: Optional[str] = Field(default=None, description="Error message if processing failed")


class DocumentSearchCriteria(BaseModel):
    """Search criteria used for the document search."""
    
    query: str = Field(..., description="Search query")
    file_types: Optional[str] = Field(default=None, description="File type filters")
    status_filter: Optional[str] = Field(default=None, description="Status filter")
    user_filter: Optional[str] = Field(default=None, description="User filter")
    date_from: Optional[str] = Field(default=None, description="Start date filter")
    date_to: Optional[str] = Field(default=None, description="End date filter")
    min_size: Optional[int] = Field(default=None, description="Minimum file size filter")
    max_size: Optional[int] = Field(default=None, description="Maximum file size filter")
    limit: int = Field(..., description="Maximum number of results")


class AdvancedSearchData(BaseModel):
    """Advanced document search results data."""
    
    results: List[DocumentSearchResult] = Field(default_factory=list, description="Search results")
    total_found: int = Field(..., description="Total number of documents found")
    search_criteria: DocumentSearchCriteria = Field(..., description="Search criteria used")
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
    avg_processing_time_seconds: float = Field(..., description="Average processing time in seconds")
    total_processed: int = Field(..., description="Total number of processed documents")


class DocumentRecentActivity(BaseModel):
    """Recent document activity metrics."""
    
    uploads_last_7_days: int = Field(..., description="Number of uploads in last 7 days")
    processed_last_7_days: int = Field(..., description="Number of processed documents in last 7 days")


class DocumentStatisticsData(BaseModel):
    """Document statistics data model."""
    
    counts_by_status: Dict[str, int] = Field(default_factory=dict, description="Document counts by status")
    total_documents: int = Field(..., description="Total number of documents")
    storage: DocumentStorageStats = Field(..., description="Storage usage statistics")
    file_types: List[DocumentFileTypeStats] = Field(default_factory=list, description="File type distribution")
    processing: DocumentProcessingStats = Field(..., description="Processing statistics")
    recent_activity: DocumentRecentActivity = Field(..., description="Recent activity metrics")
    top_uploaders: List[DocumentTopUser] = Field(default_factory=list, description="Top document uploaders")
    timestamp: str = Field(..., description="Statistics timestamp")