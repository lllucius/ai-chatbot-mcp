"Service layer for user business logic."

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
from ..schemas.user import UserUpdate
from ..utils.security import get_password_hash, verify_password
from ..utils.timestamp import utcnow
from .base import BaseService

logger = logging.getLogger(__name__)


class UserService(BaseService):
    "User service for business logic operations."

    def __init__(self, db: AsyncSession):
        "Initialize class instance."
        super().__init__(db, "user_service")

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str = None,
        is_superuser: bool = False,
    ) -> User:
        "Create new user."
        operation = "create_user"
        self._log_operation_start(operation, username=username, email=email)
        try:
            (await self._ensure_db_session())
            existing_username = await self.db.execute(
                select(User).where((User.username == username))
            )
            if existing_username.scalar_one_or_none():
                raise ValidationError("Username already exists")
            existing_email = await self.db.execute(
                select(User).where((User.email == email))
            )
            if existing_email.scalar_one_or_none():
                raise ValidationError("Email already exists")
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
            (await self.db.commit())
            (await self.db.refresh(user))
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
            (await self.db.rollback())
            raise ValidationError(f"User creation failed: {e}")

    async def get_user_profile(self, user_id: UUID) -> User:
        "Get user profile data."
        operation = "get_user_profile"
        self._log_operation_start(operation, user_id=str(user_id))
        try:
            (await self._ensure_db_session())
            user_result = await self.db.execute(
                select(User).where((User.id == user_id))
            )
            user = user_result.scalar_one_or_none()
            if not user:
                self.logger.warning(
                    "User not found", user_id=str(user_id), operation=operation
                )
                raise NotFoundError(f"User not found with ID: {user_id}")
            doc_count_result = await self.db.execute(
                select(func.count(Document.id)).where((Document.owner_id == user_id))
            )
            document_count = doc_count_result.scalar() or 0
            conv_count_result = await self.db.execute(
                select(func.count(Conversation.id)).where(
                    (Conversation.user_id == user_id)
                )
            )
            conversation_count = conv_count_result.scalar() or 0
            msg_count_result = await self.db.execute(
                select(func.sum(Conversation.message_count)).where(
                    (Conversation.user_id == user_id)
                )
            )
            total_messages = msg_count_result.scalar() or 0
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
        "Update existing user."
        operation = "update_user"
        update_fields = {
            k: v for (k, v) in user_update.model_dump().items() if (v is not None)
        }
        self._log_operation_start(
            operation, user_id=str(user_id), update_fields=list(update_fields.keys())
        )
        try:
            (await self._ensure_db_session())
            user_result = await self.db.execute(
                select(User).where((User.id == user_id))
            )
            user = user_result.scalar_one_or_none()
            if not user:
                self.logger.warning("User not found for update", user_id=str(user_id))
                raise NotFoundError(f"User not found with ID: {user_id}")
            if user_update.email and (user_update.email != user.email):
                existing_email = await self.db.execute(
                    select(User).where(
                        and_((User.email == user_update.email), (User.id != user_id))
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
            (await self.db.commit())
            (await self.db.refresh(user))
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
            (await self.db.rollback())
            raise

    async def change_password(
        self, user_id: UUID, current_password: str, new_password: str
    ) -> bool:
        "Change Password operation."
        operation = "change_password"
        self._log_operation_start(operation, user_id=str(user_id))
        try:
            (await self._ensure_db_session())
            user_result = await self.db.execute(
                select(User).where((User.id == user_id))
            )
            user = user_result.scalar_one_or_none()
            if not user:
                self.logger.warning(
                    "User not found for password change", user_id=str(user_id)
                )
                raise NotFoundError(f"User not found with ID: {user_id}")
            if not verify_password(current_password, user.hashed_password):
                self.logger.warning(
                    "Invalid current password provided",
                    user_id=str(user_id),
                    username=user.username,
                )
                raise AuthenticationError("Current password is incorrect")
            user.hashed_password = get_password_hash(new_password)
            (await self.db.commit())
            self._log_operation_success(
                operation, user_id=str(user_id), username=user.username
            )
            return True
        except (NotFoundError, AuthenticationError):
            raise
        except Exception as e:
            self._log_operation_error(operation, e, user_id=str(user_id))
            (await self.db.rollback())
            raise

    async def list_users(
        self,
        page: int = 1,
        size: int = 20,
        active_only: bool = False,
        superuser_only: bool = False,
    ) -> Tuple[(List[User], int)]:
        "List users entries."
        filters = []
        if active_only:
            filters.append((User.is_active is True))
        if superuser_only:
            filters.append((User.is_superuser is True))
        count_query = select(func.count(User.id))
        if filters:
            count_query = count_query.where(and_(*filters))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        query = select(User).order_by(desc(User.created_at))
        if filters:
            query = query.where(and_(*filters))
        query = query.offset(((page - 1) * size)).limit(size)
        result = await self.db.execute(query)
        users = result.scalars().all()
        return (list(users), total)

    async def delete_user(self, user_id: UUID) -> bool:
        "Delete user."
        user_result = await self.db.execute(select(User).where((User.id == user_id)))
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        (await self.db.delete(user))
        (await self.db.commit())
        logger.info(f"User deleted: {user.username}")
        return True

    async def get_user_statistics(self) -> Dict[(str, Any)]:
        "Get user statistics data."
        total_result = await self.db.execute(select(func.count(User.id)))
        total_users = total_result.scalar() or 0
        active_result = await self.db.execute(
            select(func.count(User.id)).where((User.is_active is True))
        )
        active_users = active_result.scalar() or 0
        super_result = await self.db.execute(
            select(func.count(User.id)).where((User.is_superuser is True))
        )
        superusers = super_result.scalar() or 0
        thirty_days_ago = utcnow() - timedelta(days=30)
        recent_result = await self.db.execute(
            select(func.count(User.id)).where((User.created_at >= thirty_days_ago))
        )
        recent_users = recent_result.scalar() or 0
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": (total_users - active_users),
            "superusers": superusers,
            "recent_registrations": recent_users,
            "activity_rate": ((active_users / total_users) if (total_users > 0) else 0),
        }
