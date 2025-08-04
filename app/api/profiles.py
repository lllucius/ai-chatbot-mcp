"""LLM profile management API endpoints."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.common import (
    APIResponse,
    BaseResponse,
    ErrorResponse,
    SuccessResponse,
)
from shared.schemas.llm_profile import (
    LLMProfileCreate,
    LLMProfileListResponse,
    LLMProfileResponse,
    LLMProfileUpdate,
)
from shared.schemas.task_responses import (
    ProfileParametersData,
    ProfileValidationData,
)

from ..config import settings
from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user
from ..models.user import User
from ..services.llm_profile_service import LLMProfileService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["profiles"])


async def get_profile_service(db: AsyncSession = Depends(get_db)) -> LLMProfileService:
    """Get LLM profile service instance with database session."""
    return LLMProfileService(db)


@router.post("/", response_model=LLMProfileResponse)
@handle_api_errors("Failed to create profile")
async def create_profile(
    request: LLMProfileCreate,
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> LLMProfileResponse:
    """Create a new LLM parameter profile with validation."""
    log_api_call("create_profile", user_id=current_user.id)
    profile = await profile_service.create_profile(request)
    return LLMProfileResponse.model_validate(profile)


@router.get("/", response_model=LLMProfileListResponse)
@handle_api_errors("Failed to list profiles")
async def list_profiles(
    active_only: bool = Query(True, description="Show only active profiles"),
    search: Optional[str] = Query(None, description="Search in profiles"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> LLMProfileListResponse:
    """List all LLM parameter profiles with filtering and pagination."""
    log_api_call("list_profiles", user_id=current_user.id)

    profiles, total = await profile_service.list_profiles(
        active_only=active_only, search=search, page=page, size=size
    )
    pages = (total + size - 1) // size if size else 1
    profile_responses = []
    for p in profiles:
        profile_responses.append(
            LLMProfileResponse(
                name=p.name,
                title=p.title,
                description=p.description,
                model_name=settings.openai_chat_model,
                parameters=p.to_openai_params(),
                is_default=p.is_default,
                is_active=p.is_active,
                usage_count=p.usage_count,
                last_used_at=p.last_used_at,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )
    return LLMProfileListResponse(
        profiles=profile_responses, total=total, page=page, size=size, pages=pages
    )


@router.get("/byname/{profile_name}", response_model=LLMProfileResponse)
@handle_api_errors("Failed to get profile details")
async def get_profile_details(
    profile_name: str,
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> LLMProfileResponse:
    """Get detailed information about a specific LLM profile by name."""
    log_api_call(
        "get_profile_details", user_id=current_user.id, profile_name=profile_name
    )
    profile = await profile_service.get_profile(profile_name)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{profile_name}' not found",
        )

    response_data = {
        "name": profile.name,
        "title": profile.title,
        "description": profile.description,
        "model_name": settings.openai_chat_model,
        "parameters": profile.to_openai_params(),
        "is_default": profile.is_default,
        "is_active": profile.is_active,
        "usage_count": profile.usage_count,
        "last_used_at": profile.last_used_at,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }
    return LLMProfileResponse.model_validate(response_data)


@router.put("/byname/{profile_name}", response_model=LLMProfileResponse)
@handle_api_errors("Failed to update profile")
async def update_profile(
    profile_name: str,
    profile_data: LLMProfileUpdate,
    current_user: User = Depends(get_current_superuser),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> LLMProfileResponse:
    """
    Update an existing LLM profile with new parameters or metadata.
    """
    log_api_call("update_llm_profile", user_id=current_user.id, profile_name=profile_name)

    updated_profile = await profile_service.update_profile(profile_name, profile_data.model_dump(exclude_unset=True))

    return LLMProfileResponse.model_validate(updated_profile)


@router.delete("/byname/{profile_name}", response_model=APIResponse)
@handle_api_errors("Failed to delete profile")
async def delete_profile(
    profile_name: str,
    current_user: User = Depends(get_current_superuser),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> BaseResponse:
    """
    Delete an LLM profile from the system.
    """
    log_api_call("delete_llm_profile", user_id=current_user.id, profile_name=profile_name)

    await profile_service.delete_profile(profile_name)

    return SuccessResponse.create(
        message=f"Profile '{profile_name}' deleted successfully"
    )


@router.post("/byname/{profile_name}/set-default", response_model=APIResponse)
@handle_api_errors("Failed to set default profile")
async def set_default_profile(
    profile_name: str,
    current_user: User = Depends(get_current_superuser),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> BaseResponse:
    """Set a profile as the default LLM parameter profile for the system."""
    log_api_call(
        "set_default_profile", user_id=current_user.id, profile_name=profile_name
    )
    success = await profile_service.set_default_profile(profile_name)
    if success:
        return SuccessResponse.create(
            message=f"Profile '{profile_name}' set as default"
        )
    else:
        return ErrorResponse.create(
            error_code="PROFILE_NOT_FOUND",
            message=f"Profile '{profile_name}' not found",
            status_code=404
        )


@router.get("/default/parameters", response_model=APIResponse)
@handle_api_errors("Failed to get default profile parameters")
async def get_default_profile_parameters(
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> APIResponse:
    """Get parameters from the default LLM profile in OpenAI-compatible format."""
    log_api_call("get_default_profile_parameters", user_id=current_user.id)
    params = await profile_service.get_profile_for_openai()
    response_payload = ProfileParametersData(
        parameters=params,
        profile_name="default",
    )
    return APIResponse(
        success=True,
        message="Default profile parameters retrieved successfully",
        data=response_payload.model_dump(),
    )


@router.get("/stats", response_model=APIResponse)
@handle_api_errors("Failed to get profile statistics")
async def get_profile_stats(
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
):
    """Get comprehensive LLM profile usage statistics and analytics."""
    log_api_call("get_profile_stats", user_id=current_user.id)
    stats = await profile_service.get_profile_stats()
    return APIResponse(
        success=True,
        message="Profile statistics retrieved successfully",
        data=stats,
    )


@router.post("/validate", response_model=APIResponse)
@handle_api_errors("Failed to validate parameters")
async def validate_parameters(
    parameters: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
):
    """Validate LLM parameters before profile creation or update."""
    log_api_call("validate_parameters", user_id=current_user.id)
    errors = await profile_service.validate_parameters(**parameters)
    response_payload = ProfileValidationData(
        valid=len(errors) == 0,
        errors=errors,
        parameters=parameters,
    )
    return APIResponse(
        success=len(errors) == 0,
        message="Parameter validation completed" + (" successfully" if len(errors) == 0 else " with errors"),
        data=response_payload.model_dump(),
    )
