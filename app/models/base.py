"""Base database models and mixins for common functionality.

This module provides foundation classes for all database models including:
- BaseModelDB: Core database model with UUID primary keys and timestamps
- UUIDMixin: UUID primary key generation
- TimestampMixin: Automatic timestamp tracking

All models inherit from these base classes to ensure consistent behavior,
proper indexing, and audit trail capabilities.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class TimestampMixin:
    """Provide automatic timestamp tracking for creation and modification.

    Attributes:
        created_at (Mapped[datetime]): Record creation timestamp.
        updated_at (Mapped[datetime]): Record modification timestamp.

    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        doc="When the record was created",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )


class UUIDMixin:
    """Provide UUID primary key generation for global uniqueness.

    Attributes:
        id (Mapped[uuid.UUID]): Primary key with UUID4 generation.

    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the record",
    )


class BaseModelDB(DeclarativeBase, UUIDMixin, TimestampMixin):
    """Base database model providing UUID primary keys and timestamp tracking.

    Combines UUIDMixin and TimestampMixin to provide a foundation for all database
    entities with automatic UUID primary key generation, timestamp tracking, and
    intelligent table name generation from class names.
    """

    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        """Generate database table names from class names using snake_case conversion.

        Returns:
            str: Database table name in snake_case format.

        """
        # Convert CamelCase to snake_case
        import re

        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", cls.__name__)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()
