"""
Database models package.

This package contains all SQLAlchemy database models for the application.
Models are separated from Pydantic schemas to avoid conflicts.

Current Date and Time (UTC): 2025-07-14 05:03:11
Current User: lllucius
"""

# Import SQLAlchemy base classes only
from .base import BaseModelDB, TimestampMixin, UUIDMixin
from .conversation import Conversation, Message
from .document import Document, DocumentChunk

# Import database models (SQLAlchemy)
from .user import User

# Import new registry models
from .mcp_server import MCPServer
from .mcp_tool import MCPTool
from .prompt import Prompt
from .llm_profile import LLMProfile

__all__ = [
    # Base classes
    "BaseModelDB",
    "TimestampMixin",
    "UUIDMixin",
    # Models
    "User",
    "Document",
    "DocumentChunk",
    "Conversation",
    "Message",
    # Registry models
    "MCPServer",
    "MCPTool",
    "Prompt",
    "LLMProfile",
]
