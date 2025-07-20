"""
Authentication API endpoints.

This module provides endpoints for user authentication including
registration, login, token refresh, and password management.

Generated on: 2025-07-14 03:12:05 UTC
Current User: lllucius
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import AuthenticationError, ValidationError
from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    Token,
)
from ..schemas.common import BaseResponse
from ..schemas.user import UserResponse
from ..services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Get authentication service instance."""
    return AuthService(db)


@router.post("/register", response_model=UserResponse)
async def register(
    request: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account.

    Creates a new user with the provided credentials.
    Username and email must be unique.
    """
    try:
        user = await auth_service.register_user(request)
        return UserResponse.model_validate(user)

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login", response_model=Token)
async def login(
    request: LoginRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and return access token.

    Validates user credentials and returns a JWT token
    for accessing protected endpoints.
    """
    try:
        token_data = await auth_service.authenticate_user(
            request.username, request.password
        )
        return token_data

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information.

    Returns the profile information for the currently
    authenticated user.
    """
    return UserResponse.model_validate(current_user)


@router.post("/logout", response_model=BaseResponse)
async def logout():
    """
    Logout current user.

    Note: Since we use stateless JWT tokens, this endpoint
    mainly serves as a client-side logout indicator.
    Clients should discard their tokens.
    """
    return BaseResponse(success=True, message="Logged out successfully")


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Refresh access token.

    Generates a new access token for the current user.
    Requires a valid existing token.
    """
    try:
        token_data = auth_service.create_access_token({"sub": current_user.username})
        return token_data

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )


@router.post("/password-reset", response_model=BaseResponse)
async def request_password_reset(
    request: PasswordResetRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """
    Request password reset.

    Initiates password reset process for the given email address.
    Note: This is a placeholder implementation.
    """
    # TODO: Implement actual password reset with email tokens
    return BaseResponse(
        success=True, message="Password reset instructions sent to email"
    )


@router.post("/password-reset/confirm", response_model=BaseResponse)
async def confirm_password_reset(
    request: PasswordResetConfirm, auth_service: AuthService = Depends(get_auth_service)
):
    """
    Confirm password reset.

    Resets user password using the provided reset token.
    Note: This is a placeholder implementation.
    """
    # TODO: Implement actual password reset confirmation
    return BaseResponse(success=True, message="Password reset successfully")
