"""
Common Pydantic schemas used across the application.

This module provides base schemas and common response formats
using modern Pydantic V2 features and serialization.

"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Field

from ..utils.timestamp import utcnow

# Generic type variable for paginated responses
T = TypeVar("T")


class BaseResponse(BaseModel):
    """Base response schema for API endpoints."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        validate_assignment=True,
        extra="ignore",
    )

    success: bool = Field(description="Whether the request was successful")
    message: str = Field(description="Human-readable message")
    timestamp: Optional[datetime] = Field(
        default_factory=utcnow, description="When the response was generated"
    )

    def model_dump_json(self, **kwargs):
        """Custom JSON serialization with datetime handling."""
        data = self.model_dump(**kwargs)

        # Convert timestamp to ISO format string
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"

        import json

        return json.dumps(data)


class SuccessResponse(BaseResponse):
    """Standard success response."""

    success: bool = Field(default=True, description="Always true for success responses")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data payload")


class ErrorResponse(BaseResponse):
    """Standard error response."""

    success: bool = Field(default=False, description="Always false for error responses")
    error_code: Optional[str] = Field(default=None, description="Machine-readable error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field-specific errors."""

    error_code: str = Field(default="VALIDATION_ERROR")
    validation_errors: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of validation errors"
    )


class HealthCheckResponse(BaseResponse):
    """Health check response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    status: str = Field(description="Overall health status")
    version: str = Field(description="Application version")
    timestamp: datetime = Field(default_factory=utcnow, description="Health check timestamp")
    components: Optional[Dict[str, Any]] = Field(
        default=None, description="Individual component health statuses"
    )

    def model_dump_json(self, **kwargs):
        """Custom JSON serialization with datetime handling."""
        data = self.model_dump(**kwargs)

        # Convert timestamp to ISO format string
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"

        import json

        return json.dumps(data)


class FileUploadResponse(BaseResponse):
    """Response for file upload operations."""

    filename: str = Field(description="Original filename")
    file_id: Optional[str] = Field(default=None, description="Generated file ID")
    file_size: int = Field(description="File size in bytes")
    content_type: Optional[str] = Field(default=None, description="MIME content type")
    upload_url: Optional[str] = Field(default=None, description="URL where file was uploaded")


class BulkOperationResponse(BaseResponse):
    """Response for bulk operations."""

    total_items: int = Field(description="Total number of items processed")
    successful_items: int = Field(description="Number of successfully processed items")
    failed_items: int = Field(description="Number of failed items")
    errors: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of errors that occurred"
    )


class TokenResponse(BaseModel):
    """JWT token response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration time in seconds")
    expires_at: datetime = Field(description="Token expiration timestamp")

    def model_dump_json(self, **kwargs):
        """Custom JSON serialization with datetime handling."""
        data = self.model_dump(**kwargs)

        # Convert expires_at to ISO format string
        if "expires_at" in data and data["expires_at"] is not None:
            if isinstance(data["expires_at"], datetime):
                data["expires_at"] = data["expires_at"].isoformat() + "Z"

        import json

        return json.dumps(data)


class MetricsResponse(BaseModel):
    """System metrics response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    cpu_usage: Optional[float] = Field(default=None, description="CPU usage percentage")
    memory_usage: Optional[float] = Field(default=None, description="Memory usage percentage")
    disk_usage: Optional[float] = Field(default=None, description="Disk usage percentage")
    active_connections: Optional[int] = Field(
        default=None, description="Active database connections"
    )
    request_count: Optional[int] = Field(default=None, description="Total request count")
    error_rate: Optional[float] = Field(default=None, description="Error rate percentage")
    response_time: Optional[float] = Field(default=None, description="Average response time in ms")
    timestamp: datetime = Field(default_factory=utcnow, description="Metrics collection timestamp")

    def model_dump_json(self, **kwargs):
        """Custom JSON serialization with datetime handling."""
        data = self.model_dump(**kwargs)

        # Convert timestamp to ISO format string
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"

        import json

        return json.dumps(data)


class ConfigurationResponse(BaseModel):
    """Application configuration response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    app_name: str = Field(description="Application name")
    app_version: str = Field(description="Application version")
    debug_mode: bool = Field(description="Whether debug mode is enabled")
    environment: str = Field(description="Runtime environment")
    features: Dict[str, bool] = Field(description="Enabled features")
    limits: Dict[str, Union[int, float]] = Field(description="Configuration limits")


class PaginationParams(BaseModel):
    """Query parameters for pagination."""

    model_config = ConfigDict(from_attributes=True, validate_assignment=True)

    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=10, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: Optional[str] = Field(
        default="asc", pattern="^(asc|desc)$", description="Sort order: asc or desc"
    )
    total: Optional[int] = Field(default=None, description="Total number of items")

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        """Get limit for database queries."""
        return self.per_page


class PaginatedResponse(BaseResponse, Generic[T]):
    """Generic paginated response schema."""

    items: List[Any] = Field(default_factory=list)
    pagination: PaginationParams

    @classmethod
    def create(
        cls, items: List[Any], page: int, size: int, total: int, message: str
    ) -> "PaginatedResponse":
        return cls(
            success=True,
            message=message,
            items=items,
            pagination=PaginationParams(page=page, per_page=size, total=total),
        )


class SearchParams(PaginationParams):
    """
    Search parameters schema extending pagination with search-specific options.

    Combines pagination functionality with search algorithm selection and
    result limiting. Supports multiple search algorithms including vector,
    text, hybrid, and MMR (Maximum Marginal Relevance) approaches.

    Attributes:
        query: Search query string (1-500 characters)
        algorithm: Search algorithm type (vector/text/hybrid/mmr)
        limit: Maximum number of results to return (1-50)

    Inherits from PaginationParams:
        page: Page number for pagination
        per_page: Items per page
    """

    query: Optional[str] = Field(
        default=None, min_length=1, max_length=500, description="Search query string"
    )
    algorithm: Optional[str] = Field(
        default="hybrid",
        pattern="^(vector|text|hybrid|mmr)$",
        description="Search algorithm to use",
    )
    threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0, description="Threshold to use")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional search filters")
