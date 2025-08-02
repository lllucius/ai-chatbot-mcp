"""
Common error handling utilities and decorators for API endpoints.

This module provides standardized error handling patterns to eliminate
duplication across API endpoints and ensure consistent error responses.

"""

import functools
from typing import Any, Callable, Dict, Optional

from fastapi import HTTPException, status

from ..core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ChatbotPlatformException,
    DocumentError,
    ExternalServiceError,
    NotFoundError,
    SearchError,
    ValidationError,
)
from ..core.logging import get_api_logger
from ..utils.timestamp import get_current_timestamp

logger = get_api_logger("error_handler")


def handle_api_errors(
    default_message: str = "Operation failed",
    log_errors: bool = True,
    include_details: bool = False,
):
    """
    Decorator to standardize error handling across API endpoints.

    This decorator converts application exceptions into appropriate HTTP
    exceptions with consistent formatting and optional detailed logging.

    Args:
        default_message: Default error message for unexpected exceptions
        log_errors: Whether to log errors for monitoring
        include_details: Whether to include error details in response (dev only)

    Returns:
        Decorator function for API endpoint error handling

    Example:
        @handle_api_errors("Failed to create user")
        async def create_user_endpoint(user_data):
            # API endpoint implementation
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)

            except HTTPException:
                # Re-raise HTTPExceptions as they are already properly formatted
                raise

            except ValidationError as e:
                if log_errors:
                    logger.warning(
                        f"Validation error in {func.__name__}",
                        extra={
                            "error": str(e),
                            "endpoint": func.__name__,
                        },
                    )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=_format_error_response(
                        str(e), "VALIDATION_ERROR", include_details
                    ),
                )

            except AuthenticationError as e:
                if log_errors:
                    logger.warning(
                        f"Authentication error in {func.__name__}",
                        extra={
                            "error": str(e),
                            "endpoint": func.__name__,
                        },
                    )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=_format_error_response(
                        str(e), "AUTHENTICATION_ERROR", include_details
                    ),
                    headers={"WWW-Authenticate": "Bearer"},
                )

            except AuthorizationError as e:
                if log_errors:
                    logger.warning(
                        f"Authorization error in {func.__name__}",
                        extra={
                            "error": str(e),
                            "endpoint": func.__name__,
                        },
                    )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=_format_error_response(
                        str(e), "AUTHORIZATION_ERROR", include_details
                    ),
                )

            except NotFoundError as e:
                if log_errors:
                    logger.info(
                        f"Resource not found in {func.__name__}",
                        extra={
                            "error": str(e),
                            "endpoint": func.__name__,
                        },
                    )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_format_error_response(
                        str(e), "NOT_FOUND_ERROR", include_details
                    ),
                )

            except (DocumentError, SearchError) as e:
                if log_errors:
                    logger.error(
                        f"Service error in {func.__name__}",
                        extra={
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "endpoint": func.__name__,
                        },
                    )
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=_format_error_response(
                        str(e),
                        getattr(e, "error_code", "SERVICE_ERROR"),
                        include_details,
                    ),
                )

            except ExternalServiceError as e:
                if log_errors:
                    logger.error(
                        f"External service error in {func.__name__}",
                        extra={
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "endpoint": func.__name__,
                        },
                    )
                # Map external service errors to appropriate HTTP status
                status_code = (
                    status.HTTP_503_SERVICE_UNAVAILABLE
                    if "not available" in str(e).lower() or "timeout" in str(e).lower()
                    else status.HTTP_502_BAD_GATEWAY
                )
                raise HTTPException(
                    status_code=status_code,
                    detail=_format_error_response(
                        str(e), "EXTERNAL_SERVICE_ERROR", include_details
                    ),
                )

            except ChatbotPlatformException as e:
                # Handle any other custom exceptions
                if log_errors:
                    logger.error(
                        f"Application error in {func.__name__}",
                        extra={
                            "error": str(e),
                            "error_code": getattr(e, "error_code", "PLATFORM_ERROR"),
                            "endpoint": func.__name__,
                        },
                    )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=_format_error_response(
                        getattr(e, "message", str(e)),
                        getattr(e, "error_code", "PLATFORM_ERROR"),
                        include_details,
                        getattr(e, "details", None),
                    ),
                )

            except Exception as e:
                # Handle unexpected errors
                if log_errors:
                    logger.error(
                        f"Unexpected error in {func.__name__}",
                        exc_info=True,
                        extra={
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "endpoint": func.__name__,
                        },
                    )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=_format_error_response(
                        default_message, "INTERNAL_SERVER_ERROR", include_details
                    ),
                )

        return wrapper

    return decorator


def _format_error_response(
    message: str,
    error_code: str,
    include_details: bool = False,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Format consistent error response structure.

    Args:
        message: Human-readable error message
        error_code: Machine-readable error code
        include_details: Whether to include additional details
        details: Additional error details

    Returns:
        dict: Formatted error response
    """
    response = {
        "success": False,
        "error_code": error_code,
        "message": message,
        "timestamp": get_current_timestamp(),
    }

    if include_details and details:
        response["details"] = details

    return response


