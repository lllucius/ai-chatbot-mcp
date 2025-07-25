"""
Services package for business logic components.

This package provides services for authentication, user management,
document processing, search, conversations, and external integrations.

"""

from .auth import AuthService
from .conversation import ConversationService
from .document import DocumentService
from .embedding import EmbeddingService
from .llm_profile_service import LLMProfileService
from .mcp_client import (FastMCPClientService, cleanup_mcp_client,
                         get_mcp_client)
from .mcp_registry import MCPRegistryService
from .openai_client import OpenAIClient
from .prompt_service import PromptService
from .search import SearchService
from .user import UserService

__all__ = [
    "AuthService",
    "UserService",
    "DocumentService",
    "SearchService",
    "EmbeddingService",
    "ConversationService",
    "OpenAIClient",
    "FastMCPClientService",
    "get_mcp_client",
    "cleanup_mcp_client",
    "MCPRegistryService",
    "PromptService",
    "LLMProfileService",
]
