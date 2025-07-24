"API endpoints for deps operations."

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

security = HTTPBearer()


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    "Get current user optional data."
    if not credentials:
        return None
    try:
        auth_service = AuthService(db)
        username = auth_service.verify_token(credentials.credentials)
        if not username:
            return None
        user = await auth_service.get_user_by_username(username)
        if (not user) or (not user.is_active):
            return None
        return user
    except Exception:
        return None


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    "Get auth service data."
    return AuthService(db)


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    "Get user service data."
    return UserService(db)


async def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    "Get document service data."
    return DocumentService(db)


async def get_search_service(db: AsyncSession = Depends(get_db)) -> SearchService:
    "Get search service data."
    return SearchService(db)


async def get_conversation_service(
    db: AsyncSession = Depends(get_db),
) -> ConversationService:
    "Get conversation service data."
    return ConversationService(db)


async def get_embedding_service(db: AsyncSession = Depends(get_db)) -> EmbeddingService:
    "Get embedding service data."
    return EmbeddingService(db)


class PaginationParams:
    "PaginationParams class for specialized functionality."

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(20, ge=1, le=100, description="Items per page"),
        sort_by: Optional[str] = Query(None, description="Sort field"),
        sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    ):
        "Initialize class instance."
        self.page = page
        self.size = size
        self.sort_by = sort_by
        self.sort_order = sort_order

    @property
    def offset(self) -> int:
        "Offset operation."
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        "Limit operation."
        return self.size


def get_pagination_params() -> Generator[(PaginationParams, None, None)]:
    "Get pagination params data."

    def _get_pagination_params(
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100),
        sort_by: Optional[str] = Query(None),
        sort_order: str = Query("desc", regex="^(asc|desc)$"),
    ) -> PaginationParams:
        "Get Pagination Params operation."
        return PaginationParams(page, size, sort_by, sort_order)

    return _get_pagination_params


class SearchParams:
    "SearchParams class for specialized functionality."

    def __init__(
        self,
        q: str = Query(..., description="Search query"),
        algorithm: str = Query("hybrid", regex="^(vector|text|hybrid|mmr)$"),
        limit: int = Query(10, ge=1, le=50),
        threshold: float = Query(0.7, ge=0.0, le=1.0),
    ):
        "Initialize class instance."
        self.query = q
        self.algorithm = algorithm
        self.limit = limit
        self.threshold = threshold


def get_search_params() -> Generator[(SearchParams, None, None)]:
    "Get search params data."

    def _get_search_params(
        q: str = Query(..., min_length=1),
        algorithm: str = Query("hybrid", regex="^(vector|text|hybrid|mmr)$"),
        limit: int = Query(10, ge=1, le=50),
        threshold: float = Query(0.7, ge=0.0, le=1.0),
    ) -> SearchParams:
        "Get Search Params operation."
        return SearchParams(q, algorithm, limit, threshold)

    return _get_search_params
