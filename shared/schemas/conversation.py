"""Conversation and message-related Pydantic schemas.

This module provides schemas for chat conversations, messages,
and related operations.
All fields include a 'description' argument.
"""

from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .base import BaseSchema
from .common import BaseResponse
from .tool_calling import ToolCallSummary, ToolHandlingMode


class ConversationBase(BaseSchema):
    """Base conversation schema with common fields."""

    title: Annotated[str, Field(min_length=1, max_length=500)] = Field(
        ..., description="Conversation title"
    )
    is_active: bool = Field(True, description="Whether conversation is active")


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""

    metainfo: Optional[Dict[str, Any]] = Field(None, description="Additional metainfo")


class ConversationUpdate(BaseSchema):
    """Schema for updating conversation information."""

    title: Optional[Annotated[str, Field(min_length=1, max_length=500)]] = Field(
        None, description="New title"
    )
    is_active: Optional[bool] = Field(None, description="New active status")
    metainfo: Optional[Dict[str, Any]] = Field(None, description="Updated metainfo")


class ConversationResponse(ConversationBase):
    """Schema for conversation response data."""

    id: int = Field(..., description="Conversation ID")
    user_id: int = Field(..., description="Owner user ID")
    message_count: int = Field(0, description="Number of messages")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_message_at: Optional[datetime] = Field(
        None, description="Last message timestamp"
    )
    metainfo: Optional[Dict[str, Any]] = Field(None, description="Additional metainfo")

    model_config = {
        "from_attributes": True,
        "json_encoders": {datetime: lambda v: v.isoformat()},
    }


class MessageBase(BaseSchema):
    """Base message schema with common fields."""

    role: Annotated[str, Field(pattern="^(user|assistant|system)$")] = Field(
        ..., description="Message role"
    )
    content: Annotated[str, Field(min_length=1, max_length=10000)] = Field(
        ..., description="Message content"
    )


class MessageCreate(MessageBase):
    """Schema for creating a new message."""

    conversation_id: int = Field(..., description="Parent conversation ID")
    token_count: int = Field(0, ge=0, description="Number of tokens")
    tool_calls: Optional[Dict[str, Any]] = Field(None, description="Tool calls made")
    tool_call_results: Optional[Dict[str, Any]] = Field(
        None, description="Tool call results"
    )
    metainfo: Optional[Dict[str, Any]] = Field(None, description="Additional metainfo")


class MessageResponse(MessageBase):
    """Schema for message response data."""

    id: int = Field(..., description="Message ID")
    conversation_id: int = Field(..., description="Parent conversation ID")
    token_count: int = Field(0, description="Number of tokens")
    tool_calls: Optional[Dict[str, Any]] = Field(None, description="Tool calls made")
    tool_call_results: Optional[Dict[str, Any]] = Field(
        None, description="Tool call results"
    )
    metainfo: Optional[Dict[str, Any]] = Field(None, description="Additional metainfo")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = {
        "from_attributes": True,
        "json_encoders": {datetime: lambda v: v.isoformat()},
    }


class ChatRequest(BaseSchema):
    """Schema for chat request with enhanced registry integration."""

    user_message: Annotated[str, Field(min_length=1, max_length=10000)] = Field(
        ..., description="User message"
    )
    conversation_id: Optional[int] = Field(
        None, description="Existing conversation ID"
    )
    conversation_title: Optional[Annotated[str, Field(max_length=500)]] = Field(
        None, description="New conversation title"
    )
    use_rag: bool = Field(True, description="Whether to use RAG for context")
    use_tools: bool = Field(True, description="Whether to enable tool calling")
    tool_handling_mode: ToolHandlingMode = Field(
        default=ToolHandlingMode.COMPLETE_WITH_RESULTS,
        description="How to handle tool call results: return_results or complete_with_results",
    )
    rag_documents: Optional[List[int]] = Field(
        None, description="Specific document IDs for RAG"
    )
    prompt_name: Optional[str] = Field(
        None, description="Name of prompt to use from prompt registry"
    )
    profile_name: Optional[str] = Field(
        None, description="Name of LLM profile to use from profile registry"
    )
    llm_profile: Optional[Dict[str, Any]] = Field(
        None, description="LLM profile object with parameter configuration"
    )


