"""
LLM Profile registry API endpoints.

This module provides endpoints for managing LLM parameter profiles,
including CRUD operations, statistics, and parameter validation.

"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user
from ..models.user import User
from ..schemas.common import BaseResponse
from ..schemas.llm_profile import LLMProfileResponse
from ..services.llm_profile_service import LLMProfileService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["profiles"])


async def get_profile_service(db: AsyncSession = Depends(get_db)) -> LLMProfileService:
    """Get LLM profile service instance."""
    return LLMProfileService(db)


@router.get("/", response_model=Dict[str, Any])
@handle_api_errors("Failed to list profiles")
async def list_profiles(
    active_only: bool = Query(True, description="Show only active profiles"),
    search: Optional[str] = Query(None, description="Search in profiles"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
):
    """
    List all LLM parameter profiles with optional filtering and pagination.

    Returns information about available profiles including their
    parameters, usage statistics, and metadata.
    """
    log_api_call("list_profiles", user_id=current_user.id)

    try:
        profiles, total = await profile_service.list_profiles(
            active_only=active_only, search=search, page=page, size=size
        )

        # Return format expected by SDK - direct profiles list
        return {
            "success": True,
            "message": f"Retrieved {len(profiles)} profiles",
            "profiles": [
                {
                    "name": p.name,
                    "title": p.title,
                    "description": p.description,
                    "is_default": p.is_default,
                    "is_active": p.is_active,
                    "parameters": p.to_openai_params(),
                    "usage_count": p.usage_count,
                    "last_used_at": (p.last_used_at.isoformat() if p.last_used_at else None),
                    "created_at": p.created_at.isoformat(),
                }
                for p in profiles
            ],
            "total": total,
            "page": page,
            "size": size,
            "filters": {
                "active_only": active_only,
                "search": search,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profiles: {str(e)}",
        )


@router.get("/{profile_name}", response_model=LLMProfileResponse)
@handle_api_errors("Failed to get profile details")
async def get_profile_details(
    profile_name: str,
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
):
    """
    Get detailed information about a specific LLM profile.

    Returns the complete profile parameters, metadata, and usage statistics.
    """
    log_api_call("get_profile_details", user_id=current_user.id, profile_name=profile_name)

    profile = await profile_service.get_profile(profile_name)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{profile_name}' not found",
        )

    # Convert profile model to response schema
    response_data = {
        "name": profile.name,
        "title": profile.title,
        "description": profile.description,
        "model_name": settings.openai_chat_model,  # Use default model from settings
        "parameters": {
            "temperature": profile.temperature,
            "top_p": profile.top_p,
            "top_k": profile.top_k,
            "repeat_penalty": profile.repeat_penalty,
            "max_tokens": profile.max_tokens,
            "max_new_tokens": profile.max_new_tokens,
            "context_length": profile.context_length,
            "presence_penalty": profile.presence_penalty,
            "frequency_penalty": profile.frequency_penalty,
            "stop": profile.stop,
            "other_params": profile.other_params,
        },
        "is_default": profile.is_default,
        "is_active": profile.is_active,
        "usage_count": profile.usage_count,
        "last_used_at": profile.last_used_at,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }

    return LLMProfileResponse(**response_data)


@router.post("/{profile_name}/set-default", response_model=BaseResponse)
@handle_api_errors("Failed to set default profile")
async def set_default_profile(
    profile_name: str,
    current_user: User = Depends(get_current_superuser),
    profile_service: LLMProfileService = Depends(get_profile_service),
):
    """
    Set a profile as the default LLM parameter profile.

    Only available to superusers.
    """
    log_api_call("set_default_profile", user_id=current_user.id, profile_name=profile_name)

    try:
        success = await profile_service.set_default_profile(profile_name)

        if success:
            return BaseResponse(success=True, message=f"Profile '{profile_name}' set as default")
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{profile_name}' not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set default profile: {str(e)}",
        )


@router.get("/default/parameters", response_model=Dict[str, Any])
@handle_api_errors("Failed to get default profile parameters")
async def get_default_profile_parameters(
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
):
    """
    Get the parameters from the default LLM profile.

    Returns the parameters in OpenAI format ready for use in API calls.
    """
    log_api_call("get_default_profile_parameters", user_id=current_user.id)

    try:
        params = await profile_service.get_profile_for_openai()

        return {
            "success": True,
            "data": {
                "parameters": params,
                "profile_name": "default",
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get default profile parameters: {str(e)}",
        )


@router.get("/stats/", response_model=Dict[str, Any])
@handle_api_errors("Failed to get profile statistics")
async def get_profile_stats(
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
):
    """Get LLM profile usage statistics and analytics."""
    log_api_call("get_profile_stats", user_id=current_user.id)

    try:
        stats = await profile_service.get_profile_stats()

        return {
            "success": True,
            "data": stats,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile statistics: {str(e)}",
        )


@router.post("/validate", response_model=Dict[str, Any])
@handle_api_errors("Failed to validate parameters")
async def validate_parameters(
    parameters: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
):
    """
    Validate LLM parameters before creating or updating a profile.

    Returns validation results with any errors or warnings.
    """
    log_api_call("validate_parameters", user_id=current_user.id)

    try:
        errors = await profile_service.validate_parameters(**parameters)

        return {
            "success": len(errors) == 0,
            "data": {
                "valid": len(errors) == 0,
                "errors": errors,
                "parameters": parameters,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate parameters: {str(e)}",
        )
