"Pydantic schemas for auth data validation."

import re
from typing import Optional
from pydantic import EmailStr, Field, field_validator
from .base import BaseSchema


class LoginRequest(BaseSchema):
    "LoginRequest schema for data validation and serialization."

    username: str = Field(
        ..., min_length=3, max_length=50, description="Username or email"
    )
    password: str = Field(..., min_length=8, max_length=100, description="Password")
    model_config = {
        "json_schema_extra": {
            "example": {"username": "johndoe", "password": "SecurePass123"}
        }
    }


class RegisterRequest(BaseSchema):
    "RegisterRequest schema for data validation and serialization."

    username: str = Field(
        ..., min_length=3, max_length=50, description="Unique username"
    )
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(
        ..., min_length=8, max_length=100, description="Strong password"
    )
    full_name: Optional[str] = Field(
        None, max_length=255, description="Full display name"
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        "Validate username data."
        if not re.match("^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        "Validate password data."
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search("[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search("[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search("\\d", v):
            raise ValueError("Password must contain at least one number")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "SecurePass123",
                "full_name": "John Doe",
            }
        }
    }


class Token(BaseSchema):
    "Token class for specialized functionality."

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
            }
        }
    }


class PasswordResetRequest(BaseSchema):
    "PasswordResetRequest schema for data validation and serialization."

    email: EmailStr = Field(..., description="Email address for password reset")
    model_config = {"json_schema_extra": {"example": {"email": "john@example.com"}}}


class PasswordResetConfirm(BaseSchema):
    "PasswordResetConfirm class for specialized functionality."

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(
        ..., min_length=8, max_length=100, description="New password"
    )

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        "Validate password data."
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search("[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search("[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search("\\d", v):
            raise ValueError("Password must contain at least one number")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {"token": "reset_token_here", "new_password": "NewSecurePass123"}
        }
    }
