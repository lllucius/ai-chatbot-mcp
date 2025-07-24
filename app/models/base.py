"Base model definitions and database schemas."

import uuid
from datetime import datetime
from sqlalchemy import DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class TimestampMixin:
    "TimestampMixin class for specialized functionality."

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
        doc="When the record was last updated",
    )


class UUIDMixin:
    "UUIDMixin class for specialized functionality."

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the record",
    )


class BaseModelDB(DeclarativeBase, UUIDMixin, TimestampMixin):
    "BaseModelDB class for specialized functionality."

    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        "Tablename   operation."
        import re

        name = re.sub("(.)([A-Z][a-z]+)", "\\1_\\2", cls.__name__)
        return re.sub("([a-z0-9])([A-Z])", "\\1_\\2", name).lower()
