"""
User-related Pydantic schemas for API requests and responses.

This module defines schemas for user operations including creation,
updates, authentication, and API responses using modern Pydantic V2.

"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import ConfigDict, EmailStr, Field, field_validator

from ..utils.timestamp import utcnow
from .base import BaseSchema
from .common import BaseResponse, PaginationParams


class UserBase(BaseSchema):
    """Base user schema with common fields."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        validate_assignment=True,
        extra="ignore",
    )

    username: str = Field(
        min_length=3,
        max_length=50,
        pattern="^[a-zA-Z0-9_-]+$",
        description="Unique username",
    )
    email: EmailStr = Field(description="User email address")
    full_name: Optional[str] = Field(default=None, max_length=100, description="User's full name")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not v:
            raise ValueError("Username cannot be empty")
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if len(v) > 50:
            raise ValueError("Username cannot be longer than 50 characters")
        return v.lower()


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(
        min_length=8, max_length=128, description="User password (minimum 8 characters)"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseSchema):
    """Schema for updating a user."""

    model_config = ConfigDict(from_attributes=True, validate_assignment=True, extra="ignore")

    email: Optional[EmailStr] = Field(default=None, description="New email address")
    full_name: Optional[str] = Field(default=None, max_length=100, description="Updated full name")
    is_active: Optional[bool] = Field(default=None, description="Whether user is active")


class UserPasswordUpdate(BaseSchema):
    """Schema for updating user password."""

    model_config = ConfigDict(validate_assignment=True)

    current_password: str = Field(description="Current password")
    new_password: str = Field(min_length=8, max_length=128, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserResponse(UserBase):
    """Schema for user API responses."""

    id: uuid.UUID = Field(description="Unique user identifier")
    is_active: bool = Field(description="Whether the user account is active")
    is_superuser: bool = Field(description="Whether the user has admin privileges")
    created_at: datetime = Field(description="When the user account was created")

    def model_dump_json(self, **kwargs):
        """Custom JSON serialization with UUID and datetime handling."""
        data = self.model_dump(**kwargs)

        # Convert UUID to string
        if "id" in data and data["id"] is not None:
            if isinstance(data["id"], uuid.UUID):
                data["id"] = str(data["id"])

        # Convert datetime fields to ISO format strings
        for field_name in ["created_at", "updated_at"]:
            if field_name in data and data[field_name] is not None:
                if isinstance(data[field_name], datetime):
                    data[field_name] = data[field_name].isoformat() + "Z"

        import json

        return json.dumps(data)


class UserListResponse(BaseResponse):
    """Response schema for user list endpoints."""

    users: List[UserResponse] = Field(description="List of users")
    total_count: int = Field(description="Total number of users")


class UserDetailResponse(BaseResponse):
    """Response schema for user detail endpoints."""

    user: UserResponse = Field(description="User details")


class UserSearchParams(PaginationParams):
    """Search parameters for user queries."""

    username: Optional[str] = Field(default=None, description="Filter by username (partial match)")
    email: Optional[str] = Field(default=None, description="Filter by email (partial match)")
    is_active: Optional[bool] = Field(default=None, description="Filter by active status")
    is_superuser: Optional[bool] = Field(default=None, description="Filter by superuser status")


class UserStatsResponse(BaseSchema):
    """Response schema for user statistics."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    total_users: int = Field(description="Total number of users")
    active_users: int = Field(description="Number of active users")
    inactive_users: int = Field(description="Number of inactive users")
    superusers: int = Field(description="Number of superusers")
    users_created_today: int = Field(description="Users created today")
    users_created_this_week: int = Field(description="Users created this week")
    users_created_this_month: int = Field(description="Users created this month")
    last_updated: datetime = Field(
        default_factory=utcnow, description="When statistics were last calculated"
    )

    def model_dump_json(self, **kwargs):
        """Custom JSON serialization with datetime handling."""
        data = self.model_dump(**kwargs)

        # Convert last_updated to ISO format string
        if "last_updated" in data and data["last_updated"] is not None:
            if isinstance(data["last_updated"], datetime):
                data["last_updated"] = data["last_updated"].isoformat() + "Z"

        import json

        return json.dumps(data)
