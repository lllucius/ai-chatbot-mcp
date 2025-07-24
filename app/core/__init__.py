"Core functionality package for the AI chatbot platform."

from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    ChatbotPlatformException,
    DocumentError,
    EmbeddingError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)
from .tool_executor import (
    ToolCall,
    ToolProvider,
    ToolResult,
    UnifiedToolExecutor,
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
