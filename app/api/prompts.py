"""Prompt registry management API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.common import (
    APIResponse,
    BaseResponse,
    ErrorResponse,
    SuccessResponse,
)
from shared.schemas.prompt import (
    PromptCreate,
    PromptListResponse,
    PromptResponse,
    PromptUpdate,
)
from shared.schemas.prompt_responses import (
    PromptCategoriesData,
    PromptStatisticsData,
)

from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user
from ..models.user import User
from ..services.prompt_service import PromptService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["prompts"])


async def get_prompt_service(db: AsyncSession = Depends(get_db)) -> PromptService:
    """Get prompt service instance with database session."""
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
    """List all prompts with filtering, categorization, and pagination."""
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
        prompt_responses.append(
            PromptResponse(
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
            )
        )

    return PromptListResponse(
        prompts=prompt_responses, total=total, page=page, size=size, pages=pages
    )


@router.get("/byname/{prompt_name}", response_model=PromptResponse)
@handle_api_errors("Failed to get prompt details")
async def get_prompt_details(
    prompt_name: str,
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> PromptResponse:
    """Get detailed information about a specific prompt by name."""
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


@router.post("/", response_model=PromptResponse)
@handle_api_errors("Failed to create prompt")
async def create_prompt(
    request: PromptCreate,
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> PromptResponse:
    """
    Create a new prompt template in the registry.
    """
    log_api_call("create_prompt", user_id=current_user.id)

    prompt = await prompt_service.create_prompt(request)

    return PromptResponse(
        name=prompt.name,
        title=prompt.title,
        description=prompt.description,
        category=prompt.category,
        content=prompt.content,
        variables=prompt.variables,
        tags=prompt.tags,
        is_active=prompt.is_active,
        usage_count=prompt.usage_count,
        last_used_at=prompt.last_used_at,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
    )


@router.put("/byname/{prompt_name}", response_model=PromptResponse)
@handle_api_errors("Failed to update prompt")
async def update_prompt(
    prompt_name: str,
    data: PromptUpdate,
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> PromptResponse:
    """
    Update an existing prompt template.
    """
    log_api_call("update_prompt", user_id=current_user.id, prompt_name=prompt_name)

    prompt = await prompt_service.update_prompt(prompt_name, data.model_dump(exclude_unset=True))

    return PromptResponse.model_validate(prompt)


@router.delete("/byname/{prompt_name}", response_model=APIResponse)
@handle_api_errors("Failed to delete prompt")
async def delete_prompt(
    prompt_name: str,
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    """
    Delete a prompt template from the registry.
    """
    log_api_call("delete_prompt", user_id=current_user.id, prompt_name=prompt_name)

    await prompt_service.delete_prompt(prompt_name)

    return SuccessResponse.create(
        message=f"Prompt '{prompt_name}' deleted successfully"
    )


@router.get("/categories/", response_model=APIResponse)
@handle_api_errors("Failed to get categories")
async def get_categories(
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> APIResponse:
    """Get all available prompt categories and tags for organization."""
    log_api_call("get_prompt_categories", user_id=current_user.id)

    categories = await prompt_service.get_categories()
    tags = await prompt_service.get_all_tags()

    response_payload = PromptCategoriesData(
        categories=categories,
        tags=tags,
    )

    return APIResponse(
        success=True,
        message="Prompt categories and tags retrieved successfully",
        data=response_payload.model_dump(),
    )


@router.post("/byname/{prompt_name}/set-default", response_model=APIResponse)
@handle_api_errors("Failed to set default prompt")
async def set_default_prompt(
    prompt_name: str,
    current_user: User = Depends(get_current_superuser),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> BaseResponse:
    """Set a prompt as the default system prompt for conversations."""
    log_api_call("set_default_prompt", user_id=current_user.id, prompt_name=prompt_name)

    success = await prompt_service.set_default_prompt(prompt_name)

    if success:
        return SuccessResponse.create(
            message=f"Prompt '{prompt_name}' set as default"
        )
    else:
        return ErrorResponse.create(
            error_code="PROMPT_NOT_FOUND",
            message=f"Prompt '{prompt_name}' not found",
            status_code=404
        )


@router.get("/stats", response_model=APIResponse)
@handle_api_errors("Failed to get prompt statistics")
async def get_prompt_stats(
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> APIResponse:
    """Get comprehensive prompt usage statistics and analytics."""
    log_api_call("get_prompt_stats", user_id=current_user.id)

    stats = await prompt_service.get_prompt_stats()

    response_payload = PromptStatisticsData(
        data=stats,
    )

    return APIResponse(
        success=True,
        message="Prompt statistics retrieved successfully",
        data=response_payload.model_dump(),
    )
