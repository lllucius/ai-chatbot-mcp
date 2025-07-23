"""
Conversation and message-related Pydantic schemas.

This module provides schemas for chat conversations, messages,
and related operations.

Generated on: 2025-07-20 13:48:01 UTC
Current User: lllucius
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, constr, field_validator

from .base import BaseSchema
from .common import BaseResponse
from .tool_calling import ToolCallSummary, ToolHandlingMode


class ConversationBase(BaseSchema):
    """Base conversation schema with common fields."""

    title: constr(min_length=1, max_length=500) = Field(
        ..., description="Conversation title"
    )
    is_active: bool = Field(True, description="Whether conversation is active")


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""

    metainfo: Optional[Dict[str, Any]] = Field(None, description="Additional metainfo")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "AI Discussion",
                "is_active": True,
                "metainfo": {"category": "technical", "priority": "normal"},
            }
        }
    }


class ConversationUpdate(BaseSchema):
    """Schema for updating conversation information."""

    title: Optional[constr(min_length=1, max_length=500)] = Field(
        None, description="New title"
    )
    is_active: Optional[bool] = Field(None, description="New active status")
    metainfo: Optional[Dict[str, Any]] = Field(None, description="Updated metainfo")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Updated AI Discussion",
                "is_active": True,
                "metainfo": {"category": "research"},
            }
        }
    }


class ConversationResponse(ConversationBase):
    """Schema for conversation response data."""

    id: UUID = Field(..., description="Conversation ID")
    user_id: UUID = Field(..., description="Owner user ID")
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
        "json_schema_extra": {
            "example": {
                "id": "4b40c3d9-208c-49ed-bd96-31c0b971e318",
                "title": "AI Discussion",
                "is_active": True,
                "user_id": "4b40c3d9-208c-49ed-bd96-31c0b971e318",
                "message_count": 5,
                "last_message_at": "2025-07-14T03:47:30Z",
                "metainfo": {"category": "technical"},
                "created_at": "2025-07-14T03:47:30Z",
                "updated_at": "2025-07-14T03:47:30Z",
            }
        },
    }


class MessageBase(BaseSchema):
    """Base message schema with common fields."""

    role: constr(pattern="^(user|assistant|system)$") = Field(
        ..., description="Message role"
    )
    content: constr(min_length=1, max_length=10000) = Field(
        ..., description="Message content"
    )


class MessageCreate(MessageBase):
    """Schema for creating a new message."""

    conversation_id: UUID = Field(..., description="Parent conversation ID")
    token_count: int = Field(0, ge=0, description="Number of tokens")
    tool_calls: Optional[Dict[str, Any]] = Field(None, description="Tool calls made")
    tool_call_results: Optional[Dict[str, Any]] = Field(
        None, description="Tool call results"
    )
    metainfo: Optional[Dict[str, Any]] = Field(None, description="Additional metainfo")

    model_config = {
        "json_schema_extra": {
            "example": {
                "role": "user",
                "content": "What is machine learning?",
                "conversation_id": "4b40c3d9-208c-49ed-bd96-31c0b971e318",
                "token_count": 5,
                "metainfo": {"source": "web_ui"},
            }
        }
    }


class MessageResponse(MessageBase):
    """Schema for message response data."""

    id: UUID = Field(..., description="Message ID")
    conversation_id: UUID = Field(..., description="Parent conversation ID")
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
        "json_schema_extra": {
            "example": {
                "id": "4b40c3d9-208c-49ed-bd96-31c0b971e318",
                "role": "assistant",
                "content": "Machine learning is a subset of artificial intelligence...",
                "conversation_id": "4b40c3d9-208c-49ed-bd96-31c0b971e318",
                "token_count": 150,
                "tool_calls": None,
                "tool_call_results": None,
                "metainfo": {"model": "gpt-4"},
                "created_at": "2025-07-14T03:47:30Z",
            }
        },
    }


class ChatRequest(BaseSchema):
    """Schema for chat request with enhanced registry integration."""

    user_message: constr(min_length=1, max_length=10000) = Field(
        ..., description="User message"
    )
    conversation_id: Optional[UUID] = Field(
        None, description="Existing conversation ID"
    )
    conversation_title: Optional[constr(max_length=500)] = Field(
        None, description="New conversation title"
    )
    use_rag: bool = Field(True, description="Whether to use RAG for context")
    use_tools: bool = Field(True, description="Whether to enable tool calling")
    tool_handling_mode: ToolHandlingMode = Field(
        default=ToolHandlingMode.COMPLETE_WITH_RESULTS,
        description="How to handle tool call results: return_results or complete_with_results",
    )
    rag_documents: Optional[List[UUID]] = Field(
        None, description="Specific document IDs for RAG"
    )
    max_tokens: Optional[int] = Field(
        None, ge=1, le=4000, description="Maximum response tokens"
    )
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Response temperature")

    # Registry integration fields
    prompt_name: Optional[str] = Field(
        None, description="Name of prompt to use from prompt registry"
    )
    profile_name: Optional[str] = Field(
        None, description="Name of LLM profile to use from profile registry"
    )

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v):
        """Validate temperature is within acceptable range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_message": "What is machine learning?",
                "conversation_id": None,
                "conversation_title": "ML Discussion",
                "use_rag": True,
                "use_tools": True,
                "tool_handling_mode": "complete_with_results",
                "rag_documents": [
                    "4b40c3d9-208c-49ed-bd96-31c0b971e318",
                    "5c50a4ea-1111-49ed-bd96-31c0b971e319",
                ],
                "max_tokens": 1000,
                "temperature": 0.7,
                "prompt_name": "technical_assistant",
                "profile_name": "balanced",
            }
        }
    }


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
        [], description="List of conversations"
    )
    total: int = Field(0, description="Total number of conversations")


class MessageListResponse(BaseResponse):
    """Response schema for message list."""

    messages: List[MessageResponse] = Field([], description="List of messages")
    conversation: ConversationResponse = Field(..., description="Parent conversation")
    total: int = Field(0, description="Total number of messages")


class ConversationStats(BaseSchema):
    """Schema for conversation statistics."""

    total_conversations: int = Field(0, description="Total conversations")
    active_conversations: int = Field(0, description="Active conversations")
    total_messages: int = Field(0, description="Total messages")
    avg_messages_per_conversation: float = Field(
        0.0, description="Average messages per conversation"
    )
    most_recent_activity: Optional[datetime] = Field(
        None, description="Most recent activity"
    )

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}
