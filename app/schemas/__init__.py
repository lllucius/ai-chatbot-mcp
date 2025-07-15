"""
Pydantic schemas for the AI Chatbot Platform.

This module provides request/response schemas for API endpoints,
data validation, and serialization.

Generated on: 2025-07-14 03:06:28 UTC
Current User: lllucius
"""

from .common import *
from .auth import *
from .user import *
from .document import *
from .conversation import *

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
    "UserProfile",
    "PasswordChangeRequest",
    
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
