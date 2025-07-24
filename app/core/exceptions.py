"Core exceptions functionality and business logic."

from typing import Any, Dict, Optional


class ChatbotPlatformException(Exception):
    "Custom exception for error handling."

    def __init__(
        self,
        message: str,
        error_code: str = "GENERAL_ERROR",
        details: Optional[Dict[(str, Any)]] = None,
    ):
        "Initialize class instance."
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ChatbotPlatformException):
    "Custom exception for error handling."

    def __init__(self, message: str, details: Optional[Dict[(str, Any)]] = None):
        "Initialize class instance."
        super().__init__(message, "VALIDATION_ERROR", details)


class AuthenticationError(ChatbotPlatformException):
    "Custom exception for error handling."

    def __init__(self, message: str, details: Optional[Dict[(str, Any)]] = None):
        "Initialize class instance."
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class AuthorizationError(ChatbotPlatformException):
    "Custom exception for error handling."

    def __init__(self, message: str, details: Optional[Dict[(str, Any)]] = None):
        "Initialize class instance."
        super().__init__(message, "AUTHORIZATION_ERROR", details)


class NotFoundError(ChatbotPlatformException):
    "Custom exception for error handling."

    def __init__(self, message: str, details: Optional[Dict[(str, Any)]] = None):
        "Initialize class instance."
        super().__init__(message, "NOT_FOUND_ERROR", details)


class DocumentError(ChatbotPlatformException):
    "Custom exception for error handling."

    def __init__(self, message: str, details: Optional[Dict[(str, Any)]] = None):
        "Initialize class instance."
        super().__init__(message, "DOCUMENT_ERROR", details)


class EmbeddingError(ChatbotPlatformException):
    "Custom exception for error handling."

    def __init__(self, message: str, details: Optional[Dict[(str, Any)]] = None):
        "Initialize class instance."
        super().__init__(message, "EMBEDDING_ERROR", details)


class ExternalServiceError(ChatbotPlatformException):
    "Custom exception for error handling."

    def __init__(self, message: str, details: Optional[Dict[(str, Any)]] = None):
        "Initialize class instance."
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)


class ConfigurationError(ChatbotPlatformException):
    "Custom exception for error handling."

    def __init__(self, message: str, details: Optional[Dict[(str, Any)]] = None):
        "Initialize class instance."
        super().__init__(message, "CONFIGURATION_ERROR", details)


class RateLimitError(ChatbotPlatformException):
    "Custom exception for error handling."

    def __init__(self, message: str, details: Optional[Dict[(str, Any)]] = None):
        "Initialize class instance."
        super().__init__(message, "RATE_LIMIT_ERROR", details)


class SearchError(ChatbotPlatformException):
    "Custom exception for error handling."

    def __init__(self, message: str, details: Optional[Dict[(str, Any)]] = None):
        "Initialize class instance."
        super().__init__(message, "SEARCH_ERROR", details)
