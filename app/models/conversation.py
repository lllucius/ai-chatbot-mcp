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
    Conversation model for managing chat sessions and dialogue threads.

    This model represents conversation threads between users and AI assistants,
    including conversation metadata, message tracking, and user relationships.
    Extends BaseModelDB to inherit common database functionality.

    Attributes:
        title: Human-readable conversation title or name (max 500 chars)
        is_active: Whether the conversation is currently active and accessible
        message_count: Cached count of messages in this conversation
        user_id: UUID of the user who owns this conversation
        metainfo: Additional JSON metadata for conversation context
        messages: Collection of messages in chronological order
        user: Reference to the user who owns this conversation

    Database Indexes:
        - idx_conversations_user_id: Fast lookup by user ownership
        - idx_conversations_active: Filter by active status
        - idx_conversations_title: Search by conversation title

    Relationships:
        - messages: One-to-many relationship with Message model, ordered by created_at
        - user: Many-to-one relationship with User model
        - Uses cascade delete to maintain referential integrity

    Business Logic:
        - message_count is maintained automatically when messages are added/removed
        - Conversations can be deactivated without deletion for archival purposes
        - metainfo field supports flexible conversation context storage

    Note:
        This model inherits id, created_at, and updated_at fields from BaseModelDB.
        Messages are automatically ordered by creation timestamp in the relationship.
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
        """
        Return string representation of Conversation model.

        Provides a concise string representation for debugging and logging.

        Returns:
            str: String representation containing title and user_id
        """
        return f"<Conversation(title='{self.title}', user_id={self.user_id})>"


class Message(BaseModelDB):
    """
    Message model for individual chat messages within conversations.

    This model represents individual messages in conversation threads, supporting
    various message types including user inputs, AI responses, and system messages.
    Includes support for tool calls and comprehensive message metadata.

    Attributes:
        role: Message role identifier (user, assistant, system) - max 20 chars
        content: The actual message text content (unlimited length)
        token_count: Number of tokens in the message for usage tracking
        conversation_id: UUID of the parent conversation this message belongs to
        tool_calls: JSON data containing tool calls made in this message
        tool_call_results: JSON data containing results from executed tool calls
        metainfo: Additional JSON metadata for message context and processing
        conversation: Reference to the parent conversation

    Message Roles:
        - user: Messages from human users
        - assistant: Messages from AI assistant
        - system: System messages and instructions

    Database Indexes:
        - idx_messages_conversation_id: Fast lookup by conversation
        - idx_messages_role: Filter by message role
        - idx_messages_created_at: Chronological ordering and time-based queries

    Relationships:
        - conversation: Many-to-one relationship with Conversation model
        - Uses cascade delete through conversation relationship

    Tool Call Support:
        - tool_calls: Stores tool invocation data and parameters
        - tool_call_results: Stores execution results and responses
        - Supports complex tool interaction workflows

    Note:
        This model inherits id, created_at, and updated_at fields from BaseModelDB.
        Messages are ordered chronologically within conversations.
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
        """
        Return string representation of Message model.

        Provides a concise string representation for debugging and logging.

        Returns:
            str: String representation containing role and conversation_id
        """
        return f"<Message(role='{self.role}', conv_id={self.conversation_id})>"
