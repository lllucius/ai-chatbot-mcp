"""User management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.auth import PasswordResetConfirm, PasswordResetRequest
from shared.schemas.common import (
    APIResponse,
    ErrorResponse,
    PaginatedResponse,
    PaginationParams,
)
from shared.schemas.user import (
    UserPasswordUpdate,
    UserResponse,
    UserStatsResponse,
    UserUpdate,
)

from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user, get_user_service
from ..models.user import User
from ..models.user import User as UserModel
from ..services.user import UserService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["users"])


@router.get("/me", response_model=APIResponse[UserResponse])
@handle_api_errors("Failed to retrieve user profile")
async def get_my_profile(
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> APIResponse[UserResponse]:
    """Get current user profile with statistics."""
    log_api_call("get_my_profile", user_id=str(current_user.id))

    user = await user_service.get_user_profile(current_user.id)
    payload = UserResponse.model_validate(user)
    return APIResponse[UserResponse](
        success=True,
        message="User profile retrieved successfully",
        data=payload,
    )


@router.put("/me", response_model=APIResponse[UserResponse])
@handle_api_errors("Profile update failed")
async def update_my_profile(
    request: UserUpdate,
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> APIResponse[UserResponse]:
    """Update current user profile information."""
    log_api_call("update_my_profile", user_id=str(current_user.id))

    user = await user_service.update_user(current_user.id, request)
    payload = UserResponse.model_validate(user)
    return APIResponse[UserResponse](
        success=True,
        message="User profile updated successfully",
        data=payload,
    )


@router.post("/me/change-password", response_model=APIResponse)
@handle_api_errors("Password change failed")
async def change_password(
    request: UserPasswordUpdate,
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> APIResponse:
    """Change current user password with security verification."""
    log_api_call("change_password", user_id=str(current_user.id))

    success = await user_service.change_password(
        current_user.id, request.current_password, request.new_password
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_FORBIDDEN,
            detail="Current password is incorrect",
        )
    return APIResponse(
        success=True,
        message="Password changed successfully",
    )


@router.post("/password-reset", response_model=APIResponse)
@handle_api_errors("Password reset request failed")
async def request_password_reset(
    request: PasswordResetRequest,
    user_service: UserService = Depends(get_user_service),
) -> APIResponse:
    """Request password reset for user account."""
    log_api_call("request_password_reset", email=request.email)

    # Implementation note: This provides a consolidated password reset endpoint
    # that handles the full password reset workflow through the UserService
    await user_service.request_password_reset(request.email)

    return APIResponse(
        success=True,
        message="Password reset request processed. Check email for instructions.",
    )


@router.post("/password-reset/confirm", response_model=APIResponse)
@handle_api_errors("Password reset confirmation failed")
async def confirm_password_reset(
    request: PasswordResetConfirm,
    user_service: UserService = Depends(get_user_service),
) -> APIResponse:
    """Confirm password reset with token."""
    log_api_call("confirm_password_reset", token=request.token[:8] + "...")

    await user_service.confirm_password_reset(request.token, request.new_password)

    return APIResponse(
        success=True,
        message="Password reset successfully. You can now log in with your new password.",
    )


# Admin endpoints (require superuser privileges)


@router.get("/", response_model=APIResponse[PaginatedResponse[UserResponse]])
@handle_api_errors("Failed to retrieve users")
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False),
    superuser_only: bool = Query(False),
    current_user=Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
) -> APIResponse[PaginatedResponse[UserResponse]]:
    """List all users with filtering and pagination."""
    log_api_call(
        "list_users",
        user_id=str(current_user.id),
        page=page,
        size=size,
        active_only=active_only,
        superuser_only=superuser_only,
    )

    users, total = await user_service.list_users(
        page=page, size=size, active_only=active_only, superuser_only=superuser_only
    )

    user_responses = [UserResponse.model_validate(user) for user in users]

    payload = PaginatedResponse(
        items=user_responses,
        pagination=PaginationParams(
            total=total,
            page=page,
            per_page=size,
        ),
    )

    return APIResponse[PaginatedResponse[UserResponse]](
        success=True,
        message="Users retrieved successfully",
        data=payload,
    )


@router.get("/byid/{user_id}", response_model=APIResponse[UserResponse])
@handle_api_errors("Failed to retrieve user")
async def get_user_byid(
    user_id: int,
    current_user=Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
) -> APIResponse[UserResponse]:
    """Get user by ID (admin only)."""
    log_api_call("get_user_byid", target_user_id=str(user_id))

    user = await user_service.get_user_profile(user_id)
    payload = UserResponse.model_validate(user)
    return APIResponse[UserResponse](
        success=True,
        message="User profile retrieved successfully",
        data=payload,
    )

@router.get("/byname/{user_name}", response_model=APIResponse[UserResponse])
@handle_api_errors("Failed to retrieve user")
async def get_user_byname(
    user_name: str,
    current_user=Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
) -> APIResponse[UserResponse]:
    """Get user by name (admin only)."""
    log_api_call("get_user_byname", target_user_name=user_name)
    user = await user_service.get_user_profile(user_name)
    payload = UserResponse.model_validate(user)
    return APIResponse[UserResponse](
        success=True,
        message="User profile retrieved successfully",
        data=payload,
    )



@router.put("/byid/{user_id}", response_model=APIResponse[UserResponse])
@handle_api_errors("User update failed")
async def update_user(
    user_id: int,
    request: UserUpdate,
    current_user=Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
) -> APIResponse[UserResponse]:
    """Update user by ID (admin only)."""
    log_api_call(
        "update_user", admin_user_id=str(current_user.id), target_user_id=str(user_id)
    )

    user = await user_service.update_user(user_id, request)
    payload = UserResponse.model_validate(user)
    return APIResponse[UserResponse](
        success=True,
        message="User updated successfully",
        data=payload,
    )


@router.delete("/byid/{user_id}", response_model=APIResponse)
@handle_api_errors("User deletion failed")
async def delete_user(
    user_id: int,
    current_user=Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
) -> APIResponse:
    """Delete user by ID (admin only)."""
    log_api_call(
        "delete_user", admin_user_id=str(current_user.id), target_user_id=str(user_id)
    )

    # Prevent self-deletion
    if user_id == current_user.id:
        return ErrorResponse.create(
            error_code="SELF_DELETION_FORBIDDEN",
            message="Cannot delete your own account",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return APIResponse(
        success=True,
        message="User deleted successfully",
    )


@router.post("/byid/{user_id}/promote", response_model=APIResponse)
@handle_api_errors("Failed to promote user")
async def promote_user_to_superuser(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
) -> APIResponse:
    """Promote a user to superuser status."""
    log_api_call(
        "promote_user", user_id=str(current_user.id), target_user_id=str(user_id)
    )

    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a superuser",
            )

        # Promote user
        user.is_superuser = True
        await user_service.db.commit()

        return APIResponse(
            success=True,
            message=f"User {user.username} promoted to superuser successfully",
        )
    except HTTPException:
        raise
    except Exception:
        await user_service.db.rollback()
        raise


@router.post("/byid/{user_id}/demote", response_model=APIResponse)
@handle_api_errors("Failed to demote user")
async def demote_user_from_superuser(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
) -> APIResponse:
    """Demote a superuser to regular user status."""
    log_api_call(
        "demote_user", user_id=str(current_user.id), target_user_id=str(user_id)
    )

    # Prevent self-demotion
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot demote yourself"
        )

    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a superuser",
            )

        # Demote user
        user.is_superuser = False
        await user_service.db.commit()

        return APIResponse(
            success=True,
            message=f"User {user.username} demoted from superuser successfully",
        )
    except HTTPException:
        raise
    except Exception:
        await user_service.db.rollback()
        raise


@router.post("/byid/{user_id}/activate", response_model=APIResponse)
@handle_api_errors("Failed to activate user")
async def activate_user_account(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
) -> APIResponse:
    """Activate a user account."""
    log_api_call(
        "activate_user", user_id=str(current_user.id), target_user_id=str(user_id)
    )

    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User is already active"
            )

        # Activate user
        user.is_active = True
        await user_service.db.commit()

        return APIResponse(
            success=True,
            message=f"User {user.username} activated successfully",
        )
    except HTTPException:
        raise
    except Exception:
        await user_service.db.rollback()
        raise


@router.post("/byid/{user_id}/deactivate", response_model=APIResponse)
@handle_api_errors("Failed to deactivate user")
async def deactivate_user_account(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
) -> APIResponse:
    """Deactivate a user account."""
    log_api_call(
        "deactivate_user", user_id=str(current_user.id), target_user_id=str(user_id)
    )

    # Prevent self-deactivation
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate yourself"
        )

    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already inactive",
            )

        # Deactivate user
        user.is_active = False
        await user_service.db.commit()

        return APIResponse(
            success=True,
            message=f"User {user.username} deactivated successfully",
        )
    except HTTPException:
        raise
    except Exception:
        await user_service.db.rollback()
        raise


@router.post("/byid/{user_id}/reset-password", response_model=APIResponse)
@handle_api_errors("Failed to reset password")
async def admin_reset_user_password(
    user_id: int,
    new_password: str = Query(..., min_length=8, description="New password"),
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
) -> APIResponse:
    """Reset a user's password (admin operation)."""
    log_api_call(
        "admin_reset_password",
        user_id=str(current_user.id),
        target_user_id=str(user_id),
    )

    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Validate password strength
        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long",
            )

        # Update password
        await user_service.update_user_password(user_id, new_password)

        return APIResponse(
            success=True,
            message=f"Password reset successfully for user {user.username}",
        )
    except HTTPException:
        raise
    except Exception:
        raise


@router.get("/stats", response_model=APIResponse[UserStatsResponse])
@handle_api_errors("Failed to get user statistics")
async def get_user_statistics(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserStatsResponse]:
    """Get comprehensive user statistics for administrative reporting."""
    log_api_call("get_user_statistics", user_id=str(current_user.id))

    # Basic user counts
    total_users = await db.scalar(select(func.count(UserModel.id)))
    active_users = await db.scalar(
        select(func.count(UserModel.id)).where(UserModel.is_active)
    )
    superusers = await db.scalar(
        select(func.count(UserModel.id)).where(UserModel.is_superuser)
    )

    UserStatsResponse(
        total_users=total_users or 0,
        active_users=active_users or 0,
        inactive_users=(total_users or 0) - (active_users or 0),
        superusers=superusers or 0,
    )

    stats_data = UserStatsResponse(
        total_users=total_users or 0,
        active_users=active_users or 0,
        inactive_users=(total_users or 0) - (active_users or 0),
        superusers=superusers or 0,
    )

    return APIResponse[UserStatsResponse](
        success=True,
        message="User statistics retrieved successfully",
        data=stats_data,
    )
