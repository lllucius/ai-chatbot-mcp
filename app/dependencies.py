"""FastAPI dependencies for authentication, authorization, and service injection.

This module provides comprehensive reusable dependencies for FastAPI endpoints
including user authentication, authorization checks, service injection, and
common utilities. Implements enterprise-grade dependency injection patterns
with proper security controls, validation, and integration with the application's
service architecture for scalable and maintainable API development.
"""

from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.database import get_db
from app.models.user import User
from app.services.auth import AuthService
from app.services.conversation import ConversationService
from app.services.document import DocumentService
from app.services.embedding import EmbeddingService
from app.services.mcp_service import MCPService
from app.services.profile_service import LLMProfileService
from app.services.prompt_service import PromptService
from app.services.search import SearchService
from app.services.user import UserService

# Security scheme for JWT tokens
security = HTTPBearer()


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None

    try:
        auth_service = AuthService(db)
        username = auth_service.verify_token(credentials.credentials)

        if not username:
            return None

        user = await auth_service.get_user_by_username(username)
        if not user or not user.is_active:
            return None

        return user

    except Exception:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user."""
    try:
        auth_service = AuthService(db)
        username = auth_service.verify_token(credentials.credentials)

        if not username:
            raise AuthenticationError("Invalid or expired token")

        user = await auth_service.get_user_by_username(username)
        if not user:
            raise AuthenticationError("User not found")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        return user

    except AuthenticationError:
        raise
    except Exception:
        raise AuthenticationError("Authentication failed")


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Get current user and verify superuser privileges."""
    if not current_user.is_superuser:
        raise AuthorizationError("Not enough permissions. Superuser access required.")

    return current_user


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Get AuthService instance."""
    return AuthService(db)


async def get_mcp_service(db: AsyncSession = Depends(get_db)) -> MCPService:
    """Get MCPService instance."""
    service = MCPService(db)
    await service.initialize()
    return service


async def get_profile_service(db: AsyncSession = Depends(get_db)) -> LLMProfileService:
    """Get LLM profile service instance with database session."""
    return LLMProfileService(db)


async def get_prompt_service(db: AsyncSession = Depends(get_db)) -> PromptService:
    """Get prompt service instance with database session."""
    return PromptService(db)


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Get UserService instance."""
    return UserService(db)


async def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    """Get DocumentService instance."""
    return DocumentService(db)


async def get_search_service(db: AsyncSession = Depends(get_db)) -> SearchService:
    """Get SearchService instance."""
    return SearchService(db)


async def get_conversation_service(
    db: AsyncSession = Depends(get_db),
) -> ConversationService:
    """Get ConversationService instance."""
    return ConversationService(db)


async def get_embedding_service(db: AsyncSession = Depends(get_db)) -> EmbeddingService:
    """Get EmbeddingService instance."""
    return EmbeddingService(db)
