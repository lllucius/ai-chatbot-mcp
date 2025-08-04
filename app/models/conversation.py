"""Conversation and message models for chat functionality.

This module provides SQLAlchemy models for managing conversations and messages
in the AI chatbot platform, including user relationships, message tracking,
and conversation metadata.
"""

import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModelDB

if TYPE_CHECKING:
    from .user import User


class Conversation(BaseModelDB):
    """Conversation model for chat sessions and dialogue management.

    Attributes:
        title (Mapped[Optional[str]]): Conversation title for identification.
        is_active (Mapped[bool]): Whether the conversation is active.
        message_count (Mapped[int]): Cached count of messages in conversation.
        user_id (Mapped[uuid.UUID]): Foreign key to conversation owner.
        metainfo (Mapped[Optional[Dict[str, Any]]]): JSON metadata storage.
        messages (relationship): One-to-many relationship with Message entities.
        user (relationship): Many-to-one relationship with User entity.

    """

    __tablename__ = "conversations"

    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metainfo: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
    user: Mapped["User"] = relationship("User", back_populates="conversations")

    # Indexes
    __table_args__ = (
        Index("idx_conversations_user_id", "user_id"),
        Index("idx_conversations_active", "is_active"),
        Index("idx_conversations_title", "title"),
    )

    def __repr__(self) -> str:
        """Return string representation of Conversation model.

        Returns:
            str: String representation containing title and user_id.

        """
        return f"<Conversation(title='{self.title}', user_id={self.user_id})>"


class Message(BaseModelDB):
    """Message model for individual chat messages within conversations.

    Attributes:
        role (Mapped[str]): Message role identifier (user, assistant, system).
        content (Mapped[str]): The actual message text content.
        token_count (Mapped[int]): Number of tokens in the message for usage tracking.
        conversation_id (Mapped[uuid.UUID]): Foreign key to parent conversation.
        tool_calls (Mapped[Optional[Dict[str, Any]]]): JSON data for tool calls.
        tool_call_results (Mapped[Optional[Dict[str, Any]]]): JSON data for tool results.
        metainfo (Mapped[Optional[Dict[str, Any]]]): Additional message metadata.
        conversation (relationship): Reference to the parent conversation.

    """

    __tablename__ = "messages"

    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_calls: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    tool_call_results: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    metainfo: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )

    # Indexes
    __table_args__ = (
        Index("idx_messages_conversation_id", "conversation_id"),
        Index("idx_messages_role", "role"),
        Index("idx_messages_created_at", "created_at"),
    )


    def __repr__(self) -> str:
        """Return string representation of Message model.

        Returns:
            str: String representation containing role and conversation_id.

        """
        return f"<Message(role='{self.role}', conv_id={self.conversation_id})>"
