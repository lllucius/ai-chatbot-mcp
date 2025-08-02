"""
LLM Profile registry API endpoints with comprehensive profile management.

This module provides endpoints for managing LLM parameter profiles including
creation, retrieval, updates, statistics, and parameter validation. It implements
role-based access control for administrative operations and provides comprehensive
profile configuration capabilities for Large Language Model integration.

Key Features:
- LLM profile CRUD operations with validation
- Parameter management and OpenAI compatibility
- Default profile configuration and management
- Usage statistics and analytics tracking
- Parameter validation and error reporting
- Profile search and filtering capabilities

Profile Management:
- Create custom parameter profiles for different use cases
- Set default profiles for system-wide configuration
- Validate parameters before profile creation
- Track usage statistics and performance metrics
- Manage profile lifecycle (active/inactive states)

Security Features:
- Role-based access control for administrative operations
- Input validation and parameter sanitization
- Audit logging for profile management activities
- Protection against unauthorized profile modifications
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user
from ..models.user import User
from ..schemas.admin import (
    ProfileParametersResponse,
    ProfileStatsResponse,
    ProfileValidationResponse,
)
from ..schemas.common import BaseResponse
from ..schemas.llm_profile import (
    LLMProfileCreate,
    LLMProfileListResponse,
    LLMProfileResponse,
)
from ..services.llm_profile_service import LLMProfileService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["profiles"])


async def get_profile_service(db: AsyncSession = Depends(get_db)) -> LLMProfileService:
    """
    Get LLM profile service instance with database session.

    Creates and returns an LLMProfileService instance configured with the provided
    database session for profile management operations including CRUD operations,
    parameter validation, and statistics tracking.

    Args:
        db: Database session dependency for service initialization

    Returns:
        LLMProfileService: Configured service instance for LLM profile operations

    Note:
        This is a dependency function used by FastAPI's dependency injection system.
    """
    return LLMProfileService(db)


@router.post("/", response_model=LLMProfileResponse)
@handle_api_errors("Failed to create profile")
async def create_profile(
    request: LLMProfileCreate,
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> LLMProfileResponse:
    """
    Create a new LLM parameter profile with validation.

    Creates a new LLM parameter profile with the specified configuration including
    temperature, top_p, max_tokens, and other model-specific parameters. The profile
    can be used to customize LLM behavior for different conversation contexts and
    use cases.

    Args:
        request: Profile creation data including name, parameters, and metadata
        current_user: Current authenticated user creating the profile
        profile_service: Injected LLM profile service instance

    Returns:
        LLMProfileResponse: Created profile with all parameters and metadata

    Raises:
        HTTP 400: If profile name already exists or parameters are invalid
        HTTP 422: If request data validation fails
        HTTP 500: If profile creation process fails

    Profile Parameters:
        - temperature: Controls randomness in model responses (0.0-2.0)
        - top_p: Nucleus sampling parameter for token selection
        - max_tokens: Maximum number of tokens in model response
        - presence_penalty: Penalty for token presence in context
        - frequency_penalty: Penalty for token frequency in response
        - Custom parameters for advanced model configuration

    Example:
        POST /api/v1/profiles/
        {
            "name": "creative-writing",
            "title": "Creative Writing Profile",
            "description": "High creativity for creative writing tasks",
            "temperature": 1.2,
            "top_p": 0.9,
            "max_tokens": 2000
        }
    """
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
    """
    List all LLM parameter profiles with filtering and pagination.

    Returns a paginated list of LLM parameter profiles with optional filtering
    by active status and search terms. Includes comprehensive profile information
    including parameters, usage statistics, and metadata for each profile.

    Args:
        active_only: If True, returns only active profiles (default: True)
        search: Optional search term to filter profiles by name/description
        page: Page number for pagination (starts at 1)
        size: Number of profiles per page (1-100, default: 20)
        current_user: Current authenticated user requesting the list
        profile_service: Injected LLM profile service instance

    Returns:
        LLMProfileListResponse: Paginated profile list including:
            - profiles: List of profile objects with full metadata
            - total: Total number of profiles matching filters
            - page: Current page number
            - size: Items per page
            - pages: Total number of pages

    Filtering:
        - Active status filtering for operational profiles only
        - Text search across profile names and descriptions
        - Pagination for large profile collections

    Profile Information:
        - Complete parameter configuration
        - Usage statistics and performance metrics
        - Metadata including creation and modification dates
        - Default status and activation state

    Example:
        GET /api/v1/profiles/?active_only=true&search=creative&page=1&size=10
    """
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
    """
    Get detailed information about a specific LLM profile by name.

    Returns complete profile configuration including all parameters, metadata,
    usage statistics, and current status. Provides comprehensive information
    needed for profile management and LLM integration.

    Args:
        profile_name: Name of the profile to retrieve
        current_user: Current authenticated user requesting profile details
        profile_service: Injected LLM profile service instance

    Returns:
        LLMProfileResponse: Complete profile information including:
            - name: Profile identifier and display name
            - parameters: Full LLM parameter configuration
            - metadata: Creation, modification, and usage information
            - status: Active state and default designation
            - statistics: Usage count and last access time

    Raises:
        HTTP 404: If profile with specified name is not found
        HTTP 500: If profile retrieval process fails

    Profile Details:
        - Complete parameter set with OpenAI-compatible format
        - Usage tracking and performance statistics
        - Administrative metadata and status information
        - Parameter validation and constraint information

    Example:
        GET /api/v1/profiles/byname/creative-writing
    """
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


@router.put("/byname/{profile_name}", response_model=LLMProfileResponse)
@handle_api_errors("Failed to update profile")
async def update_profile(
    profile_name: str,
    profile_data: Dict[str, Any],
    current_user: User = Depends(get_current_superuser),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> LLMProfileResponse:
    """
    Update an existing LLM profile with new parameters or metadata.
    """
    log_api_call("update_llm_profile", user_id=current_user.id, profile_name=profile_name)
    
    updated_profile = await profile_service.update_profile(profile_name, profile_data)
    
    response_data = {
        "name": updated_profile.name,
        "title": updated_profile.title,
        "description": updated_profile.description,
        "model_name": updated_profile.model_name,
        "parameters": updated_profile.parameters,
        "is_default": updated_profile.is_default,
        "is_active": updated_profile.is_active,
        "usage_count": updated_profile.usage_count,
        "last_used_at": updated_profile.last_used_at,
        "created_at": updated_profile.created_at,
        "updated_at": updated_profile.updated_at,
    }
    return LLMProfileResponse(**response_data)


@router.delete("/byname/{profile_name}", response_model=BaseResponse)
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
    
    return BaseResponse(
        success=True,
        message=f"Profile '{profile_name}' deleted successfully"
    )


@router.post("/byname/{profile_name}/set-default", response_model=BaseResponse)
@handle_api_errors("Failed to set default profile")
async def set_default_profile(
    profile_name: str,
    current_user: User = Depends(get_current_superuser),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> BaseResponse:
    """
    Set a profile as the default LLM parameter profile for the system.

    Designates the specified profile as the system default, which will be used
    for all LLM operations unless explicitly overridden. Only one profile can
    be set as default at a time, and this operation requires superuser privileges.

    Args:
        profile_name: Name of the profile to set as default
        current_user: Current authenticated superuser performing the operation
        profile_service: Injected LLM profile service instance

    Returns:
        BaseResponse: Success confirmation with operation details

    Raises:
        HTTP 403: If user is not a superuser
        HTTP 404: If profile with specified name is not found
        HTTP 500: If default setting operation fails

    Security Notes:
        - Requires superuser privileges for system-wide configuration
        - Previous default profile is automatically unset
        - Operation is logged for administrative audit trail
        - System immediately uses new default for subsequent operations

    Impact:
        - All new conversations use the new default profile
        - Existing conversations retain their original profile settings
        - API clients receive new default parameters automatically

    Example:
        POST /api/v1/profiles/byname/balanced/set-default
    """
    log_api_call(
        "set_default_profile", user_id=current_user.id, profile_name=profile_name
    )
    success = await profile_service.set_default_profile(profile_name)
    if success:
        return BaseResponse(
            success=True, message=f"Profile '{profile_name}' set as default"
        )
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{profile_name}' not found",
        )


@router.get("/default/parameters", response_model=ProfileParametersResponse)
@handle_api_errors("Failed to get default profile parameters")
async def get_default_profile_parameters(
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> Dict[str, Any]:
    """
    Get parameters from the default LLM profile in OpenAI-compatible format.

    Returns the current default profile's parameters formatted for direct use
    with OpenAI API calls. This endpoint provides the system's current LLM
    configuration for client applications and integration purposes.

    Args:
        current_user: Current authenticated user requesting default parameters
        profile_service: Injected LLM profile service instance

    Returns:
        ProfileParametersResponse: Default profile parameters including:
            - parameters: OpenAI-compatible parameter dictionary
            - profile_name: Name of the current default profile
            - metadata: Additional configuration information

    Parameter Format:
        - OpenAI API-compatible parameter names and values
        - Properly formatted for direct API integration
        - Includes all relevant LLM configuration options
        - Ready for use in chat completion requests

    Use Cases:
        - Client application configuration
        - API integration setup
        - Default behavior verification
        - System configuration validation

    Example:
        GET /api/v1/profiles/default/parameters
        Response: {
            "parameters": {
                "temperature": 0.7,
                "top_p": 1.0,
                "max_tokens": 1000,
                "presence_penalty": 0.0,
                "frequency_penalty": 0.0
            },
            "profile_name": "default"
        }
    """
    log_api_call("get_default_profile_parameters", user_id=current_user.id)
    params = await profile_service.get_profile_for_openai()
    return {
        "success": True,
        "data": {
            "parameters": params,
            "profile_name": "default",
        },
    }


@router.get("/stats", response_model=ProfileStatsResponse)
@handle_api_errors("Failed to get profile statistics")
async def get_profile_stats(
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> Dict[str, Any]:
    """
    Get comprehensive LLM profile usage statistics and analytics.

    Returns detailed analytics about LLM profile usage including popularity
    metrics, performance statistics, and usage patterns across the system.
    Provides insights for profile optimization and system management.

    Args:
        current_user: Current authenticated user requesting statistics
        profile_service: Injected LLM profile service instance

    Returns:
        ProfileStatsResponse: Comprehensive profile statistics including:
            - total_profiles: Number of profiles in the system
            - active_profiles: Number of currently active profiles
            - usage_metrics: Profile usage frequency and patterns
            - performance_data: Response time and success rate statistics
            - popular_profiles: Most frequently used profiles
            - recent_activity: Recent profile usage trends

    Analytics Data:
        - Profile popularity rankings
        - Usage frequency distributions
        - Performance benchmarks
        - Trend analysis over time
        - Error rates and success metrics

    Use Cases:
        - System performance monitoring
        - Profile optimization decisions
        - Usage pattern analysis
        - Capacity planning and scaling
        - Administrative reporting

    Example:
        GET /api/v1/profiles/stats
    """
    log_api_call("get_profile_stats", user_id=current_user.id)
    stats = await profile_service.get_profile_stats()
    return {
        "success": True,
        "data": stats,
    }


@router.post("/validate", response_model=ProfileValidationResponse)
@handle_api_errors("Failed to validate parameters")
async def validate_parameters(
    parameters: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    profile_service: LLMProfileService = Depends(get_profile_service),
) -> Dict[str, Any]:
    """
    Validate LLM parameters before profile creation or update.

    Validates the provided LLM parameters against system constraints and
    compatibility requirements. Returns detailed validation results including
    any errors, warnings, or recommendations for parameter optimization.

    Args:
        parameters: Dictionary of LLM parameters to validate
        current_user: Current authenticated user requesting validation
        profile_service: Injected LLM profile service instance

    Returns:
        ProfileValidationResponse: Validation results including:
            - valid: Boolean indicating overall validation status
            - errors: List of validation errors found
            - warnings: List of potential issues or recommendations
            - parameters: Echo of validated parameters with corrections
            - suggestions: Recommended parameter adjustments

    Validation Checks:
        - Parameter type and format validation
        - Value range and constraint verification
        - OpenAI API compatibility checking
        - Performance impact assessment
        - Best practice recommendations

    Parameter Constraints:
        - temperature: 0.0 to 2.0 (controls response randomness)
        - top_p: 0.0 to 1.0 (nucleus sampling threshold)
        - max_tokens: 1 to model limit (response length control)
        - penalties: -2.0 to 2.0 (presence/frequency penalties)
        - Custom parameter format validation

    Example:
        POST /api/v1/profiles/validate
        {
            "temperature": 0.8,
            "top_p": 0.9,
            "max_tokens": 1500,
            "presence_penalty": 0.1
        }
    """
    log_api_call("validate_parameters", user_id=current_user.id)
    errors = await profile_service.validate_parameters(**parameters)
    return {
        "success": len(errors) == 0,
        "data": {
            "valid": len(errors) == 0,
            "errors": errors,
            "parameters": parameters,
        },
    }
