import json
from typing import Any, Dict, List, Optional, TypeVar

from fastapi import status
from fastapi.responses import JSONResponse

from shared.schemas.common import (
    APIResponse,
    ErrorDetail,
    ErrorDetails,
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
    """Create successful response using unified envelope format."""
    response = APIResponse(
        success=True, data=data, message=message, meta=meta, timestamp=utcnow()
    )
    # Use the custom JSON serialization from the model to handle datetime
    content_str = response.model_dump_json(exclude_none=True)
    content = json.loads(content_str)
    return JSONResponse(
        content=content, status_code=status_code
    )


def error_response(
    error_code: str,
    message: str = "An error occurred",
    status_code: int = status.HTTP_400_BAD_REQUEST,
    data: Any = None,
    error_details: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Create error response using unified envelope format."""
    response = APIResponse(
        success=False,
        data=data,
        message=message,
        error=ErrorDetails(code=error_code, details=error_details),
        timestamp=utcnow(),
        meta=meta,
    )
    # Use the custom JSON serialization from the model to handle datetime
    content_str = response.model_dump_json(exclude_none=True)
    content = json.loads(content_str)
    return JSONResponse(
        content=content, status_code=status_code
    )


def paginated_response(
    items: List[T],
    page: int,
    size: int,
    total: int,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    """Create paginated response using unified envelope format."""
    # Calculate pagination metadata
    total_pages = (total + size - 1) // size  # Ceiling division
    has_next = page < total_pages
    has_prev = page > 1

    pagination_meta = {
        "page": page,
        "per_page": size,
        "total": total,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_prev": has_prev
    }

    return success_response(
        data=items,
        message=message,
        meta={"pagination": pagination_meta},
        status_code=status_code
    )


def validation_error_response(
    errors: List[Dict[str, Any]], message: str = "Validation failed"
) -> JSONResponse:
    """Create validation error response using unified envelope format."""
    error_details = [
        ErrorDetail(
            code=error.get("type", "validation_error"),
            message=error.get("msg", "Invalid value"),
            field=".".join(str(loc) for loc in error.get("loc", [])),
            details=error,
        )
        for error in errors
    ]

    response = APIResponse(
        success=False,
        message=message,
        error=ErrorDetails(
            code="VALIDATION_ERROR",
            details={"validation_errors": [err.model_dump() for err in error_details]}
        ),
        timestamp=utcnow(),
    )

    # Use the custom JSON serialization from the model to handle datetime
    content_str = response.model_dump_json(exclude_none=True)
    content = json.loads(content_str)
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )
