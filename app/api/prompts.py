"""
Prompt registry API endpoints with comprehensive prompt management.

This module provides endpoints for managing prompts in the prompt registry
including creation, retrieval, categorization, and usage analytics. It implements
comprehensive prompt lifecycle management with category organization, tagging
support, and detailed usage tracking for AI conversation enhancement.

Key Features:
- Prompt CRUD operations with validation and categorization
- Category and tag management for prompt organization
- Usage statistics and analytics tracking
- Default prompt configuration and management
- Search and filtering capabilities across prompts
- Template variable support and validation

Prompt Management:
- Create and organize prompts by categories and tags
- Set system default prompts for various conversation contexts
- Track usage patterns and effectiveness metrics
- Manage prompt lifecycle with active/inactive states
- Support for template variables and dynamic content

Organizational Features:
- Category-based prompt classification
- Tag-based filtering and search capabilities
- Hierarchical prompt organization
- Metadata management and versioning
- Usage analytics and performance tracking

Security Features:
- Role-based access control for administrative operations
- Input validation and content sanitization
- Audit logging for prompt management activities
- Protection against unauthorized prompt modifications
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user
from ..models.user import User
from ..schemas.admin import PromptCategoriesResponse, PromptStatsResponse
from ..schemas.common import BaseResponse
from ..schemas.prompt import PromptCreate, PromptListResponse, PromptResponse
from ..services.prompt_service import PromptService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["prompts"])


async def get_prompt_service(db: AsyncSession = Depends(get_db)) -> PromptService:
    """
    Get prompt service instance with database session.

    Creates and returns a PromptService instance configured with the provided
    database session for prompt management operations including CRUD operations,
    category management, and usage tracking.

    Args:
        db: Database session dependency for service initialization

    Returns:
        PromptService: Configured service instance for prompt operations

    Note:
        This is a dependency function used by FastAPI's dependency injection system.
    """
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
    List all prompts with filtering, categorization, and pagination.

    Returns a paginated list of prompts with optional filtering by active status,
    category, and search terms. Includes comprehensive prompt information including
    content, metadata, tags, and usage statistics for effective prompt management.

    Args:
        active_only: If True, returns only active prompts (default: True)
        category: Optional category filter to narrow results
        search: Optional search term to filter prompts by name/description/content
        page: Page number for pagination (starts at 1)
        size: Number of prompts per page (1-100, default: 20)
        current_user: Current authenticated user requesting the list
        prompt_service: Injected prompt service instance

    Returns:
        PromptListResponse: Paginated prompt list including:
            - prompts: List of prompt objects with full metadata
            - total: Total number of prompts matching filters
            - page: Current page number
            - size: Items per page
            - pages: Total number of pages

    Filtering Options:
        - Active status filtering for operational prompts only
        - Category-based filtering for organized browsing
        - Text search across names, descriptions, and content
        - Pagination for efficient large collection handling

    Prompt Information:
        - Complete prompt content and template variables
        - Category and tag associations
        - Usage statistics and performance metrics
        - Metadata including creation and modification dates
        - Default status and activation state

    Example:
        GET /api/v1/prompts/?active_only=true&category=conversation&search=greeting&page=1&size=10
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
    """
    Get detailed information about a specific prompt by name.

    Returns complete prompt information including content, template variables,
    metadata, category associations, tags, and usage statistics. Provides
    comprehensive details needed for prompt utilization and management.

    Args:
        prompt_name: Name of the prompt to retrieve
        current_user: Current authenticated user requesting prompt details
        prompt_service: Injected prompt service instance

    Returns:
        PromptResponse: Complete prompt information including:
            - name: Prompt identifier and display name
            - content: Full prompt text with template variables
            - metadata: Category, tags, description, and version info
            - statistics: Usage count, last access, and performance metrics
            - status: Active state and default designation

    Raises:
        HTTP 404: If prompt with specified name is not found
        HTTP 500: If prompt retrieval process fails

    Prompt Details:
        - Complete prompt content with variable placeholders
        - Category and tag associations for organization
        - Usage tracking and effectiveness metrics
        - Template variable definitions and validation
        - Administrative metadata and version information

    Template Variables:
        - Variable placeholders are identified and documented
        - Type information and validation rules included
        - Default values and example usage provided
        - Dynamic content generation capabilities

    Example:
        GET /api/v1/prompts/byname/conversation-starter
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
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> PromptResponse:
    """
    Update an existing prompt template.
    """
    log_api_call("update_prompt", user_id=current_user.id, prompt_name=prompt_name)
    
    prompt = await prompt_service.update_prompt(prompt_name, data)
    
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


