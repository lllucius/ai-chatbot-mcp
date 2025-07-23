"""
API module for the AI Chatbot Platform.

This module contains all FastAPI router definitions and endpoints
for the application's REST API, including new registry-based APIs.

Generated on: 2025-07-14 03:12:05 UTC
Updated on: 2025-07-23 04:30:00 UTC - Added registry APIs
Current User: lllucius
"""

from .auth import router as auth_router
from .conversations import router as conversations_router
from .documents import router as documents_router
from .health import router as health_router
from .profiles import router as profiles_router
from .prompts import router as prompts_router
from .search import router as search_router
from .tools import router as tools_router
from .users import router as users_router

__all__ = [
    "auth_router",
    "users_router",
    "documents_router",
    "conversations_router",
    "search_router",
    "health_router",
    "tools_router",
    "prompts_router",
    "profiles_router",
]
