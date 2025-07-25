"""
Conversation and message models for chat functionality.

This module defines models for managing chat conversations and messages,
including AI responses, tool calls, and conversation metainfo.

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
    """
    Conversation model for chat sessions.

    Attributes:
        title: Conversation title or name
        is_active: Whether the conversation is active
        message_count: Number of messages in conversation
        user_id: ID of the user who owns this conversation
        metainfo: Additional conversation metainfo
        messages: Related message objects
        user: Related user object
    """

    __tablename__ = "conversations"

    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
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
        """Return string representation of Conversation model."""
        return f"<Conversation(title='{self.title}', user_id={self.user_id})>"


class Message(BaseModelDB):
    """
    Message model for individual chat messages.

    Attributes:
        role: Message role (user, assistant, system)
        content: Message content/text
        token_count: Number of tokens in message
        conversation_id: ID of the parent conversation
        tool_calls: Tool calls made in this message
        tool_call_results: Results from tool calls
        metainfo: Additional message metainfo
        conversation: Related conversation object
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
    tool_call_results: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    metainfo: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index("idx_messages_conversation_id", "conversation_id"),
        Index("idx_messages_role", "role"),
        Index("idx_messages_created_at", "created_at"),
    )


#    def __repr__(self) -> str:
#        return f"<Message(role='{self.role}', conv_id={self.conversation_id})>"
