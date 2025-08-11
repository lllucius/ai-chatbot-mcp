"""MCP server and tool management API endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.common import APIResponse
from shared.schemas.mcp import (
    AdvancedSearchResponse,
    ConversationStatsResponse,
    DocumentStatsResponse,
    ProfileStatsResponse,
    PromptCategoriesResponse,
    PromptStatsResponse,
    QueueResponse,
    RegistryStatsResponse,
    SearchResponse,
    TaskMonitorResponse,
    TaskStatsResponse,
    TaskStatusResponse,
    WorkersResponse,
)

from ..database import get_db
from ..dependencies import get_current_superuser, get_mcp_service
from ..models.user import User
from ..services.mcp_service import MCPService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["mcp"])


@router.get("/servers", response_model=APIResponse[List[MCPServerSchema]])
@handle_api_errors("Failed to list MCP servers")
async def list_servers(
    enabled_only: bool = Query(False, description="Show only enabled servers"),
    connected_only: bool = Query(False, description="Show only connected servers"),
    detailed: bool = Query(False, description="Include detailed information"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
) -> APIResponse[List[MCPServerSchema]]:
    """List all registered MCP servers with optional filtering."""
    log_api_call("list_mcp_servers", user_id=current_user.id)

    filters = MCPListFiltersSchema(
        enabled_only=enabled_only, connected_only=connected_only
    )

    servers = await mcp_service.list_servers(filters)

    payload = []
    for server in servers:
        payload.append(MCPServerSchema.model_validate(server))

    return APIResponse[List[MCPServerSchema]](
        success=True,
        message=f"Retrieved {len(servers)} MCP servers",
        data=payload,
    )


@router.post("/servers", response_model=APIResponse[MCPServerSchema])
@handle_api_errors("Failed to create MCP server")
async def create_server(
    server_data: MCPServerCreateSchema,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
) -> APIResponse[MCPServerSchema]:
    """Create a new MCP server with comprehensive configuration."""
    log_api_call(
        "create_mcp_server", user_id=current_user.id, server_name=server_data.name
    )

    server = await mcp_service.create_server(server_data)
    payload = MCPServerSchema.model_validate(server)
    return APIResponse[MCPServerSchema](
        success=True,
        message=f"MCP server '{server_data.name}' created successfully",
        data=payload,
    )


@router.get(
    "/servers/byname/{server_name}", response_model=APIResponse[MCPServerSchema]
)
@handle_api_errors("Failed to get MCP server")
async def get_server(
    server_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
) -> APIResponse[MCPServerSchema]:
    """Get detailed information about a specific MCP server by name."""
    log_api_call("get_mcp_server", user_id=current_user.id, server_name=server_name)

    server = await mcp_service.get_server(server_name)

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server '{server_name}' not found",
        )

    payload = MCPServerSchema.model_validate(server)
    return APIResponse[MCPServerSchema](
        success=True,
        message=f"Retrieved MCP server '{server_name}'",
        data=payload,
    )


@router.patch(
    "/servers/byname/{server_name}", response_model=APIResponse[MCPServerSchema]
)
@handle_api_errors("Failed to update MCP server")
async def update_server(
    server_name: str,
    server_update: MCPServerUpdateSchema,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
) -> APIResponse[MCPServerSchema]:
    """Update configuration settings for an existing MCP server."""
    log_api_call("update_mcp_server", user_id=current_user.id, server_name=server_name)

    server = await mcp_service.update_server(server_name, server_update)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server '{server_name}' not found",
        )

    payload = MCPServerSchema.model_validate(server)
    return APIResponse[MCPServerSchema](
        success=True,
        message=f"MCP server '{server_name}' updated successfully",
        data=payload,
    )


@router.delete("/servers/byname/{server_name}", response_model=APIResponse)
@handle_api_errors("Failed to delete MCP server")
async def delete_server(
    server_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """Delete an MCP server and clean up associated resources."""
    log_api_call("delete_mcp_server", user_id=current_user.id, server_name=server_name)

    deleted = await mcp_service.delete_server(server_name)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server '{server_name}' not found",
        )
    return APIResponse(
        success=True,
        message=f"MCP server '{server_name}' deleted successfully",
    )


@router.get("/tools", response_model=APIResponse[List[MCPToolResponse]])
@handle_api_errors("Failed to list MCP tools")
async def list_tools(
    server: Optional[str] = Query(None, description="Filter by server name"),
    enabled_only: bool = Query(False, description="Show only enabled tools"),
    detailed: bool = Query(False, description="Include detailed information"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[MCPToolResponse]]:
    """List all available MCP tools with filtering and detailed information."""
    log_api_call("list_mcp_tools", user_id=current_user.id)

    mcp_service = MCPService(db)
    filters = MCPListFiltersSchema(enabled_only=enabled_only)
    if server:
        filters.server_name = server
    tools = await mcp_service.list_tools(filters)

    payload = []
    for tool in tools:
        payload.append(MCPToolResponse.model_validate(tool))

    return APIResponse[List[MCPToolResponse]](
        success=True,
        message=f"Retrieved {len(tools)} MCP tools",
        data=payload,
    )


@router.patch("/tools/byname/{tool_name}/enable", response_model=APIResponse)
@handle_api_errors("Failed to enable MCP tool")
async def enable_tool(
    tool_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
) -> APIResponse:
    """Enable a specific MCP tool for system-wide availability."""
    log_api_call("enable_mcp_tool", user_id=current_user.id, tool_name=tool_name)

    success = await mcp_service.enable_tool(tool_name)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP tool '{tool_name}' not found",
        )

    return APIResponse(
        success=True, message=f"MCP tool '{tool_name}' enabled successfully"
    )


@router.patch("/tools/byname/{tool_name}/disable", response_model=APIResponse)
@handle_api_errors("Failed to disable MCP tool")
async def disable_tool(
    tool_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """Disable a specific MCP tool to remove it from system availability."""
    log_api_call("disable_mcp_tool", user_id=current_user.id, tool_name=tool_name)

    success = await mcp_service.disable_tool(tool_name)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP tool '{tool_name}' not found",
        )

    return APIResponse(
        success=True, message=f"MCP tool '{tool_name}' disabled successfully"
    )


@router.get("/stats", response_model=APIResponse[MCPToolUsageStatsSchema])
@handle_api_errors("Failed to get MCP statistics")
async def get_mcp_stats(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
) -> APIResponse[MCPToolUsageStatsSchema]:
    """Get comprehensive MCP usage statistics and performance analytics."""
    log_api_call("get_mcp_stats", user_id=current_user.id)

    stats = await mcp_service.get_tool_stats()

    return APIResponse[MCPToolUsageStatsSchema](
        success=True,
        message="MCP statistics retrieved successfully",
        data=stats,
    )


@router.get("/tools/byname/{tool_name}", response_model=APIResponse[MCPToolsResponse])
@handle_api_errors("Failed to get MCP tool details")
async def get_tool_details(
    tool_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[MCPToolsResponse]:
    """Get detailed information about a specific MCP tool by name.

    Retrieves comprehensive details about an MCP tool including its schema,
    current status, usage statistics, and configuration parameters.
    """
    log_api_call("get_mcp_tool_details", user_id=current_user.id)

    mcp_service = MCPService(db)
    tool = await mcp_service.get_tool(tool_name)

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found",
        )

    payload = MCPToolsResponse.model_validate(tool)
    return APIResponse[MCPToolsResponse](
        success=True,
        message=f"Retrieved details for tool '{tool_name}'",
        data=payload,
    )


@router.post("/tools/byname/{tool_name}/test", response_model=APIResponse)
@handle_api_errors("Failed to test MCP tool")
async def test_tool(
    tool_name: str,
    test_params: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Test execution of a specific MCP tool with optional parameters.

    Executes a test run of the specified tool to verify functionality,
    connectivity, and parameter validation.
    """
    log_api_call("test_mcp_tool", user_id=current_user.id)

    mcp_service = MCPService(db)

    await mcp_service.test_tool_execution(tool_name, test_params or {})

    return APIResponse(
        success=True,
        message=f"Tool '{tool_name}' test completed successfully",
    )


@router.post("/refresh", response_model=APIResponse)
@handle_api_errors("Failed to refresh MCP")
async def refresh_mcp(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """Refresh MCP server connections and perform comprehensive tool discovery."""
    log_api_call("refresh_mcp", user_id=current_user.id)

    await mcp_service.refresh_from_registry()

    return APIResponse(
        success=True,
        message="MCP refresh completed successfully",
    )
