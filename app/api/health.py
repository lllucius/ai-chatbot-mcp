"""
Health check API endpoints.

This module provides health monitoring endpoints for the application,
including database connectivity, external services, and system metrics.

"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..middleware.performance import get_performance_stats
from ..schemas.common import BaseResponse
from ..utils.api_errors import handle_api_errors, log_api_call
from ..utils.caching import (api_response_cache, embedding_cache,
                             search_result_cache)
from ..utils.timestamp import utcnow

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=BaseResponse)
async def basic_health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.

    Returns:
        dict: Basic application status
    """
    return {
        "success": True,
        "message": "AI Chatbot Platform is running",
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": utcnow(),
    }


@router.get("/detailed")
@handle_api_errors("Health check failed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
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
        "fastmcp": await _check_fastmcp_health(db),
        "timestamp": utcnow(),
        "overall_status": "healthy",
    }

    # Determine overall status
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


@router.get("/database")
@handle_api_errors("Database health check failed")
async def database_health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Database connectivity health check.

    Args:
        db: Database session

    Returns:
        dict: Database health status
    """
    log_api_call("database_health_check")
    return await _check_database_health(db)


@router.get("/services")
@handle_api_errors("Services health check failed")
async def services_health_check() -> Dict[str, Any]:
    """
    External services health check.

    Returns:
        dict: External services health status
    """
    log_api_call("services_health_check")
    return {
        "openai": await _check_openai_health(),
        "fastmcp": await _check_fastmcp_health(),
        "timestamp": utcnow(),
    }


async def _check_cache_health() -> Dict[str, Any]:
    """Check cache system health and performance."""
    try:
        cache_stats = {
            "embedding_cache": embedding_cache.get_stats(),
            "api_response_cache": api_response_cache.get_stats(),
            "search_result_cache": search_result_cache.get_stats(),
        }

        # Test cache functionality
        test_key = "health_check_test"
        test_value = "test_data"

        # Test set/get operations on each cache
        await embedding_cache.set(test_key, test_value, ttl=60)
        retrieved = await embedding_cache.get(test_key)
        await embedding_cache.delete(test_key)

        if retrieved != test_value:
            return {
                "status": "unhealthy",
                "message": "Cache test operation failed",
                "stats": cache_stats,
            }

        # Calculate overall cache health
        total_hit_rate = 0
        total_requests = 0

        for cache_name, stats in cache_stats.items():
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
    """Check database connectivity and basic operations."""
    try:
        # Test basic connectivity
        result = await db.execute(text("SELECT 1 as test"))
        test_value = result.scalar()

        if test_value != 1:
            raise Exception("Database query returned unexpected result")

        # Test table existence (basic schema check)
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

        # Check for required tables
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
    """Check OpenAI API health."""
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
            "status": ("healthy" if health_result.get("openai_available") else "unhealthy"),
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


async def _check_fastmcp_health(db: Optional[AsyncSession] = None) -> Dict[str, Any]:
    """Check FastMCP services health with enhanced registry integration."""
    try:
        if not settings.mcp_enabled:
            return {
                "status": "warning",
                "message": "FastMCP disabled (optional service)",
                "enabled": False,
            }

        # Import here to avoid circular imports
        from ..database import AsyncSessionLocal
        from ..services.mcp_client import get_mcp_client

        # Use provided db session or create a new one
        if db:
            mcp_client = await get_mcp_client(db)
            health_result = await mcp_client.health_check(db)
        else:
            async with AsyncSessionLocal() as session:
                mcp_client = await get_mcp_client(session)
                health_result = await mcp_client.health_check(session)

        if not health_result.mcp_available:
            return {
                "status": "warning",
                "message": "FastMCP library not available (optional)",
                "enabled": settings.mcp_enabled,
                "available": False,
            }

        # Get registry-specific information
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
            message = (
                f"All enabled MCP servers are connected ({connected_servers}/{enabled_servers})"
            )

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


@router.get("/metrics")
@handle_api_errors("Failed to get system metrics")
async def get_system_metrics() -> Dict[str, Any]:
    """
    Get system performance metrics.

    Returns:
        dict: System metrics and performance data
    """
    log_api_call("get_system_metrics")

    try:
        import time

        import psutil

        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "system": {
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
            "application": {
                "uptime_seconds": time.time() - psutil.Process().create_time(),
                "version": settings.app_version,
                "debug_mode": settings.debug,
            },
            "timestamp": utcnow(),
        }

    except ImportError:
        return {
            "error": "psutil not available for system metrics",
            "timestamp": utcnow(),
        }


@router.get("/readiness")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Kubernetes-style readiness probe.

    Args:
        db: Database session

    Returns:
        dict: Readiness status
    """
    try:
        # Check critical dependencies
        db_health = await _check_database_health(db)
        cache_health = await _check_cache_health()

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

        return {
            "status": "ready",
            "message": "Application is ready to serve traffic",
            "timestamp": utcnow(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Application not ready: {str(e)}",
        )


@router.get("/performance")
@handle_api_errors("Failed to get performance metrics")
async def get_performance_metrics() -> Dict[str, Any]:
    """
    Get comprehensive performance metrics and statistics.

    Returns:
        dict: Performance metrics and system health data
    """
    log_api_call("get_performance_metrics")
    return get_performance_stats()


@router.get("/liveness")
async def liveness_check() -> Dict[str, Any]:
    """
    Kubernetes-style liveness probe.

    Returns:
        dict: Liveness status
    """
    return {"status": "alive", "message": "Application is alive", "timestamp": utcnow()}
