"""
User model for authentication and user management.

This module defines the User model with authentication fields,
profile information, and relationships to other entities.

"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModelDB

if TYPE_CHECKING:
    from .conversation import Conversation
    from .document import Document


class User(BaseModelDB):
    """
    User model for authentication and comprehensive profile management.

    This model represents system users with authentication capabilities,
    profile information, and relationships to user-generated content.
    Extends BaseModelDB to inherit common fields and database functionality.

    Attributes:
        username: Unique username for login authentication (max 50 chars)
        email: User email address for identification (max 255 chars, unique)
        hashed_password: Bcrypt hashed password for secure authentication
        full_name: Optional full display name for user profile (max 255 chars)
        is_active: Whether the user account is active and can authenticate
        is_superuser: Whether the user has administrative privileges
        last_login: Timestamp of the user's last successful login
        documents: Collection of documents owned by this user
        conversations: Collection of conversations created by this user

    Database Indexes:
        - idx_users_username: Fast lookup by username
        - idx_users_email: Fast lookup by email
        - idx_users_active: Filter by active status
        - idx_users_superuser: Filter by superuser status

    Relationships:
        - documents: One-to-many relationship with Document model
        - conversations: One-to-many relationship with Conversation model
        - Both relationships use cascade delete to maintain referential integrity

    Security Features:
        - Password storage uses bcrypt hashing
        - Username and email uniqueness enforced at database level
        - Account activation/deactivation support
        - Role-based access control via is_superuser flag

    Note:
        This model inherits id, created_at, and updated_at fields from BaseModelDB.
        All password operations should use the security utilities for proper hashing.
    """

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="owner", cascade="all, delete-orphan"
    )

    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_email", "email"),
        Index("idx_users_active", "is_active"),
        Index("idx_users_superuser", "is_superuser"),
    )

    def __repr__(self) -> str:
        """
        Return string representation of User model.

        Provides a concise string representation of the User instance
        for debugging and logging purposes.

        Returns:
            str: String representation containing username and email
        """
        return f"<User(username='{self.username}', email='{self.email}')>"
