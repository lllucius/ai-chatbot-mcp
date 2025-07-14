"""
User service for user management and profile operations.

This service provides methods for user CRUD operations, profile management,
and user-related statistics and analytics.

Generated on: 2025-07-14 03:08:19 UTC
Current User: lllucius
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from ..models.user import User
from ..models.document import Document
from ..models.conversation import Conversation
from ..schemas.user import UserUpdate, UserProfile
from ..utils.security import get_password_hash, verify_password
from ..core.exceptions import NotFoundError, ValidationError, AuthenticationError
from ..config import settings

logger = logging.getLogger(__name__)


class UserService:
    """
    Service for user management and profile operations.
    
    This service handles user CRUD operations, profile management,
    statistics generation, and user-related business logic.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize user service.
        
        Args:
            db: Database session for user operations
        """
        self.db = db
    
    async def get_user_profile(self, user_id: int) -> UserProfile:
        """
        Get detailed user profile with statistics.
        
        Args:
            user_id: User ID
            
        Returns:
            UserProfile: User profile with statistics
            
        Raises:
            NotFoundError: If user not found
        """
        # Get user
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("User not found")
        
        # Get statistics
        doc_count_result = await self.db.execute(
            select(func.count(Document.id)).where(Document.owner_id == user_id)
        )
        document_count = doc_count_result.scalar() or 0
        
        conv_count_result = await self.db.execute(
            select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
        )
        conversation_count = conv_count_result.scalar() or 0
        
        msg_count_result = await self.db.execute(
            select(func.sum(Conversation.message_count))
            .where(Conversation.user_id == user_id)
        )
        total_messages = msg_count_result.scalar() or 0
        
        # Create profile
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
            "total_messages": total_messages
        }
        
        return UserProfile.model_validate(profile_data)
    
    async def update_user(self, user_id: int, user_update: UserUpdate) -> User:
        """
        Update user profile information.
        
        Args:
            user_id: User ID to update
            user_update: Update data
            
        Returns:
            User: Updated user object
            
        Raises:
            NotFoundError: If user not found
            ValidationError: If update data is invalid
        """
        # Get user
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("User not found")
        
        # Check for email conflicts
        if user_update.email and user_update.email != user.email:
            existing_email = await self.db.execute(
                select(User).where(
                    and_(User.email == user_update.email, User.id != user_id)
                )
            )
            if existing_email.scalar_one_or_none():
                raise ValidationError("Email already in use")
        
        # Update fields
        if user_update.email is not None:
            user.email = user_update.email
        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        if user_update.is_active is not None:
            user.is_active = user_update.is_active
        
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info(f"User updated: {user.username}")
        return user
    
    async def change_password(
        self, 
        user_id: int, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """
        Change user password.
        
        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            bool: True if password changed successfully
            
        Raises:
            NotFoundError: If user not found
            AuthenticationError: If current password is incorrect
        """
        # Get user
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("User not found")
        
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()
        
        logger.info(f"Password changed for user: {user.username}")
        return True
    
    async def list_users(
        self,
        page: int = 1,
        size: int = 20,
        active_only: bool = False,
        superuser_only: bool = False
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
            filters.append(User.is_active == True)
        if superuser_only:
            filters.append(User.is_superuser == True)
        
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
    
    async def delete_user(self, user_id: int) -> bool:
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
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
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
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_result.scalar() or 0
        
        # Superusers
        super_result = await self.db.execute(
            select(func.count(User.id)).where(User.is_superuser == True)
        )
        superusers = super_result.scalar() or 0
        
        # Recent registrations (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
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
            "activity_rate": active_users / total_users if total_users > 0 else 0
        }