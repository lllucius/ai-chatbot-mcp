"""Logging middleware for request tracking and debugging.

Provides structured logging capabilities for HTTP request/response tracking,
performance monitoring, and debugging support with correlation tracking
and comprehensive observability features.
"""

import json
import re
import time

from fastapi import Request, Response
from fastapi.responses import StreamingResponse

from ..config import settings
from ..core.logging import get_component_logger

logger = get_component_logger("middleware.logging")


TRUNC_SIZE = 5000

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

    # Log response details with proper streaming/non-streaming handling
    response = await _log_response_content_improved(response, correlation_id)

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
                        if len(body_text) > TRUNC_SIZE:
                            body_text = body_text[:TRUNC_SIZE] + "... (truncated)"
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


async def _log_response_content_improved(response: Response, correlation_id: str) -> Response:
    """Log detailed response content with proper streaming and Pydantic model support."""
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel

    response_details = {
        "correlation_id": correlation_id,
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "response_type": type(response).__name__
    }

    try:
        # Handle Pydantic models
        if hasattr(response, 'body') and isinstance(response.body, BaseModel):
            pydantic_data = response.body.model_dump()
            _log_response_with_body(response_details, pydantic_data, "pydantic")

        # Handle StreamingResponse
        elif isinstance(response, StreamingResponse):
            response = _handle_streaming_response(response, response_details, correlation_id)

        # Handle responses with body_iterator (streaming)
        elif hasattr(response, "body_iterator") and response.body_iterator:
            response = _handle_body_iterator_response(response, response_details, correlation_id)

        # Handle regular responses with body
        elif hasattr(response, "body") and response.body:
            await _handle_regular_response_body(response, response_details)

        else:
            response_details["body"] = None
            _log_response_simple(response_details)

    except Exception as e:
        logger.error(
            f"Error logging response content: {e}",
            extra={"extra_fields": {"correlation_id": correlation_id}},
        )

    return response


def _handle_streaming_response(response: StreamingResponse, response_details: dict, correlation_id: str) -> StreamingResponse:
    """Handle StreamingResponse by capturing content while preserving true streaming."""
    if not hasattr(response, 'body_iterator'):
        response_details["body"] = "<No body_iterator available>"
        _log_response_simple(response_details)
        return response

    original_iterator = response.body_iterator
    accumulated_content = []

    async def capture_and_stream():
        """Generator that captures content while streaming without blocking."""
        try:
            async for chunk in original_iterator:
                # Capture chunk for later logging
                accumulated_content.append(chunk)
                # Immediately yield the chunk to maintain streaming
                yield chunk
        except Exception as e:
            logger.error(f"Error in streaming capture: {e}")
            raise
        finally:
            # Schedule logging after streaming completes (non-blocking)
            import asyncio
            asyncio.create_task(_log_accumulated_content_async(accumulated_content, response_details.copy(), correlation_id))

    # Replace the iterator with our capturing version
    response.body_iterator = capture_and_stream()

    # Log immediate response info (without body content)
    response_details["body"] = "<Streaming in progress - content will be logged after completion>"
    _log_response_simple(response_details, "streaming_started")

    return response


def _handle_body_iterator_response(response: Response, response_details: dict, correlation_id: str) -> Response:
    """Handle responses with body_iterator using non-blocking approach."""
    original_body_iterator = response.body_iterator
    accumulated_content = []

    async def capture_and_replay():
        """Generator that captures and replays content without pre-loading."""
        try:
            async for chunk in original_body_iterator:
                accumulated_content.append(chunk)
                yield chunk
        except Exception as e:
            logger.error(f"Error in body iterator capture: {e}")
            raise
        finally:
            # Schedule logging after iteration completes
            import asyncio
            asyncio.create_task(_log_accumulated_content_async(accumulated_content, response_details.copy(), correlation_id))

    # Replace with capturing iterator
    response.body_iterator = capture_and_replay()

    # Log immediate response info
    response_details["body"] = "<Body iterator in progress - content will be logged after completion>"
    _log_response_simple(response_details, "iterator_started")

    return response


async def _handle_regular_response_body(response: Response, response_details: dict):
    """Handle regular response bodies."""
    try:
        body = response.body
        if isinstance(body, bytes):
            _process_and_log_body_content(body, response_details)
        else:
            body_text = str(body)
            _log_response_with_text(response_details, body_text, "text")
    except Exception as e:
        response_details["body"] = f"<Error processing response body: {e}>"
        _log_response_simple(response_details)


def _process_and_log_body_content(body_bytes: bytes, response_details: dict):
    """Process body content and log with proper formatting."""
    try:
        body_text = body_bytes.decode("utf-8", errors="replace")

        # Check if it's SSE data first
        if _is_sse_content(body_text, response_details):
            _log_response_with_sse(response_details, body_text)
            return

        # Try to parse as JSON
        try:
            body_json = json.loads(body_text)
            _log_response_with_body(response_details, body_json, "json")
            return
        except json.JSONDecodeError:
            # Handle as text - use the proper text logging format
            _log_response_with_text(response_details, body_text, "text")
            return

    except Exception as e:
        response_details["body"] = f"<Error decoding body: {e}>"
        _log_response_simple(response_details)


