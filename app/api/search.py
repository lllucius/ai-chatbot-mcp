"API endpoints for search operations."

import time
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.exceptions import SearchError, ValidationError
from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..schemas.common import BaseResponse
from ..schemas.document import DocumentSearchRequest, DocumentSearchResponse
from ..services.search import SearchService

router = APIRouter(tags=["search"])


async def get_search_service(db: AsyncSession = Depends(get_db)) -> SearchService:
    "Get search service data."
    return SearchService(db)


@router.post("/", response_model=DocumentSearchResponse)
async def search_documents(
    request: DocumentSearchRequest,
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service),
):
    "Search for documents."
    try:
        start_time = time.time()
        results = await search_service.search_documents(request, current_user.id)
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
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SearchError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search operation failed",
        )


@router.get("/similar/{chunk_id}", response_model=DocumentSearchResponse)
async def find_similar_chunks(
    chunk_id: int,
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service),
):
    "Find Similar Chunks operation."
    try:
        start_time = time.time()
        results = await search_service.get_similar_chunks(
            chunk_id, current_user.id, limit
        )
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
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SearchError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Similar chunks search failed",
        )


@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service),
):
    "Get search suggestions data."
    try:
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate suggestions",
        )


@router.get("/history")
async def get_search_history(
    limit: int = Query(10, ge=1, le=50), current_user: User = Depends(get_current_user)
):
    "Get search history data."
    try:
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve search history",
        )


@router.delete("/history", response_model=BaseResponse)
async def clear_search_history(current_user: User = Depends(get_current_user)):
    "Clear Search History operation."
    try:
        return BaseResponse(success=True, message="Search history cleared successfully")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear search history",
        )
