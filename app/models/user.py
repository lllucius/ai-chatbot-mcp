"""User model for authentication and profile management.

This module implements the User entity with authentication capabilities,
profile management, and security features including password hashing,
role-based access control, and relationship management with user-generated
content.
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
    """User model with authentication and profile management.

    Provides secure user authentication with bcrypt password hashing,
    role-based access control, and relationships with user-generated content.

    Attributes:
        username (Mapped[str]): Unique username for authentication.
        email (Mapped[str]): User email address for identification.
        hashed_password (Mapped[str]): Bcrypt-hashed password.
        full_name (Mapped[Optional[str]]): Optional display name.
        is_active (Mapped[bool]): Account activation status.
        is_superuser (Mapped[bool]): Administrative privilege flag.
        last_login (Mapped[Optional[datetime]]): Timestamp of most recent login.
        documents (relationship): One-to-many relationship with Document entities.
        conversations (relationship): One-to-many relationship with Conversation entities.

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
        """Return string representation of User model.

        Returns:
            str: String representation containing username and email.

        """
        return f"<User(username='{self.username}', email='{self.email}')>"
