"""
Conversation and message-related Pydantic schemas.

This module provides schemas for chat conversations, messages,
and related operations.

Generated on: 2025-07-14 03:47:30 UTC
Current User: lllucius
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from .common import BaseResponse, PaginatedResponse


class ConversationBase(BaseModel):
    """Base conversation schema with common fields."""
    
    title: str = Field(..., min_length=1, max_length=500, description="Conversation title")
    is_active: bool = Field(True, description="Whether conversation is active")


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""
    
    metainfo: Optional[Dict[str, Any]] = Field(None, description="Additional metainfo")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "AI Discussion",
                "is_active": True,
                "metainfo": {"category": "technical", "priority": "normal"}
            }
        }
    }


class ConversationUpdate(BaseModel):
    """Schema for updating conversation information."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="New title")
    is_active: Optional[bool] = Field(None, description="New active status")
    metainfo: Optional[Dict[str, Any]] = Field(None, description="Updated metainfo")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Updated AI Discussion",
                "is_active": True,
                "metainfo": {"category": "research"}
            }
        }
    }


class ConversationResponse(ConversationBase):
    """Schema for conversation response data."""
    
    id: int = Field(..., description="Conversation ID")
    user_id: int = Field(..., description="Owner user ID")
    message_count: int = Field(0, description="Number of messages")
    last_message_at: Optional[datetime] = Field(None, description="Last message timestamp")
    metainfo: Optional[Dict[str, Any]] = Field(None, description="Additional metainfo")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        },
        "json_schema_extra": {
            "example": {
                "id": 1,
                "title": "AI Discussion",
                "is_active": True,
                "user_id": 1,
                "message_count": 5,
                "last_message_at": "2025-07-14T03:47:30Z",
                "metainfo": {"category": "technical"},
                "created_at": "2025-07-14T03:47:30Z",
                "updated_at": "2025-07-14T03:47:30Z"
            }
        }
    }


class MessageBase(BaseModel):
    """Base message schema with common fields."""
    
    role: str = Field(..., pattern="^(user|assistant|system)$", description="Message role")
    content: str = Field(..., min_length=1, description="Message content")


class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    
    conversation_id: int = Field(..., description="Parent conversation ID")
    token_count: int = Field(0, ge=0, description="Number of tokens")
    tool_calls: Optional[Dict[str, Any]] = Field(None, description="Tool calls made")
    tool_call_results: Optional[Dict[str, Any]] = Field(None, description="Tool call results")
    metainfo: Optional[Dict[str, Any]] = Field(None, description="Additional metainfo")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "role": "user",
                "content": "What is machine learning?",
                "conversation_id": 1,
                "token_count": 5,
                "metainfo": {"source": "web_ui"}
            }
        }
    }


class MessageResponse(MessageBase):
    """Schema for message response data."""
    
    id: int = Field(..., description="Message ID")
    conversation_id: int = Field(..., description="Parent conversation ID")
    token_count: int = Field(0, description="Number of tokens")
    tool_calls: Optional[Dict[str, Any]] = Field(None, description="Tool calls made")
    tool_call_results: Optional[Dict[str, Any]] = Field(None, description="Tool call results")
    metainfo: Optional[Dict[str, Any]] = Field(None, description="Additional metainfo")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        },
        "json_schema_extra": {
            "example": {
                "id": 1,
                "role": "assistant",
                "content": "Machine learning is a subset of artificial intelligence...",
                "conversation_id": 1,
                "token_count": 150,
                "tool_calls": None,
                "tool_call_results": None,
                "metainfo": {"model": "gpt-4"},
                "created_at": "2025-07-14T03:47:30Z"
            }
        }
    }


class ChatRequest(BaseModel):
    """Schema for chat request."""
    
    user_message: str = Field(..., min_length=1, max_length=10000, description="User message")
    conversation_id: Optional[int] = Field(None, description="Existing conversation ID")
    conversation_title: Optional[str] = Field(None, max_length=500, description="New conversation title")
    use_rag: bool = Field(True, description="Whether to use RAG for context")
    use_tools: bool = Field(True, description="Whether to enable tool calling")
    rag_documents: Optional[List[int]] = Field(None, description="Specific document IDs for RAG")
    max_tokens: Optional[int] = Field(None, ge=1, le=4000, description="Maximum response tokens")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Response temperature")
    
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
                "rag_documents": [1, 2],
                "max_tokens": 1000,
                "temperature": 0.7
            }
        }
    }


class ChatResponse(BaseResponse):
    """Schema for chat response."""
    
    ai_message: MessageResponse = Field(..., description="AI response message")
    conversation: ConversationResponse = Field(..., description="Updated conversation")
    usage: Optional[Dict[str, Any]] = Field(None, description="Token usage information")
    rag_context: Optional[List[Dict[str, Any]]] = Field(None, description="RAG context used")
    tool_calls_made: Optional[List[Dict[str, Any]]] = Field(None, description="Tool calls executed")
    response_time_ms: float = Field(0.0, description="Response time in milliseconds")


class ConversationListResponse(BaseResponse):
    """Response schema for conversation list."""
    
    conversations: List[ConversationResponse] = Field([], description="List of conversations")
    total: int = Field(0, description="Total number of conversations")


class MessageListResponse(BaseResponse):
    """Response schema for message list."""
    
    messages: List[MessageResponse] = Field([], description="List of messages")
    conversation: ConversationResponse = Field(..., description="Parent conversation")
    total: int = Field(0, description="Total number of messages")


class ConversationStats(BaseModel):
    """Schema for conversation statistics."""
    
    total_conversations: int = Field(0, description="Total conversations")
    active_conversations: int = Field(0, description="Active conversations")
    total_messages: int = Field(0, description="Total messages")
    avg_messages_per_conversation: float = Field(0.0, description="Average messages per conversation")
    most_recent_activity: Optional[datetime] = Field(None, description="Most recent activity")
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }