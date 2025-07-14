"""
Database models package.

This package contains all SQLAlchemy database models for the application.
Models are separated from Pydantic schemas to avoid conflicts.

Current Date and Time (UTC): 2025-07-14 05:03:11
Current User: lllucius
"""

# Import SQLAlchemy base classes only
from .base import Base, TimestampMixin, SoftDeleteMixin, UUIDMixin

# Import database models (SQLAlchemy)
from .user import User
from .document import Document, DocumentChunk
from .conversation import Conversation, Message
from .search import SearchQuery, SearchResult

__all__ = [
    # Base classes
    "Base",
    "TimestampMixin", 
    "SoftDeleteMixin",
    "UUIDMixin",
    # Models
    "User",
    "Document",
    "DocumentChunk", 
    "Conversation",
    "Message",
    "SearchQuery",
    "SearchResult"
]