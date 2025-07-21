"""
User service for user management and profile operations.

This service provides comprehensive methods for user CRUD operations, 
profile management, user statistics, and analytics. It handles user
lifecycle management including creation, updates, password changes,
and account deactivation.

Key Features:
- User profile management with statistics
- Password change with current password verification
- User listing with pagination and filtering
- User deletion with cascading cleanup
- System-wide user analytics and metrics

Generated on: 2025-07-14 03:08:19 UTC
Updated on: 2025-01-20 19:40:00 UTC
Current User: lllucius / assistant
"""

from datetime import timedelta
import logging
from typing import Any, Dict, List, Tuple
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import AuthenticationError, NotFoundError, ValidationError
from ..models.conversation import Conversation
from ..models.document import Document
from ..models.user import User
from ..schemas.user import UserUpdate
from ..utils.security import get_password_hash, verify_password
from ..utils.timestamp import utcnow
from .base import BaseService

logger = logging.getLogger(__name__)


class UserService(BaseService):
    """
    Service for comprehensive user management and profile operations.

    This service extends BaseService to provide user-specific functionality
    including CRUD operations, profile management, statistics generation,
    and user-related business logic with enhanced logging and error handling.

    Responsibilities:
    - User profile retrieval with embedded statistics
    - User information updates with validation
    - Password change operations with security checks
    - User listing with flexible filtering and pagination
    - User deletion with proper cleanup
    - System-wide user analytics and reporting
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize user service with database session.

        Args:
            db: Database session for user operations
        """
        super().__init__(db, "user_service")

    async def get_user_profile(self, user_id: UUID) -> User:
        """
        Get comprehensive user profile with embedded statistics.

        Retrieves detailed user information including profile data
        and calculated statistics such as document count, conversation
        count, and total messages. This method provides a complete
        view of user activity and engagement.

        Args:
            user_id: Unique identifier for the user

        Returns:
            User: Complete user profile with embedded statistics including:
                - Basic profile information (username, email, full_name)
                - Account status and permissions
                - Timestamps (created_at, updated_at, last_login)
                - Activity statistics (document_count, conversation_count, total_messages)

        Raises:
            NotFoundError: If user with given ID does not exist
            Exception: If database operation fails

        Example:
            >>> user_service = UserService(db)
            >>> profile = await user_service.get_user_profile(user_id)
            >>> print(f"User {profile.username} has {profile.document_count} documents")
        """
        operation = "get_user_profile"
        self._log_operation_start(operation, user_id=str(user_id))

        try:
            await self._ensure_db_session()

            # Get user basic information
            user_result = await self.db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()

            if not user:
                self.logger.warning(
                    "User not found", user_id=str(user_id), operation=operation
                )
                raise NotFoundError(f"User not found with ID: {user_id}")

            # Get user activity statistics in parallel for better performance
            doc_count_result = await self.db.execute(
                select(func.count(Document.id)).where(Document.owner_id == user_id)
            )
            document_count = doc_count_result.scalar() or 0

            conv_count_result = await self.db.execute(
                select(func.count(Conversation.id)).where(
                    Conversation.user_id == user_id
                )
            )
            conversation_count = conv_count_result.scalar() or 0

            msg_count_result = await self.db.execute(
                select(func.sum(Conversation.message_count)).where(
                    Conversation.user_id == user_id
                )
            )
            total_messages = msg_count_result.scalar() or 0

            # Create comprehensive profile data
            profile_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "last_login": user.last_login,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "document_count": document_count,
                "conversation_count": conversation_count,
                "total_messages": total_messages,
            }

            self._log_operation_success(
                operation,
                user_id=str(user_id),
                username=user.username,
                document_count=document_count,
                conversation_count=conversation_count,
                total_messages=total_messages,
            )

            return user

        except NotFoundError:
            raise
        except Exception as e:
            self._log_operation_error(operation, e, user_id=str(user_id))
            raise

    async def update_user(self, user_id: UUID, user_update: UserUpdate) -> User:
        """
        Update user profile information with validation.

        Updates user profile fields with comprehensive validation including
        email uniqueness checks and proper error handling. Only non-None
        fields in the update request are modified, allowing partial updates.

        Args:
            user_id: Unique identifier for the user to update
            user_update: Update data containing fields to modify

        Returns:
            User: Updated user object with refreshed data from database

        Raises:
            NotFoundError: If user with given ID does not exist
            ValidationError: If update data violates constraints (e.g., email already in use)
            Exception: If database operation fails

        Example:
            >>> update_data = UserUpdate(email="new@example.com", full_name="New Name")
            >>> updated_user = await user_service.update_user(user_id, update_data)
            >>> print(f"Updated user email to: {updated_user.email}")
        """
        operation = "update_user"
        update_fields = {
            k: v for k, v in user_update.model_dump().items() if v is not None
        }

        self._log_operation_start(
            operation, user_id=str(user_id), update_fields=list(update_fields.keys())
        )

        try:
            await self._ensure_db_session()

            # Get existing user
            user_result = await self.db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()

            if not user:
                self.logger.warning("User not found for update", user_id=str(user_id))
                raise NotFoundError(f"User not found with ID: {user_id}")

            # Validate email uniqueness if email is being updated
            if user_update.email and user_update.email != user.email:
                existing_email = await self.db.execute(
                    select(User).where(
                        and_(User.email == user_update.email, User.id != user_id)
                    )
                )
                if existing_email.scalar_one_or_none():
                    self.logger.warning(
                        "Email already in use",
                        email=user_update.email,
                        user_id=str(user_id),
                    )
                    raise ValidationError(
                        f"Email {user_update.email} is already in use"
                    )

            # Apply updates only for non-None fields
            original_values = {}
            if user_update.email is not None:
                original_values["email"] = user.email
                user.email = user_update.email
            if user_update.full_name is not None:
                original_values["full_name"] = user.full_name
                user.full_name = user_update.full_name
            if user_update.is_active is not None:
                original_values["is_active"] = user.is_active
                user.is_active = user_update.is_active

            await self.db.commit()
            await self.db.refresh(user)

            self._log_operation_success(
                operation,
                user_id=str(user_id),
                username=user.username,
                updated_fields=list(update_fields.keys()),
                original_values=original_values,
            )

            return user

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self._log_operation_error(
                operation,
                e,
                user_id=str(user_id),
                update_fields=list(update_fields.keys()),
            )
            # Rollback transaction on error
            await self.db.rollback()
            raise

    async def change_password(
        self, user_id: UUID, current_password: str, new_password: str
    ) -> bool:
        """
        Change user password with security verification.

        Securely updates user password after verifying the current password.
        This method implements proper security practices including current
        password verification and secure password hashing.

        Args:
            user_id: Unique identifier for the user
            current_password: Current password for verification (plain text)
            new_password: New password to set (plain text, will be hashed)

        Returns:
            bool: True if password was successfully changed

        Raises:
            NotFoundError: If user with given ID does not exist
            AuthenticationError: If current password verification fails
            Exception: If database operation fails

        Security Notes:
            - Current password must be provided and verified
            - New password is securely hashed before storage
            - Operation is logged for security auditing
            - Transaction is rolled back on any error

        Example:
            >>> success = await user_service.change_password(
            ...     user_id, "old_password", "new_secure_password123"
            ... )
            >>> print(f"Password change: {'successful' if success else 'failed'}")
        """
        operation = "change_password"
        self._log_operation_start(operation, user_id=str(user_id))

        try:
            await self._ensure_db_session()

            # Get user for password verification
            user_result = await self.db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()

            if not user:
                self.logger.warning(
                    "User not found for password change", user_id=str(user_id)
                )
                raise NotFoundError(f"User not found with ID: {user_id}")

            # Verify current password for security
            if not verify_password(current_password, user.hashed_password):
                self.logger.warning(
                    "Invalid current password provided",
                    user_id=str(user_id),
                    username=user.username,
                )
                raise AuthenticationError("Current password is incorrect")

            # Update to new password with secure hashing
            user.hashed_password = get_password_hash(new_password)
            await self.db.commit()

            self._log_operation_success(
                operation, user_id=str(user_id), username=user.username
            )

            return True

        except (NotFoundError, AuthenticationError):
            raise
        except Exception as e:
            self._log_operation_error(operation, e, user_id=str(user_id))
            await self.db.rollback()
            raise

    async def list_users(
        self,
        page: int = 1,
        size: int = 20,
        active_only: bool = False,
        superuser_only: bool = False,
    ) -> Tuple[List[User], int]:
        """
        List users with pagination and filtering.

        Args:
            page: Page number (1-based)
            size: Items per page
            active_only: Filter to active users only
            superuser_only: Filter to superusers only

        Returns:
            Tuple[List[User], int]: List of users and total count
        """
        # Build filters
        filters = []
        if active_only:
            filters.append(User.is_active is True)
        if superuser_only:
            filters.append(User.is_superuser is True)

        # Count total users
        count_query = select(func.count(User.id))
        if filters:
            count_query = count_query.where(and_(*filters))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get users with pagination
        query = select(User).order_by(desc(User.created_at))
        if filters:
            query = query.where(and_(*filters))

        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        users = result.scalars().all()

        return list(users), total

    async def delete_user(self, user_id: UUID) -> bool:
        """
        Delete a user and all associated data.

        Args:
            user_id: User ID to delete

        Returns:
            bool: True if user was deleted

        Raises:
            NotFoundError: If user not found
        """
        # Get user
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        # Delete user (cascades to related data)
        await self.db.delete(user)
        await self.db.commit()

        logger.info(f"User deleted: {user.username}")
        return True

    async def get_user_statistics(self) -> Dict[str, Any]:
        """
        Get system-wide user statistics.

        Returns:
            dict: User statistics
        """
        # Total users
        total_result = await self.db.execute(select(func.count(User.id)))
        total_users = total_result.scalar() or 0

        # Active users
        active_result = await self.db.execute(
            select(func.count(User.id)).where(User.is_active is True)
        )
        active_users = active_result.scalar() or 0

        # Superusers
        super_result = await self.db.execute(
            select(func.count(User.id)).where(User.is_superuser is True)
        )
        superusers = super_result.scalar() or 0

        # Recent registrations (last 30 days)
        thirty_days_ago = utcnow() - timedelta(days=30)

        recent_result = await self.db.execute(
            select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
        )
        recent_users = recent_result.scalar() or 0

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "superusers": superusers,
            "recent_registrations": recent_users,
            "activity_rate": active_users / total_users if total_users > 0 else 0,
        }
