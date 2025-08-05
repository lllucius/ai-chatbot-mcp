"""Document search API endpoints."""

import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.common import (
    APIResponse,
)
from shared.schemas.document import DocumentSearchRequest, DocumentSearchResponse
from shared.schemas.search_responses import (
    SearchSuggestionData,
)

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..services.search import SearchService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["search"])


async def get_search_service(db: AsyncSession = Depends(get_db)) -> SearchService:
    """Get search service instance with database session."""
    return SearchService(db)


@router.post("/", response_model=APIResponse[DocumentSearchResponse])
@handle_api_errors("Search operation failed")
async def search_documents(
    request: DocumentSearchRequest,
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service),
) -> APIResponse[DocumentSearchResponse]:
    """Search through documents using multiple algorithms."""
    log_api_call(
        "search_documents",
        user_id=str(current_user.id),
        query=request.query,
        algorithm=request.algorithm,
    )

    start_time = time.time()

    # Perform search
    results = await search_service.search_documents(request, current_user.id)

    # Calculate search time
    search_time_ms = (time.time() - start_time) * 1000

    payload = DocumentSearchResponse(
        results=results,
        query=request.query or "",
        algorithm=request.algorithm or "hybrid",
        total_results=len(results),
        search_time_ms=search_time_ms,
    )

    return APIResponse[DocumentSearchResponse](
        success=True,
        message=f"Search completed using {request.algorithm or 'hybrid'} algorithm",
        data=payload,
    )


@router.get("/similar/byid/{chunk_id}", response_model=DocumentSearchResponse)
@handle_api_errors("Similar chunks search failed")
async def find_similar_chunks(
    chunk_id: int,
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service),
) -> APIResponse[DocumentSearchResponse]:
    """Find document chunks similar to a specified reference chunk."""
    log_api_call(
        "find_similar_chunks",
        user_id=str(current_user.id),
        chunk_id=chunk_id,
        limit=limit,
    )

    start_time = time.time()

    # Find similar chunks
    results = await search_service.get_similar_chunks(chunk_id, current_user.id, limit)

    # Calculate search time
    search_time_ms = (time.time() - start_time) * 1000

    payload = DocumentSearchResponse(
        results=results,
        query=f"similar_to_chunk_{chunk_id}",
        algorithm="vector",
        total_results=len(results),
        search_time_ms=search_time_ms,
    )

    return APIResponse[DocumentSearchResponse](
        success=True,
        message=f"Found {len(results)} similar chunks",
        data=payload,
    )


@router.get("/suggestions", response_model=APIResponse[SearchSuggestionData])
@handle_api_errors("Failed to generate suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service),
) -> APIResponse[SearchSuggestionData]:
    """Generate intelligent search query suggestions."""
    log_api_call(
        "get_search_suggestions", user_id=str(current_user.id), query=query, limit=limit
    )

    # This is a simplified implementation
    # In a production system, you might want to implement
    # more sophisticated suggestion algorithms

    suggestions = [
        f"{query} definition",
        f"{query} examples",
        f"{query} tutorial",
        f"how to {query}",
        f"{query} best practices",
    ]

    payload = SearchSuggestionData(
        query=query,
        suggestions=suggestions[:limit],
    )

    return APIResponse[SearchSuggestionData](
        success=True,
        message="Search suggestions generated successfully",
        data=payload,
    )
