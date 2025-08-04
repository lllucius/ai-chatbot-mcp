"""Authentication API endpoints."""

from fastapi import APIRouter, Depends

from ..dependencies import get_auth_service, get_current_user
from ..models.user import User
from shared.schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    Token,
)
from shared.schemas.common import BaseResponse, APIResponse, SuccessResponse, ErrorResponse
from shared.schemas.user import UserResponse

from ..services.auth import AuthService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["authentication"])


@router.post("/register", response_model=APIResponse)
@handle_api_errors("User registration failed")
async def register(
    request: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user account."""
    log_api_call("register", username=request.username, email=request.email)

    user = await auth_service.register_user(request)
    user_response = UserResponse.model_validate(user)
    return APIResponse(
        success=True,
        message="User registered successfully",
        data=user_response.model_dump()
    )


@router.post("/login", response_model=APIResponse)
@handle_api_errors("User authentication failed")
async def login(
    request: LoginRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate user and generate JWT access token."""
    log_api_call("login", username=request.username)

    token_data = await auth_service.authenticate_user(
        request.username, request.password
    )
    # Convert Token object to dict for unified response
    token_dict = token_data.model_dump() if hasattr(token_data, 'model_dump') else token_data
    return SuccessResponse.create(
        data=token_dict,
        message="User authenticated successfully"
    )


@router.get("/me", response_model=APIResponse)
@handle_api_errors("Failed to get current user information")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    log_api_call("get_current_user_info", user_id=str(current_user.id))
    user_response = UserResponse.model_validate(current_user)
    return APIResponse(
        success=True,
        message="User information retrieved successfully",
        data=user_response.model_dump()
    )


@router.post("/logout", response_model=APIResponse)
@handle_api_errors("Logout failed")
async def logout():
    """Logout current user session."""
    log_api_call("logout")
    return SuccessResponse.create(message="Logged out successfully")


@router.post("/refresh", response_model=APIResponse)
@handle_api_errors("Token refresh failed")
async def refresh_token(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh JWT access token for session continuation."""
    log_api_call("refresh_token", user_id=str(current_user.id))

    token_data = auth_service.create_access_token({"sub": current_user.username})
    # Convert Token object to dict for unified response
    token_dict = token_data.model_dump() if hasattr(token_data, 'model_dump') else token_data
    return SuccessResponse.create(
        data=token_dict,
        message="Token refreshed successfully"
    )


@router.post("/password-reset", response_model=APIResponse)
@handle_api_errors("Password reset request failed")
async def request_password_reset(
    request: PasswordResetRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """Request password reset through administrative channels."""
    log_api_call("request_password_reset", email=request.email)

    # For admin-only dashboard, password resets are handled by administrators
    # through the user management interface rather than self-service email
    return SuccessResponse.create(
        message="Password reset request noted. Contact system administrator for password changes."
    )


@router.post("/password-reset/confirm", response_model=APIResponse)
@handle_api_errors("Password reset confirmation failed")
async def confirm_password_reset(
    request: PasswordResetConfirm, auth_service: AuthService = Depends(get_auth_service)
):
    """Confirm password reset through administrative channels."""
    log_api_call("confirm_password_reset", token=request.token[:8] + "...")

    # For admin-only dashboard, password resets are handled by administrators
    # through the user management interface rather than token-based reset
    return SuccessResponse.create(
        message="Password reset must be performed by system administrator through user management interface."
    )
