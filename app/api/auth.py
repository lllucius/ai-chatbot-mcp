"API endpoints for auth operations."

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
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
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["authentication"])


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    "Get auth service data."
    return AuthService(db)


@router.post("/register", response_model=UserResponse)
@handle_api_errors("User registration failed")
async def register(
    request: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)
):
    "Register operation."
    log_api_call("register", username=request.username, email=request.email)
    user = await auth_service.register_user(request)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
@handle_api_errors("User authentication failed")
async def login(
    request: LoginRequest, auth_service: AuthService = Depends(get_auth_service)
):
    "Login operation."
    log_api_call("login", username=request.username)
    token_data = await auth_service.authenticate_user(
        request.username, request.password
    )
    return token_data


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    "Get current user info data."
    log_api_call("get_current_user_info", user_id=str(current_user.id))
    return UserResponse.model_validate(current_user)


@router.post("/logout", response_model=BaseResponse)
async def logout():
    "Logout operation."
    log_api_call("logout")
    return BaseResponse(success=True, message="Logged out successfully")


@router.post("/refresh", response_model=Token)
@handle_api_errors("Token refresh failed")
async def refresh_token(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    "Refresh Token operation."
    log_api_call("refresh_token", user_id=str(current_user.id))
    token_data = auth_service.create_access_token({"sub": current_user.username})
    return token_data


@router.post("/password-reset", response_model=BaseResponse)
async def request_password_reset(
    request: PasswordResetRequest, auth_service: AuthService = Depends(get_auth_service)
):
    "Request Password Reset operation."
    return BaseResponse(
        success=True,
        message="Password reset request noted. Contact system administrator for password changes.",
    )


@router.post("/password-reset/confirm", response_model=BaseResponse)
async def confirm_password_reset(
    request: PasswordResetConfirm, auth_service: AuthService = Depends(get_auth_service)
):
    "Confirm Password Reset operation."
    return BaseResponse(
        success=True,
        message="Password reset must be performed by system administrator through user management interface.",
    )
