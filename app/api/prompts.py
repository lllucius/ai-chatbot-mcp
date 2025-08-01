"""
Prompt registry API endpoints.

This module provides endpoints for managing prompts in the prompt registry,
including CRUD operations, statistics, and category management.

All endpoints use explicit Pydantic response models.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user
from ..models.user import User
from ..schemas.common import BaseResponse
from ..schemas.prompt import PromptResponse, PromptListResponse
from ..services.prompt_service import PromptService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["prompts"])


async def get_prompt_service(db: AsyncSession = Depends(get_db)) -> PromptService:
    """Get prompt service instance."""
    return PromptService(db)


@router.get("/", response_model=PromptListResponse)
@handle_api_errors("Failed to list prompts")
async def list_prompts(
    active_only: bool = Query(True, description="Show only active prompts"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in prompts"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> PromptListResponse:
    """
    List all prompts with optional filtering and pagination.

    Returns information about available prompts including their
    content, categories, tags, and usage statistics.
    """
    log_api_call("list_prompts", user_id=current_user.id)

        prompts, total = await prompt_service.list_prompts(
            active_only=active_only,
            category=category,
            search=search,
            page=page,
            size=size,
        )

    pages = (total + size - 1) // size if size else 1

    prompt_responses = []
    for p in prompts:
        prompt_responses.append(PromptResponse(
            name=p.name,
            title=p.title,
            description=p.description,
            category=p.category,
            content=p.content,
            variables=None,
            tags=p.tag_list,
            is_active=p.is_active,
            is_default=p.is_default,
            usage_count=p.usage_count,
            last_used_at=p.last_used_at,
            created_at=p.created_at,
            updated_at=p.updated_at,
        ))

    return PromptListResponse(
        prompts=prompt_responses,
        total=total,
        page=page,
        size=size,
        pages=pages
        )


@router.get("/byname/{prompt_name}", response_model=PromptResponse)
@handle_api_errors("Failed to get prompt details")
async def get_prompt_details(
    prompt_name: str,
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> PromptResponse:
    """
    Get detailed information about a specific prompt.

    Returns the complete prompt content, metadata, and usage statistics.
    """
    log_api_call("get_prompt_details", user_id=current_user.id, prompt_name=prompt_name)

    prompt = await prompt_service.get_prompt(prompt_name)

    if not prompt:
        raise HTTPException(
            status_code=404,
            detail=f"Prompt '{prompt_name}' not found",
        )

    return PromptResponse(
        name=prompt.name,
        title=prompt.title,
        content=prompt.content,
        description=prompt.description,
        category=prompt.category,
        variables=None,
        tags=prompt.tag_list,
        is_active=prompt.is_active,
        is_default=prompt.is_default,
        usage_count=prompt.usage_count,
        last_used_at=prompt.last_used_at,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
    )


@router.get("/categories/", response_model=Dict[str, Any])
@handle_api_errors("Failed to get categories")
async def get_categories(
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> Dict[str, Any]:
    """Get all available prompt categories."""
    log_api_call("get_prompt_categories", user_id=current_user.id)

        categories = await prompt_service.get_categories()
        tags = await prompt_service.get_all_tags()

        return {
            "success": True,
            "data": {
                "categories": categories,
                "tags": tags,
            },
        }


@router.post("/byname/{prompt_name}/set-default", response_model=BaseResponse)
@handle_api_errors("Failed to set default prompt")
async def set_default_prompt(
    prompt_name: str,
    current_user: User = Depends(get_current_superuser),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> BaseResponse:
    """
    Set a prompt as the default system prompt.

    Only available to superusers.
    """
    log_api_call("set_default_prompt", user_id=current_user.id, prompt_name=prompt_name)

        success = await prompt_service.set_default_prompt(prompt_name)

        if success:
            return BaseResponse(success=True, message=f"Prompt '{prompt_name}' set as default")
        else:
            raise HTTPException(
            status_code=404,
                detail=f"Prompt '{prompt_name}' not found",
            )


@router.get("/stats", response_model=Dict[str, Any])
@handle_api_errors("Failed to get prompt statistics")
async def get_prompt_stats(
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> Dict[str, Any]:
    """Get prompt usage statistics and analytics."""
    log_api_call("get_prompt_stats", user_id=current_user.id)

        stats = await prompt_service.get_prompt_stats()

        return {
            "success": True,
            "data": stats,
        }
