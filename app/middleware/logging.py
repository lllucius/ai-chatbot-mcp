"""Logging middleware for request tracking and debugging.

Provides structured logging capabilities for HTTP request/response tracking,
performance monitoring, and debugging support with correlation tracking
and comprehensive observability features.
"""

import json
import time

from fastapi import Request, Response

from ..config import settings
from ..core.logging import get_component_logger

logger = get_component_logger("middleware.logging")


async def logging_middleware(request: Request, call_next) -> Response:
    """Log request/response details with correlation ID for tracking."""
    start_time = time.time()

    # Generate correlation ID for this request
    from ..core.logging import set_correlation_id

    correlation_id = set_correlation_id()

    request.state.correlation_id = correlation_id

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
    """Log detailed request/response content for debugging when debug mode is enabled."""
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
    """Log detailed request content with intelligent parsing and filtering."""
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
            f"📤 DEBUG REQUEST DETAILS\n{json.dumps(request_details, indent=4)}",
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


async def _log_response_content(response: Response, correlation_id: str) -> Response:
    """Log detailed response content with intelligent formatting."""
    response_details = {
        "correlation_id": correlation_id,
        "status_code": response.status_code,
        "headers": dict(response.headers),
    }

    if hasattr(response, "body_iterator") and response.body_iterator:
        original_body_iterator = response.body_iterator
        captured_chunks = []

        async def replay_body():
            for chunk in captured_chunks:
                yield chunk

        # Capture the stream
        async for chunk in original_body_iterator:
            captured_chunks.append(chunk)

        # Log body
        full_body = b"".join(captured_chunks)
        await _consume_and_log_body(full_body, response_details)

        # Replace the original stream with a replayable one
        response.body_iterator = replay_body()

    elif hasattr(response, "body") and response.body:
        body = response.body
        if isinstance(body, bytes):
            body_text = body.decode("utf-8", errors="replace")
        else:
            body_text = str(body)

        await _consume_and_log_body(body_text.encode("utf-8"), response_details)

    else:
        response_details["body"] = None

    logger.debug(
        f"📤 DEBUG RESPONSE DETAILS\n{json.dumps(response_details, indent=4)}",
        extra={
            "extra_fields": {
                "debug_type": "response",
                "response_details": response_details,
            }
        },
    )

    return response


async def _consume_and_log_body(body_bytes: bytes, response_details: dict):
    """Capture the response body."""
    try:
        body_text = body_bytes.decode("utf-8", errors="replace")
        try:
            body_json = json.loads(body_text)
            response_details["body"] = body_json
        except json.JSONDecodeError:
            if len(body_text) > 1000:
                body_text = body_text[:1000] + "... (truncated)"
            response_details["body"] = body_text
    except Exception as e:
        response_details["body"] = f"<Error decoding body: {e}>"
