"""Authentication API endpoints."""

from typing import Annotated, List

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_auth_service, get_current_user
from app.models.user import User
from app.services.auth import AuthService
from app.utils.api_errors import handle_api_errors, log_api_call
from shared.schemas.auth import (
    APIKeyResponse,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    Token,
)
from shared.schemas.common import APIResponse, PaginatedResponse, PaginationParams
from shared.schemas.user import UserResponse

router = APIRouter(tags=["authentication"])


@router.post("/register", response_model=APIResponse[UserResponse])
@handle_api_errors("User registration failed")
async def register(
    request: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
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
    request: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
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


@router.get("/api-keys")
@handle_api_errors("Failed to retrieve API keys")
async def get_api_keys(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
) -> APIResponse[PaginatedResponse[APIKeyResponse]]:
    """Get user's API keys with pagination."""
    log_api_call("get_api_keys", user_id=str(current_user.id))
    
    # Mock API keys data - in real implementation this would come from a service
    api_keys = []
    for i in range(1, 6):  # Mock 5 keys
        api_key = APIKeyResponse(
            id=f"key_{current_user.id}_{i}",
            name=f"API Key {i}",
            key_prefix="sk_live_",
            created_at=current_user.created_at,
            expires_at=None,
            last_used_at=None,
            usage_count=i * 10,
            is_active=True,
            permissions=["read", "write"]
        )
        api_keys.append(api_key)
    
    # Apply pagination
    start = (page - 1) * size
    end = start + size
    paginated_keys = api_keys[start:end]
    
    payload = PaginatedResponse(
        items=paginated_keys,
        pagination=PaginationParams(
            total=len(api_keys),
            page=page,
            per_page=size,
        ),
    )
    
    return APIResponse[PaginatedResponse[APIKeyResponse]](
        success=True,
        message="API keys retrieved successfully",
        data=payload,
    )


@router.post("/logout", response_model=APIResponse)
@handle_api_errors("Logout failed")
async def logout() -> APIResponse:
    """Logout current user session."""
    log_api_call("logout")
    return APIResponse(
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


@router.post("/password-reset", response_model=APIResponse, deprecated=True)
@handle_api_errors("Password reset request failed")
async def request_password_reset(
    request: PasswordResetRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> APIResponse:
    """Request password reset through administrative channels.

    **DEPRECATED**: Use POST /api/v1/users/password-reset instead.
    This endpoint will be removed in v2.0.
    """
    log_api_call("request_password_reset", email=request.email)

    return APIResponse(
        success=True,
        message="Password reset request noted. Contact system administrator for password changes. "
                "DEPRECATED: Use /api/v1/users/password-reset instead.",
    )


@router.post("/password-reset/confirm", response_model=APIResponse, deprecated=True)
@handle_api_errors("Password reset confirmation failed")
async def confirm_password_reset(
    request: PasswordResetConfirm,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> APIResponse:
    """Confirm password reset through administrative channels.

    **DEPRECATED**: Use POST /api/v1/users/password-reset/confirm instead.
    This endpoint will be removed in v2.0.
    """
    log_api_call("confirm_password_reset", token=request.token[:8] + "...")

    return APIResponse(
        success=True,
        message="Password reset must be performed by system administrator through user management interface. "
                "DEPRECATED: Use /api/v1/users/password-reset/confirm instead.",
    )
