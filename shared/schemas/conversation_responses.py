"""Pydantic response schemas for conversation API endpoints.

This module provides response models for all conversation-related endpoints that currently
return raw dictionaries, ensuring type safety and proper API documentation.
"""

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ConversationMetadata(BaseModel):
    """Conversation metadata for export."""

    id: str = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: Optional[str] = Field(default=None, description="Last update timestamp")
    is_active: bool = Field(..., description="Whether conversation is active")
    message_count: int = Field(..., description="Number of messages in conversation")


class ExportedMessage(BaseModel):
    """Exported message data."""

    id: str = Field(..., description="Message ID")
    role: str = Field(..., description="Message role (user, assistant, etc.)")
    content: str = Field(..., description="Message content")
    created_at: str = Field(..., description="Message creation timestamp")
    tool_calls: Optional[Any] = Field(
        default=None, description="Tool calls made in message"
    )
    tool_call_id: Optional[str] = Field(
        default=None, description="Tool call ID if this is a tool response"
    )
    name: Optional[str] = Field(default=None, description="Name for tool messages")


class ExportInfo(BaseModel):
    """Export operation information."""

    format: str = Field(..., description="Export format used")
    exported_at: str = Field(..., description="Export timestamp")
    message_count: int = Field(..., description="Number of messages exported")
    includes_metadata: bool = Field(..., description="Whether metadata was included")


class ConversationExportDataJSON(BaseModel):
    """JSON format export data."""

    conversation: ConversationMetadata = Field(..., description="Conversation metadata")
    messages: List[ExportedMessage] = Field(
        default_factory=list, description="Exported messages"
    )


class ConversationExportDataText(BaseModel):
    """Text format export data."""

    content: str = Field(..., description="Exported conversation as text")
    format: str = Field(default="text", description="Format identifier")


class ConversationExportDataCSV(BaseModel):
    """CSV format export data."""

    content: str = Field(..., description="Exported conversation as CSV")
    format: str = Field(default="csv", description="Format identifier")


class ConversationExportData(BaseModel):
    """Generic export data that can be any format."""

    # Union type for different export data formats
    data: Any = Field(
        ..., description="Export data in the requested format"
    )  # Will be JSON, text content, or CSV content
    export_info: ExportInfo = Field(..., description="Export operation information")
