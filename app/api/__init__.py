"""
API module for the AI Chatbot Platform.

This module contains all FastAPI router definitions and endpoints
for the application's REST API.

Generated on: 2025-07-14 03:12:05 UTC
Current User: lllucius
"""

from .auth import router as auth_router
from .users import router as users_router
from .documents import router as documents_router
from .conversations import router as conversations_router
from .search import router as search_router
from .health import router as health_router

__all__ = [
    "auth_router",
    "users_router", 
    "documents_router",
    "conversations_router",
    "search_router",
    "health_router",
]