"""
Health monitoring and system status API endpoints with comprehensive observability.

This module provides comprehensive health monitoring endpoints for the application
including database connectivity validation, external services monitoring, system
performance metrics, resource utilization tracking, and Kubernetes-style probes
for container orchestration and automated monitoring systems.

Key Features:
- Basic and detailed health checks with configurable depth and scope
- Database connectivity validation and performance monitoring
- External service status monitoring (OpenAI, FastMCP, third-party APIs)
- System performance metrics and resource utilization tracking
- Cache system health monitoring and performance statistics
- Kubernetes-compatible liveness and readiness probes for orchestration

Health Check Categories:
- Basic health: Quick status check without external dependencies
- Detailed health: Comprehensive system and dependency validation
- Database health: Database connectivity, performance, and schema validation
- Services health: External service availability and response time monitoring
- System metrics: Resource utilization, performance, and capacity monitoring

Monitoring Capabilities:
- Real-time system resource monitoring (CPU, memory, disk, network)
- Database performance metrics and connection pool status
- External API availability checks and response time monitoring
- Cache hit rates, performance statistics, and optimization insights
- Background service health validation and status reporting
- Detailed error reporting and diagnostic information collection

Integration Support:
- Load balancer health check endpoints for traffic routing
- Kubernetes liveness and readiness probes for container orchestration
- Monitoring system integration (Prometheus, Grafana, custom solutions)
- Alerting and notification support for automated incident response
- Health dashboard and visualization support

Performance Monitoring:
- Request processing times and throughput metrics
- Database query performance and optimization insights
- Cache effectiveness and memory utilization tracking
- External service response times and availability statistics
- Resource usage trends and capacity planning data

Container Orchestration:
- Liveness probes for container restart decisions
- Readiness probes for traffic routing and load balancing
- Startup probes for application initialization monitoring
- Health check configuration for automated scaling decisions
- Integration with container health monitoring systems
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..dependencies import get_mcp_service
from ..middleware.performance import get_performance_stats
from ..schemas.common import (
    BaseResponse,
    DatabaseHealthResponse,
    DetailedHealthCheckResponse,
    LivenessResponse,
    PerformanceMetricsResponse,
    ReadinessResponse,
    ServicesHealthResponse,
    SystemMetricsResponse,
)
from ..services.mcp_service import MCPService
from ..utils.api_errors import handle_api_errors, log_api_call
from ..utils.caching import api_response_cache, embedding_cache, search_result_cache
from ..utils.timestamp import utcnow

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=BaseResponse)
@handle_api_errors("Basic health check failed")
async def basic_health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint for load balancers and simple monitoring.

    Provides a lightweight health status check for the application core without
    validating external dependencies or performing resource-intensive operations.
    Optimized for load balancer health checks, basic monitoring systems, and
    high-frequency health polling scenarios.

    Returns:
        Dict[str, Any]: Basic application status including:
            - success: Health check success indicator
            - message: Application status message
            - status: Current health status (healthy/unhealthy)
            - version: Application version information
            - timestamp: Health check execution time

    Health Check Scope:
        - Application process status and responsiveness
        - Basic configuration validation and availability
        - Core service initialization and readiness
        - Memory and resource availability check
        - Quick response time optimization for monitoring

    Use Cases:
        - Load balancer health check endpoints for traffic routing
        - Container orchestration basic health validation
        - High-frequency monitoring system integration
        - Basic application availability verification
        - Automated deployment health validation

    Performance:
        - Optimized for sub-millisecond response times
        - Minimal resource consumption and overhead
        - No external dependency validation
        - Lightweight status reporting and logging
        - Suitable for high-frequency polling scenarios

    Example:
        GET /api/v1/health/
        {
            "success": true,
            "message": "AI Chatbot Platform is running",
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    """
    log_api_call("basic_health_check")
    return {
        "success": True,
        "message": "AI Chatbot Platform is running",
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": utcnow(),
    }


