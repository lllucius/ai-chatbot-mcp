"""API module for the AI Chatbot Platform."""

from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.conversations import router as conversations_router
from app.api.database import router as database_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.mcp import router as mcp_router
from app.api.profiles import router as profiles_router
from app.api.prompts import router as prompts_router
from app.api.search import router as search_router
from app.api.tasks import router as tasks_router
from app.api.users import router as users_router

__all__ = [
    "auth_router",
    "users_router",
    "documents_router",
    "conversations_router",
    "search_router",
    "health_router",
    "mcp_router",
    "prompts_router",
    "profiles_router",
    "analytics_router",
    "database_router",
    "tasks_router",
]
