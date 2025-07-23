"""
API dependencies and dependency injection utilities.

This module provides reusable dependencies for FastAPI endpoints
including authentication, pagination, and service injection.
"""

from typing import Generator, Optional

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..services.auth import AuthService
from ..services.conversation import ConversationService
from ..services.document import DocumentService
from ..services.embedding import EmbeddingService
from ..services.search import SearchService
from ..services.user import UserService

# Security scheme
security = HTTPBearer()


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.

    Args:
        credentials: Optional JWT token from Authorization header
        db: Database session

    Returns:
        Optional[User]: Current user or None
    """
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


# Service dependencies
async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Get AuthService instance."""
    return AuthService(db)


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


# Pagination dependencies
class PaginationParams:
    """Pagination parameters dependency."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(20, ge=1, le=100, description="Items per page"),
        sort_by: Optional[str] = Query(None, description="Sort field"),
        sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    ):
        self.page = page
        self.size = size
        self.sort_by = sort_by
        self.sort_order = sort_order

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        """Get limit for database queries."""
        return self.size


def get_pagination_params() -> Generator[PaginationParams, None, None]:
    """Get pagination parameters dependency."""

    def _get_pagination_params(
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100),
        sort_by: Optional[str] = Query(None),
        sort_order: str = Query("desc", regex="^(asc|desc)$"),
    ) -> PaginationParams:
        return PaginationParams(page, size, sort_by, sort_order)

    return _get_pagination_params


# Search parameters dependency
class SearchParams:
    """Search parameters dependency."""

    def __init__(
        self,
        q: str = Query(..., description="Search query"),
        algorithm: str = Query("hybrid", regex="^(vector|text|hybrid|mmr)$"),
        limit: int = Query(10, ge=1, le=50),
        threshold: float = Query(0.7, ge=0.0, le=1.0),
    ):
        self.query = q
        self.algorithm = algorithm
        self.limit = limit
        self.threshold = threshold


def get_search_params() -> Generator[SearchParams, None, None]:
    """Get search parameters dependency."""

    def _get_search_params(
        q: str = Query(..., min_length=1),
        algorithm: str = Query("hybrid", regex="^(vector|text|hybrid|mmr)$"),
        limit: int = Query(10, ge=1, le=50),
        threshold: float = Query(0.7, ge=0.0, le=1.0),
    ) -> SearchParams:
        return SearchParams(q, algorithm, limit, threshold)

    return _get_search_params