class ChatResponse(BaseResponse):
    """Schema for chat response."""

    ai_message: MessageResponse = Field(..., description="AI response message")
    conversation: ConversationResponse = Field(..., description="Updated conversation")
    usage: Optional[Dict[str, Any]] = Field(None, description="Token usage information")
    rag_context: Optional[List[Dict[str, Any]]] = Field(
        None, description="RAG context used"
    )
    tool_calls_made: Optional[List[Dict[str, Any]]] = Field(
        None, description="Tool calls executed (deprecated - use tool_call_summary)"
    )
    tool_call_summary: Optional[ToolCallSummary] = Field(
        None, description="Detailed summary of tool calls executed"
    )
    response_time_ms: float = Field(0.0, description="Response time in milliseconds")


class ConversationListResponse(BaseResponse):
    """Response schema for conversation list."""

    conversations: List[ConversationResponse] = Field(
        ..., description="List of conversations"
    )
    total: int = Field(..., description="Total number of conversations")


class MessageListResponse(BaseResponse):
    """Response schema for message list."""

    messages: List[MessageResponse] = Field(..., description="List of messages")
    conversation: ConversationResponse = Field(..., description="Parent conversation")
    total: int = Field(..., description="Total number of messages")


class ConversationStats(BaseSchema):
    """Schema for conversation statistics."""

    total_conversations: int = Field(..., description="Total conversations")
    active_conversations: int = Field(..., description="Active conversations")
    total_messages: int = Field(..., description="Total messages")
    avg_messages_per_conversation: float = Field(
        ..., description="Average messages per conversation"
    )
    most_recent_activity: Optional[datetime] = Field(
        None, description="Most recent activity"
    )

    model_config = {
        "json_encoders": {datetime: lambda v: v.isoformat()}
    }


class StreamStartResponse(BaseSchema):
    """Schema for stream start event."""

    type: str = Field("start", description="Event type")
    message: str = Field(..., description="Start message")


class StreamContentResponse(BaseSchema):
    """Schema for stream content event."""

    type: str = Field("content", description="Event type")
    content: str = Field(..., description="Content chunk")


class StreamToolCallResponse(BaseSchema):
    """Schema for stream tool call event."""

    type: str = Field("tool_call", description="Event type")
    tool: Optional[Dict[str, Any]] = Field(None, description="Tool information")
    result: Optional[Dict[str, Any]] = Field(None, description="Tool result")


class StreamCompleteResponse(BaseSchema):
    """Schema for stream complete event."""

    type: str = Field("complete", description="Event type")
    response: Dict[str, Any] = Field(..., description="Complete response data")


class StreamEndResponse(BaseSchema):
    """Schema for stream end event."""

    type: str = Field("end", description="Event type")


class StreamErrorResponse(BaseSchema):
    """Schema for stream error event."""

    type: str = Field("error", description="Event type")
    error: str = Field(..., description="Error message")


class ConversationExportInfoResponse(BaseSchema):
    """Schema for conversation export metadata."""

    format: str = Field(..., description="Export format used")
    exported_at: str = Field(..., description="Export timestamp")
    message_count: int = Field(..., description="Number of messages exported")
    includes_metadata: bool = Field(..., description="Whether metadata was included")


class ConversationExportDataResponse(BaseSchema):
    """Schema for conversation export data."""

    content: str = Field(..., description="Exported content")
    format: str = Field(..., description="Content format")


class ConversationExportResponse(BaseResponse):
    """Schema for conversation export response."""

    data: ConversationExportDataResponse = Field(..., description="Export data")
    export_info: ConversationExportInfoResponse = Field(
        ..., description="Export metadata"
    )

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
