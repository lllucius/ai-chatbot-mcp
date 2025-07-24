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
from ..utils.logging import get_api_logger
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

            except ValidationError as e:
                if log_errors:
                    logger.warning(
                        f"Validation error in {func.__name__}",
                        error=str(e),
                        endpoint=func.__name__,
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
                        error=str(e),
                        endpoint=func.__name__,
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
                        error=str(e),
                        endpoint=func.__name__,
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
                        error=str(e),
                        endpoint=func.__name__,
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
                        error=str(e),
                        error_type=type(e).__name__,
                        endpoint=func.__name__,
                    )
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=_format_error_response(
                        str(e), e.error_code, include_details
                    ),
                )

            except ExternalServiceError as e:
                if log_errors:
                    logger.error(
                        f"External service error in {func.__name__}",
                        error=str(e),
                        error_type=type(e).__name__,
                        endpoint=func.__name__,
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
                        error=str(e),
                        error_code=e.error_code,
                        endpoint=func.__name__,
                    )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=_format_error_response(
                        e.message, e.error_code, include_details, e.details
                    ),
                )

            except Exception as e:
                # Handle unexpected errors
                if log_errors:
                    logger.error(
                        f"Unexpected error in {func.__name__}",
                        error=str(e),
                        error_type=type(e).__name__,
                        endpoint=func.__name__,
                        exc_info=True,
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
    Create standardized success response.

    Args:
        data: Response data payload
        message: Success message
        metadata: Additional response metadata

    Returns:
        dict: Formatted success response
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
    Log API call for monitoring and debugging.

    Args:
        operation: Name of the API operation
        **kwargs: Additional context data
    """
    logger.info(f"API call: {operation}", operation=operation, **kwargs)