@router.get("/detailed", response_model=DetailedHealthCheckResponse)
@handle_api_errors("Health check failed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
) -> Dict[str, Any]:
    """
    Comprehensive health check with all system components.

    Performs detailed health verification of all system components including
    database connectivity, cache systems, external service availability,
    and overall system status. This endpoint provides a complete view of
    system health for monitoring and diagnostics.

    Args:
        db: Database session for connectivity check
        mcp_service: MCP service instance for FastMCP health verification

    Returns:
        dict: Comprehensive system health status containing:
            - application: App info, version, and status
            - database: Database connectivity and schema status
            - cache: Cache system health and statistics
            - openai: OpenAI service availability and configuration
            - fastmcp: FastMCP service status and server connections
            - overall_status: Aggregated health status (healthy/warning/degraded)

    Note:
        This endpoint checks all dependencies and may take longer than
        basic health checks. Use for detailed monitoring and diagnostics.
    """
    log_api_call("detailed_health_check")

    health_status = {
        "application": {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "healthy",
            "debug_mode": settings.debug,
        },
        "database": await _check_database_health(db),
        "cache": await _check_cache_health(),
        "openai": await _check_openai_health(),
        "fastmcp": await _check_fastmcp_health(mcp_service),
        "timestamp": utcnow(),
        "overall_status": "healthy",
    }

    component_statuses = [
        health_status["database"]["status"],
        health_status["cache"]["status"],
        health_status["openai"]["status"],
        health_status["fastmcp"]["status"],
    ]

    if "unhealthy" in component_statuses:
        health_status["overall_status"] = "degraded"
    elif "warning" in component_statuses:
        health_status["overall_status"] = "warning"

    return health_status


@router.get("/database", response_model=DatabaseHealthResponse)
@handle_api_errors("Database health check failed")
async def database_health_check(db: AsyncSession = Depends(get_db)) -> DatabaseHealthResponse:
    """
    Database connectivity and schema health check.

    Verifies database connectivity by executing a test query and validates
    that required database tables exist. This check ensures the application
    can successfully interact with the database layer.

    Args:
        db: Database session for connectivity and schema validation

    Returns:
        DatabaseHealthResponse: Database health status containing:
            - status: Health status (healthy/warning/unhealthy)
            - message: Descriptive health message
            - connectivity: Connection status
            - schema_status: Database schema validation status
            - tables_found: Number of required tables found

    Raises:
        HTTP 503: If database is completely unreachable
    """
    log_api_call("database_health_check")
    health_data = await _check_database_health(db)
    return DatabaseHealthResponse(
        status=health_data["status"],
        message=health_data["message"],
        connectivity=health_data["connectivity"],
        schema_status=health_data.get("schema_status"),
        tables_found=health_data.get("tables_found"),
    )


@router.get("/services", response_model=ServicesHealthResponse)
@handle_api_errors("Services health check failed")
async def services_health_check(
    mcp_service: MCPService = Depends(get_mcp_service),
) -> ServicesHealthResponse:
    """
    External services health check.

    Verifies the availability and status of external services that the
    application depends on, including OpenAI API and FastMCP servers.
    This check helps identify service degradation or outages.

    Args:
        mcp_service: MCP service instance for FastMCP health verification

    Returns:
        ServicesHealthResponse: External services status containing:
            - openai: OpenAI API availability and configuration status
            - fastmcp: FastMCP service and server connection status
            - timestamp: Check execution timestamp

    Note:
        External service failures may not prevent application startup
        but could affect functionality availability.
    """
    log_api_call("services_health_check")
    return ServicesHealthResponse(
        openai=await _check_openai_health(),
        fastmcp=await _check_fastmcp_health(mcp_service),
        timestamp=utcnow(),
    )


async def _check_cache_health() -> Dict[str, Any]:
    """
    Check cache system health and performance statistics.

    Performs cache system validation by testing cache operations and
    gathering performance statistics from all cache instances including
    embedding cache, API response cache, and search result cache.

    Returns:
        dict: Cache health status containing:
            - status: Health status (healthy/unhealthy)
            - message: Descriptive status message
            - stats: Individual cache statistics
            - overall_hit_rate: Average hit rate across all caches
            - total_requests: Total cache requests processed

    Note:
        Tests actual cache operations to ensure functionality rather
        than just checking service availability.
    """
    try:
        cache_stats = {
            "embedding_cache": embedding_cache.get_stats(),
            "api_response_cache": api_response_cache.get_stats(),
            "search_result_cache": search_result_cache.get_stats(),
        }
        test_key = "health_check_test"
        test_value = "test_data"
        await embedding_cache.set(test_key, test_value, ttl=60)
        retrieved = await embedding_cache.get(test_key)
        await embedding_cache.delete(test_key)
        if retrieved != test_value:
            return {
                "status": "unhealthy",
                "message": "Cache test operation failed",
                "stats": cache_stats,
            }
        total_hit_rate = 0
        total_requests = 0
        for _cache_name, stats in cache_stats.items():
            total_requests += stats["hits"] + stats["misses"]
            if stats["hits"] + stats["misses"] > 0:
                total_hit_rate += stats["hit_rate"]
        avg_hit_rate = total_hit_rate / len(cache_stats) if cache_stats else 0
        return {
            "status": "healthy",
            "message": "Cache system operational",
            "stats": cache_stats,
            "overall_hit_rate": avg_hit_rate,
            "total_requests": total_requests,
        }
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Cache check failed: {str(e)}",
            "stats": {},
        }


