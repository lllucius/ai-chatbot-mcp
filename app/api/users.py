"""User management API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.admin_responses import (
    UserStatisticsResponse,
)
from shared.schemas.common import (
    APIResponse,
    ErrorResponse,
    PaginatedResponse,
    SuccessResponse,
)
from shared.schemas.user import UserPasswordUpdate, UserResponse, UserUpdate

from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user
from ..models.user import User
from ..services.user import UserService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["users"])


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Get user service instance with database session."""
    return UserService(db)


@router.get("/me", response_model=APIResponse)
@handle_api_errors("Failed to retrieve user profile")
async def get_my_profile(
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Get current user profile with statistics."""
    log_api_call("get_my_profile", user_id=str(current_user.id))

    profile = await user_service.get_user_profile(current_user.id)
    # Convert to dict if it's a Pydantic model
    profile_data = profile.model_dump() if hasattr(profile, 'model_dump') else profile
    return SuccessResponse.create(
        data=profile_data,
        message="User profile retrieved successfully"
    )


@router.put("/me", response_model=APIResponse)
@handle_api_errors("Profile update failed")
async def update_my_profile(
    request: UserUpdate,
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Update current user profile information."""
    log_api_call("update_my_profile", user_id=str(current_user.id))

    updated_user = await user_service.update_user(current_user.id, request)
    # Convert to dict if it's a Pydantic model
    user_data = updated_user.model_dump() if hasattr(updated_user, 'model_dump') else updated_user
    return SuccessResponse.create(
        data=user_data,
        message="User profile updated successfully"
    )


@router.post("/me/change-password", response_model=APIResponse)
@handle_api_errors("Password change failed")
async def change_password(
    request: UserPasswordUpdate,
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Change current user password with security verification."""
    log_api_call("change_password", user_id=str(current_user.id))

    success = await user_service.change_password(
        current_user.id, request.current_password, request.new_password
    )

    if success:
        return SuccessResponse.create(
            message="Password changed successfully"
        )
    else:
        return ErrorResponse.create(
            error_code="INVALID_PASSWORD",
            message="Current password is incorrect",
            status_code=status.HTTP_400_BAD_REQUEST
        )


# Admin endpoints (require superuser privileges)


@router.get("/", response_model=APIResponse)
@handle_api_errors("Failed to retrieve users")
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False),
    superuser_only: bool = Query(False),
    current_user=Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
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
    user_data = [user_resp.model_dump() for user_resp in user_responses]

    return PaginatedResponse.create_response(
        items=user_data,
        total=total,
        page=page,
        size=size,
        message="Users retrieved successfully",
    )


@router.get("/byid/{user_id}", response_model=APIResponse)
@handle_api_errors("Failed to retrieve user")
async def get_user(
    user_id: UUID,
    current_user=Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
    """Get user by ID (admin only)."""
    log_api_call(
        "get_user", admin_user_id=str(current_user.id), target_user_id=str(user_id)
    )

    profile = await user_service.get_user_profile(user_id)
    profile_data = profile.model_dump() if hasattr(profile, 'model_dump') else profile
    return SuccessResponse.create(
        data=profile_data,
        message="User profile retrieved successfully"
    )


@router.put("/byid/{user_id}", response_model=APIResponse)
@handle_api_errors("User update failed")
async def update_user(
    user_id: UUID,
    request: UserUpdate,
    current_user=Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
    """Update user by ID (admin only)."""
    log_api_call(
        "update_user", admin_user_id=str(current_user.id), target_user_id=str(user_id)
    )

    updated_user = await user_service.update_user(user_id, request)
    user_data = updated_user.model_dump() if hasattr(updated_user, 'model_dump') else updated_user
    return SuccessResponse.create(
        data=user_data,
        message="User updated successfully"
    )


@router.delete("/byid/{user_id}", response_model=APIResponse)
@handle_api_errors("User deletion failed")
async def delete_user(
    user_id: UUID,
    current_user=Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
    """Delete user by ID (admin only)."""
    log_api_call(
        "delete_user", admin_user_id=str(current_user.id), target_user_id=str(user_id)
    )

    # Prevent self-deletion
    if user_id == current_user.id:
        return ErrorResponse.create(
            error_code="SELF_DELETION_FORBIDDEN",
            message="Cannot delete your own account",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    success = await user_service.delete_user(user_id)

    if success:
        return SuccessResponse.create(
            message="User deleted successfully"
        )
    else:
        return ErrorResponse.create(
            error_code="USER_NOT_FOUND",
            message="User not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


@router.post("/users/byid/{user_id}/promote", response_model=APIResponse)
@handle_api_errors("Failed to promote user")
async def promote_user_to_superuser(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
    """Promote a user to superuser status."""
    log_api_call(
        "promote_user", user_id=str(current_user.id), target_user_id=str(user_id)
    )

    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a superuser",
            )

        # Promote user
        user.is_superuser = True
        await user_service.db.commit()

        return SuccessResponse.create(
            message=f"User {user.username} promoted to superuser successfully"
        )
    except HTTPException:
        raise
    except Exception:
        await user_service.db.rollback()
        raise


@router.post("/users/byid/{user_id}/demote", response_model=APIResponse)
@handle_api_errors("Failed to demote user")
async def demote_user_from_superuser(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
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

        return SuccessResponse.create(
            message=f"User {user.username} demoted from superuser successfully"
        )
    except HTTPException:
        raise
    except Exception:
        await user_service.db.rollback()
        raise


@router.post("/users/byid/{user_id}/activate", response_model=APIResponse)
@handle_api_errors("Failed to activate user")
async def activate_user_account(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
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

        return SuccessResponse.create(
            message=f"User {user.username} activated successfully"
        )
    except HTTPException:
        raise
    except Exception:
        await user_service.db.rollback()
        raise


@router.post("/users/byid/{user_id}/deactivate", response_model=APIResponse)
@handle_api_errors("Failed to deactivate user")
async def deactivate_user_account(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
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

        return SuccessResponse.create(
            message=f"User {user.username} deactivated successfully"
        )
    except HTTPException:
        raise
    except Exception:
        await user_service.db.rollback()
        raise


@router.post("/users/byid/{user_id}/reset-password", response_model=APIResponse)
@handle_api_errors("Failed to reset password")
async def admin_reset_user_password(
    user_id: UUID,
    new_password: str = Query(..., min_length=8, description="New password"),
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
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
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Validate password strength
        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long",
            )

        # Update password
        await user_service.update_user_password(user_id, new_password)

        return SuccessResponse.create(
            message=f"Password reset successfully for user {user.username}"
        )
    except HTTPException:
        raise
    except Exception:
        raise


@router.get("/users/stats", response_model=APIResponse)
@handle_api_errors("Failed to get user statistics")
async def get_user_statistics(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> UserStatisticsResponse:
    """Get comprehensive user statistics for administrative reporting."""
    log_api_call("get_user_statistics", user_id=str(current_user.id))

    try:
        from sqlalchemy import func, select

        from ..models.conversation import Conversation
        from ..models.document import Document
        from ..models.user import User as UserModel

        # Basic user counts
        total_users = await db.scalar(select(func.count(UserModel.id)))
        active_users = await db.scalar(
            select(func.count(UserModel.id)).where(UserModel.is_active)
        )
        superusers = await db.scalar(
            select(func.count(UserModel.id)).where(UserModel.is_superuser)
        )

        # Recent registrations (last 30 days)
        from datetime import datetime, timedelta

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_users = await db.scalar(
            select(func.count(UserModel.id)).where(
                UserModel.created_at >= thirty_days_ago
            )
        )

        # User engagement metrics
        users_with_documents = await db.scalar(
            select(func.count(func.distinct(Document.user_id)))
        )

        users_with_conversations = await db.scalar(
            select(func.count(func.distinct(Conversation.user_id)))
        )

        # Average documents per user
        avg_docs_per_user = (
            await db.scalar(
                select(func.avg(func.count(Document.id)))
                .select_from(Document)
                .group_by(Document.user_id)
            )
            or 0
        )

        # Average conversations per user
        avg_convs_per_user = (
            await db.scalar(
                select(func.avg(func.count(Conversation.id)))
                .select_from(Conversation)
                .group_by(Conversation.user_id)
            )
            or 0
        )

        # Top active users (by document count)
        top_users_docs = await db.execute(
            select(UserModel.username, func.count(Document.id).label("document_count"))
            .join(Document, UserModel.id == Document.user_id, isouter=True)
            .group_by(UserModel.id, UserModel.username)
            .order_by(func.count(Document.id).desc())
            .limit(5)
        )

        top_users_list = [
            {"username": row.username, "document_count": row.document_count}
            for row in top_users_docs.fetchall()
        ]

        stats_data = {
            "total_users": total_users or 0,
            "active_users": active_users or 0,
            "inactive_users": (total_users or 0) - (active_users or 0),
            "superusers": superusers or 0,
            "recent_registrations_30d": recent_users or 0,
            "engagement": {
                "users_with_documents": users_with_documents or 0,
                "users_with_conversations": users_with_conversations or 0,
                "avg_documents_per_user": round(avg_docs_per_user, 2),
                "avg_conversations_per_user": round(avg_convs_per_user, 2),
            },
            "top_users_by_documents": top_users_list,
            "activity_rate": round(
                (active_users or 0) / max(total_users or 1, 1) * 100, 2
            ),
        }

        return SuccessResponse.create(
            data=stats_data,
            message="User statistics retrieved successfully"
        )
    except Exception:
        raise
