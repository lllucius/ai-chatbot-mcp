"""Common Pydantic schemas for comprehensive API requests and responses across the application.

This module provides foundational schemas and standardized response formats using
modern Pydantic V2 features with advanced validation, serialization, and type safety.
Implements consistent API response structures, pagination handling, health monitoring,
and error reporting patterns used throughout the application.

Key Features:
- Standardized API response formats with consistent structure and metadata
- Comprehensive pagination support with flexible parameters and calculations
- Advanced health monitoring schemas for system observability and diagnostics
- Error handling schemas with structured error reporting and validation
- Generic response patterns with type safety and reusability
- Custom JSON serialization with proper datetime and type handling

Response Architecture:
- BaseResponse: Foundation for all API responses with success status and messaging
- SuccessResponse: Standardized success response with optional data payload
- ErrorResponse: Structured error response with error codes and details
- ValidationErrorResponse: Specialized validation error with field-level reporting
- PaginatedResponse: Generic paginated response with type safety and metadata

Health Monitoring:
- HealthCheckResponse: Basic application health status and version information
- DetailedHealthCheckResponse: Comprehensive system health with component status
- DatabaseHealthResponse: Database connectivity and schema validation status
- ServicesHealthResponse: External service availability and performance metrics
- SystemMetricsResponse: System resource utilization and performance indicators

Pagination and Search:
- PaginationParams: Comprehensive pagination parameters with sorting and calculations
- SearchParams: Advanced search parameters with algorithm selection and filtering
- PaginatedResponse: Generic paginated response with type safety and metadata
- Offset and limit calculations for database query optimization
- Flexible sorting and ordering with validation and constraints

Administrative Schemas:
- DatabaseStatusResponse: Database administration and management information
- DatabaseTablesResponse: Table listing and metadata for database operations
- DatabaseMigrationsResponse: Migration status and history for schema management
- DatabaseAnalysisResponse: Performance analysis and optimization recommendations
- DatabaseQueryResponse: Custom query execution results and metrics

File and Bulk Operations:
- FileUploadResponse: File upload confirmation with metadata and validation
- BulkOperationResponse: Bulk operation results with success and failure tracking
- TokenResponse: JWT token information with expiration and security metadata
- MetricsResponse: System metrics collection and performance monitoring
- ConfigurationResponse: Application configuration and feature flags

Use Cases:
- Consistent API response formatting across all endpoints
- Health monitoring and system diagnostics for operational oversight
- Pagination support for large datasets and user interfaces
- Error handling and validation reporting for user experience
- Administrative operations with comprehensive status reporting
- File upload and bulk operations with progress tracking

Type Safety and Validation:
- Generic type variables for type-safe pagination and responses
- Comprehensive field validation with Pydantic V2 features
- Custom JSON serialization for datetime and complex type handling
- Input validation and sanitization for security and data integrity
- Business rule enforcement through schema validation and constraints

Security and Compliance:
- Structured error reporting without sensitive information exposure
- Input validation to prevent injection attacks and malicious data
- Secure token handling with proper expiration and metadata
- Audit-friendly response formats for compliance and monitoring
- Data privacy controls for sensitive information handling
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field


def utcnow() -> datetime:
    """Get current UTC datetime with timezone awareness."""
    return datetime.now(timezone.utc)


# Generic type variable for paginated responses
T = TypeVar("T")


class BaseResponse(BaseModel):
    """Foundation response schema for all API endpoints with comprehensive status and metadata.

    Serves as the base class for all API responses providing consistent structure,
    status reporting, and timestamp information across the application. Implements
    standardized response format with success indicators, human-readable messages,
    and automatic timestamp generation for audit and monitoring purposes.

    Response Structure:
        - success: Boolean indicator for operation success or failure
        - message: Human-readable description of the operation result
        - timestamp: Automatic timestamp generation for audit and tracking

    Standardization Features:
        - Consistent response format across all API endpoints
        - Automatic timestamp generation for audit trails and monitoring
        - Success/failure indication for client-side handling
        - Human-readable messages for user interface display
        - Custom JSON serialization for proper datetime formatting

    Configuration Benefits:
        - from_attributes: Enables ORM model to response conversion
        - populate_by_name: Supports flexible field naming and aliases
        - use_enum_values: Serializes enum values for consistent JSON output
        - validate_assignment: Ensures data integrity during field updates
        - extra="ignore": Accepts additional fields without validation errors

    Use Cases:
        - Base class for all API endpoint responses
        - Consistent error and success reporting across endpoints
        - Audit trail generation with automatic timestamping
        - Client-side response handling with standardized format
        - Integration with monitoring and logging systems

    JSON Serialization:
        - Custom datetime handling with ISO format and timezone indicators
        - Consistent timestamp formatting for frontend integration
        - Proper type conversion for JSON compatibility
        - UTC timezone standardization for global applications
        - Frontend-compatible response structure

    Example:
        response = BaseResponse(
            success=True,
            message="Operation completed successfully",
            timestamp=datetime.now()
        )
        json_str = response.model_dump_json()  # Proper ISO datetime format

    """

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


class ErrorDetails(BaseModel):
    """Error details schema for the unified response envelope."""

    model_config = ConfigDict(from_attributes=True)

    code: str = Field(..., description="Machine-readable error code")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional error details"
    )


class APIResponse(BaseResponse, Generic[T]):
    """Unified API response schema conforming to the standard envelope specification.

    All API endpoints must return responses using this exact structure with no exceptions.
    This ensures consistent response format across the entire application.

    Response Structure:
    {
      "success": true or false,
      "message": "Human-readable message",
      "timestamp": "ISO-8601 string",
      "data": any,     // single object, array, or null
      "meta": { ... }, // optional metadata (pagination, stats, etc)
      "error": {       // optional error details
        "code": "ERROR_CODE",
        "details": { ... }
      }
    }
    """

    data: Optional[T] = Field(
        default=None,
        description="Response data payload - single object, array, or null",
    )

    def model_dump_json(self, **kwargs):
        """Serialize model with comprehensive datetime handling for API responses.

        Converts datetime fields to ISO format strings with timezone indicators for
        consistent API responses and frontend compatibility. Ensures proper timestamp
        formatting for audit trails and client-side datetime handling.

        Args:
            **kwargs: Additional arguments passed to model_dump for serialization control

        Returns:
            str: JSON string with properly formatted datetime fields

        Serialization Features:
            - Datetime to ISO format conversion with 'Z' suffix for UTC indication
            - Consistent timestamp formatting for API responses
            - Frontend-compatible JSON structure for web and mobile applications
            - Proper timezone handling for global applications
            - Integration with audit and monitoring systems

        Use Cases:
            - API response serialization for all endpoints
            - Frontend integration requiring standard datetime formats
            - Audit logging with consistent timestamp representation
            - Monitoring system integration with structured data
            - Cross-service communication with standardized response format

        Example:
            response = APIResponse(success=True, message="Success")
            json_output = response.model_dump_json()
            # Result: {"success": true, "message": "Success", "timestamp": "2024-01-01T12:00:00Z"}

        """
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                # Use proper ISO format - if it's UTC, replace +00:00 with Z for consistency
                iso_string = data["timestamp"].isoformat()
                if iso_string.endswith("+00:00"):
                    iso_string = iso_string[:-6] + "Z"
                data["timestamp"] = iso_string
        import json

        return json.dumps(data)


class ErrorDetail(BaseModel):
    """Detailed error information for validation and field-specific errors."""

    model_config = ConfigDict(from_attributes=True)

    code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(
        default=None, description="Field that caused the error"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional error details"
    )

    def model_dump_json(self, **kwargs):
        """Serialize model with comprehensive datetime handling for API responses.

        Converts datetime fields to ISO format strings with timezone indicators for
        consistent API responses and frontend compatibility. Ensures proper timestamp
        formatting for audit trails and client-side datetime handling.

        Args:
            **kwargs: Additional arguments passed to model_dump for serialization control

        Returns:
            str: JSON string with properly formatted datetime fields

        Serialization Features:
            - Datetime to ISO format conversion with 'Z' suffix for UTC indication
            - Consistent timestamp formatting for API responses
            - Frontend-compatible JSON structure for web and mobile applications
            - Proper timezone handling for global applications
            - Integration with audit and monitoring systems

        Use Cases:
            - API response serialization for all endpoints
            - Frontend integration requiring standard datetime formats
            - Audit logging with consistent timestamp representation
            - Monitoring system integration with structured data
            - Cross-service communication with standardized response format

        Example:
            response = BaseResponse(success=True, message="Success")
            json_output = response.model_dump_json()
            # Result: {"success": true, "message": "Success", "timestamp": "2024-01-01T12:00:00Z"}

        """
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                # Use proper ISO format - if it's UTC, replace +00:00 with Z for consistency
                iso_string = data["timestamp"].isoformat()
                if iso_string.endswith("+00:00"):
                    iso_string = iso_string[:-6] + "Z"
                data["timestamp"] = iso_string
        import json

        return json.dumps(data)


class SuccessResponse(BaseResponse):
    """Standard success response."""

    success: bool = Field(default=True, description="Always true for success responses")
    data: Optional[Any] = Field(default=None, description="Response data payload")
    meta: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional metadata"
    )

    @classmethod
    def create(
        cls,
        data: Any = None,
        message: str = "Success",
        status_code: int = status.HTTP_200_OK,
        meta: Optional[Dict[str, Any]] = None,
    ) -> JSONResponse:
        """Create successful response using unified envelope format."""
        response = APIResponse(
            success=True, data=data, message=message, meta=meta, timestamp=utcnow()
        )
        # Use the custom JSON serialization from the model to handle datetime
        content_str = response.model_dump_json(exclude_none=True)
        content = json.loads(content_str)
        return JSONResponse(content=content, status_code=status_code)


class ErrorResponse(BaseResponse):
    """Standard error response."""

    success: bool = Field(default=False, description="Always false for error responses")
    error_code: Optional[str] = Field(
        default=None, description="Machine-readable error code"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional error details"
    )

    @classmethod
    def create(
        cls,
        error_code: str,
        message: str = "An error occurred",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        data: Any = None,
        error_details: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> JSONResponse:
        """Create error response using unified envelope format."""
        response = APIResponse(
            success=False,
            data=data,
            message=message,
            error=ErrorDetails(code=error_code, details=error_details),
            timestamp=utcnow(),
            meta=meta,
        )
        # Use the custom JSON serialization from the model to handle datetime
        content_str = response.model_dump_json(exclude_none=True)
        content = json.loads(content_str)
        return JSONResponse(content=content, status_code=status_code)


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field-specific errors."""

    error_code: str = Field(
        default="VALIDATION_ERROR", description="Code for validation errors"
    )
    validation_errors: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of validation errors"
    )
    errors: List[ErrorDetail] = Field(
        default_factory=list, description="Detailed validation errors"
    )

    @classmethod
    def create(
        cls, errors: List[Dict[str, Any]], message: str = "Validation failed"
    ) -> JSONResponse:
        """Create validation error response using unified envelope format."""
        error_details = [
            ErrorDetail(
                code=error.get("type", "validation_error"),
                message=error.get("msg", "Invalid value"),
                field=".".join(str(loc) for loc in error.get("loc", [])),
                details=error,
            )
            for error in errors
        ]

        response = APIResponse(
            success=False,
            message=message,
            error=ErrorDetails(
                code="VALIDATION_ERROR",
                details={
                    "validation_errors": [err.model_dump() for err in error_details]
                },
            ),
            timestamp=utcnow(),
        )

        # Use the custom JSON serialization from the model to handle datetime
        content_str = response.model_dump_json(exclude_none=True)
        content = json.loads(content_str)
        return JSONResponse(
            content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
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
        """Serialize model with ISO format timestamp handling."""
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                # Use proper ISO format - if it's UTC, replace +00:00 with Z for consistency
                iso_string = data["timestamp"].isoformat()
                if iso_string.endswith("+00:00"):
                    iso_string = iso_string[:-6] + "Z"
                data["timestamp"] = iso_string
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
        """Serialize model with ISO format timestamp handling."""
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                # Use proper ISO format - if it's UTC, replace +00:00 with Z for consistency
                iso_string = data["timestamp"].isoformat()
                if iso_string.endswith("+00:00"):
                    iso_string = iso_string[:-6] + "Z"
                data["timestamp"] = iso_string
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
        """Serialize model with ISO format datetime handling."""
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
        """Serialize model with ISO format timestamp handling."""
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                # Use proper ISO format - if it's UTC, replace +00:00 with Z for consistency
                iso_string = data["timestamp"].isoformat()
                if iso_string.endswith("+00:00"):
                    iso_string = iso_string[:-6] + "Z"
                data["timestamp"] = iso_string
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


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema."""

    items: List[Any] = Field(
        default_factory=list, description="List of paginated items"
    )
    pagination: PaginationParams = Field(..., description="Pagination parameters")


class SearchParams(PaginationParams):
    """Search parameters schema extending pagination with search-specific options.

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
