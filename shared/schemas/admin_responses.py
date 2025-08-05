"""Administrative and database response schemas.

This module contains response schemas for administrative operations, database management,
and system monitoring that were previously scattered across common.py.
"""

from datetime import datetime, timezone
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field


def utcnow() -> datetime:
    """Get current UTC datetime with timezone awareness."""
    return datetime.now(timezone.utc)


# --- Search and Export Response Models ---


class SearchResponse(BaseModel):
    """Search response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Search operation success status")
    data: Dict[str, Any] = Field(..., description="Search results data")

    def model_dump_json(self, **kwargs):
        """Serialize model with standard JSON handling."""
        data = self.model_dump(**kwargs)
        import json

        return json.dumps(data)


class RegistryStatsResponse(BaseModel):
    """Registry statistics response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Status message")
    data: Dict[str, Any] = Field(..., description="Registry statistics data")

    def model_dump_json(self, **kwargs):
        """Serialize model with standard JSON handling."""
        data = self.model_dump(**kwargs)
        import json

        return json.dumps(data)


class ConversationStatsResponse(BaseModel):
    """Conversation statistics response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    data: Dict[str, Any] = Field(..., description="Conversation statistics data")

    def model_dump_json(self, **kwargs):
        """Serialize model with standard JSON handling."""
        data = self.model_dump(**kwargs)
        import json

        return json.dumps(data)
