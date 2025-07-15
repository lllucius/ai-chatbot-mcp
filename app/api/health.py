"""
Health check API endpoints.

This module provides health monitoring endpoints for the application,
including database connectivity, external services, and system metrics.

Generated on: 2025-07-14 04:24:47 UTC
Current User: lllucius
"""

import logging
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..database import get_db
from ..config import settings
from ..schemas.common import BaseResponse
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
        "timestamp": utcnow()
    }


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed health check with all system components.
    
    Args:
        db: Database session for connectivity check
        
    Returns:
        dict: Comprehensive system health status
    """
    health_status = {
        "application": {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "healthy",
            "debug_mode": settings.debug
        },
        "database": await _check_database_health(db),
        "openai": await _check_openai_health(),
        "fastmcp": await _check_fastmcp_health(),
        "timestamp": utcnow(),
        "overall_status": "healthy"
    }
    
    # Determine overall status
    component_statuses = [
        health_status["database"]["status"],
        health_status["openai"]["status"],
        health_status["fastmcp"]["status"]
    ]
    
    if "unhealthy" in component_statuses:
        health_status["overall_status"] = "degraded"
    elif "warning" in component_statuses:
        health_status["overall_status"] = "warning"
    
    return health_status


@router.get("/database")
async def database_health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Database connectivity health check.
    
    Args:
        db: Database session
        
    Returns:
        dict: Database health status
    """
    return await _check_database_health(db)


@router.get("/services")
async def services_health_check() -> Dict[str, Any]:
    """
    External services health check.
    
    Returns:
        dict: External services health status
    """
    return {
        "openai": await _check_openai_health(),
        "fastmcp": await _check_fastmcp_health(),
        "timestamp": utcnow()
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
        tables_result = await db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'documents', 'conversations')
        """))
        tables = [row[0] for row in tables_result.fetchall()]
        
        # Check for required tables
        required_tables = ['users', 'documents', 'conversations']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            return {
                "status": "warning",
                "message": f"Missing tables: {missing_tables}",
                "connectivity": "ok",
                "schema_status": "incomplete"
            }
        
        return {
            "status": "healthy",
            "message": "Database connectivity and schema OK",
            "connectivity": "ok",
            "schema_status": "complete",
            "tables_found": len(tables)
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Database check failed: {str(e)}",
            "connectivity": "failed"
        }


async def _check_openai_health() -> Dict[str, Any]:
    """Check OpenAI API health."""
    try:
        from ..services.openai_client import OpenAIClient
        
        if settings.openai_api_key == "your-openai-api-key-here":
            return {
                "status": "warning",
                "message": "OpenAI API key not configured",
                "configured": False
            }
        
        client = OpenAIClient()
        health_result = await client.health_check()
        
        return {
            "status": "healthy" if health_result.get("openai_available") else "unhealthy",
            "message": health_result.get("status", "Unknown"),
            "configured": True,
            "models_available": health_result.get("models_available", False),
            "chat_model": health_result.get("chat_model"),
            "embedding_model": health_result.get("embedding_model")
        }
        
    except Exception as e:
        logger.error(f"OpenAI health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"OpenAI check failed: {str(e)}",
            "configured": False
        }


async def _check_fastmcp_health() -> Dict[str, Any]:
    """Check FastMCP services health."""
    try:
        from ..services.mcp_client import get_mcp_client
        
        if not settings.mcp_enabled:
            return {
                "status": "unhealthy",
                "message": "FastMCP disabled but required",
                "enabled": False,
                "error": "FastMCP is required for this application"
            }
        
        mcp_client = await get_mcp_client()
        health_result = await mcp_client.health_check()
        
        if not health_result.get("fastmcp_available"):
            return {
                "status": "unhealthy",
                "message": "FastMCP library not available",
                "enabled": settings.mcp_enabled,
                "available": False,
                "error": "FastMCP is required but not available"
            }
        
        healthy_servers = health_result.get("healthy_servers", 0)
        total_servers = health_result.get("total_servers", 0)
        
        if healthy_servers == 0:
            status = "unhealthy"
            message = "No MCP servers are healthy (required)"
        elif healthy_servers < total_servers:
            status = "warning"
            message = f"Some MCP servers are unhealthy ({healthy_servers}/{total_servers})"
        else:
            status = "healthy"
            message = f"All MCP servers are healthy ({healthy_servers}/{total_servers})"
        
        return {
            "status": status,
            "message": message,
            "enabled": settings.mcp_enabled,
            "available": True,
            "healthy_servers": healthy_servers,
            "total_servers": total_servers,
            "initialized": health_result.get("initialized", False),
            "server_status": health_result.get("server_status", {}),
            "tools_count": health_result.get("tools_count", 0)
        }
        
    except Exception as e:
        logger.error(f"FastMCP health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"FastMCP check failed: {str(e)}",
            "enabled": settings.mcp_enabled,
            "available": False,
            "error": "FastMCP is required but failed"
        }


@router.get("/metrics")
async def get_system_metrics() -> Dict[str, Any]:
    """
    Get system performance metrics.
    
    Returns:
        dict: System metrics and performance data
    """
    try:
        import psutil
        import time
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "system": {
                "cpu_usage_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent_used": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent_used": round((disk.used / disk.total) * 100, 2)
                }
            },
            "application": {
                "uptime_seconds": time.time() - psutil.Process().create_time(),
                "version": settings.app_version,
                "debug_mode": settings.debug
            },
            "timestamp": utcnow()
        }
        
    except ImportError:
        return {
            "error": "psutil not available for system metrics",
            "timestamp": utcnow()
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return {
            "error": f"Failed to get metrics: {str(e)}",
            "timestamp": utcnow()
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
        fastmcp_health = await _check_fastmcp_health()
        
        if db_health["status"] == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not ready"
            )
        
        if fastmcp_health["status"] == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="FastMCP not ready (required)"
            )
        
        return {
            "status": "ready",
            "message": "Application is ready to serve traffic",
            "timestamp": utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Application not ready: {str(e)}"
        )


@router.get("/liveness")
async def liveness_check() -> Dict[str, Any]:
    """
    Kubernetes-style liveness probe.
    
    Returns:
        dict: Liveness status
    """
    return {
        "status": "alive",
        "message": "Application is alive",
        "timestamp": utcnow()
    }
