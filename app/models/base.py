"""Base database models and mixins for common functionality.

This module provides foundation classes for all database models including:
- BaseModelDB: Core database model with MLID primary keys and timestamps
- MLIDMixin: MLID primary key generation
- TimestampMixin: Automatic timestamp tracking

All models inherit from these base classes to ensure consistent behavior,
proper indexing, and audit trail capabilities.
"""

from datetime import datetime

from sqlalchemy import DateTime, text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ..utils.mlid import generate_mlid
from ..utils.mlid_types import MLID


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


class MLIDMixin:
    """Provide MLID primary key generation for global uniqueness.

    Attributes:
        id (Mapped[str]): Primary key with MLID generation.

    """

    id: Mapped[str] = mapped_column(
        MLID,
        primary_key=True,
        default=generate_mlid,
        doc="Unique MLID identifier for the record",
    )


class BaseModelDB(DeclarativeBase, MLIDMixin, TimestampMixin):
    """Base database model providing MLID primary keys and timestamp tracking.

    Combines MLIDMixin and TimestampMixin to provide a foundation for all database
    entities with automatic MLID primary key generation, timestamp tracking, and
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
