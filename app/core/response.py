"""
Updated response handling with proper Generic support.
"""

from typing import Any, Dict, List, Optional, TypeVar

from fastapi import status
from fastapi.responses import JSONResponse

from shared.schemas.common import (
    APIResponse,
    ErrorDetail,
    PaginatedResponse,
    ValidationErrorResponse,
)
from app.utils.timestamp import utcnow

T = TypeVar("T")


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK,
    meta: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Create successful response."""
    response = APIResponse(
        success=True, data=data, message=message, meta=meta, timestamp=utcnow()
    )
    return JSONResponse(
        content=response.model_dump(exclude_none=True), status_code=status_code
    )


def error_response(
    error: str,
    message: str = "An error occurred",
    status_code: int = status.HTTP_400_BAD_REQUEST,
    data: Any = None,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Create error response."""
    response = APIResponse(
        success=False,
        data=data,
        message=message,
        error=error,
        timestamp=utcnow(),
        meta=details,
    )
    return JSONResponse(
        content=response.model_dump(exclude_none=True), status_code=status_code
    )


def paginated_response(
    items: List[T],
    page: int,
    size: int,
    total: int,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    """Create paginated response."""
    paginated_data = PaginatedResponse.create(
        items=items, page=page, size=size, total=total
    )

    return success_response(
        data=paginated_data.model_dump(), message=message, status_code=status_code
    )


def validation_error_response(
    errors: List[Dict[str, Any]], message: str = "Validation failed"
) -> JSONResponse:
    """Create validation error response."""
    error_details = [
        ErrorDetail(
            code=error.get("type", "validation_error"),
            message=error.get("msg", "Invalid value"),
            field=".".join(str(loc) for loc in error.get("loc", [])),
            details=error,
        )
        for error in errors
    ]

    response = ValidationErrorResponse(
        message=message, errors=error_details, timestamp=utcnow()
    )

    return JSONResponse(
        content=response.model_dump(), status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )
