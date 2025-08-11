"""LLM profile management API endpoints."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import (
    get_current_superuser,
    get_current_user,
    get_profile_service,
)
from app.models.user import User
from app.services.llm_profile_service import LLMProfileService
from app.utils.api_errors import handle_api_errors, log_api_call
from shared.schemas.common import (
    APIResponse,
    BaseResponse,
    PaginatedResponse,
    PaginationParams,
)
from shared.schemas.llm_profile import (
    LLMProfileCreate,
    LLMProfileResponse,
    LLMProfileStatisticsData,
    LLMProfileUpdate,
)

router = APIRouter(tags=["profiles"])


@router.post("/", response_model=APIResponse[LLMProfileResponse])
@handle_api_errors("Failed to create profile")
async def create_profile(
    request: LLMProfileCreate,
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> APIResponse[LLMProfileResponse]:
    """Create a new LLM parameter profile with validation."""
    log_api_call("create_profile", user_id=current_user.id)

    profile = await profile_service.create_profile(
        name=request.name,
        title=request.title,
        description=request.description,
        model_name=request.model_name,
        parameters=request.parameters,
        is_default=request.is_default,
    )

    payload = LLMProfileResponse.model_validate(profile)
    return APIResponse[LLMProfileResponse](
        success=True,
        message="Profile created successfully",
        data=payload,
    )


@router.get("/", response_model=APIResponse[PaginatedResponse[LLMProfileResponse]])
@handle_api_errors("Failed to list profiles")
async def list_profiles(
    active_only: bool = Query(True, description="Show only active profiles"),
    search: Optional[str] = Query(None, description="Search in profiles"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> APIResponse[PaginatedResponse[LLMProfileResponse]]:
    """List all LLM parameter profiles with filtering and pagination."""
    log_api_call("list_profiles", user_id=current_user.id)

    profiles, total = await profile_service.list_profiles(
        active_only=active_only,
        search=search,
        page=page,
        size=size,
    )

    profile_responses = []
    for profile in profiles:
        profile_responses.append(LLMProfileResponse.model_validate(profile))

    payload = PaginatedResponse(
        items=profile_responses,
        pagination=PaginationParams(
            total=total,
            page=page,
            per_page=size,
        ),
    )

    return APIResponse[PaginatedResponse[LLMProfileResponse]](
        success=True,
        message="Profiles retrieved successfully",
        data=payload,
    )


@router.get("/byname/{profile_name}", response_model=APIResponse[LLMProfileResponse])
@handle_api_errors("Failed to get profile details")
async def get_profile_details(
    profile_name: str,
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> APIResponse[LLMProfileResponse]:
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
    payload = LLMProfileResponse.model_validate(profile)
    return APIResponse[LLMProfileResponse](
        success=True,
        message=f"Profile '{profile_name}' details retrieved successfully",
        data=payload,
    )


@router.put("/byname/{profile_name}", response_model=APIResponse[LLMProfileResponse])
@handle_api_errors("Failed to update profile")
async def update_profile(
    profile_name: str,
    profile_data: LLMProfileUpdate,
    current_user: User = Depends(get_current_superuser),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> APIResponse[LLMProfileResponse]:
    """Update an existing LLM profile with new parameters or metadata."""
    log_api_call(
        "update_llm_profile", user_id=current_user.id, profile_name=profile_name
    )

    updated_profile = await profile_service.update_profile(
        profile_name, profile_data.model_dump(exclude_unset=True)
    )

    if not updated_profile:
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{profile_name}' not found",
        )
    payload = LLMProfileResponse.model_validate(updated_profile)
    return APIResponse[LLMProfileResponse](
        success=True,
        message=f"Profile '{profile_name}' updated successfully",
        data=payload,
    )


@router.delete("/byname/{profile_name}", response_model=APIResponse)
@handle_api_errors("Failed to delete profile")
async def delete_profile(
    profile_name: str,
    current_user: User = Depends(get_current_superuser),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> APIResponse:
    """Delete an LLM profile from the system."""
    log_api_call(
        "delete_llm_profile", user_id=current_user.id, profile_name=profile_name
    )

    success = await profile_service.delete_profile(profile_name)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{profile_name}' not found",
        )

    return APIResponse(
        success=True,
        message=f"Profile '{profile_name}' set as default",
    )


@router.post(
    "/byname/{profile_name}/set-default", response_model=APIResponse[BaseResponse]
)
@handle_api_errors("Failed to set default profile")
async def set_default_profile(
    profile_name: str,
    current_user: User = Depends(get_current_superuser),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> APIResponse[BaseResponse]:
    """Set a profile as the default LLM parameter profile for the system."""
    log_api_call(
        "set_default_profile", user_id=current_user.id, profile_name=profile_name
    )
    success = await profile_service.set_default_profile(profile_name)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{profile_name}' not found",
        )

    return APIResponse(success=True, message=f"Profile '{profile_name}' set as default")


@router.get("/default", response_model=APIResponse[LLMProfileResponse])
@handle_api_errors("Failed to get default profile")
async def get_default_profile(
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> APIResponse[LLMProfileResponse]:
    """Get detailed information about the defualt LLM profile."""
    log_api_call("get_default_profile", user_id=current_user.id)
    profile = await profile_service.get_default_profile()
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Default profile not set",
        )
    payload = LLMProfileResponse.model_validate(profile)
    return APIResponse[LLMProfileResponse](
        success=True,
        message="Default profile details retrieved successfully",
        data=payload,
    )


@router.post("/byname/{profile_name}/activate", response_model=APIResponse)
@handle_api_errors("Failed to activate profile")
async def activate_profile(
    profile_name: str,
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> APIResponse:
    """Activate a profile."""
    log_api_call("activate_profile", user_id=current_user.id, profile_name=profile_name)

    try:
        profile = await profile_service.get_profile(profile_name)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

        if profile.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile is already active"
            )

        # Activate profile
        profile.is_active = True
        await profile_service.db.commit()

        return APIResponse(
            success=True,
            message=f"Profile {profile.name} activated successfully",
        )
    except HTTPException:
        raise
    except Exception:
        await profile_service.db.rollback()
        raise


@router.post("/byname/{profile_name}/deactivate", response_model=APIResponse)
@handle_api_errors("Failed to deactivate profile")
async def deactivate_profile(
    profile_name: str,
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> APIResponse:
    """Deactivate a profile."""
    log_api_call("deactivate_profile", user_id=current_user.id, profile_name=profile_name)

    try:
        profile = await profile_service.get_profile(profile_name)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                ail="Profile not found"
            )

        if not profile.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile is already inactive",
            )

        # Deactivate profile
        profile.is_active = False
        await profile_service.db.commit()

        return APIResponse(
            success=True,
            message=f"Profile {profile.name} deactivated successfully",
        )
    except HTTPException:
        raise
    except Exception:
        await profile_service.db.rollback()
        raise


@router.get("/stats", response_model=APIResponse[LLMProfileStatisticsData])
@handle_api_errors("Failed to get profile statistics")
async def get_profile_stats(
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> APIResponse[LLMProfileStatisticsData]:
    """Get comprehensive LLM profile usage statistics and analytics."""
    log_api_call("get_profile_stats", user_id=current_user.id)
    stats = await profile_service.get_profile_stats()
    payload = LLMProfileStatisticsData.model_validate(stats)
    return APIResponse[LLMProfileStatisticsData](
        success=True,
        message="Profile statistics retrieved successfully",
        data=payload,
    )


@router.post("/validate", response_model=APIResponse[dict])
@handle_api_errors("Failed to validate parameters")
async def validate_parameters(
    parameters: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> APIResponse[dict]:
    """Validate LLM parameters before profile creation or update."""
    log_api_call("validate_parameters", user_id=current_user.id)
    errors = await profile_service.validate_parameters(**parameters)
    return APIResponse[dict](
        success=len(errors) == 0,
        message="Parameter validation completed"
        + (" successfully" if len(errors) == 0 else " with errors"),
        data=errors,
    )
