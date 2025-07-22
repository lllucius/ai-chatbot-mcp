"""
FastAPI application entry point with middleware and exception handling.

This module creates and configures the FastAPI application with all necessary
middleware, exception handlers, and API routes.

Generated on: 2025-07-14 04:24:47 UTC
Current User: lllucius
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

# Import API routers
from .api import (
    auth_router,
    conversations_router,
    documents_router,
    health_router,
    search_router,
    tools_router,
    users_router,
)
from .config import settings
from .core.exceptions import ChatbotPlatformException
from .database import close_db, init_db
from .utils.logging import setup_logging
from .utils.timestamp import get_current_timestamp
from .utils.caching import start_cache_cleanup_task
from .utils.validation import validate_request_middleware
from .utils.rate_limiting import rate_limit_middleware, start_rate_limiter_cleanup
from .utils.performance import start_system_monitoring, record_request_metric


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    logger.info("Starting AI Chatbot Platform...")
    try:
        await init_db()
        logger.info("Database initialized successfully")

        # Start cache cleanup task
        await start_cache_cleanup_task()
        logger.info("Cache system initialized")

        # Start rate limiter cleanup task
        await start_rate_limiter_cleanup()
        logger.info("Rate limiting system initialized")

        # Start performance monitoring
        await start_system_monitoring()
        logger.info("Performance monitoring system initialized")

        # Initialize FastMCP and UnifiedToolExecutor
        try:
            from .core.tool_executor import get_unified_tool_executor

            await get_unified_tool_executor()
            logger.info("UnifiedToolExecutor initialized successfully")
        except Exception as e:
            logger.warning(f"UnifiedToolExecutor initialization failed (optional): {e}")
            # Continue without unified tools - it's not critical for basic operation

    except Exception as e:
        logger.error(f"Application initialization failed: {e}")
        raise

    logger.info("Application startup completed")

    yield

    # Shutdown
    logger.info("Shutting down AI Chatbot Platform...")
    try:
        # Cleanup UnifiedToolExecutor and FastMCP
        try:
            from .core.tool_executor import cleanup_unified_tool_executor
            from .services.mcp_client import cleanup_mcp_client

            await cleanup_unified_tool_executor()
            await cleanup_mcp_client()
            logger.info("Tool execution system cleaned up")
        except Exception as e:
            logger.warning(f"Tool execution cleanup failed: {e}")

        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

    logger.info("Application shutdown completed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)


# Custom OpenAPI schema
def custom_openapi():
    """Generate custom OpenAPI schema with additional information."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        routes=app.routes,
    )

    # Add custom information
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }

    # Add authentication security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token",
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Rate limiting middleware (add before other middleware)
@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    """Rate limiting middleware wrapper."""
    return await rate_limit_middleware(request, call_next)

# Input validation middleware (add before other middleware)
@app.middleware("http")
async def input_validation_middleware(request: Request, call_next):
    """Input validation middleware wrapper."""
    return await validate_request_middleware(request, call_next)


# Request timing middleware with performance monitoring
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses and record metrics."""
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(f"{process_time:.4f}")

    # Record performance metric
    record_request_metric(
        path=request.url.path,
        method=request.method,
        status_code=response.status_code,
        duration=process_time,
    )

    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for monitoring and debugging."""
    start_time = time.time()

    # Log request
    logger.info(
        "Request started",
        extra={
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
        },
    )

    # Process request
    response = await call_next(request)

    # Log response
    process_time = time.time() - start_time
    logger.info(
        "Request completed",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": f"{process_time:.4f}s",
        },
    )

    return response


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
)


# Trusted host middleware for production
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["*"]  # Configure based on deployment
    )


# Global exception handlers
@app.exception_handler(ChatbotPlatformException)
async def chatbot_platform_exception_handler(
    request: Request, exc: ChatbotPlatformException
) -> JSONResponse:
    """Handle custom application exceptions."""
    logger.error(
        f"Application error: {exc.message}",
        extra={
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": get_current_timestamp(),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with consistent format."""
    logger.warning(
        f"HTTP error {exc.status_code}: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "timestamp": get_current_timestamp(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(
        f"Unexpected error: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )

    # Don't expose internal error details in production
    error_message = str(exc) if settings.debug else "Internal server error"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": error_message,
            "timestamp": get_current_timestamp(),
        },
    )


# API Routes
app.include_router(health_router, prefix="/api/v1/health", tags=["health"])

app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])

app.include_router(users_router, prefix="/api/v1/users", tags=["users"])

app.include_router(documents_router, prefix="/api/v1/documents", tags=["documents"])

app.include_router(
    conversations_router, prefix="/api/v1/conversations", tags=["conversations"]
)

app.include_router(search_router, prefix="/api/v1/search", tags=["search"])

app.include_router(tools_router, prefix="/api/v1/tools", tags=["tools"])


# Root endpoint
@app.get("/", include_in_schema=False)
async def root() -> Dict[str, Any]:
    """Root endpoint with basic application information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": settings.app_description,
        "status": "operational",
        "docs": "/docs"
        if settings.debug
        else "Documentation not available in production",
        "timestamp": get_current_timestamp(),
    }


# Health check endpoint (for load balancers)
@app.get("/ping", include_in_schema=False)
async def ping() -> Dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok", "timestamp": get_current_timestamp()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=str(settings.log_level).lower(),
        access_log=True,
    )
