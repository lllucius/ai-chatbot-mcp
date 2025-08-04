"""API module for the AI Chatbot Platform."""

from .analytics import router as analytics_router
from .auth import router as auth_router
from .conversations import router as conversations_router
from .database import router as database_router
from .documents import router as documents_router
from .health import router as health_router
from .mcp import router as mcp_router
from .profiles import router as profiles_router
from .prompts import router as prompts_router
from .search import router as search_router
from .tasks import router as tasks_router
from .users import router as users_router

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
