"""Pydantic response schemas for health monitoring API endpoints.

This module provides response models for all health-related endpoints that currently
return raw dictionaries, ensuring type safety and proper API documentation.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .base import serialize_datetime_to_iso


class CacheStats(BaseModel):
    """Individual cache statistics."""

    hits: int = Field(..., description="Number of cache hits")
    misses: int = Field(..., description="Number of cache misses")
    hit_rate: float = Field(..., description="Cache hit rate percentage")
    total_requests: int = Field(..., description="Total number of requests")


class CacheHealthData(BaseModel):
    """Cache system health data."""

    status: str = Field(..., description="Cache system status")
    message: str = Field(..., description="Health status message")
    stats: Dict[str, CacheStats] = Field(default_factory=dict, description="Cache statistics by cache name")
    overall_hit_rate: Optional[float] = Field(default=None, description="Overall hit rate across all caches")
    total_requests: Optional[int] = Field(default=None, description="Total requests across all caches")


class DatabaseTableInfo(BaseModel):
    """Database table information."""

    name: str = Field(..., description="Table name")
    exists: bool = Field(..., description="Whether table exists")


class DatabaseHealthData(BaseModel):
    """Database health check data."""

    status: str = Field(..., description="Database connection status")
    message: str = Field(..., description="Health status message")
    version: Optional[str] = Field(default=None, description="Database version")
    connection_pool_size: Optional[int] = Field(default=None, description="Connection pool size")
    active_connections: Optional[int] = Field(default=None, description="Active connections")
    tables: Optional[List[str]] = Field(default=None, description="Available tables")
    missing_tables: Optional[List[str]] = Field(default=None, description="Missing required tables")
    response_time_ms: Optional[float] = Field(default=None, description="Database response time in milliseconds")


class ServiceStatus(BaseModel):
    """Individual service status."""

    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    response_time_ms: Optional[float] = Field(default=None, description="Response time in milliseconds")
    error: Optional[str] = Field(default=None, description="Error message if service is down")


class ServicesHealthData(BaseModel):
    """External services health data."""

    status: str = Field(..., description="Overall services status")
    message: str = Field(..., description="Health status message")
    services: List[ServiceStatus] = Field(default_factory=list, description="Individual service statuses")
    total_services: int = Field(..., description="Total number of services checked")
    healthy_services: int = Field(..., description="Number of healthy services")


class SystemResourceMetrics(BaseModel):
    """System resource metrics."""

    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_percent: float = Field(..., description="Memory usage percentage")
    disk_percent: float = Field(..., description="Disk usage percentage")
    memory_used_mb: float = Field(..., description="Memory used in MB")
    memory_total_mb: float = Field(..., description="Total memory in MB")
    disk_used_gb: float = Field(..., description="Disk used in GB")
    disk_total_gb: float = Field(..., description="Total disk space in GB")


class SystemMetricsData(BaseModel):
    """System metrics data."""

    status: str = Field(..., description="System status")
    message: str = Field(..., description="Status message")
    resources: SystemResourceMetrics = Field(..., description="Resource usage metrics")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    load_average: Optional[List[float]] = Field(default=None, description="System load average")
    timestamp: str = Field(..., description="Metrics timestamp")


class DetailedHealthCheckData(BaseModel):
    """Detailed health check aggregated data."""

    status: str = Field(..., description="Overall health status")
    message: str = Field(..., description="Health status message")
    timestamp: str = Field(..., description="Health check timestamp")
    database: DatabaseHealthData = Field(..., description="Database health information")
    cache: CacheHealthData = Field(..., description="Cache system health information")
    services: ServicesHealthData = Field(..., description="External services health information")
    system: SystemMetricsData = Field(..., description="System metrics information")
    components_healthy: int = Field(..., description="Number of healthy components")
    total_components: int = Field(..., description="Total number of components checked")


class PerformanceMetricsData(BaseModel):
    """Performance metrics data."""

    status: str = Field(..., description="Performance status")
    message: str = Field(..., description="Status message")
    avg_response_time_ms: float = Field(..., description="Average response time in milliseconds")
    total_requests: int = Field(..., description="Total number of requests processed")
    requests_per_second: float = Field(..., description="Requests per second rate")
    error_rate: float = Field(..., description="Error rate percentage")
    timestamp: str = Field(..., description="Metrics timestamp")


class LivenessProbeData(BaseModel):
    """Liveness probe data."""

    status: str = Field(default="healthy", description="Liveness status")
    message: str = Field(default="Service is alive", description="Liveness message")
    timestamp: str = Field(..., description="Probe timestamp")


class ReadinessProbeData(BaseModel):
    """Readiness probe data."""

    status: str = Field(..., description="Readiness status")
    message: str = Field(..., description="Readiness message")
    timestamp: str = Field(..., description="Probe timestamp")
    ready_components: List[str] = Field(default_factory=list, description="Ready components")


# --- Additional Health Response Models moved from common.py ---


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
        default_factory=lambda: datetime.now(timezone.utc), description="Health check timestamp"
    )

    def model_dump_json(self, **kwargs):
        """Serialize model with ISO format timestamp handling."""
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = serialize_datetime_to_iso(data["timestamp"])
        import json
        return json.dumps(data)


class SystemMetricsResponse(BaseModel):
    """System metrics response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    system: Dict[str, Any] = Field(..., description="System metrics")
    application: Dict[str, Any] = Field(..., description="Application metrics")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Metrics collection timestamp"
    )
    error: Optional[str] = Field(default=None, description="Error message if metrics unavailable")

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


