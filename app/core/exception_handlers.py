"""Updated exception handlers with proper response formatting."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import AppException
from shared.schemas.common import ErrorResponse, ValidationErrorResponse

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions."""
    logger.error(
        f"Application exception: {exc.message}", extra={"details": exc.details}
    )

    # Map exception types to HTTP status codes
    from app.core.exceptions import (
        AuthenticationException,
        AuthorizationException,
        DatabaseException,
        ExternalAPIException,
        ValidationException,
    )

    status_code_map = {
        AuthenticationException: status.HTTP_401_UNAUTHORIZED,
        AuthorizationException: status.HTTP_403_FORBIDDEN,
        ValidationException: status.HTTP_422_UNPROCESSABLE_ENTITY,
        DatabaseException: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ExternalAPIException: status.HTTP_502_BAD_GATEWAY,
    }

    status_code = status_code_map.get(type(exc), status.HTTP_400_BAD_REQUEST)

    return ErrorResponse.create(
        error_code=exc.error_code or "APPLICATION_ERROR",
        message=exc.message,
        status_code=status_code,
        error_details=exc.details,
    )


async def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.error(f"Validation error: {exc}")
    return ValidationErrorResponse.create(exc.errors())


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Handle SQLAlchemy database errors."""
    logger.error(f"Database error: {exc}")

    return ErrorResponse.create(
        error_code="DATABASE_ERROR",
        message="Database operation failed",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    return ErrorResponse.create(
        error_code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def add_exception_handlers(app: FastAPI) -> None:
    """Add all exception handlers to the FastAPI app."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
