"""
Schema imports from shared package.

This module re-exports schemas from the shared package to maintain
backwards compatibility with existing imports.
"""

# Re-export all schemas from shared package
from shared.schemas import *

# Re-export specific schemas that were previously defined locally
from shared.schemas import (
    # Auth schemas
    LoginRequest,
    RegisterRequest,
    Token,
    PasswordResetRequest,
    PasswordResetConfirm,
    
    # Base schemas
    BaseSchema,
    
    # Common schemas
    BaseResponse,
    PaginationParams,
    ConversationStatsResponse,
    RegistryStatsResponse,
    DatabaseHealthResponse,
    ServicesHealthResponse,
    SystemMetricsResponse,
    
    # Conversation schemas
    ConversationBase,
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    MessageBase,
    MessageCreate,
    MessageResponse,
    ChatRequest,
    ChatResponse,
    ConversationListResponse,
    MessageListResponse,
    ConversationStats,
    
    # Document schemas
    DocumentResponse,
    DocumentListResponse,
    DocumentSearchRequest,
    DocumentSearchResponse,
    
    # LLM Profile schemas
    LLMProfileResponse,
    LLMProfileCreate,
    LLMProfileListResponse,
    
    # MCP schemas
    MCPServerResponse,
    MCPServerCreate,
    MCPServerUpdate,
    MCPToolResponse,
    MCPToolExecutionRequest,
    MCPToolExecutionResult,
    MCPServerListResponse,
    MCPToolListResponse,
    
    # Prompt schemas
    PromptResponse,
    PromptCreate,
    PromptListResponse,
    
    # Search schemas
    SearchResponse,
    
    # Tool calling schemas
    ToolHandlingMode,
    ToolCallSummary,
    
    # User schemas
    UserBase,
    UserCreate,
    UserUpdate,
    UserPasswordUpdate,
    UserResponse,
    UserListResponse,
    UserDetailResponse,
    UserSearchParams,
    UserStatsResponse,
)

# Re-export schemas with different names that may be used in existing code
MCPServerSchema = MCPServerResponse
MCPServerCreateSchema = MCPServerCreate
MCPServerUpdateSchema = MCPServerUpdate
MCPToolSchema = MCPToolResponse
MCPToolExecutionRequestSchema = MCPToolExecutionRequest
MCPToolExecutionResultSchema = MCPToolExecutionResult

# Additional aliases for backwards compatibility
HealthResponse = BaseResponse
ErrorResponse = BaseResponse
PaginatedResponse = BaseResponse

__all__ = [
    # Base
    "BaseSchema",
    # Common
    "BaseResponse",
    "PaginationParams",
    "HealthResponse",
    "ErrorResponse", 
    "PaginatedResponse",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserPasswordUpdate",
    "UserResponse",
    "UserListResponse",
    "UserDetailResponse",
    "UserSearchParams",
    "UserStatsResponse",
    # Auth
    "LoginRequest",
    "RegisterRequest",
    "Token",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    # Conversation
    "ConversationBase",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "MessageBase",
    "MessageCreate",
    "MessageResponse",
    "ChatRequest",
    "ChatResponse",
    "ConversationListResponse",
    "MessageListResponse",
    "ConversationStats",
    # Document
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentSearchRequest",
    "DocumentSearchResponse",
    # LLM Profile
    "LLMProfileResponse",
    "LLMProfileCreate",
    "LLMProfileListResponse",
    # MCP
    "MCPServerSchema",
    "MCPServerCreateSchema",
    "MCPServerUpdateSchema",
    "MCPToolSchema",
    "MCPToolExecutionRequestSchema",
    "MCPToolExecutionResultSchema",
    "MCPServerListResponse",
    "MCPToolListResponse",
    "MCPServerResponse",
    "MCPServerCreate",
    "MCPServerUpdate",
    "MCPToolResponse",
    "MCPToolExecutionRequest",
    "MCPToolExecutionResult",
    # Prompt
    "PromptResponse",
    "PromptCreate",
    "PromptListResponse",
    # Search
    "SearchResponse",
    # Tool calling
    "ToolHandlingMode",
    "ToolCallSummary",
    # Health and status
    "DatabaseHealthResponse",
    "ServicesHealthResponse",
    "SystemMetricsResponse",
    "ConversationStatsResponse",
    "RegistryStatsResponse",
]
