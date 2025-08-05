"""Pydantic response schemas for conversation API endpoints.

This module provides response models for all conversation-related endpoints that currently
return raw dictionaries, ensuring type safety and proper API documentation.
"""

from typing import Any, Dict, List, Optional

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


# Additional schemas for conversation API endpoints


class ImportConversationResult(BaseModel):
    """Result of importing a conversation."""

    conversation_id: str = Field(..., description="ID of the imported conversation")
    conversation_title: str = Field(..., description="Title of the imported conversation")
    imported_messages: int = Field(..., description="Number of messages imported")
    total_messages: int = Field(..., description="Total messages in import file")
    errors: List[str] = Field(default_factory=list, description="Import errors")


class ArchivePreviewItem(BaseModel):
    """Preview item for conversation archiving."""

    id: str = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    created_at: str = Field(..., description="Creation timestamp")
    is_active: bool = Field(..., description="Whether conversation is active")
    message_count: int = Field(..., description="Number of messages")


class ArchivePreviewResponse(BaseModel):
    """Preview response for conversation archiving."""

    total_count: int = Field(..., description="Total conversations to be archived")
    preview: List[ArchivePreviewItem] = Field(
        default_factory=list, description="Preview of conversations to archive"
    )
    criteria: Dict[str, Any] = Field(
        default_factory=dict, description="Archive criteria used"
    )


class ArchiveConversationsResult(BaseModel):
    """Result of archiving conversations."""

    archived_count: int = Field(..., description="Number of conversations archived")
    criteria: Dict[str, Any] = Field(
        default_factory=dict, description="Archive criteria used"
    )


class ConversationSearchUserInfo(BaseModel):
    """User information for search results."""

    username: str = Field(..., description="Username")
    email: str = Field(..., description="User email")


class ConversationSearchMatchingMessage(BaseModel):
    """Matching message in conversation search."""

    id: str = Field(..., description="Message ID")
    role: str = Field(..., description="Message role")
    excerpt: str = Field(..., description="Content excerpt with search term")
    created_at: str = Field(..., description="Message creation timestamp")


class ConversationSearchResult(BaseModel):
    """Search result for conversations."""

    id: str = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: Optional[str] = Field(default=None, description="Last update timestamp")
    is_active: bool = Field(..., description="Whether conversation is active")
    message_count: int = Field(..., description="Number of messages")
    user: ConversationSearchUserInfo = Field(..., description="User information")
    matching_messages: List[ConversationSearchMatchingMessage] = Field(
        default_factory=list, description="Messages matching search"
    )


class ConversationSearchCriteria(BaseModel):
    """Search criteria for conversations."""

    query: str = Field(..., description="Search query")
    search_messages: bool = Field(..., description="Whether to search messages")
    user_filter: Optional[str] = Field(default=None, description="User filter")
    date_from: Optional[str] = Field(default=None, description="Start date filter")
    date_to: Optional[str] = Field(default=None, description="End date filter")
    active_only: bool = Field(..., description="Active conversations only")
    limit: int = Field(..., description="Result limit")


class ConversationSearchData(BaseModel):
    """Data for conversation search results."""

    results: List[ConversationSearchResult] = Field(
        default_factory=list, description="Search results"
    )
    total_found: int = Field(..., description="Total results found")
    search_criteria: ConversationSearchCriteria = Field(
        ..., description="Search criteria used"
    )
    timestamp: str = Field(..., description="Search timestamp")


class ConversationStatsConversations(BaseModel):
    """Conversation statistics for conversations."""

    total: int = Field(..., description="Total conversations")
    active: int = Field(..., description="Active conversations")
    inactive: int = Field(..., description="Inactive conversations")


class ConversationStatsMessages(BaseModel):
    """Conversation statistics for messages."""

    total: int = Field(..., description="Total messages")
    avg_per_conversation: float = Field(..., description="Average messages per conversation")
    role_distribution: Dict[str, int] = Field(
        default_factory=dict, description="Message distribution by role"
    )


class ConversationStatsRecentActivity(BaseModel):
    """Recent activity statistics."""

    conversations_last_7_days: int = Field(..., description="New conversations in last 7 days")
    messages_last_7_days: int = Field(..., description="New messages in last 7 days")


class ConversationStatsUserEngagement(BaseModel):
    """User engagement statistics."""

    users_with_conversations: int = Field(..., description="Users with conversations")
    top_users: List[Dict[str, Any]] = Field(
        default_factory=list, description="Top users by activity"
    )


class ConversationStatsData(BaseModel):
    """Comprehensive conversation statistics."""

    conversations: ConversationStatsConversations = Field(
        ..., description="Conversation statistics"
    )
    messages: ConversationStatsMessages = Field(..., description="Message statistics")
    recent_activity: ConversationStatsRecentActivity = Field(
        ..., description="Recent activity statistics"
    )
    user_engagement: ConversationStatsUserEngagement = Field(
        ..., description="User engagement statistics"
    )
    timestamp: str = Field(..., description="Statistics timestamp")
