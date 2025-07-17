"""
Custom exception classes for the AI Chatbot Platform.

This module defines application-specific exceptions with proper
error codes and details for better error handling and debugging.
"""

from typing import Any, Dict, Optional


class ChatbotPlatformException(Exception):
    """
    Base exception class for all application-specific exceptions.

    Provides structure for error codes, messages, and additional details.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "GENERAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize base exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ChatbotPlatformException):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class AuthenticationError(ChatbotPlatformException):
    """Raised when authentication fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class AuthorizationError(ChatbotPlatformException):
    """Raised when authorization fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHORIZATION_ERROR", details)


class NotFoundError(ChatbotPlatformException):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "NOT_FOUND_ERROR", details)


class DocumentError(ChatbotPlatformException):
    """Raised when document processing fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DOCUMENT_ERROR", details)


class EmbeddingError(ChatbotPlatformException):
    """Raised when embedding operations fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "EMBEDDING_ERROR", details)


class ExternalServiceError(ChatbotPlatformException):
    """Raised when external service calls fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)


class ConfigurationError(ChatbotPlatformException):
    """Raised when configuration is invalid."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFIGURATION_ERROR", details)


class RateLimitError(ChatbotPlatformException):
    """Raised when rate limits are exceeded."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "RATE_LIMIT_ERROR", details)


class SearchError(ChatbotPlatformException):
    """Raised when search operations fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "SEARCH_ERROR", details)