def _is_sse_content(body_text: str, response_details: dict) -> bool:
    """Detect if content is Server-Sent Events format."""
    # Check content-type header
    content_type = response_details.get("headers", {}).get("content-type", "")
    if "text/event-stream" in content_type.lower():
        return True

    # Check for SSE field patterns
    sse_patterns = [
        r'^data:\s',
        r'^event:\s',
        r'^id:\s',
        r'^retry:\s',
        r'^\s*$',  # Empty lines
    ]

    lines = body_text.strip().split('\n')
    if len(lines) < 1:
        return False

    # Check if most lines match SSE patterns
    matching_lines = 0
    for line in lines:
        for pattern in sse_patterns:
            if re.match(pattern, line):
                matching_lines += 1
                break

    # If more than 70% of lines match SSE patterns, consider it SSE
    return matching_lines / len(lines) > 0.7


def _log_response_with_sse(response_details: dict, sse_text: str):
    """Log response with pretty-printed SSE data."""
    try:
        parsed_events = _parse_sse_data(sse_text)

        # Build the log message
        header_info = json.dumps({
            k: v for k, v in response_details.items()
            if k not in ['body', 'body_text']
        }, indent=2)

        # Format SSE events
        formatted_events = _format_sse_events(parsed_events)

        # Truncate if necessary
        if len(formatted_events) > TRUNC_SIZE:
            formatted_events = formatted_events[:TRUNC_SIZE] + f"\n... (truncated from {len(sse_text)} chars)"

        log_message = f"""📥 DEBUG RESPONSE DETAILS
Response Info:
{header_info}

Body (SSE - {len(parsed_events)} events):
{formatted_events}"""

        logger.debug(
            log_message,
            extra={
                "extra_fields": {
                    "debug_type": "response",
                    "correlation_id": response_details.get("correlation_id"),
                    "content_type": "sse",
                    "event_count": len(parsed_events),
                }
            },
        )

    except Exception as e:
        # Fallback to text logging
        response_details["body_text"] = sse_text[:TRUNC_SIZE] + ("..." if len(sse_text) > TRUNC_SIZE else "")
        response_details["sse_parse_error"] = str(e)
        _log_response_simple(response_details)


def _parse_sse_data(sse_text: str) -> list:
    """Parse SSE data into structured events."""
    events = []
    current_event = {}

    lines = sse_text.split('\n')

    for line in lines:
        line = line.rstrip('\r')

        if line == '':
            # Empty line indicates end of event
            if current_event:
                events.append(current_event.copy())
                current_event = {}
        elif line.startswith(':'):
            # Comment line
            if 'comments' not in current_event:
                current_event['comments'] = []
            current_event['comments'].append(line[1:].strip())
        elif ':' in line:
            # Field line
            field, value = line.split(':', 1)
            field = field.strip()
            value = value.strip()

            if field == 'data':
                # Data can be multi-line
                if 'data' not in current_event:
                    current_event['data'] = []
                current_event['data'].append(value)
            else:
                current_event[field] = value
        else:
            # Line without colon is treated as field with empty value
            field = line.strip()
            if field:
                current_event[field] = ''

    # Add final event if exists
    if current_event:
        events.append(current_event)

    return events


def _format_sse_events(events: list) -> str:
    """Format parsed SSE events for pretty printing."""
    if not events:
        return "<No SSE events found>"

    formatted_lines = []

    for i, event in enumerate(events):
        formatted_lines.append(f"Event #{i + 1}:")

        # Handle different fields
        for field, value in event.items():
            if field == 'data':
                # Join multi-line data
                if isinstance(value, list):
                    data_content = '\n'.join(value)
                else:
                    data_content = str(value)

                # Try to parse data as JSON for better formatting
                try:
                    data_json = json.loads(data_content)
                    pretty_data = json.dumps(data_json, indent=4)
                    formatted_lines.append("  data (JSON):")
                    for line in pretty_data.split('\n'):
                        formatted_lines.append(f"    {line}")
                except json.JSONDecodeError:
                    formatted_lines.append(f"  data: {data_content}")
            elif field == 'comments':
                for comment in value:
                    formatted_lines.append(f"  comment: {comment}")
            else:
                formatted_lines.append(f"  {field}: {value}")

        formatted_lines.append("")  # Empty line between events

    return '\n'.join(formatted_lines)


