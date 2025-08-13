"""Custom exception classes for the AI Chatbot Platform with comprehensive error handling.

This module defines application-specific exceptions with structured error codes,
detailed messages, and comprehensive error context for robust error handling,
debugging, and monitoring with consistent error reporting across all components.
"""

from typing import Any, Dict, Optional


class ChatbotPlatformException(Exception):
    """Base exception class for all application-specific exceptions with comprehensive error handling.

    Provides the foundational structure for all custom exceptions in the AI Chatbot Platform
    with standardized error codes, detailed messages, and additional context information
    for robust error management, debugging, and monitoring capabilities.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "GENERAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize base exception with comprehensive error information and context.

        Creates a structured exception with error code, message, and additional details
        for robust error handling, logging, and monitoring with consistent error
        structure across all application components.
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ChatbotPlatformException):
    """Exception raised when input validation fails with comprehensive validation context.

    Specialized exception for handling input validation errors including field validation,
    data integrity checks, business rule violations, and schema validation failures
    with detailed validation context for user feedback and debugging support.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize ValidationError with message and validation details."""
        super().__init__(message, "VALIDATION_ERROR", details)


class AuthenticationError(ChatbotPlatformException):
    """Exception raised when user authentication fails with comprehensive security context.

    Specialized exception for handling authentication failures including credential
    validation, token verification, multi-factor authentication, and session management
    errors with security-focused error reporting that doesn't expose sensitive information.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize AuthenticationError with message and authentication details."""
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class AuthorizationError(ChatbotPlatformException):
    """Exception raised when user authorization fails with comprehensive access control context.

    Specialized exception for handling authorization and access control failures including
    permission violations, role-based access control errors, resource ownership validation,
    and administrative privilege requirements with detailed access control context.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize AuthorizationError with message and authorization details."""
        super().__init__(message, "AUTHORIZATION_ERROR", details)


class NotFoundError(ChatbotPlatformException):
    """Exception raised when requested resources are not found with comprehensive resource context.

    Specialized exception for handling resource not found scenarios including entity lookup
    failures, missing files, unavailable services, and resource lifecycle management.
    Provides detailed resource context for debugging and user feedback.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize NotFoundError with message and resource details."""
        super().__init__(message, "NOT_FOUND_ERROR", details)


class DocumentError(ChatbotPlatformException):
    """Exception raised when document processing operations fail with comprehensive processing context.

    Specialized exception for handling document processing failures including file parsing,
    content extraction, format conversion, metadata processing, and storage operations.
    Provides detailed processing context for debugging and error recovery.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize DocumentError with message and document processing details."""
        super().__init__(message, "DOCUMENT_ERROR", details)


class EmbeddingError(ChatbotPlatformException):
    """Exception raised when vector embedding operations fail with comprehensive embedding context.

    Specialized exception for handling vector embedding and similarity search failures including
    text embedding generation, vector storage operations, similarity calculations, and index
    management. Provides detailed embedding context for debugging and performance optimization.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize EmbeddingError with message and embedding details."""
        super().__init__(message, "EMBEDDING_ERROR", details)


class ExternalServiceError(ChatbotPlatformException):
    """Exception raised when external service integration fails with comprehensive service context.

    Specialized exception for handling third-party service integration failures including
    API calls, service availability, authentication issues, rate limiting, and data format
    incompatibilities. Provides detailed service context for debugging and resilience planning.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize ExternalServiceError with message and service details."""
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)


class ConfigurationError(ChatbotPlatformException):
    """Exception raised when application configuration is invalid with comprehensive configuration context.

    Specialized exception for handling configuration errors including missing settings,
    invalid values, environment variable issues, and configuration file problems.
    Provides detailed configuration context for system administration and deployment.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize ConfigurationError with message and configuration details."""
        super().__init__(message, "CONFIGURATION_ERROR", details)


class RateLimitError(ChatbotPlatformException):
    """Exception raised when API rate limits are exceeded with comprehensive rate limiting context.

    Specialized exception for handling rate limiting scenarios including request throttling,
    quota exhaustion, user-specific limits, and service protection mechanisms. Provides
    detailed rate limiting context for client applications and monitoring systems.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize RateLimitError with message and rate limit details."""
        super().__init__(message, "RATE_LIMIT_ERROR", details)


class SearchError(ChatbotPlatformException):
    """Exception raised when search operations fail with comprehensive search context.

    Specialized exception for handling search functionality failures including query parsing,
    index operations, ranking algorithms, and result processing. Provides detailed search
    context for debugging and search experience optimization.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize SearchError with message and search details."""
        super().__init__(message, "SEARCH_ERROR", details)
