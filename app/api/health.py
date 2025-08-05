"""Health monitoring and system status API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.common import APIResponse
from shared.schemas.health_responses import (
    ApplicationHealthData,
    CacheHealthData,
    CacheStats,
    DatabaseHealthData,
    DetailedHealthCheckPayload,
    FastMCPHealthData,
    LivenessPayload,
    OpenAIHealthData,
    PerformanceMetricsPayload,
    ReadinessComponentsPayload,
    ServicesHealthPayload,
    SystemMetricsPayload,
)

from ..config import settings
from ..database import get_db
from ..dependencies import get_mcp_service
from ..middleware.performance import get_performance_stats
from ..services.mcp_service import MCPService
from ..utils.api_errors import handle_api_errors, log_api_call
from ..utils.caching import api_response_cache, embedding_cache, search_result_cache

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=APIResponse[ApplicationHealthData])
@handle_api_errors("Basic health check failed")
async def basic_health_check() -> APIResponse[ApplicationHealthData]:
    """Provide basic health check endpoint for load balancers and monitoring."""
    log_api_call("basic_health_check")
    payload = ApplicationHealthData(
        name=settings.app_name,
        version=settings.app_version,
        status="healthy",
        debug_mode=settings.debug
    )
    return APIResponse[ApplicationHealthData](
        success=True,
        message="AI Chatbot Platform is running",
        data=payload
    )


@router.get("/detailed", response_model=APIResponse[DetailedHealthCheckPayload])
@handle_api_errors("Health check failed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
) -> APIResponse[DetailedHealthCheckPayload]:
    """Comprehensive health check with all system components."""
    log_api_call("detailed_health_check")

    db_health = await _check_database_health(db)
    cache_health = await _check_cache_health()
    openai_health = await _check_openai_health()
    fastmcp_health = await _check_fastmcp_health(mcp_service)

    app_health = ApplicationHealthData(
        name=settings.app_name,
        version=settings.app_version,
        status="healthy",
        debug_mode=settings.debug,
    )

    component_statuses = [
        db_health.status,
        cache_health.status,
        openai_health.status,
        fastmcp_health.status,
    ]

    if "unhealthy" in component_statuses:
        overall_status = "degraded"
        message = "System health is degraded"
    elif "warning" in component_statuses:
        overall_status = "warning"
        message = "System health has warnings"
    else:
        overall_status = "healthy"
        message = "All system components are healthy"

    payload = DetailedHealthCheckPayload(
        application=app_health,
        database=db_health,
        cache=cache_health,
        openai=openai_health,
        fastmcp=fastmcp_health,
        overall_status=overall_status,
    )
    return APIResponse[DetailedHealthCheckPayload](
        success=True,
        message=message,
        data=payload,
    )


@router.get("/database", response_model=APIResponse[DatabaseHealthData])
@handle_api_errors("Database health check failed")
async def database_health_check(
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DatabaseHealthData]:
    """Database connectivity and schema health check."""
    log_api_call("database_health_check")
    health_data = await _check_database_health(db)

    if health_data.status == "unhealthy":
        message = f"Database is unhealthy: {health_data.message}"
    elif health_data.status == "warning":
        message = f"Database has warnings: {health_data.message}"
    else:
        message = "Database is healthy"

    return APIResponse[DatabaseHealthData](
        success=True,
        message=message,
        data=health_data,
    )


@router.get("/services", response_model=APIResponse[ServicesHealthPayload])
@handle_api_errors("Services health check failed")
async def services_health_check(
    mcp_service: MCPService = Depends(get_mcp_service),
) -> APIResponse[ServicesHealthPayload]:
    """External services health check."""
    log_api_call("services_health_check")

    openai_health = await _check_openai_health()
    fastmcp_health = await _check_fastmcp_health(mcp_service)

    statuses = [openai_health.status, fastmcp_health.status]
    if "unhealthy" in statuses:
        message = "Some external services are unhealthy"
    elif "warning" in statuses:
        message = "Some external services have warnings"
    else:
        message = "All external services are healthy"

    payload = ServicesHealthPayload(
        openai=openai_health,
        fastmcp=fastmcp_health,
    )

    return APIResponse[ServicesHealthPayload](
        success=True,
        message=message,
        data=payload,
    )


async def _check_cache_health() -> CacheHealthData:
    """Check cache system health and performance statistics."""
    try:
        raw_cache_stats = {
            "embedding_cache": embedding_cache.get_stats(),
            "api_response_cache": api_response_cache.get_stats(),
            "search_result_cache": search_result_cache.get_stats(),
        }

        # Convert raw stats to CacheStats objects
        cache_stats = {}
        for cache_name, stats in raw_cache_stats.items():
            cache_stats[cache_name] = CacheStats(
                hits=stats["hits"],
                misses=stats["misses"],
                hit_rate=stats["hit_rate"],
                total_requests=stats["hits"] + stats["misses"]
            )

        test_key = "health_check_test"
        test_value = "test_data"
        await embedding_cache.set(test_key, test_value, ttl=60)
        retrieved = await embedding_cache.get(test_key)
        await embedding_cache.delete(test_key)
        if retrieved != test_value:
            return CacheHealthData(
                status="unhealthy",
                message="Cache test operation failed",
                stats=cache_stats,
            )
        total_hit_rate = 0
        total_requests = 0
        for stats in cache_stats.values():
            total_requests += stats.total_requests
            if stats.total_requests > 0:
                total_hit_rate += stats.hit_rate
        avg_hit_rate = total_hit_rate / len(cache_stats) if cache_stats else 0
        return CacheHealthData(
            status="healthy",
            message="Cache system operational",
            stats=cache_stats,
            overall_hit_rate=avg_hit_rate,
            total_requests=total_requests,
        )
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return CacheHealthData(
            status="unhealthy",
            message=f"Cache check failed: {str(e)}",
            stats={},
        )


async def _check_database_health(db: AsyncSession) -> DatabaseHealthData:
    """Check database connectivity and schema validation."""
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
            return DatabaseHealthData(
                status="warning",
                message=f"Missing tables: {missing_tables}",
                tables=tables,
                missing_tables=missing_tables,
            )
        return DatabaseHealthData(
            status="healthy",
            message="Database connectivity and schema OK",
            tables=tables,
            missing_tables=[],
        )
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return DatabaseHealthData(
            status="unhealthy",
            message=f"Database check failed: {str(e)}",
        )


async def _check_openai_health() -> OpenAIHealthData:
    """Check OpenAI API service availability and configuration."""
    try:
        from ..services.openai_client import OpenAIClient

        if settings.openai_api_key == "your-openai-api-key-here":
            return OpenAIHealthData(
                status="warning",
                message="OpenAI API key not configured",
                configured=False,
            )
        client = OpenAIClient()
        health_result = await client.health_check()
        return OpenAIHealthData(
            status=(
                "healthy" if health_result.get("openai_available") else "unhealthy"
            ),
            message=health_result.get("status", "Unknown"),
            configured=True,
            models_available=health_result.get("models_available", False),
            chat_model=health_result.get("chat_model"),
            embedding_model=health_result.get("embedding_model"),
        )
    except Exception as e:
        logger.error(f"OpenAI health check failed: {e}")
        return OpenAIHealthData(
            status="unhealthy",
            message=f"OpenAI check failed: {str(e)}",
            configured=False,
        )


async def _check_fastmcp_health(mcp_service: MCPService) -> FastMCPHealthData:
    """Check FastMCP service health and server connections."""
    try:
        if not settings.mcp_enabled:
            return FastMCPHealthData(
                status="warning",
                message="FastMCP disabled (optional service)",
                enabled=False,
            )
        health_result = await mcp_service.health_check()
        if not health_result.mcp_available:
            return FastMCPHealthData(
                status="warning",
                message="FastMCP library not available (optional)",
                enabled=settings.mcp_enabled,
                available=False,
            )
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

        return FastMCPHealthData(
            status=status,
            message=message,
            enabled=settings.mcp_enabled,
            available=True,
            registry=registry_info,
            connected_servers=connected_servers,
            enabled_servers=enabled_servers,
            total_servers=total_servers,
            initialized=health_result.initialized,
            server_status=health_result.server_status,
            tools_count=registry_info.get("enabled_tools", 0),
        )
    except Exception as e:
        logger.warning(f"FastMCP health check failed: {e}")
        return FastMCPHealthData(
            status="warning",
            message=f"FastMCP check failed: {str(e)} (optional service)",
            enabled=settings.mcp_enabled,
            available=False,
        )


@router.get("/metrics", response_model=APIResponse[SystemMetricsPayload])
@handle_api_errors("Failed to get system metrics")
async def get_system_metrics() -> APIResponse[SystemMetricsPayload]:
    """Get system performance metrics and resource utilization."""
    log_api_call("get_system_metrics")
    try:
        import time

        import psutil

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        system_metrics = {
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
        }
        application_metrics = {
            "uptime_seconds": time.time() - psutil.Process().create_time(),
            "version": settings.app_version,
            "debug_mode": settings.debug,
        }

        payload = SystemMetricsPayload(
            system=system_metrics,
            application=application_metrics,
        )
        return APIResponse[SystemMetricsPayload](
            success=True,
            message="System metrics collected successfully",
            data=payload,
        )
    except ImportError:
        payload = SystemMetricsPayload(
            system={},
            application={
                "version": settings.app_version,
                "debug_mode": settings.debug,
            }
        )
        return APIResponse[SystemMetricsPayload](
            success=False,
            message="System metrics unavailable",
            data=payload,
        )


@router.get("/readiness", response_model=APIResponse[ReadinessComponentsPayload])
@handle_api_errors("Readiness check failed")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
) -> APIResponse[ReadinessComponentsPayload]:
    """
    Kubernetes-style readiness probe.
    """
    log_api_call("readiness_check")
    try:
        db_health = await _check_database_health(db)
        cache_health = await _check_cache_health()
        fastmcp_health = await _check_fastmcp_health(mcp_service)

        if db_health.status == "unhealthy":
            payload = ReadinessComponentsPayload(
                status="not_ready",
                components={
                    "database": db_health.model_dump(),
                }
            )
            return APIResponse[ReadinessComponentsPayload](
                success=False,
                message="Database not ready",
                data=payload,
            )
        if cache_health.status == "unhealthy":
            payload = ReadinessComponentsPayload(
                status="not_ready",
                components={
                    "cache": cache_health.model_dump(),
                }
            )
            return APIResponse[ReadinessComponentsPayload](
                success=False,
                message="Cache system not ready",
                data=payload,
            )
        if fastmcp_health.status == "unhealthy":
            payload = ReadinessComponentsPayload(
                status="not_ready",
                components={
                    "fastmcp": fastmcp_health.model_dump(),
                }
            )
            return APIResponse[ReadinessComponentsPayload](
                success=False,
                message="FastMCP not ready",
                data=payload,
            )

        payload = ReadinessComponentsPayload(
            status="ready",
            components={
                "database": db_health.model_dump(),
                "cache": cache_health.model_dump(),
                "fastmcp": fastmcp_health.model_dump()
            }
        )
        return APIResponse[ReadinessComponentsPayload](
            success=True,
            message="Application is ready to serve traffic",
            data=payload,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        payload = ReadinessComponentsPayload(
            status="not_ready",
            components={"error": str(e)}
        )
        return APIResponse[ReadinessComponentsPayload](
            success=False,
            message="Readiness check failed",
            data=payload,
        )


@router.get("/performance", response_model=APIResponse[PerformanceMetricsPayload])
@handle_api_errors("Failed to get performance metrics")
async def get_performance_metrics() -> APIResponse[PerformanceMetricsPayload]:
    """Get application performance metrics and statistics."""
    log_api_call("get_performance_metrics")
    performance_data = get_performance_stats()
    payload = PerformanceMetricsPayload(performance=performance_data)
    return APIResponse[PerformanceMetricsPayload](
        success=True,
        message="Performance metrics retrieved successfully",
        data=payload
    )


@router.get("/liveness", response_model=APIResponse[LivenessPayload])
@handle_api_errors("Liveness check failed")
async def liveness_check() -> APIResponse[LivenessPayload]:
    """Kubernetes-style liveness probe."""
    log_api_call("liveness_check")
    payload = LivenessPayload(status="alive")
    return APIResponse[LivenessPayload](
        success=True,
        message="Application is alive",
        data=payload,
    )
