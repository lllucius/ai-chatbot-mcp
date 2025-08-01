"""
User management API endpoints with comprehensive profile and administration features.

This module provides endpoints for user profile management, user administration,
and user-related operations. It implements role-based access control, input
validation, and comprehensive logging for user management activities.

Key Features:
- User profile management with statistics and analytics
- User administration for superuser operations
- Password change with security verification
- User listing with pagination and filtering
- Comprehensive user statistics and metrics

Security Features:
- Role-based access control (regular users vs superusers)
- Input validation and sanitization
- Password verification for sensitive operations
- Audit logging for administrative actions
- Protection against unauthorized access

"""

from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user
from ..models.user import User
from ..schemas.common import BaseResponse, PaginatedResponse, UserStatisticsResponse
from ..schemas.user import UserPasswordUpdate, UserResponse, UserUpdate
from ..services.user import UserService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["users"])


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Get user service instance."""
    return UserService(db)


@router.get("/me", response_model=UserResponse)
@handle_api_errors("Failed to retrieve user profile")
async def get_my_profile(
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get current user profile with comprehensive statistics.

    Returns detailed profile information for the authenticated user including
    account details, activity statistics, and engagement metrics. This endpoint
    provides a complete view of the user's interaction with the platform.

    Args:
        current_user: Automatically injected current user from JWT token
        user_service: Injected user service instance

    Returns:
        UserResponse: Complete user profile including:
            - Basic profile (username, email, full_name, status)
            - Account metadata (created_at, updated_at, last_login)
            - Activity statistics (document_count, conversation_count, total_messages)

    Example Response:
        {
            "id": "uuid-here",
            "username": "johndoe",
            "email": "john@example.com",
            "full_name": "John Doe",
            "is_active": true,
            "document_count": 15,
            "conversation_count": 8,
            "total_messages": 142
        }
    """
    log_api_call("get_my_profile", user_id=str(current_user.id))

    profile = await user_service.get_user_profile(current_user.id)
    return profile


