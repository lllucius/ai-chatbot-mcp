"""
Common Pydantic schemas used across the application.

This module provides base schemas and common response formats
using modern Pydantic V2 features and serialization.
All fields have an explicit "description" argument.
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

    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Human-readable message")
    timestamp: Optional[datetime] = Field(
        default_factory=utcnow, description="When the response was generated"
    )

    def model_dump_json(self, **kwargs):
        """Custom JSON serialization with datetime handling."""
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json

        return json.dumps(data)


class SuccessResponse(BaseResponse):
    """Standard success response."""

    success: bool = Field(default=True, description="Always true for success responses")
    data: Optional[Dict[str, Any]] = Field(
        default=None, description="Response data payload"
    )


class ErrorResponse(BaseResponse):
    """Standard error response."""

    success: bool = Field(default=False, description="Always false for error responses")
    error_code: Optional[str] = Field(
        default=None, description="Machine-readable error code"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional error details"
    )


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field-specific errors."""

    error_code: str = Field(
        default="VALIDATION_ERROR", description="Code for validation errors"
    )
    validation_errors: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of validation errors"
    )


class HealthCheckResponse(BaseResponse):
    """Health check response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Health check timestamp"
    )
    components: Optional[Dict[str, Any]] = Field(
        default=None, description="Individual component health statuses"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json

        return json.dumps(data)


class DetailedHealthCheckResponse(BaseModel):
    """Detailed health check response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    application: Dict[str, Any] = Field(
        ..., description="Application health information"
    )
    database: Dict[str, Any] = Field(..., description="Database health status")
    cache: Dict[str, Any] = Field(..., description="Cache system health status")
    openai: Dict[str, Any] = Field(..., description="OpenAI service health status")
    fastmcp: Dict[str, Any] = Field(..., description="FastMCP service health status")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Health check timestamp"
    )
    overall_status: str = Field(..., description="Overall system health status")

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json

        return json.dumps(data)


class FileUploadResponse(BaseResponse):
    """Response for file upload operations."""

    filename: str = Field(..., description="Original filename")
    file_id: Optional[str] = Field(default=None, description="Generated file ID")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: Optional[str] = Field(default=None, description="MIME content type")
    upload_url: Optional[str] = Field(
        default=None, description="URL where file was uploaded"
    )


class BulkOperationResponse(BaseResponse):
    """Response for bulk operations."""

    total_items: int = Field(..., description="Total number of items processed")
    successful_items: int = Field(
        ..., description="Number of successfully processed items"
    )
    failed_items: int = Field(..., description="Number of failed items")
    errors: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of errors that occurred"
    )


