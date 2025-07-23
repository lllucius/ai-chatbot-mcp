"""
Input validation and sanitization utilities for enhanced security.

This module provides middleware and utilities for validating and sanitizing
input data to prevent common security vulnerabilities.
"""

import logging
import re
from typing import Any, Dict, List

from fastapi import HTTPException, Request
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class InputValidator:
    """
    Input validation and sanitization utilities.
    """

    # Common validation patterns
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,50}$")
    FILENAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")

    # Dangerous patterns to block
    SQL_INJECTION_PATTERNS = [
        re.compile(
            r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b",
            re.IGNORECASE,
        ),
        re.compile(r'[\'";]'),
        re.compile(r"--"),
        re.compile(r"/\*.*?\*/", re.DOTALL),
    ]

    XSS_PATTERNS = [
        re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),
        re.compile(r"<iframe[^>]*>", re.IGNORECASE),
    ]

    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Validate email format."""
        if not email or len(email) > 254:
            return False
        return bool(cls.EMAIL_PATTERN.match(email))

    @classmethod
    def validate_username(cls, username: str) -> bool:
        """Validate username format."""
        if not username:
            return False
        return bool(cls.USERNAME_PATTERN.match(username))

    @classmethod
    def validate_filename(cls, filename: str) -> bool:
        """Validate filename for upload safety."""
        if not filename or len(filename) > 255:
            return False
        return bool(cls.FILENAME_PATTERN.match(filename))

    @classmethod
    def sanitize_string(cls, text: str, max_length: int = 1000) -> str:
        """
        Sanitize string input to prevent XSS and other attacks.

        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length

        Returns:
            str: Sanitized text
        """
        if not text:
            return ""

        # Truncate if too long
        text = text[:max_length]

        # Remove null bytes and control characters
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

        # Basic HTML entity encoding for dangerous characters
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&#x27;")

        return text.strip()

    @classmethod
    def check_sql_injection(cls, text: str) -> bool:
        """
        Check for potential SQL injection patterns.

        Args:
            text: Text to check

        Returns:
            bool: True if potential SQL injection detected
        """
        if not text:
            return False

        for pattern in cls.SQL_INJECTION_PATTERNS:
            if pattern.search(text):
                return True
        return False

    @classmethod
    def check_xss(cls, text: str) -> bool:
        """
        Check for potential XSS patterns.

        Args:
            text: Text to check

        Returns:
            bool: True if potential XSS detected
        """
        if not text:
            return False

        for pattern in cls.XSS_PATTERNS:
            if pattern.search(text):
                return True
        return False

    @classmethod
    def validate_json_payload(
        cls, payload: Dict[str, Any], max_depth: int = 10
    ) -> bool:
        """
        Validate JSON payload structure and depth.

        Args:
            payload: JSON payload to validate
            max_depth: Maximum nesting depth allowed

        Returns:
            bool: True if valid
        """

        def check_depth(obj, current_depth=0):
            """
            Recursively check the nesting depth of an object.

            Args:
                obj: Object to check (dict, list, or primitive)
                current_depth: Current nesting level (default: 0)

            Returns:
                bool: True if depth is within limits, False otherwise
            """
            if current_depth > max_depth:
                return False

            if isinstance(obj, dict):
                return all(check_depth(v, current_depth + 1) for v in obj.values())
            elif isinstance(obj, list):
                return all(check_depth(item, current_depth + 1) for item in obj)
            return True

        return check_depth(payload)


async def validate_request_middleware(request: Request, call_next):
    """
    Middleware to validate incoming requests for security issues.
    """
    try:
        # Check request size (basic DoS protection)
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(status_code=413, detail="Request too large")

        # Check for suspicious user agents (basic bot protection)
        user_agent = request.headers.get("user-agent", "")
        if not user_agent or len(user_agent) > 500:
            logger.warning(f"Suspicious user agent: {user_agent[:100]}...")

        # Process request normally
        response = await call_next(request)
        return response

    except ValidationError as e:
        logger.warning(f"Request validation failed: {e}")
        raise HTTPException(status_code=422, detail="Invalid request format")
    except Exception as e:
        logger.error(f"Request validation middleware error: {e}")
        raise HTTPException(status_code=400, detail="Request validation failed")


def validate_search_query(query: str) -> str:
    """
    Validate and sanitize search queries.

    Args:
        query: Search query string

    Returns:
        str: Sanitized query

    Raises:
        HTTPException: If query contains dangerous patterns
    """
    if not query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    if len(query) > 1000:
        raise HTTPException(status_code=400, detail="Search query too long")

    # Check for SQL injection
    if InputValidator.check_sql_injection(query):
        logger.warning(f"Potential SQL injection in search query: {query[:100]}")
        raise HTTPException(status_code=400, detail="Invalid search query")

    # Check for XSS
    if InputValidator.check_xss(query):
        logger.warning(f"Potential XSS in search query: {query[:100]}")
        raise HTTPException(status_code=400, detail="Invalid search query")

    return InputValidator.sanitize_string(query)


def validate_file_upload(
    filename: str, content_type: str, allowed_types: List[str]
) -> None:
    """
    Validate file upload parameters.

    Args:
        filename: Name of uploaded file
        content_type: MIME type of file
        allowed_types: List of allowed file extensions

    Raises:
        HTTPException: If file validation fails
    """
    if not filename:
        raise HTTPException(status_code=400, detail="Filename cannot be empty")

    # Sanitize filename
    filename = InputValidator.sanitize_string(filename)

    if not InputValidator.validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename format")

    # Check file extension
    if "." not in filename:
        raise HTTPException(status_code=400, detail="File must have an extension")

    extension = filename.split(".")[-1].lower()
    if extension not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{extension}' not allowed. Allowed types: {', '.join(allowed_types)}",
        )

    # Basic MIME type validation
    expected_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
        "md": "text/markdown",
        "rtf": "application/rtf",
    }

    if extension in expected_types and content_type != expected_types[extension]:
        logger.warning(
            f"MIME type mismatch for {filename}: expected {expected_types[extension]}, got {content_type}"
        )


def validate_message_content(content: str) -> str:
    """
    Validate and sanitize message content for chat.

    Args:
        content: Message content

    Returns:
        str: Sanitized content

    Raises:
        HTTPException: If content is invalid
    """
    if not content or not content.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty")

    if len(content) > 10000:  # 10KB limit
        raise HTTPException(status_code=400, detail="Message too long")

    # Check for dangerous patterns
    if InputValidator.check_xss(content):
        logger.warning("Potential XSS in message content")
        raise HTTPException(status_code=400, detail="Invalid message content")

    return InputValidator.sanitize_string(content, max_length=10000)
