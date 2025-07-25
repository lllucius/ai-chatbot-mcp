"""
Shared models between the API and SDK.

This module defines common Pydantic models that are used by both the
API endpoints and the client SDK to ensure consistency and reduce duplication.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Base models
class BaseResponse(BaseModel):
    """Base response model for API responses."""

    success: bool = Field(True, description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable message")
    timestamp: Optional[str] = Field(None, description="Response timestamp")


class PaginationParams(BaseModel):
    """Pagination parameters for list requests."""

    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(10, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: Optional[str] = Field(
        "asc", pattern="^(asc|desc)$", description="Sort order"
    )


# Common field types used across models
def uuid_field(description: str) -> UUID:
    """Helper for UUID fields with description."""
    return Field(..., description=description)


def optional_str_field(
    description: str, max_length: Optional[int] = None
) -> Optional[str]:
    """Helper for optional string fields."""
    return Field(None, max_length=max_length, description=description)


def datetime_field(description: str) -> datetime:
    """Helper for datetime fields."""
    return Field(..., description=description)


def metadata_field() -> Optional[Dict[str, Any]]:
    """Helper for metadata fields."""
    return Field(None, description="Additional metadata")
