"""Core middleware components for request processing and security enforcement.

Provides foundational middleware for request timing, input validation, and
rate limiting with security controls and performance monitoring.
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
    """Measure request processing time and record performance metrics.

    Provides microsecond-accurate timing measurement and records metrics
    for monitoring and analysis. Adds X-Process-Time header to response.

    Args:
        request: The incoming HTTP request object
        call_next: The next middleware or endpoint handler in the chain

    Returns:
        Response: The HTTP response with timing header added

    Raises:
        Exception: Logs metric recording failures without affecting request processing
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
    """Validate and sanitize request input to prevent security vulnerabilities.

    Implements input validation and sanitization to protect against injection attacks,
    XSS, malformed data, and other common web application vulnerabilities.

    Args:
        request: The incoming HTTP request object requiring validation
        call_next: The next middleware or endpoint handler in the processing chain

    Returns:
        Response: The HTTP response from the downstream handler after validation

    Raises:
        HTTPException: Raised for validation failures with appropriate status codes
            (400, 413, 415, 422)
    """
    return await _validate_request_middleware(request, call_next)


async def rate_limiting_middleware(request: Request, call_next) -> Response:
    """Apply rate limiting to prevent abuse and ensure fair resource allocation.

    Implements rate limiting algorithms including token bucket and sliding window
    to prevent DoS attacks and ensure fair usage. Provides user-specific quotas
    and distributed rate limiting support.

    Args:
        request: The incoming HTTP request object for rate limit evaluation
        call_next: The next middleware or endpoint handler in the processing chain

    Returns:
        Response: The HTTP response with rate limiting headers (X-RateLimit-*)
            or 429 Too Many Requests when rate limits are exceeded

    Raises:
        HTTPException: Raised when rate limits are exceeded (429 Too Many Requests)
    """
    return await _rate_limit_middleware(request, call_next)
