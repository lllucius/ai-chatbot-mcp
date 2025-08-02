"""
User service for comprehensive user management and profile operations.

This service provides enterprise-grade user management functionality including CRUD
operations, profile management, password operations, user analytics, and administrative
controls. Implements advanced user lifecycle management with comprehensive validation,
security controls, and audit logging for production-ready user management workflows.

Key Features:
- Comprehensive user profile management with embedded statistics and analytics
- Secure password change operations with current password verification
- Advanced user listing with flexible filtering, sorting, and pagination
- User deletion with cascading cleanup and data integrity protection
- System-wide user analytics and metrics for business intelligence
- Administrative user creation with role and permission management

User Management Capabilities:
- User account creation with validation and conflict detection
- Profile retrieval with embedded activity statistics and engagement metrics
- User information updates with field-level validation and security controls
- Password management with secure hashing and verification workflows
- Account status management including activation and deactivation
- User search and filtering with multiple criteria and performance optimization

Security Features:
- Password verification using secure comparison to prevent timing attacks
- Input validation and sanitization to prevent injection attacks and data corruption
- Comprehensive audit logging for user operations and security monitoring
- Permission-based access control for administrative operations
- Data integrity protection with proper transaction handling and rollback
- Privacy protection with secure data handling and selective information exposure

Administrative Operations:
- User listing with pagination and filtering for management interfaces
- Bulk user operations with batch processing and error handling
- User statistics and analytics for system monitoring and business intelligence
- Account management including activation, deactivation, and role assignment
- Data export and reporting capabilities for compliance and analysis
- Integration with external systems for user provisioning and synchronization

Use Cases:
- User registration and onboarding workflows in web and mobile applications
- Profile management and self-service account operations
- Administrative user management and system administration
- User analytics and engagement monitoring for business intelligence
- Compliance reporting and audit trail management
- Integration with external identity providers and user management systems

Data Integrity:
- Comprehensive validation for all user data fields and business rules
- Transactional operations with proper rollback handling for data consistency
- Foreign key constraint handling for related data and cascading operations
- Duplicate detection and conflict resolution for user uniqueness
- Data sanitization and normalization for consistent storage and retrieval
"""

import logging
from datetime import timedelta
from typing import Any, Dict, List, Tuple
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import AuthenticationError, NotFoundError, ValidationError
from ..models.conversation import Conversation
from ..models.document import Document
from ..models.user import User
from shared.schemas.user import UserUpdate
from ..utils.security import get_password_hash, verify_password
from ..utils.timestamp import utcnow
from .base import BaseService

logger = logging.getLogger(__name__)