def _log_response_with_body(response_details: dict, body_data, content_type: str):
    """Log response with pretty-printed JSON body."""
    try:
        # Create the log message with pretty-printed JSON
        pretty_json = json.dumps(body_data, indent=2, ensure_ascii=False)

        # Check if we need to truncate
        if len(pretty_json) > TRUNC_SIZE:
            # Try compact format
            compact_json = json.dumps(body_data, separators=(',', ':'), ensure_ascii=False)
            if len(compact_json) <= TRUNC_SIZE:
                body_display = compact_json
            else:
                body_display = _smart_truncate_json(pretty_json, TRUNC_SIZE)
        else:
            body_display = pretty_json

        # Build the log message manually to avoid JSON escaping
        header_info = json.dumps({
            k: v for k, v in response_details.items()
            if k not in ['body', 'body_text']
        }, indent=2)

        log_message = f"""📥 DEBUG RESPONSE DETAILS
Response Info:
{header_info}

Body ({content_type}):
{body_display}"""

        logger.debug(
            log_message,
            extra={
                "extra_fields": {
                    "debug_type": "response",
                    "correlation_id": response_details.get("correlation_id"),
                    "content_type": content_type,
                }
            },
        )

    except Exception as e:
        # Fallback to simple logging
        response_details["body"] = f"<Error formatting body: {e}>"
        _log_response_simple(response_details)


def _log_response_with_text(response_details: dict, text_content: str, content_type: str):
    """Log response with properly formatted text content."""
    try:
        # Truncate if necessary
        if len(text_content) > TRUNC_SIZE:
            display_content = text_content[:TRUNC_SIZE] + f"\n... (truncated from {len(text_content)} chars)"
        else:
            display_content = text_content

        # Build the log message manually
        header_info = json.dumps({
            k: v for k, v in response_details.items()
            if k not in ['body', 'body_text']
        }, indent=2)

        log_message = f"""📥 DEBUG RESPONSE DETAILS
Response Info:
{header_info}

Body ({content_type}):
{display_content}"""

        logger.debug(
            log_message,
            extra={
                "extra_fields": {
                    "debug_type": "response",
                    "correlation_id": response_details.get("correlation_id"),
                    "content_type": content_type,
                }
            },
        )

    except Exception as e:
        # Fallback to simple logging
        response_details["body"] = f"<Error formatting text: {e}>"
        _log_response_simple(response_details)


def _log_response_simple(response_details: dict, debug_type: str = "response"):
    """Log response using simple JSON formatting."""
    logger.debug(
        f"📥 DEBUG RESPONSE DETAILS\n{json.dumps(response_details, indent=2)}",
        extra={
            "extra_fields": {
                "debug_type": debug_type,
                "response_details": response_details,
            }
        },
    )


def _smart_truncate_json(json_str: str, max_length: int) -> str:
    """Intelligently truncate JSON while trying to maintain validity."""
    if len(json_str) <= max_length:
        return json_str

    # Find a good truncation point (end of a complete line if possible)
    truncate_point = max_length - 20  # Leave room for truncation message

    # Look for the last complete line break before truncation point
    last_newline = json_str.rfind('\n', 0, truncate_point)
    if last_newline > max_length * 0.7:  # If we found a reasonable newline
        truncate_point = last_newline

    truncated = json_str[:truncate_point]

    # Add closing braces/brackets if needed to make it more readable
    open_braces = truncated.count('{') - truncated.count('}')
    open_brackets = truncated.count('[') - truncated.count(']')

    closing = ''
    if open_brackets > 0:
        closing += ']' * min(open_brackets, 3)
    if open_braces > 0:
        closing += '}' * min(open_braces, 3)

    total_chars = len(json_str)
    return f"{truncated}{closing}\n... (truncated from {total_chars} chars)"


async def _log_accumulated_content_async(accumulated_content: list, response_details: dict, correlation_id: str):
    """Asynchronously log accumulated streaming content after completion."""
    try:
        if accumulated_content:
            full_body = b"".join(accumulated_content)

            # Add streaming stats
            response_details["total_chunks"] = len(accumulated_content)
            response_details["total_bytes"] = sum(len(chunk) for chunk in accumulated_content)

            # Process and log the body content
            try:
                body_text = full_body.decode("utf-8", errors="replace")

                # Check if it's SSE data first
                if _is_sse_content(body_text, response_details):
                    _log_response_with_sse(response_details, body_text)
                    return

                # Try JSON parsing
                try:
                    body_json = json.loads(body_text)
                    _log_response_with_body(response_details, body_json, "json_streamed")
                except json.JSONDecodeError:
                    _log_response_with_text(response_details, body_text, "text_streamed")
            except Exception as e:
                response_details["body"] = f"<Error decoding body: {e}>"
                _log_response_simple(response_details, "streaming_complete")
        else:
            response_details["body"] = "<Empty stream>"
            _log_response_simple(response_details, "streaming_complete")

    except Exception as e:
        logger.error(
            f"Error logging accumulated streaming content: {e}",
            extra={"extra_fields": {"correlation_id": correlation_id}}
        )


# Legacy functions (kept for compatibility, but not used by new implementation)
async def _log_response_content(response: Response, correlation_id: str) -> Response:
    """Legacy function - replaced by _log_response_content_improved."""
    return await _log_response_content_improved(response, correlation_id)


async def _consume_and_log_body(body_bytes: bytes, response_details: dict):
    """Legacy function - replaced by _process_and_log_body_content."""
    _process_and_log_body_content(body_bytes, response_details)