@router.put("/me", response_model=UserResponse)
@handle_api_errors("Profile update failed")
async def update_my_profile(
    request: UserUpdate,
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update current user profile.

    Allows users to update their own profile information
    such as email and full name.
    """
    log_api_call("update_my_profile", user_id=str(current_user.id))

    updated_user = await user_service.update_user(current_user.id, request)
    return UserResponse.model_validate(updated_user)


@router.post("/me/change-password", response_model=BaseResponse)
@handle_api_errors("Password change failed")
async def change_password(
    request: UserPasswordUpdate,
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Change current user password.

    Requires the current password for verification
    and the new password.
    """
    log_api_call("change_password", user_id=str(current_user.id))

    success = await user_service.change_password(
        current_user.id, request.current_password, request.new_password
    )

    if success:
        return BaseResponse(success=True, message="Password changed successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )


# Admin endpoints (require superuser privileges)


@router.get("/", response_model=PaginatedResponse[UserResponse])
@handle_api_errors("Failed to retrieve users")
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False),
    superuser_only: bool = Query(False),
    current_user=Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
    """
    List all users (admin only).

    Returns paginated list of users with optional filtering.
    Requires superuser privileges.
    """
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

    return PaginatedResponse.create(
        items=user_responses,
        total=total,
        page=page,
        size=size,
        message="Users retrieved successfully",
    )


@router.get("/byid/{user_id}", response_model=UserResponse)
@handle_api_errors("Failed to retrieve user")
async def get_user(
    user_id: UUID,
    current_user=Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get user by ID (admin only).

    Returns detailed user information including statistics.
    Requires superuser privileges.
    """
    log_api_call(
        "get_user", admin_user_id=str(current_user.id), target_user_id=str(user_id)
    )

    profile = await user_service.get_user_profile(user_id)
    return profile


@router.put("/byid/{user_id}", response_model=UserResponse)
@handle_api_errors("User update failed")
async def update_user(
    user_id: UUID,
    request: UserUpdate,
    current_user=Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update user by ID (admin only).

    Allows administrators to update any user's profile.
    Requires superuser privileges.
    """
    log_api_call(
        "update_user", admin_user_id=str(current_user.id), target_user_id=str(user_id)
    )

    updated_user = await user_service.update_user(user_id, request)
    return UserResponse.model_validate(updated_user)


@router.delete("/byid/{user_id}", response_model=BaseResponse)
@handle_api_errors("User deletion failed")
async def delete_user(
    user_id: UUID,
    current_user=Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
    """
    Delete user by ID (admin only).

    Permanently deletes a user and all associated data.
    Requires superuser privileges.
    """
    log_api_call(
        "delete_user", admin_user_id=str(current_user.id), target_user_id=str(user_id)
    )

    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    success = await user_service.delete_user(user_id)

    if success:
        return BaseResponse(success=True, message="User deleted successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


@router.post("/users/byid/{user_id}/promote", response_model=BaseResponse)
@handle_api_errors("Failed to promote user")
async def promote_user_to_superuser(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
    """
    Promote a user to superuser status.

    Grants superuser privileges to the specified user.
    Requires current user to be a superuser.

    Args:
        user_id: ID of the user to promote
    """
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

        return BaseResponse(
            success=True,
            message=f"User {user.username} promoted to superuser successfully",
            timestamp=user_service._get_current_timestamp(),
        )
    except HTTPException:
        raise
    except Exception as e:
        await user_service.db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to promote user: {str(e)}",
        )


@router.post("/users/byid/{user_id}/demote", response_model=BaseResponse)
@handle_api_errors("Failed to demote user")
async def demote_user_from_superuser(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
    """
    Demote a superuser to regular user status.

    Removes superuser privileges from the specified user.
    Requires current user to be a superuser.

    Args:
        user_id: ID of the user to demote
    """
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

        return BaseResponse(
            success=True,
            message=f"User {user.username} demoted from superuser successfully",
            timestamp=user_service._get_current_timestamp(),
        )
    except HTTPException:
        raise
    except Exception as e:
        await user_service.db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to demote user: {str(e)}",
        )


@router.post("/users/byid/{user_id}/activate", response_model=BaseResponse)
@handle_api_errors("Failed to activate user")
async def activate_user_account(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
    """
    Activate a user account.

    Enables a previously deactivated user account.
    Requires current user to be a superuser.

    Args:
        user_id: ID of the user to activate
    """
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

        return BaseResponse(
            success=True,
            message=f"User {user.username} activated successfully",
            timestamp=user_service._get_current_timestamp(),
        )
    except HTTPException:
        raise
    except Exception as e:
        await user_service.db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate user: {str(e)}",
        )


@router.post("/users/byid/{user_id}/deactivate", response_model=BaseResponse)
@handle_api_errors("Failed to deactivate user")
async def deactivate_user_account(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
    """
    Deactivate a user account.

    Disables a user account without deleting it.
    Requires current user to be a superuser.

    Args:
        user_id: ID of the user to deactivate
    """
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

        return BaseResponse(
            success=True,
            message=f"User {user.username} deactivated successfully",
            timestamp=user_service._get_current_timestamp(),
        )
    except HTTPException:
        raise
    except Exception as e:
        await user_service.db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate user: {str(e)}",
        )


@router.post("/users/byid/{user_id}/reset-password", response_model=BaseResponse)
@handle_api_errors("Failed to reset password")
async def admin_reset_user_password(
    user_id: UUID,
    new_password: str = Query(..., min_length=8, description="New password"),
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
    """
    Reset a user's password (admin operation).

    Allows superusers to reset any user's password.
    The new password must meet security requirements.

    Args:
        user_id: ID of the user whose password to reset
        new_password: New password (minimum 8 characters)
    """
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

        return BaseResponse(
            success=True,
            message=f"Password reset successfully for user {user.username}",
            timestamp=user_service._get_current_timestamp(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}",
        )


@router.get("/users/stats", response_model=UserStatisticsResponse)
@handle_api_errors("Failed to get user statistics")
async def get_user_statistics(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> UserStatisticsResponse:
    """
    Get comprehensive user statistics.

    Returns detailed statistics about users including counts,
    activity metrics, and distribution analytics.

    Requires superuser access.
    """
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

        return UserStatisticsResponse(
            success=True,
            data={
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
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user statistics: {str(e)}",
        )
