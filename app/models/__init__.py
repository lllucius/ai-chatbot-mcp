"""
Database models package.

This package contains all SQLAlchemy database models for the application.
Models are separated from Pydantic schemas to avoid conflicts.

"""

# Import SQLAlchemy base classes only
from .base import BaseModelDB, TimestampMixin, UUIDMixin
from .conversation import Conversation, Message
from .document import Document, DocumentChunk
from .llm_profile import LLMProfile
# Import new registry models
from .mcp_server import MCPServer
from .mcp_tool import MCPTool
from .prompt import Prompt
# Import database models (SQLAlchemy)
from .user import User

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
