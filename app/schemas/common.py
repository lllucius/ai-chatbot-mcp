"Pydantic schemas for common data validation."

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel, ConfigDict, Field
from ..utils.timestamp import utcnow

T = TypeVar("T")


class BaseResponse(BaseModel):
    "BaseResponse schema for data validation and serialization."

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
        "Model Dump Json operation."
        data = self.model_dump(**kwargs)
        if ("timestamp" in data) and (data["timestamp"] is not None):
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json

        return json.dumps(data)


class SuccessResponse(BaseResponse):
    "SuccessResponse schema for data validation and serialization."

    success: bool = Field(default=True, description="Always true for success responses")
    data: Optional[Dict[(str, Any)]] = Field(
        default=None, description="Response data payload"
    )


class ErrorResponse(BaseResponse):
    "ErrorResponse schema for data validation and serialization."

    success: bool = Field(default=False, description="Always false for error responses")
    error_code: Optional[str] = Field(
        default=None, description="Machine-readable error code"
    )
    details: Optional[Dict[(str, Any)]] = Field(
        default=None, description="Additional error details"
    )


class ValidationErrorResponse(ErrorResponse):
    "ValidationErrorResponse schema for data validation and serialization."

    error_code: str = Field(default="VALIDATION_ERROR")
    validation_errors: List[Dict[(str, Any)]] = Field(
        default_factory=list, description="List of validation errors"
    )


class HealthCheckResponse(BaseResponse):
    "HealthCheckResponse schema for data validation and serialization."

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    status: str = Field(description="Overall health status")
    version: str = Field(description="Application version")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Health check timestamp"
    )
    components: Optional[Dict[(str, Any)]] = Field(
        default=None, description="Individual component health statuses"
    )

    def model_dump_json(self, **kwargs):
        "Model Dump Json operation."
        data = self.model_dump(**kwargs)
        if ("timestamp" in data) and (data["timestamp"] is not None):
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json

        return json.dumps(data)


class FileUploadResponse(BaseResponse):
    "FileUploadResponse schema for data validation and serialization."

    filename: str = Field(description="Original filename")
    file_id: Optional[str] = Field(default=None, description="Generated file ID")
    file_size: int = Field(description="File size in bytes")
    content_type: Optional[str] = Field(default=None, description="MIME content type")
    upload_url: Optional[str] = Field(
        default=None, description="URL where file was uploaded"
    )


class BulkOperationResponse(BaseResponse):
    "BulkOperationResponse schema for data validation and serialization."

    total_items: int = Field(description="Total number of items processed")
    successful_items: int = Field(description="Number of successfully processed items")
    failed_items: int = Field(description="Number of failed items")
    errors: List[Dict[(str, Any)]] = Field(
        default_factory=list, description="List of errors that occurred"
    )


class TokenResponse(BaseModel):
    "TokenResponse schema for data validation and serialization."

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration time in seconds")
    expires_at: datetime = Field(description="Token expiration timestamp")

    def model_dump_json(self, **kwargs):
        "Model Dump Json operation."
        data = self.model_dump(**kwargs)
        if ("expires_at" in data) and (data["expires_at"] is not None):
            if isinstance(data["expires_at"], datetime):
                data["expires_at"] = data["expires_at"].isoformat() + "Z"
        import json

        return json.dumps(data)


class MetricsResponse(BaseModel):
    "MetricsResponse schema for data validation and serialization."

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
        "Model Dump Json operation."
        data = self.model_dump(**kwargs)
        if ("timestamp" in data) and (data["timestamp"] is not None):
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json

        return json.dumps(data)


class ConfigurationResponse(BaseModel):
    "ConfigurationResponse schema for data validation and serialization."

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    app_name: str = Field(description="Application name")
    app_version: str = Field(description="Application version")
    debug_mode: bool = Field(description="Whether debug mode is enabled")
    environment: str = Field(description="Runtime environment")
    features: Dict[(str, bool)] = Field(description="Enabled features")
    limits: Dict[(str, Union[(int, float)])] = Field(description="Configuration limits")


class PaginationParams(BaseModel):
    "PaginationParams class for specialized functionality."

    model_config = ConfigDict(from_attributes=True, validate_assignment=True)
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=10, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: Optional[str] = Field(
        default="asc", pattern="^(asc|desc)$", description="Sort order: asc or desc"
    )


class PaginatedResponse(BaseResponse, Generic[T]):
    "PaginatedResponse schema for data validation and serialization."

    items: List[Any] = Field(default_factory=list)
    pagination: PaginationParams

    @classmethod
    def create(
        cls, items: List[Any], page: int, size: int, total: int, message: str
    ) -> "PaginatedResponse":
        "Create operation."
        return cls(
            success=True,
            message=message,
            items=items,
            pagination=PaginationParams(page=page, per_page=size),
        )


class SearchParams(PaginationParams):
    "SearchParams class for specialized functionality."

    query: Optional[str] = Field(
        default=None, min_length=1, max_length=500, description="Search query string"
    )
    algorithm: Optional[str] = Field(
        default="hybrid",
        pattern="^(vector|text|hybrid|mmr)$",
        description="Search algorithm to use",
    )
    limit: Optional[int] = Field(
        default=10, ge=1, le=50, description="Number of results to return"
    )
    threshold: Optional[float] = Field(
        default=0.7, ge=0.0, le=1.0, description="Threshold to use"
    )
    filters: Optional[Dict[(str, Any)]] = Field(
        default=None, description="Additional search filters"
    )
