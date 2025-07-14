"""
Core modules for the AI Chatbot Platform.

This package provides core functionality including exception handling,
security utilities, and other foundational components.
"""

from .exceptions import *

__all__ = [
    "ChatbotPlatformException",
    "ValidationError",
    "AuthenticationError", 
    "AuthorizationError",
    "NotFoundError",
    "DocumentError",
    "EmbeddingError",
    "ExternalServiceError",
]