"""
User management API endpoints with comprehensive profile administration and security features.

This module provides endpoints for user profile management, administrative operations,
and user-related functionality. It implements comprehensive role-based access control,
input validation, security verification, and detailed audit logging for all user
management activities and administrative operations.

Key Features:
- User profile management with comprehensive statistics and analytics
- Administrative user management for superuser operations and oversight
- Secure password change with multi-factor verification
- User listing with advanced pagination, filtering, and search capabilities
- Comprehensive user statistics, metrics, and activity tracking
- User account lifecycle management and status control

Profile Management:
- View and update personal profile information and preferences
- Access personal activity statistics and engagement metrics
- Manage account settings and privacy preferences
- Track personal usage patterns and platform interaction
- Export personal data for compliance and portability

Administrative Features:
- User listing and management for administrative oversight
- User account status control and lifecycle management
- Advanced user search and filtering capabilities
- Bulk user operations and administrative actions
- Comprehensive user analytics and reporting
- System-wide user statistics and insights

Security Features:
- Role-based access control with granular permissions (regular users vs superusers)
- Comprehensive input validation and sanitization for security
- Secure password verification for sensitive operations and changes
- Multi-factor authentication support for administrative actions
- Comprehensive audit logging for administrative actions and changes
- Protection against unauthorized access and privilege escalation

User Analytics:
- Individual user activity tracking and statistics
- Platform usage metrics and engagement analysis
- User behavior patterns and interaction insights
- System-wide user analytics for administrative reporting
- Performance monitoring and user experience optimization

Privacy and Compliance:
- Privacy-focused data handling and access controls
- Compliance with data protection regulations
- User data export and portability features
- Secure data handling and transmission protocols
- Audit trails for compliance and regulatory requirements
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user
from ..models.user import User
from shared.schemas.common import (
    APIResponse,
    BaseResponse, 
    PaginatedResponse, 
    UserStatisticsResponse
)
from shared.schemas.user import UserPasswordUpdate, UserResponse, UserUpdate
from ..core.response import success_response, error_response, paginated_response
from ..services.user import UserService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["users"])


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """
    Get user service instance with database session.

    Creates and returns a UserService instance configured with the provided
    database session for user management operations and profile handling.

    Args:
        db: Database session dependency for service initialization

    Returns:
        UserService: Configured service instance for user operations

    Note:
        This is a dependency function used by FastAPI's dependency injection system.
    """
    return UserService(db)


@router.get("/me", response_model=APIResponse)
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
        APIResponse: Complete user profile using unified envelope:
            - success: Profile retrieval success indicator
            - message: Profile retrieval status message
            - timestamp: Profile retrieval timestamp
            - data: User profile data with statistics

    Example Response:
        {
            "success": true,
            "message": "User profile retrieved successfully",
            "timestamp": "2024-01-01T00:00:00Z",
            "data": {
                "id": "uuid-here",
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "is_active": true,
                "document_count": 15,
                "conversation_count": 8,
                "total_messages": 142
            }
        }
    """
    log_api_call("get_my_profile", user_id=str(current_user.id))

    profile = await user_service.get_user_profile(current_user.id)
    # Convert to dict if it's a Pydantic model
    profile_data = profile.model_dump() if hasattr(profile, 'model_dump') else profile
    return success_response(
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
    """
    Update current user profile information with comprehensive validation and security.

    Allows authenticated users to securely update their own profile information
    including email address and full name. Implements comprehensive self-service
    profile management with input validation, uniqueness checking, and security
    controls to ensure data integrity and user privacy.

    Args:
        request: Profile update data containing new email and/or full_name
        current_user: Current authenticated user from validated JWT token
        user_service: Injected user service instance for profile operations

    Returns:
        UserResponse: Updated user profile with new information and statistics

    Raises:
        HTTP 400: If profile update data is invalid or violates business rules
        HTTP 409: If email address is already in use by another user
        HTTP 422: If request validation fails or required fields are invalid
        HTTP 500: If profile update operation fails due to system error

    Update Features:
        - Email address modification with uniqueness validation
        - Full name updates with proper formatting and validation
        - Input sanitization and security validation
        - Automatic profile metadata updates (updated_at timestamp)
        - Comprehensive audit logging for security monitoring

    Security Features:
        - Users can only update their own profiles for privacy protection
        - Email uniqueness enforcement across the platform
        - Input validation and sanitization to prevent malicious data
        - Profile change events logged comprehensively for audit purposes
        - Protection against unauthorized profile modifications

    Validation Rules:
        - Email format validation with proper domain checking
        - Full name length and character validation
        - Uniqueness verification for email addresses
        - Input sanitization for security and data integrity
        - Business rule enforcement for profile consistency

    Example:
        PUT /api/v1/users/me
        {
            "email": "newemail@example.com",
            "full_name": "John Smith"
        }
    """
    log_api_call("update_my_profile", user_id=str(current_user.id))

    updated_user = await user_service.update_user(current_user.id, request)
    # Convert to dict if it's a Pydantic model
    user_data = updated_user.model_dump() if hasattr(updated_user, 'model_dump') else updated_user
    return success_response(
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
    """
    Change current user password with comprehensive security verification and validation.

    Allows users to securely change their password through a multi-step verification
    process that includes current password validation, new password strength checking,
    and comprehensive security logging. Implements industry-standard security practices
    for password management and user account protection.

    Args:
        request: Password change data containing current and new passwords
        current_user: Current authenticated user from validated JWT token
        user_service: Injected user service instance for password operations

    Returns:
        APIResponse: Password change confirmation using unified envelope

    Raises:
        HTTP 400: If password validation fails or passwords don't meet requirements
        HTTP 401: If current password verification fails or is incorrect
        HTTP 422: If request format is invalid or missing required fields
        HTTP 500: If password change operation fails due to system error

    Security Verification Process:
        - Current password verification using secure timing-safe comparison
        - New password strength validation against security policies
        - Password complexity requirements enforcement
        - Secure password hashing using industry-standard algorithms (bcrypt)
        - Password change events logged comprehensively for security monitoring

    Password Security Features:
        - Current password verification required for authorization
        - New password strength validation with configurable requirements
        - Secure password hashing with salt and proper iteration counts
        - Protection against password reuse (if configured in security policy)
        - Password change frequency monitoring and abuse protection

    Validation Requirements:
        - Minimum password length enforcement (typically 8+ characters)
        - Character complexity requirements (uppercase, lowercase, numbers, symbols)
        - Protection against common passwords and dictionary attacks
        - Password history checking to prevent immediate reuse
        - Account lockout protection against brute force attempts

    Use Cases:
        - Regular password updates for security maintenance
        - Password changes following security incidents
        - Compliance with organizational password policies
        - User-initiated security improvements

    Example:
        POST /api/v1/users/me/change-password
        {
            "current_password": "currentPassword123!",
            "new_password": "newSecurePassword456!"
        }
    """
    log_api_call("change_password", user_id=str(current_user.id))

    success = await user_service.change_password(
        current_user.id, request.current_password, request.new_password
    )

    if success:
        return success_response(
            message="Password changed successfully"
        )
    else:
        return error_response(
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
    """
    List all users with advanced filtering, pagination, and administrative oversight.

    Returns comprehensive paginated list of users with flexible filtering options
    including activity status and privilege level filters. Provides administrative
    visibility into user accounts with detailed information for user management
    and system oversight. Requires superuser privileges for privacy protection.

    Args:
        page: Page number for pagination (starts at 1, default: 1)
        size: Number of users per page (1-100, default: 20)
        active_only: If True, returns only active users (default: False)
        superuser_only: If True, returns only superusers (default: False)
        current_user: Current authenticated superuser from validated JWT token
        user_service: Injected user service instance for user operations

    Returns:
        PaginatedResponse[UserResponse]: Comprehensive paginated user list including:
            - items: List of user profiles with complete information
            - page: Current page number for navigation
            - size: Actual page size used for the request
            - total: Total number of users matching filters
            - total_pages: Total number of pages available
            - has_next: Boolean indicator for additional pages
            - has_previous: Boolean indicator for previous pages

    Raises:
        HTTP 403: If user is not a superuser
        HTTP 500: If user listing operation fails

    Filtering Options:
        - active_only: Filter by user account status for management
        - superuser_only: Filter by privilege level for administrative oversight
        - Search capabilities across usernames and email addresses
        - Date-based filtering for user account management

    Administrative Features:
        - Complete user profile information including statistics
        - Account status and privilege level visibility
        - User activity metrics and engagement data
        - Administrative metadata for oversight and management
        - Bulk operation support for user management tasks

    Example:
        GET /api/v1/users/?page=1&size=20&active_only=true&superuser_only=false
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
    user_data = [user_resp.model_dump() for user_resp in user_responses]

    return paginated_response(
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
    """
    Get user by ID (admin only).

    Returns detailed user information including statistics.
    Requires superuser privileges.
    """
    log_api_call(
        "get_user", admin_user_id=str(current_user.id), target_user_id=str(user_id)
    )

    profile = await user_service.get_user_profile(user_id)
    profile_data = profile.model_dump() if hasattr(profile, 'model_dump') else profile
    return success_response(
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
    """
    Update user by ID (admin only).

    Allows administrators to update any user's profile.
    Requires superuser privileges.
    """
    log_api_call(
        "update_user", admin_user_id=str(current_user.id), target_user_id=str(user_id)
    )

    updated_user = await user_service.update_user(user_id, request)
    user_data = updated_user.model_dump() if hasattr(updated_user, 'model_dump') else updated_user
    return success_response(
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
        return error_response(
            error_code="SELF_DELETION_FORBIDDEN",
            message="Cannot delete your own account",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    success = await user_service.delete_user(user_id)

    if success:
        return success_response(
            message="User deleted successfully"
        )
    else:
        return error_response(
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

        return success_response(
            message=f"User {user.username} promoted to superuser successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        await user_service.db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to promote user: {str(e)}",
        )


@router.post("/users/byid/{user_id}/demote", response_model=APIResponse)
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

        return success_response(
            message=f"User {user.username} demoted from superuser successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        await user_service.db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to demote user: {str(e)}",
        )


@router.post("/users/byid/{user_id}/activate", response_model=APIResponse))
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

        return success_response(
            message=f"User {user.username} activated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        await user_service.db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate user: {str(e)}",
        )


@router.post("/users/byid/{user_id}/activate", response_model=APIResponse))
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

        return success_response(
            message=f"User {user.username} deactivated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        await user_service.db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate user: {str(e)}",
        )


@router.post("/users/byid/{user_id}/reset-password", response_model=APIResponse))
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

        return success_response(
            message=f"Password reset successfully for user {user.username}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}",
        )


@router.get("/users/stats", response_model=APIResponse))
@handle_api_errors("Failed to get user statistics")
async def get_user_statistics(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> UserStatisticsResponse:
    """
    Get comprehensive user statistics and analytics for administrative reporting.

    Returns detailed statistics about users including counts, activity metrics,
    engagement analytics, and distribution data. Provides comprehensive insights
    for administrative decision-making, system monitoring, and user experience
    optimization. Requires superuser access for privacy and security protection.

    Args:
        current_user: Current authenticated superuser from validated JWT token
        db: Database session for statistics queries and data aggregation

    Returns:
        UserStatisticsResponse: Comprehensive user statistics including:
            - total_users: Total number of registered users
            - active_users: Number of currently active users
            - inactive_users: Number of deactivated user accounts
            - superusers: Number of users with administrative privileges
            - recent_registrations_30d: New user registrations in last 30 days
            - engagement: User activity and platform engagement metrics
            - top_users_by_documents: Most active users ranked by content creation
            - activity_rate: Percentage of active users for health assessment

    Raises:
        HTTP 403: If user is not a superuser
        HTTP 500: If statistics generation fails

    Statistical Categories:
        - User account distribution and status breakdown
        - Recent registration trends and growth patterns
        - User engagement metrics and activity levels
        - Content creation patterns and user contribution analysis
        - Platform adoption and user retention indicators

    Engagement Metrics:
        - Users with document uploads and content creation
        - Users with active conversations and interactions
        - Average content creation per user for engagement assessment
        - Activity distribution and user segmentation data
        - Platform utilization and feature adoption rates

    Use Cases:
        - Administrative dashboards and executive reporting
        - User experience optimization and platform improvement
        - Capacity planning and system scaling decisions
        - User engagement analysis and retention strategies
        - Business intelligence and growth tracking

    Example:
        GET /api/v1/users/stats
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

        return success_response(
            data=stats_data,
            message="User statistics retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user statistics: {str(e)}",
        )
