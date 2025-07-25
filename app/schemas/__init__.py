"""
Pydantic schemas for the AI Chatbot Platform.

This module provides request/response schemas for API endpoints,
data validation, and serialization.

"""

from .auth import LoginRequest, PasswordResetConfirm, PasswordResetRequest, RegisterRequest, Token
from .common import BaseResponse, ErrorResponse
from .common import HealthCheckResponse as HealthResponse
from .common import PaginatedResponse, PaginationParams, SearchParams
from .conversation import (ChatRequest, ChatResponse, ConversationCreate, ConversationListResponse,
                           ConversationResponse, ConversationStats, ConversationUpdate,
                           MessageCreate, MessageListResponse, MessageResponse)
from .document import (DocumentChunkResponse, DocumentResponse, DocumentSearchRequest,
                       DocumentUpdate, DocumentUploadResponse, ProcessingStatusResponse)
from .user import UserPasswordUpdate, UserResponse, UserStatsResponse, UserUpdate

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
