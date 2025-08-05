"""Authentication API endpoints."""

from fastapi import APIRouter, Depends
from typing import Annotated

from shared.schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    Token,
)
from shared.schemas.common import (
    APIResponse,
)
from shared.schemas.user import UserResponse

from ..dependencies import get_auth_service, get_current_user
from ..models.user import User
from ..services.auth import AuthService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["authentication"])


@router.post("/register", response_model=APIResponse[UserResponse])
@handle_api_errors("User registration failed")
async def register(
    request: RegisterRequest, auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> APIResponse[UserResponse]:
    """Register a new user account."""
    log_api_call("register", username=request.username, email=request.email)

    user = await auth_service.register_user(request)
    payload = UserResponse.model_validate(user)
    return APIResponse[UserResponse](
        success=True,
        message="User registered successfully",
        data=payload,
    )


@router.post("/login", response_model=APIResponse[Token])
@handle_api_errors("User authentication failed")
async def login(
    request: LoginRequest, auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> APIResponse[Token]:
    """Authenticate user and generate JWT access token."""
    log_api_call("login", username=request.username)

    token_data = await auth_service.authenticate_user(
        request.username, request.password
    )
    if not isinstance(token_data, Token):
        # Defensive: convert dict to Token
        token_data = Token(**token_data)
    return APIResponse[Token](
        success=True,
        message="User authenticated successfully",
        data=token_data,
    )


@router.get("/me", response_model=APIResponse[UserResponse])
@handle_api_errors("Failed to get current user information")
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
) -> APIResponse[UserResponse]:
    """Get current authenticated user information."""
    log_api_call("get_current_user_info", user_id=str(current_user.id))
    payload = UserResponse.model_validate(current_user)
    return APIResponse[UserResponse](
        success=True,
        message="User information retrieved successfully",
        data=payload,
    )


@router.post("/logout", response_model=APIResponse)
@handle_api_errors("Logout failed")
async def logout() -> APIResponse:
    """Logout current user session."""
    log_api_call("logout")
    return APIResponse[LogoutResponseModel](
        success=True,
        message="Logged out successfully",
    )


@router.post("/refresh", response_model=APIResponse[Token])
@handle_api_errors("Token refresh failed")
async def refresh_token(
    current_user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> APIResponse[Token]:
    """Refresh JWT access token for session continuation."""
    log_api_call("refresh_token", user_id=str(current_user.id))

    token_data = auth_service.create_access_token({"sub": current_user.username})
    if not isinstance(token_data, Token):
        token_data = Token(**token_data)
    return APIResponse[Token](
        success=True,
        message="Token refreshed successfully",
        data=token_data,
    )


@router.post("/password-reset", response_model=APIResponse)
@handle_api_errors("Password reset request failed")
async def request_password_reset(
    request: PasswordResetRequest, auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> APIResponse:
    """Request password reset through administrative channels."""
    log_api_call("request_password_reset", email=request.email)

    return APIResponse[PasswordResetRequestResponseModel](
        success=True,
        message="Password reset request noted. Contact system administrator for password changes.",
    )


@router.post("/password-reset/confirm", response_model=APIResponse)
@handle_api_errors("Password reset confirmation failed")
async def confirm_password_reset(
    request: PasswordResetConfirm, auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> APIResponse:
    """Confirm password reset through administrative channels."""
    log_api_call("confirm_password_reset", token=request.token[:8] + "...")

    return APIResponse[PasswordResetConfirmResponseModel](
        success=True,
        message="Password reset must be performed by system administrator through user management interface.",
    )
