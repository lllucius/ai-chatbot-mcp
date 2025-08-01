"""
Core middleware components for the AI Chatbot Platform.

This module contains core middleware functionality including timing,
validation, and rate limiting that were previously scattered in main.py
and various utils modules.
"""

import time

from fastapi import Request, Response

from ..core.logging import get_component_logger
from ..middleware.performance import record_request_metric
from ..middleware.rate_limiting import rate_limit_middleware as _rate_limit_middleware
from ..middleware.validation import (
    validate_request_middleware as _validate_request_middleware,
)

logger = get_component_logger("middleware.core")


async def timing_middleware(request: Request, call_next) -> Response:
    """
    Request timing middleware with performance monitoring.

    Adds processing time headers to responses and records performance metrics.

    Args:
        request: The HTTP request
        call_next: The next middleware or endpoint handler

    Returns:
        Response: The HTTP response with timing headers
    """
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Add timing header to response
    response.headers["X-Process-Time"] = f"{process_time:.4f}"

    # Record performance metric
    try:
        record_request_metric(
            path=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration=process_time,
        )
    except Exception as e:
        logger.warning(
            f"Failed to record performance metric: {e}",
            extra={
                "extra_fields": {
                    "path": request.url.path,
                    "method": request.method,
                    "error": str(e),
                }
            },
        )

    return response


async def validation_middleware(request: Request, call_next) -> Response:
    """
    Input validation middleware wrapper.

    Validates and sanitizes input data to prevent common security vulnerabilities.

    Args:
        request: The HTTP request
        call_next: The next middleware or endpoint handler

    Returns:
        Response: The HTTP response
    """
    return await _validate_request_middleware(request, call_next)


async def rate_limiting_middleware(request: Request, call_next) -> Response:
    """
    Rate limiting middleware wrapper.

    Applies rate limiting to prevent abuse and ensure fair usage.

    Args:
        request: The HTTP request
        call_next: The next middleware or endpoint handler

    Returns:
        Response: The HTTP response
    """
    return await _rate_limit_middleware(request, call_next)