class ReadinessResponse(BaseModel):
    """Readiness check response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    status: str = Field(..., description="Readiness status")
    message: str = Field(..., description="Readiness message")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Check timestamp"
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
        default_factory=lambda: datetime.now(timezone.utc), description="Check timestamp"
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
    not_ready_components: List[str] = Field(default_factory=list, description="Not ready components")

class OpenAIHealthData(BaseModel):
    """OpenAI service health data."""

    status: str = Field(..., description="OpenAI service status")
    message: str = Field(..., description="Health status message")
    configured: bool = Field(default=False, description="Whether API key is configured")
    models_available: Optional[bool] = Field(default=None, description="Whether required models are accessible")
    chat_model: Optional[str] = Field(default=None, description="Available chat model information")
    embedding_model: Optional[str] = Field(default=None, description="Available embedding model information")


class FastMCPHealthData(BaseModel):
    """FastMCP service health data."""

    status: str = Field(..., description="FastMCP service status")
    message: str = Field(..., description="Health status message")
    enabled: bool = Field(..., description="Whether MCP is enabled in configuration")
    available: Optional[bool] = Field(default=None, description="Whether FastMCP library is available")
    registry: Optional[Dict[str, Any]] = Field(default=None, description="Registry statistics and information")
    connected_servers: Optional[int] = Field(default=None, description="Number of successfully connected servers")
    enabled_servers: Optional[int] = Field(default=None, description="Number of enabled servers")
    total_servers: Optional[int] = Field(default=None, description="Total number of configured servers")
    initialized: Optional[bool] = Field(default=None, description="Whether service is properly initialized")
    server_status: Optional[Dict[str, Any]] = Field(default=None, description="Individual server status information")
    tools_count: Optional[int] = Field(default=None, description="Number of available tools")


class ApplicationHealthData(BaseModel):
    """Application health status information."""

    name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    status: str = Field(..., description="Application health status")
    debug_mode: bool = Field(..., description="Whether debug mode is enabled")


class DetailedHealthCheckPayload(BaseModel):
    """Comprehensive health check payload."""

    application: ApplicationHealthData = Field(..., description="App info")
    database: DatabaseHealthData = Field(..., description="Database health")
    cache: CacheHealthData = Field(..., description="Cache health")
    openai: OpenAIHealthData = Field(..., description="OpenAI health")
    fastmcp: FastMCPHealthData = Field(..., description="FastMCP health")
    overall_status: str = Field(..., description="Overall system status")


class ServicesHealthPayload(BaseModel):
    """External services health payload."""

    openai: OpenAIHealthData = Field(..., description="OpenAI health")
    fastmcp: FastMCPHealthData = Field(..., description="FastMCP health")


class SystemMetricsPayload(BaseModel):
    """System metrics and resource utilization."""

    system: Dict[str, Any] = Field(..., description="System metrics (typed below)")
    application: Dict[str, Any] = Field(..., description="App metrics (typed below)")


class ReadinessComponentsPayload(BaseModel):
    """Payload for readiness check."""

    status: str = Field(..., description="Readiness status")
    components: Dict[str, Any] = Field(..., description="Readiness details")


class PerformanceMetricsPayload(BaseModel):
    """Performance metrics payload."""

    performance: Dict[str, Any] = Field(..., description="Performance metrics")


class LivenessPayload(BaseModel):
    """Liveness status payload."""

    status: str = Field(..., description="Liveness status")


