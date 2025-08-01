"""
Core modules for the AI Chatbot Platform.

This package provides core functionality including exception handling,
tool execution, and other foundational components.
"""

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
from .logging import StructuredLogger, get_logger, setup_logging

__all__ = [
    "ChatbotPlatformException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "DocumentError",
    "EmbeddingError",
    "ExternalServiceError",
    "setup_logging",
    "get_logger",
    "StructuredLogger",
]