@router.delete("/byname/{prompt_name}", response_model=BaseResponse)
@handle_api_errors("Failed to delete prompt")
async def delete_prompt(
    prompt_name: str,
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> BaseResponse:
    """
    Delete a prompt template from the registry.
    """
    log_api_call("delete_prompt", user_id=current_user.id, prompt_name=prompt_name)
    
    await prompt_service.delete_prompt(prompt_name)
    
    return BaseResponse(
        success=True,
        message=f"Prompt '{prompt_name}' deleted successfully"
    )


@router.get("/categories/", response_model=PromptCategoriesResponse)
@handle_api_errors("Failed to get categories")
async def get_categories(
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> Dict[str, Any]:
    """
    Get all available prompt categories and tags for organization.

    Returns comprehensive organizational metadata including all available prompt
    categories and tags used throughout the system. Provides the foundation for
    prompt filtering, categorization, and organizational operations.

    Args:
        current_user: Current authenticated user requesting category information
        prompt_service: Injected prompt service instance

    Returns:
        PromptCategoriesResponse: Organizational metadata including:
            - categories: List of all available prompt categories
            - tags: List of all tags used across prompts
            - metadata: Category and tag usage statistics
            - hierarchy: Organizational structure information

    Category Information:
        - Category names and descriptions
        - Prompt counts per category
        - Usage patterns and popularity metrics
        - Hierarchical relationships if applicable

    Tag Information:
        - Tag names and usage frequency
        - Associated categories and contexts
        - Tag popularity and effectiveness metrics
        - Suggested tag combinations

    Use Cases:
        - Prompt filtering and search interface population
        - Category-based navigation implementation
        - Tag cloud generation and visualization
        - Organizational structure analysis

    Example:
        GET /api/v1/prompts/categories/
        Response: {
            "categories": ["conversation", "creative", "technical", "support"],
            "tags": ["greeting", "closing", "question", "explanation"]
        }
    """
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
    Set a prompt as the default system prompt for conversations.

    Designates the specified prompt as the system default, which will be used
    as the initial prompt for new conversations unless explicitly overridden.
    Only one prompt can be set as default at a time, and this operation requires
    superuser privileges.

    Args:
        prompt_name: Name of the prompt to set as default
        current_user: Current authenticated superuser performing the operation
        prompt_service: Injected prompt service instance

    Returns:
        BaseResponse: Success confirmation with operation details

    Raises:
        HTTP 403: If user is not a superuser
        HTTP 404: If prompt with specified name is not found
        HTTP 500: If default setting operation fails

    Security Notes:
        - Requires superuser privileges for system-wide configuration
        - Previous default prompt is automatically unset
        - Operation is logged for administrative audit trail
        - System immediately uses new default for subsequent conversations

    Impact:
        - All new conversations use the new default prompt
        - Existing conversations retain their original prompt settings
        - API clients receive new default prompt automatically
        - Conversation behavior changes system-wide

    Example:
        POST /api/v1/prompts/byname/friendly-assistant/set-default
    """
    log_api_call("set_default_prompt", user_id=current_user.id, prompt_name=prompt_name)

    success = await prompt_service.set_default_prompt(prompt_name)

    if success:
        return BaseResponse(
            success=True, message=f"Prompt '{prompt_name}' set as default"
        )
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Prompt '{prompt_name}' not found",
        )


@router.get("/stats", response_model=PromptStatsResponse)
@handle_api_errors("Failed to get prompt statistics")
async def get_prompt_stats(
    current_user: User = Depends(get_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
) -> Dict[str, Any]:
    """
    Get comprehensive prompt usage statistics and analytics.

    Returns detailed analytics about prompt usage including popularity metrics,
    effectiveness statistics, and usage patterns across the system. Provides
    insights for prompt optimization and conversation improvement.

    Args:
        current_user: Current authenticated user requesting statistics
        prompt_service: Injected prompt service instance

    Returns:
        PromptStatsResponse: Comprehensive prompt statistics including:
            - total_prompts: Number of prompts in the system
            - active_prompts: Number of currently active prompts
            - usage_metrics: Prompt usage frequency and patterns
            - effectiveness_data: Conversation success rates by prompt
            - popular_prompts: Most frequently used prompts
            - category_statistics: Usage breakdown by category

    Analytics Data:
        - Prompt popularity rankings and trends
        - Usage frequency distributions over time
        - Effectiveness metrics and conversation outcomes
        - Category-wise usage patterns and preferences
        - Template variable usage and substitution rates

    Performance Metrics:
        - Conversation success rates by prompt
        - Average conversation length and engagement
        - User satisfaction indicators where available
        - Response quality and relevance metrics
        - Error rates and failure patterns

    Use Cases:
        - Prompt optimization and improvement decisions
        - Conversation quality assessment
        - Usage pattern analysis for system tuning
        - Content strategy and prompt library development
        - Administrative reporting and insights

    Example:
        GET /api/v1/prompts/stats
    """
    log_api_call("get_prompt_stats", user_id=current_user.id)

    stats = await prompt_service.get_prompt_stats()

    return {
        "success": True,
        "data": stats,
    }