class TokenResponse(BaseModel):
    """JWT token response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    expires_at: datetime = Field(..., description="Token expiration timestamp")

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "expires_at" in data and data["expires_at"] is not None:
            if isinstance(data["expires_at"], datetime):
                data["expires_at"] = data["expires_at"].isoformat() + "Z"
        import json

        return json.dumps(data)


class MetricsResponse(BaseModel):
    """System metrics response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    cpu_usage: Optional[float] = Field(default=None, description="CPU usage percentage")
    memory_usage: Optional[float] = Field(
        default=None, description="Memory usage percentage"
    )
    disk_usage: Optional[float] = Field(
        default=None, description="Disk usage percentage"
    )
    active_connections: Optional[int] = Field(
        default=None, description="Active database connections"
    )
    request_count: Optional[int] = Field(
        default=None, description="Total request count"
    )
    error_rate: Optional[float] = Field(
        default=None, description="Error rate percentage"
    )
    response_time: Optional[float] = Field(
        default=None, description="Average response time in ms"
    )
    timestamp: datetime = Field(
        default_factory=utcnow, description="Metrics collection timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json

        return json.dumps(data)


class ConfigurationResponse(BaseModel):
    """Application configuration response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    app_name: str = Field(..., description="Application name")
    app_version: str = Field(..., description="Application version")
    debug_mode: bool = Field(..., description="Whether debug mode is enabled")
    environment: str = Field(..., description="Runtime environment")
    features: Dict[str, bool] = Field(..., description="Enabled features")
    limits: Dict[str, Union[int, float]] = Field(
        ..., description="Configuration limits"
    )


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

    items: List[Any] = Field(
        default_factory=list, description="List of paginated items"
    )
    pagination: PaginationParams = Field(..., description="Pagination parameters")

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
        threshold: Similarity threshold
        filters: Additional search filters
    """

    query: Optional[str] = Field(
        default=None, min_length=1, max_length=500, description="Search query string"
    )
    algorithm: Optional[str] = Field(
        default="hybrid",
        pattern="^(vector|text|hybrid|mmr)$",
        description="Search algorithm to use",
    )
    threshold: Optional[float] = Field(
        default=0.7, ge=0.0, le=1.0, description="Threshold to use"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional search filters"
    )


# --- Health Check Response Models ---


class DatabaseHealthResponse(BaseModel):
    """Database health check response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    status: str = Field(..., description="Database health status")
    message: str = Field(..., description="Health check message")
    connectivity: str = Field(..., description="Database connectivity status")
    schema_status: Optional[str] = Field(default=None, description="Schema validation status")
    tables_found: Optional[int] = Field(default=None, description="Number of tables found")


class ServicesHealthResponse(BaseModel):
    """External services health check response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    openai: Dict[str, Any] = Field(..., description="OpenAI service health status")
    fastmcp: Dict[str, Any] = Field(..., description="FastMCP service health status")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Health check timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


class SystemMetricsResponse(BaseModel):
    """System metrics response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    system: Dict[str, Any] = Field(..., description="System metrics")
    application: Dict[str, Any] = Field(..., description="Application metrics")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Metrics collection timestamp"
    )
    error: Optional[str] = Field(default=None, description="Error message if metrics unavailable")

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


class ReadinessResponse(BaseModel):
    """Readiness check response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    status: str = Field(..., description="Readiness status")
    message: str = Field(..., description="Readiness message")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Check timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


class PerformanceMetricsResponse(BaseModel):
    """Performance metrics response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    data: Dict[str, Any] = Field(..., description="Performance metrics data")


class LivenessResponse(BaseModel):
    """Liveness check response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    status: str = Field(..., description="Liveness status")
    message: str = Field(..., description="Liveness message")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Check timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


# --- Database Response Models ---


class DatabaseStatusResponse(BaseModel):
    """Database status response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    connection_status: str = Field(..., description="Database connection status")
    version_info: Dict[str, Any] = Field(..., description="Database version information")
    schema_info: Dict[str, Any] = Field(..., description="Schema information")
    performance_metrics: Dict[str, Any] = Field(..., description="Performance metrics")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Status check timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


class DatabaseTablesResponse(BaseModel):
    """Database tables response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    tables: List[Dict[str, Any]] = Field(..., description="List of database tables")
    total_tables: int = Field(..., description="Total number of tables")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Query timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


class DatabaseMigrationsResponse(BaseModel):
    """Database migrations response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    applied_migrations: List[Dict[str, Any]] = Field(..., description="Applied migrations")
    pending_migrations: List[Dict[str, Any]] = Field(..., description="Pending migrations")
    migration_status: str = Field(..., description="Overall migration status")
    last_migration: Optional[Dict[str, Any]] = Field(default=None, description="Last migration")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Query timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


class DatabaseAnalysisResponse(BaseModel):
    """Database analysis response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    table_stats: List[Dict[str, Any]] = Field(..., description="Table statistics")
    index_analysis: List[Dict[str, Any]] = Field(..., description="Index analysis")
    performance_insights: Dict[str, Any] = Field(..., description="Performance insights")
    recommendations: List[str] = Field(default_factory=list, description="Optimization recommendations")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Analysis timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


class DatabaseQueryResponse(BaseModel):
    """Database query execution response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Query execution success status")
    query: str = Field(..., description="Executed query")
    result_type: str = Field(..., description="Type of query result")
    rows_affected: Optional[int] = Field(default=None, description="Number of rows affected")
    execution_time_ms: float = Field(..., description="Query execution time in milliseconds")
    results: Optional[List[Dict[str, Any]]] = Field(default=None, description="Query results")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Execution timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


# --- User Statistics Response Models ---


class UserStatisticsResponse(BaseModel):
    """User statistics response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    data: Dict[str, Any] = Field(..., description="User statistics data")

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        import json
        return json.dumps(data)


# --- Search and Export Response Models ---


class SearchResponse(BaseModel):
    """Search response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Search operation success status")
    data: Dict[str, Any] = Field(..., description="Search results data")

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        import json
        return json.dumps(data)


class RegistryStatsResponse(BaseModel):
    """Registry statistics response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Status message")
    data: Dict[str, Any] = Field(..., description="Registry statistics data")

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        import json
        return json.dumps(data)


class ConversationStatsResponse(BaseModel):
    """Conversation statistics response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    data: Dict[str, Any] = Field(..., description="Conversation statistics data")

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        import json
        return json.dumps(data)
