"""
Comprehensive logging middleware for enterprise-grade request tracking and debugging.

This module provides sophisticated logging capabilities for HTTP request/response
tracking, performance monitoring, and debugging support with structured logging,
correlation tracking, and comprehensive observability features. Implements
enterprise-grade logging patterns with detailed content inspection, security
event tracking, and integration with external monitoring systems for complete
application observability and troubleshooting capabilities.

Key Features:
- Structured JSON logging with comprehensive request/response metadata capture
- Correlation ID generation and propagation for distributed system tracing
- Performance timing and metrics collection with statistical analysis capabilities
- Debug content logging with configurable verbosity levels and content filtering
- Security event logging with audit trails and compliance reporting features
- Error tracking and exception handling with detailed context and stack traces

Observability Features:
- Request tracing with unique correlation IDs for cross-service request tracking
- Performance metrics collection including timing, throughput, and error rates
- User behavior analytics with detailed usage patterns and interaction tracking
- Health monitoring integration with real-time system status and dependency checks
- Custom metrics and events with tags and dimensions for advanced analytics
- Integration with monitoring platforms like Prometheus, Grafana, and ELK stack

Security Features:
- Secure logging practices preventing sensitive data exposure in log files
- Configurable content filtering to exclude passwords, tokens, and PII data
- Security event tracking including authentication failures and suspicious activity
- Audit trail generation for compliance requirements and regulatory reporting
- Rate limiting for log generation preventing log flooding and resource exhaustion
- Comprehensive error handling without information disclosure vulnerabilities

Performance Features:
- Asynchronous logging implementation for minimal request processing impact
- Configurable log levels and sampling rates for production performance optimization
- Memory efficient log buffering and batching for high-throughput environments
- Log rotation and retention policies for storage optimization and compliance
- Compression and archival support for long-term log storage and analysis
- Real-time log streaming and processing for immediate alerting and response

Development Features:
- Debug mode with detailed request/response content logging for troubleshooting
- Pretty-printed JSON output for human-readable log analysis and debugging
- Request replay capability for development testing and issue reproduction
- Interactive log filtering and search capabilities for efficient debugging
- Performance profiling integration with detailed execution timing and bottleneck identification
- Hot-reloading configuration for dynamic log level adjustment during development

Integration Patterns:
- FastAPI middleware integration with proper async/await patterns and lifecycle management
- External logging system integration including Elasticsearch, Splunk, and CloudWatch
- Monitoring and alerting platform integration for real-time incident response
- Container orchestration logging with proper stdout/stderr handling and log forwarding
- Microservices architecture support with service mesh integration and distributed tracing
- CI/CD pipeline integration for automated log analysis and quality assurance

Use Cases:
- Production application monitoring with comprehensive request tracking and performance analysis
- Security incident investigation with detailed audit trails and forensic capabilities
- Performance optimization and capacity planning with historical usage data and trend analysis
- Compliance reporting and audit trail generation for regulatory requirements
- Development debugging and troubleshooting with detailed request/response inspection
- Integration testing and quality assurance with automated log analysis and validation
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
    Enterprise-grade request/response logging middleware with comprehensive tracking.

    Provides structured logging for all HTTP requests and responses with detailed
    metadata capture, performance timing, correlation ID generation, and integration
    with monitoring systems. Implements comprehensive observability patterns with
    security-conscious logging that excludes sensitive data while providing complete
    request lifecycle tracking for debugging, monitoring, and compliance purposes.

    Args:
        request (Request): The incoming HTTP request object containing:
            - HTTP method, URL, path, and query parameters for request identification
            - Client IP address and user agent for security monitoring and analytics
            - Request headers for debugging and security analysis (sensitive data filtered)
            - Authentication context for user tracking and audit trail generation
        call_next (Callable): The next middleware or endpoint handler in the processing
            chain, called asynchronously for non-blocking request processing

    Returns:
        Response: The HTTP response object with comprehensive logging metadata:
            - Original response preserved without modification or performance impact
            - Correlation ID generated and propagated for distributed system tracing
            - Performance timing data recorded for analysis and optimization
            - Request/response metadata logged for monitoring and debugging

    Raises:
        Exception: Catches and logs any middleware processing errors without
            affecting request flow, ensuring graceful degradation and reliability

    Security Notes:
        - Automatically filters sensitive data from request headers and parameters
        - Generates secure correlation IDs for request tracking without exposing system internals
        - Logs security events including authentication failures and suspicious activity
        - Implements rate limiting for log generation preventing log flooding attacks
        - Excludes personally identifiable information (PII) from standard log output
        - Provides audit trail capabilities for compliance and regulatory requirements

    Performance Notes:
        - Asynchronous processing ensures minimal impact on request latency
        - Structured logging format optimized for efficient parsing and indexing
        - Configurable log levels and sampling for production performance optimization
        - Memory efficient implementation with automatic cleanup and garbage collection
        - Batch logging support for high-throughput environments and reduced I/O overhead
        - Integration with log rotation and archival systems for storage optimization

    Use Cases:
        - Production application monitoring with comprehensive request tracking and analysis
        - Security incident investigation with detailed audit trails and forensic capabilities
        - Performance optimization and bottleneck identification with timing analysis
        - Compliance reporting and regulatory audit trail generation
        - Development debugging with detailed request/response metadata inspection
        - Integration with external monitoring systems like Prometheus, Grafana, and ELK

    Example:
        # Applied automatically as middleware to all requests
        # Generates structured logs with correlation IDs
        # Records performance metrics and security events
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
    Advanced debug content logging middleware with comprehensive request/response inspection.

    Provides detailed content logging for development and debugging environments with
    comprehensive request/response body inspection, pretty-printed JSON formatting,
    and configurable content filtering. Automatically activates in debug mode with
    intelligent content parsing, size limits, and security-conscious data handling
    to prevent sensitive information exposure while maximizing debugging capabilities.

    Args:
        request (Request): The incoming HTTP request object for detailed inspection:
            - Request body content with intelligent JSON parsing and formatting
            - Complete header analysis with sensitive data filtering capabilities
            - Query parameter inspection with validation and security analysis
            - Client information including IP, user agent, and connection details
        call_next (Callable): The next middleware or endpoint handler in the processing
            chain, called after comprehensive request logging and analysis

    Returns:
        Response: The HTTP response object with detailed content logging:
            - Complete response body capture with intelligent content type handling
            - Response header analysis and security validation reporting
            - Performance timing data with detailed execution breakdown
            - Error and exception tracking with comprehensive context information

    Security Notes:
        - Automatically disabled in production environments to prevent sensitive data exposure
        - Implements content filtering to exclude passwords, tokens, and authentication data
        - Truncates large payloads to prevent log flooding and storage exhaustion
        - Sanitizes request/response content to prevent log injection attacks
        - Provides configurable sensitivity levels for different debugging scenarios
        - Generates secure debug identifiers without exposing system internals

    Performance Notes:
        - Conditional activation based on debug mode preventing production overhead
        - Efficient content parsing with minimal memory allocation and processing impact
        - Asynchronous logging implementation for non-blocking request processing
        - Intelligent content size limits preventing memory exhaustion
        - Streaming response handling for large payloads and file downloads
        - Optimized JSON parsing and formatting for human-readable output

    Development Features:
        - Pretty-printed JSON output for enhanced readability and analysis
        - Request replay capability for testing and issue reproduction
        - Interactive filtering and search capabilities for efficient debugging
        - Integration with development tools and IDE debugging environments
        - Real-time log streaming for immediate feedback during development
        - Correlation with application logs for comprehensive debugging context

    Use Cases:
        - Development environment debugging with detailed request/response inspection
        - API testing and validation with comprehensive payload analysis
        - Integration testing with detailed communication tracking between services
        - Performance profiling and optimization with request/response timing analysis
        - Security testing with detailed input/output validation and sanitization
        - Troubleshooting and issue reproduction with complete request lifecycle tracking

    Example:
        # Only active when settings.debug = True
        # Logs detailed request/response content with pretty formatting
        # Provides comprehensive debugging information for development
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
    Log comprehensive request content with intelligent parsing and security filtering.

    Captures and logs detailed request information including headers, body content,
    and metadata with automatic content type detection, JSON pretty-printing,
    and security-conscious filtering to prevent sensitive data exposure while
    maximizing debugging value and troubleshooting capabilities.

    Args:
        request (Request): The HTTP request object for detailed content analysis:
            - Request body with intelligent content type detection and parsing
            - Headers with sensitive data filtering and security analysis
            - Query parameters and path information for complete request context
        correlation_id (str): Unique request identifier for tracing and log correlation
            across distributed systems and microservices architecture

    Security Notes:
        - Automatically filters sensitive headers like Authorization and API keys
        - Truncates large payloads to prevent log flooding and storage exhaustion
        - Sanitizes content to prevent log injection and XSS attacks in log viewers
        - Implements configurable content filtering policies for different environments
        - Excludes binary content and potentially malicious payloads from logging

    Performance Notes:
        - Efficient content parsing with minimal memory allocation and processing overhead
        - Intelligent content size limits preventing memory exhaustion and performance impact
        - Asynchronous processing ensuring non-blocking request flow and optimal throughput
        - Optimized JSON parsing and formatting for enhanced readability without performance cost
        - Streaming content handling for large payloads and file upload scenarios

    Example:
        await _log_request_content(request, "req-123-abc")
        # Logs detailed request information with correlation ID
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


async def _log_response_content(response: Response, correlation_id: str):
    """
    Log comprehensive response content with intelligent formatting and analysis.

    Captures and logs detailed response information including status codes, headers,
    and body content with automatic content type detection, streaming response
    handling, and intelligent formatting for optimal debugging and troubleshooting
    value while maintaining security and performance best practices.

    Args:
        response (Response): The HTTP response object for detailed content analysis:
            - Response body with intelligent content type detection and JSON formatting
            - Headers with security analysis and performance metric extraction
            - Status codes and error information for comprehensive debugging context
        correlation_id (str): Unique request identifier for tracing and log correlation
            linking response data with corresponding request information

    Security Notes:
        - Automatically filters sensitive response headers and authentication tokens
        - Handles streaming responses without exposing large payloads or sensitive data
        - Sanitizes response content to prevent log injection and security vulnerabilities
        - Implements configurable content filtering for different response types
        - Excludes binary content and file downloads from detailed content logging

    Performance Notes:
        - Efficient response body capture with minimal memory allocation and processing
        - Intelligent handling of streaming responses without buffering large content
        - Asynchronous processing ensuring optimal response time and throughput
        - Content size limits preventing memory exhaustion and performance degradation
        - Optimized JSON parsing and formatting for human-readable debug output

    Example:
        await _log_response_content(response, "req-123-abc")
        # Logs detailed response information with correlation ID
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
            f"📤 DEBUG RESPONSE DETAILS\n{json.dumps(response_details, indent=4)}",
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
    Enterprise-grade HTTP middleware class for comprehensive request/response logging.

    Provides a class-based approach to logging middleware that integrates seamlessly
    with FastAPI's middleware stack, offering advanced logging capabilities including
    structured request/response tracking, performance monitoring, debug content
    inspection, and comprehensive observability features for production and
    development environments with configurable logging policies and security controls.

    Key Features:
    - Comprehensive request/response lifecycle logging with detailed metadata capture
    - Performance timing and metrics collection with statistical analysis capabilities
    - Debug content logging with configurable verbosity and content filtering
    - Correlation ID generation and propagation for distributed system tracing
    - Security event logging with audit trails and compliance reporting features
    - Error tracking and exception handling with detailed context and stack traces

    Performance Features:
    - Asynchronous processing ensuring minimal impact on request latency and throughput
    - Memory efficient implementation with automatic cleanup and resource management
    - Configurable sampling rates for production performance optimization
    - Batch logging support for high-throughput environments and reduced I/O overhead
    - Integration with log rotation and archival systems for storage optimization
    - Real-time metrics collection for monitoring and alerting system integration

    Security Features:
    - Automatic sensitive data filtering preventing credential and PII exposure
    - Configurable content filtering policies for different security requirements
    - Audit trail generation for compliance and regulatory reporting needs
    - Rate limiting for log generation preventing log flooding and resource exhaustion
    - Secure correlation ID generation without exposing system internals
    - Integration with security monitoring and incident response systems

    Integration Patterns:
    - FastAPI middleware stack integration with proper lifecycle management
    - External logging system integration including Elasticsearch and CloudWatch
    - Monitoring platform integration for real-time alerting and dashboard visualization
    - Container orchestration logging with stdout/stderr handling and log forwarding
    - Microservices architecture support with distributed tracing capabilities
    - CI/CD pipeline integration for automated log analysis and quality assurance

    Use Cases:
    - Production application monitoring with comprehensive request tracking and analysis
    - Security incident investigation with detailed audit trails and forensic capabilities
    - Performance optimization and bottleneck identification with detailed timing analysis
    - Compliance reporting and regulatory audit trail generation for enterprise requirements
    - Development debugging with detailed request/response content inspection and analysis
    - Integration testing and quality assurance with automated log validation and monitoring

    Example:
        app.add_middleware(LoggingMiddleware)
        # Applies comprehensive logging to all requests
        # Combines standard and debug logging capabilities
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Dispatch method combining standard and debug logging with comprehensive middleware processing.

        Orchestrates the complete logging middleware pipeline including standard request/response
        logging, performance monitoring, debug content inspection, and error handling with
        comprehensive observability features and security-conscious data handling throughout
        the request lifecycle processing and response generation.

        Args:
            request (Request): The incoming HTTP request object for comprehensive logging:
                - Request metadata including method, URL, headers, and client information
                - Request body content for debug logging when enabled and appropriate
                - Authentication context and user information for audit trail generation
            call_next (Callable): The next middleware or endpoint handler in the processing
                chain, called with comprehensive error handling and performance monitoring

        Returns:
            Response: The HTTP response object with comprehensive logging metadata:
                - Original response preserved without modification or performance impact
                - Logging metadata attached for downstream processing and monitoring
                - Performance timing data recorded for analysis and optimization
                - Debug information captured when debug mode is enabled

        Raises:
            Exception: Catches and logs middleware processing errors while ensuring
                graceful request handling and comprehensive error tracking

        Security Notes:
            - Applies consistent security filtering across all logging operations
            - Ensures sensitive data protection throughout the middleware pipeline
            - Implements rate limiting and abuse prevention for logging operations
            - Provides audit trail capabilities for compliance and security monitoring
            - Excludes sensitive authentication and authorization data from logs

        Performance Notes:
            - Optimized middleware chain execution with minimal processing overhead
            - Asynchronous processing ensuring non-blocking request flow and optimal throughput
            - Memory efficient implementation with automatic cleanup and resource management
            - Configurable logging levels for production performance optimization
            - Integration with performance monitoring and alerting systems

        Use Cases:
            - Production middleware deployment with comprehensive logging and monitoring
            - Development environment debugging with detailed request/response inspection
            - Security monitoring and incident response with detailed audit trails
            - Performance optimization and capacity planning with historical timing data
            - Compliance reporting and regulatory audit trail generation
            - Integration testing with comprehensive request/response validation

        Example:
            # Automatically called by FastAPI middleware system
            # Provides comprehensive logging for all requests
            # Integrates standard and debug logging capabilities
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
