"""
Pydantic schemas for the AI Chatbot Platform.

This module provides request/response schemas for API endpoints,
data validation, and serialization.

"""

from .auth import (LoginRequest, PasswordResetConfirm, PasswordResetRequest,
                   RegisterRequest, Token)
from .common import BaseResponse, ErrorResponse
from .common import HealthCheckResponse as HealthResponse
from .common import PaginatedResponse, PaginationParams, SearchParams
from .conversation import (ChatRequest, ChatResponse, ConversationCreate,
                           ConversationListResponse, ConversationResponse,
                           ConversationStats, ConversationUpdate,
                           MessageCreate, MessageListResponse, MessageResponse)
from .document import (DocumentChunkResponse, DocumentResponse,
                       DocumentSearchRequest, DocumentUpdate,
                       DocumentUploadResponse, ProcessingStatusResponse)
from .llm_profile import (LLMProfileCreate, LLMProfileListResponse,
                          LLMProfileResponse, LLMProfileUpdate)
from .mcp import (MCPBatchUsageSchema, MCPConnectionStatusSchema,
                  MCPDiscoveryRequestSchema, MCPDiscoveryResultSchema,
                  MCPHealthStatusSchema, MCPListFiltersSchema,
                  MCPOpenAIToolsResponseSchema, MCPServerCreateSchema,
                  MCPServerSchema, MCPServerUpdateSchema, MCPToolCreateSchema,
                  MCPToolExecutionRequestSchema, MCPToolExecutionResultSchema,
                  MCPToolSchema, MCPToolUpdateSchema, MCPToolUsageStatsSchema,
                  OpenAIToolSchema)
from .prompt import (PromptCreate, PromptListResponse, PromptResponse,
                     PromptUpdate)
from .user import (UserPasswordUpdate, UserResponse, UserStatsResponse,
                   UserUpdate)

__all__ = [
    # Common schemas
    "BaseResponse",
    "ErrorResponse",
    "PaginationParams",
    "PaginatedResponse",
    "HealthResponse",
    "SearchParams",
    # Auth schemas
    "LoginRequest",
    "RegisterRequest",
    "Token",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    # User schemas
    "UserResponse",
    "UserUpdate",
    "UserPasswordUpdate",
    "UserStatsResponse",
    # Document schemas
    "DocumentResponse",
    "DocumentUpdate",
    "DocumentChunkResponse",
    "DocumentSearchRequest",
    "DocumentUploadResponse",
    "ProcessingStatusResponse",
    # LLM Profile schemas
    "LLMProfileResponse",
    "LLMProfileCreate",
    "LLMProfileUpdate",
    "LLMProfileListResponse",
    # MCP schemas
    "MCPServerCreateSchema",
    "MCPServerUpdateSchema", 
    "MCPServerSchema",
    "MCPToolCreateSchema",
    "MCPToolUpdateSchema",
    "MCPToolSchema",
    "MCPToolExecutionRequestSchema",
    "MCPToolExecutionResultSchema",
    "MCPToolUsageStatsSchema",
    "MCPDiscoveryRequestSchema",
    "MCPDiscoveryResultSchema",
    "MCPHealthStatusSchema",
    "MCPConnectionStatusSchema",
    "MCPBatchUsageSchema",
    "MCPListFiltersSchema",
    "OpenAIToolSchema",
    "MCPOpenAIToolsResponseSchema",
    # Prompt schemas
    "PromptResponse",
    "PromptCreate",
    "PromptUpdate",
    "PromptListResponse",
    # Conversation schemas
    "ConversationResponse",
    "ConversationCreate",
    "ConversationUpdate",
    "MessageResponse",
    "MessageCreate",
    "ChatRequest",
    "ChatResponse",
    "ConversationListResponse",
    "MessageListResponse",
    "ConversationStats",
]
