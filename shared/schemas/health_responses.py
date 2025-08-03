"""
Pydantic response schemas for health monitoring API endpoints.

This module provides response models for all health-related endpoints that currently
return raw dictionaries, ensuring type safety and proper API documentation.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .base import BaseModelSchema


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
    not_ready_components: List[str] = Field(default_factory=list, description="Not ready components")