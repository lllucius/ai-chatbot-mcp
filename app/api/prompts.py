"""
Prompt registry API endpoints.

This module provides endpoints for managing prompts in the prompt registry,
including CRUD operations, statistics, and category management.

"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user
from ..models.user import User
from ..schemas.common import BaseResponse
from ..services.prompt_service import PromptService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["prompts"])


async def get_prompt_service(db: AsyncSession = Depends(get_db)) -> PromptService:
    """Get prompt service instance."""
    return PromptService(db)


@router.get("/", response_model=Dict[str, Any])
@handle_api_errors("Failed to list prompts")
async def list_prompts(
    active_only: bool = Query(True, description="Show only active prompts"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in prompts"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    """
    List all prompts with optional filtering and pagination.

    Returns information about available prompts including their
    content, categories, tags, and usage statistics.
    """
    log_api_call("list_prompts", user_id=current_user.id)

    try:
        prompts, total = await prompt_service.list_prompts(
            active_only=active_only,
            category=category,
            search=search,
            page=page,
            size=size,
        )

        return {
            "success": True,
            "data": {
                "prompts": [
                    {
                        "name": p.name,
                        "title": p.title,
                        "description": p.description,
                        "category": p.category,
                        "tags": p.tag_list,
                        "is_default": p.is_default,
                        "is_active": p.is_active,
                        "usage_count": p.usage_count,
                        "last_used_at": (
                            p.last_used_at.isoformat() if p.last_used_at else None
                        ),
                        "created_at": p.created_at.isoformat(),
                    }
                    for p in prompts
                ],
                "total": total,
                "page": page,
                "size": size,
                "filters": {
                    "active_only": active_only,
                    "category": category,
                    "search": search,
                },
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve prompts: {str(e)}",
        )


@router.get("/{prompt_name}", response_model=Dict[str, Any])
@handle_api_errors("Failed to get prompt details")
async def get_prompt_details(
    prompt_name: str,
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    """
    Get detailed information about a specific prompt.

    Returns the complete prompt content, metadata, and usage statistics.
    """
    log_api_call("get_prompt_details", user_id=current_user.id, prompt_name=prompt_name)

    try:
        prompt = await prompt_service.get_prompt(prompt_name)

        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt '{prompt_name}' not found",
            )

        return {
            "success": True,
            "data": {
                "name": prompt.name,
                "title": prompt.title,
                "content": prompt.content,
                "description": prompt.description,
                "category": prompt.category,
                "tags": prompt.tag_list,
                "is_default": prompt.is_default,
                "is_active": prompt.is_active,
                "usage_count": prompt.usage_count,
                "last_used_at": (
                    prompt.last_used_at.isoformat() if prompt.last_used_at else None
                ),
                "created_at": prompt.created_at.isoformat(),
                "updated_at": prompt.updated_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prompt details: {str(e)}",
        )


@router.get("/categories/", response_model=Dict[str, Any])
@handle_api_errors("Failed to get categories")
async def get_categories(
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    """Get all available prompt categories."""
    log_api_call("get_prompt_categories", user_id=current_user.id)

    try:
        categories = await prompt_service.get_categories()
        tags = await prompt_service.get_all_tags()

        return {
            "success": True,
            "data": {
                "categories": categories,
                "tags": tags,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get categories: {str(e)}",
        )


@router.post("/{prompt_name}/set-default", response_model=BaseResponse)
@handle_api_errors("Failed to set default prompt")
async def set_default_prompt(
    prompt_name: str,
    current_user: User = Depends(get_current_superuser),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    """
    Set a prompt as the default system prompt.

    Only available to superusers.
    """
    log_api_call("set_default_prompt", user_id=current_user.id, prompt_name=prompt_name)

    try:
        success = await prompt_service.set_default_prompt(prompt_name)

        if success:
            return BaseResponse(
                success=True, message=f"Prompt '{prompt_name}' set as default"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt '{prompt_name}' not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set default prompt: {str(e)}",
        )


@router.get("/stats/", response_model=Dict[str, Any])
@handle_api_errors("Failed to get prompt statistics")
async def get_prompt_stats(
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    """Get prompt usage statistics and analytics."""
    log_api_call("get_prompt_stats", user_id=current_user.id)

    try:
        stats = await prompt_service.get_prompt_stats()

        return {
            "success": True,
            "data": stats,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prompt statistics: {str(e)}",
        )
