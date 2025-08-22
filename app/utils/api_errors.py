"""Common error handling utilities and decorators for API endpoints.

This module provides standardized error handling patterns to eliminate
duplication across API endpoints and ensure consistent error responses.

"""

import functools
from typing import Any, Callable

from fastapi import status

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
from shared.schemas.common import ErrorResponse

logger = get_api_logger("error_handler")


def handle_api_errors(
    default_message: str = "Operation failed",
    log_errors: bool = True,
    include_details: bool = False,
):
    """Standardize error handling across API endpoints.

    This decorator converts application exceptions into appropriate RFC9457
    formatted error responses with consistent formatting and optional detailed logging.

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

            except ValidationError as e:
                if log_errors:
                    logger.warning(
                        f"Validation error in {func.__name__}",
                        extra={
                            "error": str(e),
                            "endpoint": func.__name__,
                        },
                    )
                return ErrorResponse.create(
                    error_code="VALIDATION_ERROR",
                    message=e.message,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error_details=e.details if include_details else None,
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
                return ErrorResponse.create(
                    error_code="AUTHENTICATION_ERROR",
                    message=e.message,
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    error_details=e.details if include_details else None,
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
                return ErrorResponse.create(
                    error_code="AUTHORIZATION_ERROR",
                    message=e.message,
                    status_code=status.HTTP_403_FORBIDDEN,
                    error_details=e.details if include_details else None,
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
                return ErrorResponse.create(
                    error_code="NOT_FOUND_ERROR",
                    message=e.message,
                    status_code=status.HTTP_404_NOT_FOUND,
                    error_details=e.details if include_details else None,
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
                return ErrorResponse.create(
                    error_code=f"{type(e).__name__.upper().replace('ERROR', '')}_ERROR",
                    message=e.message,
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    error_details=e.details if include_details else None,
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
                return ErrorResponse.create(
                    error_code="EXTERNAL_SERVICE_ERROR",
                    message=e.message,
                    status_code=status_code,
                    error_details=e.details if include_details else None,
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
                return ErrorResponse.create(
                    error_code=getattr(e, "error_code", "PLATFORM_ERROR"),
                    message=getattr(e, "message", str(e)),
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error_details=e.details if include_details else None,
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
                return ErrorResponse.create(
                    error_code="INTERNAL_SERVER_ERROR",
                    message=default_message,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return wrapper

    return decorator


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