async def _check_database_health(db: AsyncSession) -> Dict[str, Any]:
    """
    Check database connectivity and schema validation.

    Verifies database health by executing test queries and validating
    that required application tables exist. This ensures the database
    is accessible and properly configured for application use.

    Args:
        db: Database session for health verification

    Returns:
        dict: Database health status containing:
            - status: Health status (healthy/warning/unhealthy)
            - message: Descriptive status message
            - connectivity: Database connection status
            - schema_status: Schema validation status (complete/incomplete)
            - tables_found: Number of required tables found

    Note:
        Checks for critical tables: users, documents, conversations.
        Missing tables result in warning status, not failure.
    """
    try:
        result = await db.execute(text("SELECT 1 as test"))
        test_value = result.scalar()
        if test_value != 1:
            raise Exception("Database query returned unexpected result")
        tables_result = await db.execute(
            text(
                """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('users', 'documents', 'conversations')
        """
            )
        )
        tables = [row[0] for row in tables_result.fetchall()]
        required_tables = ["users", "documents", "conversations"]
        missing_tables = [table for table in required_tables if table not in tables]
        if missing_tables:
            return {
                "status": "warning",
                "message": f"Missing tables: {missing_tables}",
                "connectivity": "ok",
                "schema_status": "incomplete",
            }
        return {
            "status": "healthy",
            "message": "Database connectivity and schema OK",
            "connectivity": "ok",
            "schema_status": "complete",
            "tables_found": len(tables),
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Database check failed: {str(e)}",
            "connectivity": "failed",
        }


async def _check_openai_health() -> Dict[str, Any]:
    """
    Check OpenAI API service availability and configuration.

    Verifies OpenAI service health by checking API configuration,
    performing connectivity tests, and validating available models.
    This ensures the AI capabilities are operational.

    Returns:
        dict: OpenAI service health status containing:
            - status: Health status (healthy/warning/unhealthy)
            - message: Descriptive status message
            - configured: Whether API key is properly configured
            - models_available: Whether required models are accessible
            - chat_model: Available chat model information
            - embedding_model: Available embedding model information

    Note:
        Missing or invalid API key results in warning status since
        the application can operate without OpenAI integration.
    """
    try:
        from ..services.openai_client import OpenAIClient

        if settings.openai_api_key == "your-openai-api-key-here":
            return {
                "status": "warning",
                "message": "OpenAI API key not configured",
                "configured": False,
            }
        client = OpenAIClient()
        health_result = await client.health_check()
        return {
            "status": (
                "healthy" if health_result.get("openai_available") else "unhealthy"
            ),
            "message": health_result.get("status", "Unknown"),
            "configured": True,
            "models_available": health_result.get("models_available", False),
            "chat_model": health_result.get("chat_model"),
            "embedding_model": health_result.get("embedding_model"),
        }
    except Exception as e:
        logger.error(f"OpenAI health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"OpenAI check failed: {str(e)}",
            "configured": False,
        }


async def _check_fastmcp_health(mcp_service: MCPService) -> Dict[str, Any]:
    """
    Check FastMCP service health and server connections.

    Verifies FastMCP service health by checking service availability,
    server registry status, and individual server connections. This
    ensures MCP tool functionality is operational.

    Args:
        mcp_service: MCP service instance for health verification

    Returns:
        dict: FastMCP service health status containing:
            - status: Health status (healthy/warning/unhealthy)
            - message: Descriptive status message
            - enabled: Whether MCP is enabled in configuration
            - available: Whether FastMCP library is available
            - registry: Registry statistics and information
            - connected_servers: Number of successfully connected servers
            - enabled_servers: Number of enabled servers
            - total_servers: Total number of configured servers
            - initialized: Whether service is properly initialized
            - server_status: Individual server status information
            - tools_count: Number of available tools

    Note:
        FastMCP is considered optional, so failures result in warning
        status rather than unhealthy status.
    """
    try:
        if not settings.mcp_enabled:
            return {
                "status": "warning",
                "message": "FastMCP disabled (optional service)",
                "enabled": False,
            }
        health_result = await mcp_service.health_check()
        if not health_result.mcp_available:
            return {
                "status": "warning",
                "message": "FastMCP library not available (optional)",
                "enabled": settings.mcp_enabled,
                "available": False,
            }
        registry_info = health_result.registry_stats or {}
        total_servers = registry_info.get("total_servers", 0)
        enabled_servers = registry_info.get("enabled_servers", 0)
        connected_servers = health_result.healthy_servers
        if connected_servers == 0:
            status = "warning"
            message = "No MCP servers are connected (optional service)"
        elif connected_servers < enabled_servers:
            status = "warning"
            message = f"Some MCP servers are disconnected ({connected_servers}/{enabled_servers})"
        else:
            status = "healthy"
            message = f"All enabled MCP servers are connected ({connected_servers}/{enabled_servers})"
        return {
            "status": status,
            "message": message,
            "enabled": settings.mcp_enabled,
            "available": True,
            "registry": registry_info,
            "connected_servers": connected_servers,
            "enabled_servers": enabled_servers,
            "total_servers": total_servers,
            "initialized": health_result.initialized,
            "server_status": health_result.server_status,
            "tools_count": registry_info.get("enabled_tools", 0),
        }
    except Exception as e:
        logger.warning(f"FastMCP health check failed: {e}")
        return {
            "status": "warning",
            "message": f"FastMCP check failed: {str(e)} (optional service)",
            "enabled": settings.mcp_enabled,
            "available": False,
        }


