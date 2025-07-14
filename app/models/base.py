"""
Base database model with common functionality.

This module provides the base model class that all other models inherit from,
including common fields and functionality like timestamps and soft deletes.

Current Date and Time (UTC): 2025-07-14 05:01:09
Current User: lllucius
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, String, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pydantic import BaseModel, ConfigDict


class Base(DeclarativeBase):
    """Base class for all database models."""
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        # Convert CamelCase to snake_case
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


class TimestampMixin:
    """Mixin for adding timestamp fields to models."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        doc="When the record was created"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        doc="When the record was last updated"
    )


class SoftDeleteMixin:
    """Mixin for adding soft delete functionality to models."""
    
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether the record has been soft deleted"
    )
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the record was soft deleted"
    )


class UUIDMixin:
    """Mixin for adding UUID primary key to models."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the record"
    )


# Pydantic V2 Base Models

class BaseSchema(BaseModel):
    """Base Pydantic model with modern V2 configuration."""
    
    model_config = ConfigDict(
        # Enable ORM mode for SQLAlchemy integration
        from_attributes=True,
        # Allow population by field name and alias
        populate_by_name=True,
        # Use enum values instead of enum objects
        use_enum_values=True,
        # Validate assignment
        validate_assignment=True,
        # Allow extra fields in input (but don't include in output)
        extra='ignore',
        # Serialize by alias
        ser_by_alias=True
    )


class TimestampSchema(BaseSchema):
    """Base schema with timestamp fields and serializers."""
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def model_dump_json(self, **kwargs):
        """Custom JSON serialization with datetime handling."""
        data = self.model_dump(**kwargs)
        
        # Convert datetime fields to ISO format strings
        for field_name in ['created_at', 'updated_at', 'deleted_at']:
            if field_name in data and data[field_name] is not None:
                if isinstance(data[field_name], datetime):
                    data[field_name] = data[field_name].isoformat() + 'Z'
        
        import json
        return json.dumps(data)


class UUIDSchema(BaseSchema):
    """Base schema with UUID field and serializer."""
    
    id: Optional[uuid.UUID] = None
    
    def model_dump_json(self, **kwargs):
        """Custom JSON serialization with UUID handling."""
        data = self.model_dump(**kwargs)
        
        # Convert UUID to string
        if 'id' in data and data['id'] is not None:
            if isinstance(data['id'], uuid.UUID):
                data['id'] = str(data['id'])
        
        import json
        return json.dumps(data)


class BaseModelSchema(BaseSchema):
    """Complete base schema with UUID and timestamps."""
    
    id: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def model_dump_json(self, **kwargs):
        """Custom JSON serialization with UUID and datetime handling."""
        data = self.model_dump(**kwargs)
        
        # Convert UUID to string
        if 'id' in data and data['id'] is not None:
            if isinstance(data['id'], uuid.UUID):
                data['id'] = str(data['id'])
        
        # Convert datetime fields to ISO format strings
        for field_name in ['created_at', 'updated_at', 'deleted_at']:
            if field_name in data and data[field_name] is not None:
                if isinstance(data[field_name], datetime):
                    data[field_name] = data[field_name].isoformat() + 'Z'
        
        import json
        return json.dumps(data)


class PaginationSchema(BaseSchema):
    """Schema for pagination metadata."""
    
    page: int = 1
    per_page: int = 10
    total_items: int = 0
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False
    
    @classmethod
    def create(
        cls,
        page: int,
        per_page: int,
        total_items: int
    ) -> "PaginationSchema":
        """Create pagination metadata."""
        total_pages = (total_items + per_page - 1) // per_page
        
        return cls(
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


class PaginatedResponse(BaseSchema):
    """Generic paginated response schema."""
    
    items: list = []
    pagination: PaginationSchema
    
    @classmethod
    def create(
        cls,
        items: list,
        page: int,
        per_page: int,
        total_items: int
    ) -> "PaginatedResponse":
        """Create a paginated response."""
        return cls(
            items=items,
            pagination=PaginationSchema.create(page, per_page, total_items)
        )