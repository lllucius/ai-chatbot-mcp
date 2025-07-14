"""
User model for authentication and user management.

This module defines the User model with authentication fields,
profile information, and relationships to other entities.

Generated on: 2025-07-14 03:47:30 UTC
Current User: lllucius
"""

from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from .base import BaseModelDB

if TYPE_CHECKING:
    from .document import Document
    from .conversation import Conversation


class User(BaseModelDB):
    """
    User model for authentication and profile management.
    
    Attributes:
        username: Unique username for login
        email: User email address
        hashed_password: Bcrypt hashed password
        full_name: Optional full display name
        is_active: Whether the user account is active
        is_superuser: Whether the user has admin privileges
        last_login: Timestamp of last login
        documents: Related documents owned by user
        conversations: Related conversations owned by user
    """
    
    __tablename__ = "users"
    
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    documents: Mapped[List["Document"]] = relationship(
        "Document", 
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation",
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_email", "email"),
        Index("idx_users_active", "is_active"),
        Index("idx_users_superuser", "is_superuser"),
    )
    
    def __repr__(self) -> str:
        return f"<User(username='{self.username}', email='{self.email}')>"