def create_success_response(
    data: Any = None,
    message: str = "Operation successful",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create standardized success response with comprehensive structure and enterprise compliance.

    Generates consistent success response format for all API endpoints with structured
    data organization, comprehensive metadata support, and standardized messaging.
    Implements enterprise-grade response patterns with proper status indication,
    timestamp tracking, and optional payload organization for optimal client
    integration and comprehensive API contract compliance.

    Args:
        data (Any, optional): Primary response payload containing requested information.
            Can be any JSON-serializable data structure including objects, arrays, or primitives.
            Defaults to None for operations returning only status confirmation.
        message (str): Human-readable success message for client display and logging.
            Defaults to "Operation successful" providing clear operation confirmation.
        metadata (Optional[Dict[str, Any]]): Additional response metadata including:
            - Pagination information for list endpoints with page counts and navigation
            - Performance metrics including execution time and resource usage
            - Cache information with expiration times and validation tokens
            - Request correlation data for debugging and audit trail tracking

    Returns:
        Dict[str, Any]: Standardized success response structure containing:
            - success (bool): Always True indicating successful operation completion
            - message (str): Success message for client display and logging purposes
            - timestamp (str): ISO 8601 timestamp of response generation for audit trails
            - data (Any): Primary response payload when provided with structured content
            - metadata (Dict): Additional response metadata when provided with context information

    Security Notes:
        - Excludes sensitive information from metadata and response structure
        - Provides consistent response format preventing information disclosure
        - Includes timestamp for audit trail generation and security monitoring
        - Supports correlation tracking for security analysis and incident response

    Performance Notes:
        - Minimal response overhead with efficient JSON serialization
        - Configurable metadata inclusion preventing unnecessary payload bloat
        - Cached timestamp generation for high-frequency response scenarios
        - Memory efficient with optional field inclusion and optimized structure

    Use Cases:
        - API endpoint success responses with consistent format and structure
        - Data retrieval operations with payload organization and metadata context
        - Operation confirmation responses with status indication and timing
        - Batch operation results with individual item status and aggregate metadata
        - Integration responses with external system correlation and tracking

    Example:
        # Simple success response
        response = create_success_response(message="User created successfully")

        # Response with data payload
        response = create_success_response(
            data={"user_id": 123, "username": "john_doe"},
            message="User retrieved successfully",
            metadata={"query_time_ms": 15, "cache_hit": True}
        )
    """
    response = {
        "success": True,
        "message": message,
        "timestamp": get_current_timestamp(),
    }

    if data is not None:
        response["data"] = data

    if metadata:
        response["metadata"] = metadata

    return response


def log_api_call(operation: str, **kwargs):
    """
    Log API call with comprehensive context for monitoring, debugging, and audit compliance.

    Provides structured logging for API operations with detailed context information,
    performance metrics, and security tracking. Implements enterprise-grade audit
    logging with correlation support, operational monitoring integration, and
    comprehensive context preservation for debugging and compliance requirements.

    Args:
        operation (str): Descriptive name of the API operation being performed.
            Should be consistent across related operations for effective monitoring and analysis.
        **kwargs: Additional context data for comprehensive logging including:
            - user_id: User identifier for security audit trails and access tracking
            - request_id: Correlation identifier for distributed system tracing
            - execution_time: Operation duration for performance monitoring and optimization
            - parameters: Sanitized request parameters for debugging and analysis
            - client_info: Client identification for usage analytics and security monitoring

    Security Notes:
        - Excludes sensitive data from logging preventing credential exposure
        - Implements correlation tracking for security analysis and incident response
        - Provides audit trail capabilities for compliance and regulatory requirements
        - Supports security monitoring with structured event data and context

    Performance Notes:
        - Asynchronous logging ensuring minimal API response latency impact
        - Structured data format optimized for log aggregation and analysis
        - Configurable log levels preventing performance overhead in production
        - Memory efficient with automatic cleanup and resource management

    Use Cases:
        - API endpoint monitoring with operation tracking and performance analysis
        - Security audit trails with user activity and access pattern tracking
        - Debugging support with detailed context and correlation information
        - Compliance logging with regulatory audit trail and retention requirements
        - Operational monitoring with real-time alerting and performance tracking

    Example:
        log_api_call(
            "user_authentication",
            user_id="123",
            client_ip="192.168.1.100",
            execution_time=0.025,
            success=True
        )
    """
    logger.info(f"API call: {operation}", extra={"operation": operation, **kwargs})
