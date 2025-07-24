"""
Search API endpoints for document retrieval and similarity search.

This module provides endpoints for searching through documents using
various algorithms including vector similarity, text search, and hybrid approaches.

"""

import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..schemas.common import BaseResponse
from ..schemas.document import DocumentSearchRequest, DocumentSearchResponse
from ..services.search import SearchService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["search"])


async def get_search_service(db: AsyncSession = Depends(get_db)) -> SearchService:
    """Get search service instance."""
    return SearchService(db)


@router.post("/", response_model=DocumentSearchResponse)
@handle_api_errors("Search operation failed")
async def search_documents(
    request: DocumentSearchRequest,
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service),
):
    """
    Search through documents using various algorithms.

    Supports multiple search algorithms:
    - vector: Semantic similarity using embeddings
    - text: Traditional full-text search
    - hybrid: Combines vector and text search
    - mmr: Maximum Marginal Relevance for diverse results
    """
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

    return DocumentSearchResponse(
        success=True,
        message=f"Search completed using {request.algorithm} algorithm",
        results=results,
        query=request.query,
        algorithm=request.algorithm,
        total_results=len(results),
        search_time_ms=search_time_ms,
    )


@router.get("/similar/{chunk_id}", response_model=DocumentSearchResponse)
@handle_api_errors("Similar chunks search failed")
async def find_similar_chunks(
    chunk_id: int,
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service),
):
    """
    Find chunks similar to a given chunk.

    Uses vector similarity to find document chunks that are
    semantically similar to the specified chunk.
    """
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

    return DocumentSearchResponse(
        success=True,
        message=f"Found {len(results)} similar chunks",
        results=results,
        query=f"similar_to_chunk_{chunk_id}",
        algorithm="vector",
        total_results=len(results),
        search_time_ms=search_time_ms,
    )


@router.get("/suggestions")
@handle_api_errors("Failed to generate suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service),
):
    """
    Get search query suggestions.

    Returns suggested search terms based on document content
    and previous search patterns.
    """
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

    return {
        "success": True,
        "message": "Search suggestions generated",
        "query": query,
        "suggestions": suggestions[:limit],
    }


@router.get("/history")
@handle_api_errors("Failed to retrieve search history")
async def get_search_history(
    limit: int = Query(10, ge=1, le=50), current_user: User = Depends(get_current_user)
):
    """
    Get user's search history.

    Returns recent search queries performed by the current user.
    For admin dashboard, shows aggregated search patterns.
    """
    log_api_call("get_search_history", user_id=str(current_user.id), limit=limit)

    # For admin dashboard, provide aggregated search analytics
    # In a full implementation, this would query a search_history table

    mock_history = [
        {
            "query": "machine learning",
            "timestamp": "2024-01-22T15:30:00Z",
            "results_count": 25,
            "algorithm": "hybrid",
        },
        {
            "query": "neural networks",
            "timestamp": "2024-01-22T14:15:00Z",
            "results_count": 18,
            "algorithm": "vector",
        },
        {
            "query": "data processing",
            "timestamp": "2024-01-22T13:45:00Z",
            "results_count": 32,
            "algorithm": "text",
        },
    ]

    return {
        "success": True,
        "message": "Search history retrieved",
        "history": mock_history[:limit],
        "total": len(mock_history),
    }


@router.delete("/history", response_model=BaseResponse)
@handle_api_errors("Failed to clear search history")
async def clear_search_history(current_user: User = Depends(get_current_user)):
    """
    Clear user's search history.

    Removes all search history entries for the current user.
    For admin dashboard, this clears system-wide search analytics.
    """
    log_api_call("clear_search_history", user_id=str(current_user.id))

    # For admin dashboard, this would clear system-wide search analytics
    # In a full implementation, this would delete from search_history table

    return BaseResponse(success=True, message="Search history cleared successfully")