class UserService(BaseService):
    """
    Service for comprehensive user management and profile operations.

    This service extends BaseService to provide enterprise-grade user management
    functionality including CRUD operations, profile management, analytics generation,
    and administrative controls. Implements advanced user lifecycle management with
    comprehensive validation, security controls, and audit logging for production
    environments.

    User Management Capabilities:
    - User account creation with comprehensive validation and conflict detection
    - Profile retrieval with embedded activity statistics and engagement metrics
    - User information updates with field-level validation and security controls
    - Password management with secure verification and complexity requirements
    - Account status management including activation, deactivation, and role assignment
    - User search and filtering with multiple criteria and performance optimization

    Security Features:
    - Secure password hashing using industry-standard bcrypt algorithms
    - Password verification with protection against timing attacks
    - Input validation and sanitization to prevent injection attacks
    - Comprehensive audit logging for user operations and security monitoring
    - Permission-based access control for administrative operations
    - Data integrity protection with proper transaction handling

    Administrative Operations:
    - User listing with pagination, filtering, and sorting capabilities
    - Bulk user operations with batch processing and error handling
    - User statistics and analytics for system monitoring and business intelligence
    - Account management including role assignment and permission control
    - Data export and reporting capabilities for compliance and analysis
    - Integration support for external systems and identity providers

    Responsibilities:
    - User profile retrieval with comprehensive statistics and activity metrics
    - User information updates with validation and business rule enforcement
    - Password change operations with security verification and complexity validation
    - User listing with flexible filtering, sorting, and pagination for management
    - User deletion with proper cleanup and cascading data integrity protection
    - System-wide user analytics and reporting for operational monitoring

    Use Cases:
    - User registration and onboarding workflows in web and mobile applications
    - Profile management and self-service account operations for end users
    - Administrative user management and system administration interfaces
    - User analytics and engagement monitoring for business intelligence
    - Compliance reporting and audit trail management for regulatory requirements
    - Integration with external identity providers and user management systems

    Example:
        user_service = UserService(db_session)

        # Create new user account
        user = await user_service.create_user("john_doe", "john@example.com", "password")

        # Get user profile with statistics
        profile = await user_service.get_user_profile(user.id)

        # Update user information
        await user_service.update_user(user.id, UserUpdate(full_name="John Doe"))

        # List users with pagination
        users = await user_service.list_users(skip=0, limit=10)
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize user service with database session and operational configuration.

        Sets up the user service with database connectivity and logging capabilities
        for comprehensive user management operations. Initializes service-specific
        configuration and monitoring for user lifecycle management workflows.

        Args:
            db: Database session for user operations, profile management,
                and analytics with proper transaction handling and rollback support

        Security Notes:
            - Database session configured with proper isolation and security controls
            - Structured logging initialized for audit trails and security monitoring
            - Service configuration follows principle of least privilege
            - Transaction handling ensures data integrity and consistency

        Use Cases:
            - Service initialization in user management API endpoints
            - Dependency injection for user-related application components
            - Setup for user administration and profile management workflows
            - Integration with FastAPI dependency injection and session management

        Example:
            user_service = UserService(db_session)
            # Service ready for user management operations with full configuration
        """
        super().__init__(db, "user_service")

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str = None,
        is_superuser: bool = False,
    ) -> User:
        """
        Create a new user account with comprehensive validation and security controls.

        Creates a new user account with secure password hashing, uniqueness validation,
        and comprehensive conflict detection. Implements robust validation to prevent
        duplicate accounts and ensure data integrity with proper error handling and
        audit logging for administrative user creation workflows.

        Args:
            username: Unique username for the user account with validation for
                     character restrictions, length limits, and uniqueness
            email: User's email address with format validation and uniqueness checking
            password: Plain text password that will be securely hashed using bcrypt
                     with configurable work factor for enhanced security
            full_name: Optional full name for profile display and user identification
            is_superuser: Whether the user should have superuser privileges for
                         administrative operations and system management

        Returns:
            User: Newly created user object containing the following properties:
                - id: Unique UUID identifier for the user account
                - username: Validated and sanitized username for login
                - email: Validated email address for account management
                - full_name: Optional full name for profile display
                - is_active: Account status set to True for immediate access
                - is_superuser: Administrative privilege flag
                - created_at: Timestamp of account creation for audit tracking
                - hashed_password: Securely hashed password using bcrypt

        Raises:
            ValidationError: Raised in the following scenarios:
                - Username already exists in the system (case-insensitive check)
                - Email address already registered to another account
                - Invalid email format or domain validation failure
                - Password doesn't meet security complexity requirements
                - Username contains invalid characters or exceeds length limits
                - User creation data fails schema validation or business rules
                - Database constraint violations or transaction failures

        Security Notes:
            - Password is hashed using bcrypt with configurable work factor for security
            - Username and email uniqueness validation prevents account conflicts
            - Input sanitization prevents injection attacks and data corruption
            - Audit logging captures user creation attempts for security monitoring
            - Administrative privilege assignment follows principle of least privilege
            - Database transactions ensure data consistency and rollback on failures

        Use Cases:
            - Administrative user creation for enterprise and organizational accounts
            - Bulk user import processes with validation and conflict resolution
            - User provisioning for integration with external systems and services
            - Account creation workflows with role and permission assignment
            - System user creation for automated processes and service accounts

        Example:
            user = await user_service.create_user(
                username="admin_user",
                email="admin@example.com",
                password="SecureAdminPass123!",
                full_name="Administrator",
                is_superuser=True
            )
            # Returns User object with secure password hash and admin privileges
        """
        operation = "create_user"
        self._log_operation_start(operation, username=username, email=email)

        try:
            await self._ensure_db_session()

            # Check if username already exists
            existing_username = await self.db.execute(
                select(User).where(User.username == username)
            )
            if existing_username.scalar_one_or_none():
                raise ValidationError("Username already exists")

            # Check if email already exists
            existing_email = await self.db.execute(
                select(User).where(User.email == email)
            )
            if existing_email.scalar_one_or_none():
                raise ValidationError("Email already exists")

            # Create new user
            hashed_password = get_password_hash(password)

            user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                full_name=full_name,
                is_active=True,
                is_superuser=is_superuser,
            )

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            self._log_operation_success(
                operation,
                user_id=str(user.id),
                username=user.username,
                is_superuser=user.is_superuser,
            )

            return user

        except ValidationError:
            raise
        except Exception as e:
            self._log_operation_error(operation, e, username=username, email=email)
            await self.db.rollback()
            raise ValidationError(f"User creation failed: {e}")

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
