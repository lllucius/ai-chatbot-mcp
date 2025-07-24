"Utility functions for validation operations."

import logging
import re
from typing import Any, Dict, List
from fastapi import HTTPException, Request
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class InputValidator:
    "InputValidator class for specialized functionality."

    EMAIL_PATTERN = re.compile("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")
    USERNAME_PATTERN = re.compile("^[a-zA-Z0-9_]{3,50}$")
    FILENAME_PATTERN = re.compile("^[a-zA-Z0-9._-]+$")
    SQL_INJECTION_PATTERNS = [
        re.compile(
            "\\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\\b",
            re.IGNORECASE,
        ),
        re.compile("[\\'\";]"),
        re.compile("--"),
        re.compile("/\\*.*?\\*/", re.DOTALL),
    ]
    XSS_PATTERNS = [
        re.compile("<script[^>]*>.*?</script>", (re.IGNORECASE | re.DOTALL)),
        re.compile("javascript:", re.IGNORECASE),
        re.compile("on\\w+\\s*=", re.IGNORECASE),
        re.compile("<iframe[^>]*>", re.IGNORECASE),
    ]

    @classmethod
    def validate_email(cls, email: str) -> bool:
        "Validate email data."
        if (not email) or (len(email) > 254):
            return False
        return bool(cls.EMAIL_PATTERN.match(email))

    @classmethod
    def validate_username(cls, username: str) -> bool:
        "Validate username data."
        if not username:
            return False
        return bool(cls.USERNAME_PATTERN.match(username))

    @classmethod
    def validate_filename(cls, filename: str) -> bool:
        "Validate filename data."
        if (not filename) or (len(filename) > 255):
            return False
        return bool(cls.FILENAME_PATTERN.match(filename))

    @classmethod
    def sanitize_string(cls, text: str, max_length: int = 1000) -> str:
        "Sanitize String operation."
        if not text:
            return ""
        text = text[:max_length]
        text = re.sub("[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F\\x7F]", "", text)
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&#x27;")
        return text.strip()

    @classmethod
    def check_sql_injection(cls, text: str) -> bool:
        "Check Sql Injection operation."
        if not text:
            return False
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if pattern.search(text):
                return True
        return False

    @classmethod
    def check_xss(cls, text: str) -> bool:
        "Check Xss operation."
        if not text:
            return False
        for pattern in cls.XSS_PATTERNS:
            if pattern.search(text):
                return True
        return False

    @classmethod
    def validate_json_payload(
        cls, payload: Dict[(str, Any)], max_depth: int = 10
    ) -> bool:
        "Validate json payload data."

        def check_depth(obj, current_depth=0):
            "Check Depth operation."
            if current_depth > max_depth:
                return False
            if isinstance(obj, dict):
                return all((check_depth(v, (current_depth + 1)) for v in obj.values()))
            elif isinstance(obj, list):
                return all((check_depth(item, (current_depth + 1)) for item in obj))
            return True

        return check_depth(payload)


async def validate_request_middleware(request: Request, call_next):
    "Validate request middleware data."
    try:
        content_length = request.headers.get("content-length")
        if content_length and (int(content_length) > ((50 * 1024) * 1024)):
            raise HTTPException(status_code=413, detail="Request too large")
        user_agent = request.headers.get("user-agent", "")
        if (not user_agent) or (len(user_agent) > 500):
            logger.warning(f"Suspicious user agent: {user_agent[:100]}...")
        response = await call_next(request)
        return response
    except ValidationError as e:
        logger.warning(f"Request validation failed: {e}")
        raise HTTPException(status_code=422, detail="Invalid request format")
    except Exception as e:
        logger.error(f"Request validation middleware error: {e}")
        raise HTTPException(status_code=400, detail="Request validation failed")


def validate_search_query(query: str) -> str:
    "Validate search query data."
    if not query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    if len(query) > 1000:
        raise HTTPException(status_code=400, detail="Search query too long")
    if InputValidator.check_sql_injection(query):
        logger.warning(f"Potential SQL injection in search query: {query[:100]}")
        raise HTTPException(status_code=400, detail="Invalid search query")
    if InputValidator.check_xss(query):
        logger.warning(f"Potential XSS in search query: {query[:100]}")
        raise HTTPException(status_code=400, detail="Invalid search query")
    return InputValidator.sanitize_string(query)


def validate_file_upload(
    filename: str, content_type: str, allowed_types: List[str]
) -> None:
    "Validate file upload data."
    if not filename:
        raise HTTPException(status_code=400, detail="Filename cannot be empty")
    filename = InputValidator.sanitize_string(filename)
    if not InputValidator.validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename format")
    if "." not in filename:
        raise HTTPException(status_code=400, detail="File must have an extension")
    extension = filename.split(".")[(-1)].lower()
    if extension not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{extension}' not allowed. Allowed types: {', '.join(allowed_types)}",
        )
    expected_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
        "md": "text/markdown",
        "rtf": "application/rtf",
    }
    if (extension in expected_types) and (content_type != expected_types[extension]):
        logger.warning(
            f"MIME type mismatch for {filename}: expected {expected_types[extension]}, got {content_type}"
        )


def validate_message_content(content: str) -> str:
    "Validate message content data."
    if (not content) or (not content.strip()):
        raise HTTPException(status_code=400, detail="Message content cannot be empty")
    if len(content) > 10000:
        raise HTTPException(status_code=400, detail="Message too long")
    if InputValidator.check_xss(content):
        logger.warning("Potential XSS in message content")
        raise HTTPException(status_code=400, detail="Invalid message content")
    return InputValidator.sanitize_string(content, max_length=10000)
