"""Base database models and mixins for common functionality.

This module provides foundation classes for all database models including:
- BaseModelDB: Core database model with BIGSERIAL primary keys and timestamps
- BigSerialMixin: BIGSERIAL primary key generation
- TimestampMixin: Automatic timestamp tracking

All models inherit from these base classes to ensure consistent behavior,
proper indexing, and audit trail capabilities.
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, text
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


class BigSerialMixin:
    """Provide BIGSERIAL primary key generation for auto-incrementing IDs.

    Attributes:
        id (Mapped[int]): Primary key with auto-incrementing BIGSERIAL.

    """

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for the record",
    )


class BaseModelDB(DeclarativeBase, BigSerialMixin, TimestampMixin):
    """Base database model providing BIGSERIAL primary keys and timestamp tracking.

    Combines BigSerialMixin and TimestampMixin to provide a foundation for all database
    entities with automatic BIGSERIAL primary key generation, timestamp tracking, and
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