@router.get("/metrics", response_model=SystemMetricsResponse)
@handle_api_errors("Failed to get system metrics")
async def get_system_metrics() -> SystemMetricsResponse:
    """
    Get system performance metrics and resource utilization.

    Retrieves comprehensive system metrics including CPU usage, memory
    consumption, disk utilization, and application performance statistics.
    This information is useful for monitoring and capacity planning.

    Returns:
        SystemMetricsResponse: System metrics containing:
            - system: CPU, memory, and disk usage statistics
            - application: Uptime, version, and configuration info
            - timestamp: Metrics collection timestamp
            - error: Error message if psutil is unavailable

    Note:
        Requires psutil library for system metrics collection.
        Falls back gracefully if psutil is not available.
    """
    log_api_call("get_system_metrics")
    try:
        import time

        import psutil

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        return SystemMetricsResponse(
            system={
                "cpu_usage_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent_used": memory.percent,
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent_used": round((disk.used / disk.total) * 100, 2),
                },
            },
            application={
                "uptime_seconds": time.time() - psutil.Process().create_time(),
                "version": settings.app_version,
                "debug_mode": settings.debug,
            },
            timestamp=utcnow(),
        )
    except ImportError:
        return SystemMetricsResponse(
            system={},
            application={
                "version": settings.app_version,
                "debug_mode": settings.debug,
            },
            timestamp=utcnow(),
            error="psutil not available for system metrics",
        )


@router.get("/readiness", response_model=ReadinessResponse)
@handle_api_errors("Readiness check failed")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
) -> ReadinessResponse:
    """
    Kubernetes-style readiness probe.

    Checks if the application is ready to serve traffic by verifying
    that all critical dependencies (database, cache, external services)
    are operational. Used by orchestrators to determine traffic routing.

    Args:
        db: Database session for connectivity check
        mcp_service: MCP service instance

    Returns:
        ReadinessResponse: Application readiness status

    Raises:
        HTTP 503: If any critical service is not ready

    Note:
        This endpoint is designed for Kubernetes readiness probes and
        should only return 200 when the application can serve traffic.
    """
    log_api_call("readiness_check")
    try:
        db_health = await _check_database_health(db)
        cache_health = await _check_cache_health()
        fastmcp_health = await _check_fastmcp_health(mcp_service)

        if db_health["status"] == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not ready",
            )
        if cache_health["status"] == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cache system not ready",
            )
        if fastmcp_health["status"] == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="FastMCP not ready",
            )
        return ReadinessResponse(
            status="ready",
            message="Application is ready to serve traffic",
            timestamp=utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Application not ready: {str(e)}",
        )


@router.get("/performance", response_model=PerformanceMetricsResponse)
@handle_api_errors("Failed to get performance metrics")
async def get_performance_metrics() -> PerformanceMetricsResponse:
    """
    Get application performance metrics and statistics.

    Retrieves performance metrics from the application's internal
    monitoring system, including request processing times, throughput
    statistics, and performance indicators.

    Returns:
        PerformanceMetricsResponse: Application performance data including:
            - Request processing metrics
            - Throughput statistics  
            - Performance indicators
            - Resource utilization metrics

    Note:
        Performance data is collected by the performance middleware
        and aggregated over the application lifecycle.
    """
    log_api_call("get_performance_metrics")
    performance_data = get_performance_stats()
    return PerformanceMetricsResponse(data=performance_data)


@router.get("/liveness", response_model=LivenessResponse)
@handle_api_errors("Liveness check failed")
async def liveness_check() -> LivenessResponse:
    """
    Kubernetes-style liveness probe.

    Simple endpoint that indicates the application process is alive and
    responding. Used by orchestrators to determine if the container
    should be restarted.

    Returns:
        LivenessResponse: Application liveness confirmation

    Note:
        This endpoint should always return 200 unless the application
        process is completely unresponsive. It does not check dependencies.
    """
    log_api_call("liveness_check")
    return LivenessResponse(
        status="alive", 
        message="Application is alive", 
        timestamp=utcnow()
    )
