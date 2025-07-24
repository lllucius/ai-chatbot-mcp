"Conversation model definitions and database schemas."

import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import JSON, Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModelDB

if TYPE_CHECKING:
    from .user import User


class Conversation(BaseModelDB):
    "Conversation data model for database operations."

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
    metainfo: Mapped[Optional[Dict[(str, Any)]]] = mapped_column(JSON, nullable=True)
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    __table_args__ = (
        Index("idx_conversations_user_id", "user_id"),
        Index("idx_conversations_active", "is_active"),
        Index("idx_conversations_title", "title"),
    )

    def __repr__(self) -> str:
        "Return detailed object representation."
        return f"<Conversation(title='{self.title}', user_id={self.user_id})>"


class Message(BaseModelDB):
    "Message data model for database operations."

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
    tool_calls: Mapped[Optional[Dict[(str, Any)]]] = mapped_column(JSON, nullable=True)
    tool_call_results: Mapped[Optional[Dict[(str, Any)]]] = mapped_column(
        JSON, nullable=True
    )
    metainfo: Mapped[Optional[Dict[(str, Any)]]] = mapped_column(JSON, nullable=True)
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )
    __table_args__ = (
        Index("idx_messages_conversation_id", "conversation_id"),
        Index("idx_messages_role", "role"),
        Index("idx_messages_created_at", "created_at"),
    )
