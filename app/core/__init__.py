"""
Core modules for the AI Chatbot Platform.

This package provides core functionality including exception handling,
tool execution, and other foundational components.
"""

from .exceptions import *
from .tool_executor import (
    UnifiedToolExecutor,
    ToolCall,
    ToolResult,
    ToolProvider,
    get_unified_tool_executor,
)

__all__ = [
    "ChatbotPlatformException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "DocumentError",
    "EmbeddingError",
    "ExternalServiceError",
    "UnifiedToolExecutor",
    "ToolCall",
    "ToolResult",
    "ToolProvider",
    "get_unified_tool_executor",
]
