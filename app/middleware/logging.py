"""
Logging middleware for request/response tracking and debugging.

This module provides middleware for logging HTTP requests and responses,
including detailed content logging when debug mode is enabled.
"""

import json
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from ..config import settings
from ..core.logging import get_component_logger

logger = get_component_logger("middleware.logging")


async def logging_middleware(request: Request, call_next) -> Response:
    """
    Standard request/response logging middleware.

    Logs basic information about all HTTP requests and responses including
    timing, status codes, and client information.

    Args:
        request: The HTTP request
        call_next: The next middleware or endpoint handler

    Returns:
        Response: The HTTP response
    """
    start_time = time.time()

    # Generate correlation ID for this request
    from ..core.logging import set_correlation_id

    correlation_id = set_correlation_id()

    # Log request start
    logger.info(
        "Request started",
        extra={
            "extra_fields": {
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
                "correlation_id": correlation_id,
            }
        },
    )

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Log request completion
    logger.info(
        "Request completed",
        extra={
            "extra_fields": {
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2),
                "correlation_id": correlation_id,
            }
        },
    )

    return response


async def debug_content_middleware(request: Request, call_next) -> Response:
    """
    Debug middleware for logging request/response content.

    When debug mode is enabled, this middleware logs the full content
    of requests and responses in a nicely formatted way for debugging.

    Args:
        request: The HTTP request
        call_next: The next middleware or endpoint handler

    Returns:
        Response: The HTTP response
    """
    if not settings.debug:
        # Skip debug logging in production
        return await call_next(request)

    correlation_id = getattr(request.state, "correlation_id", "unknown")

    # Log request details
    await _log_request_content(request, correlation_id)

    # Process request and capture response
    response = await call_next(request)

    # Log response details
    await _log_response_content(response, correlation_id)

    return response


async def _log_request_content(request: Request, correlation_id: str):
    """
    Log detailed request content for debugging.

    Args:
        request: The HTTP request
        correlation_id: Request correlation ID
    """
    try:
        # Prepare request details
        request_details = {
            "correlation_id": correlation_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client": {
                "host": request.client.host if request.client else None,
                "port": request.client.port if request.client else None,
            },
        }

        # Try to read and parse request body
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Read body (be careful not to consume it)
                body = await request.body()
                if body:
                    # Try to parse as JSON for better formatting
                    try:
                        body_json = json.loads(body.decode("utf-8"))
                        request_details["body"] = body_json
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # If not JSON, log as text (truncate if too long)
                        body_text = body.decode("utf-8", errors="replace")
                        if len(body_text) > 1000:
                            body_text = body_text[:1000] + "... (truncated)"
                        request_details["body"] = body_text
                else:
                    request_details["body"] = None
            except Exception as e:
                request_details["body"] = f"<Error reading body: {e}>"

        # Format and log request
        logger.debug(
            "📥 DEBUG REQUEST DETAILS",
            extra={
                "extra_fields": {
                    "debug_type": "request",
                    "request_details": request_details,
                }
            },
        )

    except Exception as e:
        logger.error(
            f"Error logging request content: {e}",
            extra={"extra_fields": {"correlation_id": correlation_id}},
        )


async def _log_response_content(response: Response, correlation_id: str):
    """
    Log detailed response content for debugging.

    Args:
        response: The HTTP response
        correlation_id: Request correlation ID
    """
    try:
        # Prepare response details
        response_details = {
            "correlation_id": correlation_id,
            "status_code": response.status_code,
            "headers": dict(response.headers),
        }

        # Try to capture response body
        if hasattr(response, "body") and response.body:
            try:
                # Handle different response types
                if isinstance(response, StreamingResponse):
                    response_details["body"] = (
                        "<Streaming Response - Body not captured>"
                    )
                else:
                    body = response.body
                    if isinstance(body, bytes):
                        body_text = body.decode("utf-8", errors="replace")
                    else:
                        body_text = str(body)

                    # Try to parse as JSON for better formatting
                    try:
                        body_json = json.loads(body_text)
                        response_details["body"] = body_json
                    except json.JSONDecodeError:
                        # If not JSON, log as text (truncate if too long)
                        if len(body_text) > 1000:
                            body_text = body_text[:1000] + "... (truncated)"
                        response_details["body"] = body_text

            except Exception as e:
                response_details["body"] = f"<Error reading body: {e}>"
        else:
            response_details["body"] = None

        # Format and log response
        logger.debug(
            "📤 DEBUG RESPONSE DETAILS",
            extra={
                "extra_fields": {
                    "debug_type": "response",
                    "response_details": response_details,
                }
            },
        )

    except Exception as e:
        logger.error(
            f"Error logging response content: {e}",
            extra={"extra_fields": {"correlation_id": correlation_id}},
        )


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Base HTTP middleware class for logging.

    Provides an alternative class-based approach for logging middleware
    that can be used with FastAPI's middleware stack.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Dispatch method that combines standard and debug logging.

        Args:
            request: The HTTP request
            call_next: The next middleware or endpoint handler

        Returns:
            Response: The HTTP response
        """
        # Apply standard logging
        response = await logging_middleware(request, call_next)

        # Apply debug logging if enabled
        if settings.debug:
            # Note: This is a simplified version since we can't easily
            # re-process the response here. The debug_content_middleware
            # should be applied separately in the middleware stack.
            pass

        return response
