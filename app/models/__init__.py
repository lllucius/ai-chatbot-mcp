"""Database models package for AI Chatbot Platform.

This package provides SQLAlchemy database models with BIGSERIAL primary keys,
timestamp tracking, and comprehensive relationships for the AI Chatbot Platform.

Core Models:
- User: User authentication and profile management
- Document: Document storage with chunking and embeddings
- Conversation: Chat session and message management
- MCPServer/MCPTool: Model Context Protocol integration
- LLMProfile: Language model configuration management
- Prompt: Prompt template management

All models inherit from BaseModelDB providing BIGSERIAL primary keys, automatic
timestamps, and consistent table naming conventions.
"""

# Import SQLAlchemy base classes only
from app.models.base import BaseModelDB, BigSerialMixin, TimestampMixin
from app.models.conversation import Conversation, Message
from app.models.document import Document, DocumentChunk

# Import new registry models
from app.models.job import Job
from app.models.mcp_server import MCPServer
from app.models.mcp_tool import MCPTool
from app.models.profile import LLMProfile
from app.models.prompt import Prompt

# Import database models (SQLAlchemy)
from app.models.user import User

__all__ = [
    # Base classes
    "BaseModelDB",
    "TimestampMixin",
    "BigSerialMixin",
    # Models
    "User",
    "Document",
    "DocumentChunk",
    "Conversation",
    "Message",
    # Registry models
    "Job",
    "MCPServer",
    "MCPTool",
    "Prompt",
    "LLMProfile",
]
