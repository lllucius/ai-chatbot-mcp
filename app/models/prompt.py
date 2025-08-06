"""Prompt registry model for managing prompts and tracking usage.

This module defines the Prompt model for storing and managing prompts
with usage tracking and categorization capabilities.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import JSON, Boolean, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModelDB


class Prompt(BaseModelDB):
    """Prompt model for managing prompts and their usage.

    Stores prompt templates with categorization, usage tracking, and
    management capabilities for the AI chatbot platform.

    """

    __tablename__ = "prompts"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique name/identifier for the prompt",
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, doc="Display title for the prompt"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, doc="The actual prompt content"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Optional description of the prompt's purpose"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether this is the default prompt",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether the prompt is active/available",
    )
    usage_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of times the prompt has been used",
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, doc="Timestamp of last usage"
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="Optional category for organizing prompts",
    )
    tags: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Optional tags for search and organization",
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_prompts_default", "is_default"),
        Index("idx_prompts_active", "is_active"),
        Index("idx_prompts_usage_count", "usage_count"),
        Index("idx_prompts_last_used", "last_used_at"),
        Index("idx_prompts_category", "category"),
    )

    def record_usage(self):
        """Record a prompt usage event."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()

    def __repr__(self) -> str:
        """Return string representation of Prompt model."""
        default_marker = " (default)" if self.is_default else ""
        status = "active" if self.is_active else "inactive"
        return f"<Prompt(name='{self.name}', status='{status}', usage={self.usage_count}{default_marker})>"
