"""
Base Pydantic schemas for API responses.

This module provides base schemas and common response formats
using modern Pydantic V2 features, completely separate from SQLAlchemy models.

"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


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
        extra="ignore",
        # Serialize by alias (deprecated in v2, use serialize_as_any)
        serialize_as_any=True,
    )


class TimestampSchema(BaseSchema):
    """Base schema with timestamp fields."""

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def model_dump_json(self, **kwargs):
        """Custom JSON serialization with datetime handling."""
        data = self.model_dump(**kwargs)

        # Convert datetime fields to ISO format strings
        for field_name in ["created_at", "updated_at", "deleted_at"]:
            if field_name in data and data[field_name] is not None:
                if isinstance(data[field_name], datetime):
                    data[field_name] = data[field_name].isoformat() + "Z"

        import json

        return json.dumps(data)


class UUIDSchema(BaseSchema):
    """Base schema with UUID field."""

    id: Optional[uuid.UUID] = None

    def model_dump_json(self, **kwargs):
        """Custom JSON serialization with UUID handling."""
        data = self.model_dump(**kwargs)

        # Convert UUID to string
        if "id" in data and data["id"] is not None:
            if isinstance(data["id"], uuid.UUID):
                data["id"] = str(data["id"])

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
        if "id" in data and data["id"] is not None:
            if isinstance(data["id"], uuid.UUID):
                data["id"] = str(data["id"])

        # Convert datetime fields to ISO format strings
        for field_name in ["created_at", "updated_at", "deleted_at"]:
            if field_name in data and data[field_name] is not None:
                if isinstance(data[field_name], datetime):
                    data[field_name] = data[field_name].isoformat() + "Z"

        import json

        return json.dumps(data)
