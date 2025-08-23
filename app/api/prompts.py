"""Prompt registry management API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.exceptions import NotFoundError, ValidationError
from app.dependencies import get_current_superuser, get_current_user, get_prompt_service
from app.models.user import User
from app.services.prompt_service import PromptService
from app.utils.api_errors import handle_api_errors, log_api_call
from shared.schemas.common import APIResponse, PaginatedResponse, PaginationParams
from shared.schemas.prompt import (
    PromptCategoriesData,
    PromptCreate,
    PromptResponse,
    PromptStatisticsData,
    PromptUpdate,
)

router = APIRouter(tags=["prompts"])


@router.get("/", response_model=APIResponse[PaginatedResponse[PromptResponse]])
@handle_api_errors("Failed to list prompts")
async def list_prompts(
    active_only: bool = Query(True, description="Show only active prompts"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in prompts"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> APIResponse[PaginatedResponse[PromptResponse]]:
    """List all prompts with filtering, categorization, and pagination."""
    log_api_call("list_prompts", user_id=current_user.id)

    prompts, total = await prompt_service.list_prompts(
        active_only=active_only,
        category=category,
        search=search,
        page=page,
        size=size,
    )

    prompt_responses = []
    for prompt in prompts:
        prompt_responses.append(PromptResponse.model_validate(prompt))

    payload = PaginatedResponse(
        items=prompt_responses,
        pagination=PaginationParams(
            total=total,
            page=page,
            per_page=size,
        ),
    )

    return APIResponse[PaginatedResponse[PromptResponse]](
        success=True,
        message="Prompts retrieved successfully",
        data=payload,
    )


@router.get("/byname/{prompt_name}", response_model=APIResponse[PromptResponse])
@handle_api_errors("Failed to get prompt details")
async def get_prompt_details(
    prompt_name: str,
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> APIResponse[PromptResponse]:
    """Get detailed information about a specific prompt by name."""
    log_api_call("get_prompt_details", user_id=current_user.id, prompt_name=prompt_name)

    prompt = await prompt_service.get_prompt(prompt_name)

    if not prompt:
        raise NotFoundError(f"Prompt '{prompt_name}' not found")

    payload = PromptResponse.model_validate(prompt)
    return APIResponse[PromptResponse](
        success=True,
        message="Prompt retrieved successfully",
        data=payload,
    )


@router.post("/", response_model=APIResponse[PromptResponse])
@handle_api_errors("Failed to create prompt")
async def create_prompt(
    request: PromptCreate,
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> APIResponse[PromptResponse]:
    """Create a new prompt template in the registry."""
    log_api_call("create_prompt", user_id=current_user.id)

    prompt = await prompt_service.create_prompt(
        name=request.name,
        title=request.title,
        content=request.content,
        description=request.description,
        category=request.category,
        tags=request.tags
    )

    payload = PromptResponse.model_validate(prompt)
    return APIResponse[PromptResponse](
        success=True,
        message="Prompt created successfully",
        data=payload,
    )


@router.put("/byname/{prompt_name}", response_model=APIResponse[PromptResponse])
@handle_api_errors("Failed to update prompt")
async def update_prompt(
    prompt_name: str,
    data: PromptUpdate,
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> APIResponse[PromptResponse]:
    """Update an existing prompt template."""
    log_api_call("update_prompt", user_id=current_user.id, prompt_name=prompt_name)

    prompt = await prompt_service.update_prompt(
        prompt_name, data.model_dump(exclude_unset=True)
    )
    payload = PromptResponse.model_validate(prompt)
    return APIResponse[PromptResponse](
        success=True,
        message="Prompt updated successfully",
        data=payload,
    )


@router.delete("/byname/{prompt_name}", response_model=APIResponse)
@handle_api_errors("Failed to delete prompt")
async def delete_prompt(
    prompt_name: str,
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> APIResponse:
    """Delete a prompt template from the registry."""
    log_api_call("delete_prompt", user_id=current_user.id, prompt_name=prompt_name)

    await prompt_service.delete_prompt(prompt_name)

    return APIResponse(
        success=True,
        message=f"Prompt '{prompt_name}' deleted successfully",
    )


@router.post("/byname/{prompt_name}/activate", response_model=APIResponse)
@handle_api_errors("Failed to activate prompt")
async def activate_prompt(
    prompt_name: str,
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> APIResponse:
    """Activate a prompt."""
    log_api_call("activate_prompt", user_id=current_user.id, prompt_name=prompt_name)

    try:
        prompt = await prompt_service.get_prompt(prompt_name)
        if not prompt:
            raise NotFoundError("Prompt not found")

        if prompt.is_active:
            raise ValidationError("Prompt is already active")

        # Activate prompt
        prompt.is_active = True
        await prompt_service.db.commit()

        return APIResponse(
            success=True,
            message=f"Prompt {prompt.name} activated successfully",
        )
    except Exception:
        await prompt_service.db.rollback()
        raise


@router.post("/byname/{prompt_name}/deactivate", response_model=APIResponse)
@handle_api_errors("Failed to deactivate prompt")
async def deactivate_prompt(
    prompt_name: str,
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> APIResponse:
    """Deactivate a prompt."""
    log_api_call("deactivate_prompt", user_id=current_user.id, prompt_name=prompt_name)

    try:
        prompt = await prompt_service.get_prompt(prompt_name)
        if not prompt:
            raise NotFoundError("Prompt not found")

        if not prompt.is_active:
            raise ValidationError("Prompt is already inactive")

        # Deactivate prompt
        prompt.is_active = False
        await prompt_service.db.commit()

        return APIResponse(
            success=True,
            message=f"Prompt {prompt.name} deactivated successfully",
        )
    except Exception:
        await prompt_service.db.rollback()
        raise


@router.get("/categories/", response_model=APIResponse[PromptCategoriesData])
@handle_api_errors("Failed to get categories")
async def get_categories(
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> APIResponse[PromptCategoriesData]:
    """Get all available prompt categories and tags for organization."""
    log_api_call("get_prompt_categories", user_id=current_user.id)

    categories = await prompt_service.get_categories()
    tags = await prompt_service.get_all_tags()

    payload = PromptCategoriesData(
        categories=categories,
        tags=tags,
    )

    return APIResponse(
        success=True,
        message="Prompt categories and tags retrieved successfully",
        data=payload,
    )


@router.post("/byname/{prompt_name}/set-default", response_model=APIResponse)
@handle_api_errors("Failed to set default prompt")
async def set_default_prompt(
    prompt_name: str,
    current_user: User = Depends(get_current_superuser),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> APIResponse:
    """Set a prompt as the default system prompt for conversations."""
    log_api_call("set_default_prompt", user_id=current_user.id, prompt_name=prompt_name)

    success = await prompt_service.set_default_prompt(prompt_name)

    if not success:
        raise NotFoundError(f"Prompt '{prompt_name}' not found")

    return APIResponse(
        success=True,
        message=f"Prompt '{prompt_name}' set as default",
    )


@router.get("/stats", response_model=APIResponse[PromptStatisticsData])
@handle_api_errors("Failed to get prompt statistics")
async def get_prompt_stats(
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> APIResponse[PromptStatisticsData]:
    """Get comprehensive prompt usage statistics and analytics."""
    log_api_call("get_prompt_stats", user_id=current_user.id)

    stats = await prompt_service.get_prompt_stats()

    payload = PromptStatisticsData.model_validate(stats)

    return APIResponse[PromptStatisticsData](
        success=True,
        message="Prompt statistics retrieved successfully",
        data=payload,
    )
