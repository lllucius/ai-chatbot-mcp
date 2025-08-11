"""Common error handling utilities and decorators for API endpoints.

This module provides standardized error handling patterns to eliminate
duplication across API endpoints and ensure consistent error responses.

"""

import functools
from typing import Any, Callable, Dict, Optional

from fastapi import HTTPException, status

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ChatbotPlatformException,
    DocumentError,
    ExternalServiceError,
    NotFoundError,
    SearchError,
    ValidationError,
)
from app.core.logging import get_api_logger
from app.utils.timestamp import get_current_timestamp

logger = get_api_logger("error_handler")


def handle_api_errors(
    default_message: str = "Operation failed",
    log_errors: bool = True,
    include_details: bool = False,
):
    """Standardize error handling across API endpoints.

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
    """Format consistent error response structure.

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
    """Create standardized success response with structured data organization.

    Generates consistent success response format for all API endpoints with
    optional data payload and metadata support.

    Args:
        data: Primary response payload (optional)
        message: Human-readable success message
        metadata: Additional response metadata (optional)

    Returns:
        Dict containing success indicator, message, timestamp, and optional data/metadata

    Example:
        response = create_success_response(
            data={"user_id": 123},
            message="User created successfully"
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
    """Log API call with context for monitoring, debugging, and audit compliance.

    Provides structured logging for API operations with context information,
    performance metrics, and security tracking for comprehensive audit trails.

    Args:
        operation: Descriptive name of the API operation being performed
        **kwargs: Additional context data including user_id, request_id,
            execution_time, parameters, and client_info

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
