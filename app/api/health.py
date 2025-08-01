"""
Health monitoring and system status API endpoints.

This module provides comprehensive health monitoring endpoints for the application,
including database connectivity, external services monitoring, system metrics,
and Kubernetes-style probes for container orchestration.

Key Features:
- Basic and detailed health checks
- Database connectivity and schema validation
- External service status monitoring (OpenAI, FastMCP)
- System performance metrics and resource utilization
- Cache system health and statistics
- Kubernetes-compatible liveness and readiness probes

Monitoring Capabilities:
- Real-time system resource monitoring
- Database performance metrics
- External API availability checks
- Cache hit rates and performance statistics
- Background service health validation
- Detailed error reporting and diagnostics

Integration Support:
- Load balancer health check endpoints
- Kubernetes liveness/readiness probes
- Monitoring system integration
- Alerting and notification support
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
    Basic health check endpoint.

    Provides a quick health status check for the application without
    checking external dependencies. This is suitable for load balancer
    health checks and basic monitoring.

    Returns:
        dict: Basic application status including version and timestamp

    Example:
        GET /api/v1/health/
        {
            "success": true,
            "message": "AI Chatbot Platform is running",
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": "2024-01-01T12:00:00Z"
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
    Detailed health check with all system components.

    Args:
        db: Database session for connectivity check

    Returns:
        dict: Comprehensive system health status
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
    Database connectivity health check.
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
    """
    log_api_call("services_health_check")
    return ServicesHealthResponse(
        openai=await _check_openai_health(),
        fastmcp=await _check_fastmcp_health(mcp_service),
        timestamp=utcnow(),
    )


async def _check_cache_health() -> Dict[str, Any]:
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
