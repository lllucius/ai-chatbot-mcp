"""
Pydantic schemas for the AI Chatbot Platform.

This module provides request/response schemas for API endpoints,
data validation, and serialization.

Generated on: 2025-07-14 03:06:28 UTC
Current User: lllucius
"""

from .auth import (
    LoginRequest,
    RegisterRequest,
    Token,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from .common import (
    BaseResponse,
    ErrorResponse,
    PaginationParams,
    PaginatedResponse,
    HealthCheckResponse as HealthResponse,
    SearchParams,
)
from .conversation import (
    ConversationResponse,
    ConversationCreate,
    ConversationUpdate,
    MessageResponse,
    MessageCreate,
    ChatRequest,
    ChatResponse,
    ConversationListResponse,
    MessageListResponse,
    ConversationStats,
)
from .document import (
    DocumentResponse,
    DocumentUpdate,
    DocumentChunkResponse,
    DocumentSearchRequest,
    DocumentUploadResponse,
    ProcessingStatusResponse,
)
from .user import (
    UserResponse,
    UserUpdate,
    UserPasswordUpdate,
    UserStatsResponse,
)

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
