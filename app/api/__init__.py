"""API module for the AI Chatbot Platform."""

from app.api.ab_testing import router as ab_testing_router
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.conversations import router as conversations_router
from app.api.data_management import router as data_management_router
from app.api.database import router as database_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.mcp import router as mcp_router
from app.api.profiles import router as profiles_router
from app.api.prompts import router as prompts_router
from app.api.search import router as search_router
from app.api.tasks import router as tasks_router
from app.api.toolserver import router as toolserver_router
from app.api.users import router as users_router

__all__ = [
    "ab_testing_router",
    "analytics_router",
    "auth_router",
    "conversations_router",
    "data_management_router",
    "database_router",
    "documents_router",
    "health_router",
    "mcp_router",
    "profiles_router",
    "prompts_router",
    "search_router",
    "tasks_router",
    "toolserver_router",
    "users_router",
]
