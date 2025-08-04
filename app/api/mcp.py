"""MCP server and tool management API endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.common import (
    APIResponse,
    ErrorResponse,
    SuccessResponse,
)
from shared.schemas.mcp import (
    MCPListFiltersSchema,
    MCPServerCreateSchema,
    MCPServerSchema,
    MCPServerUpdateSchema,
    MCPStatsResponse,
    MCPToolsResponse,
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
):
    """List all registered MCP servers with optional filtering."""
    log_api_call("list_mcp_servers", user_id=current_user.id)

    filters = MCPListFiltersSchema(
        enabled_only=enabled_only, connected_only=connected_only
    )

    servers = await mcp_service.list_servers(filters)

    return APIResponse[List[MCPServerSchema]](
        success=True,
        message=f"Retrieved {len(servers)} MCP servers",
        data=servers,
    )


@router.post("/servers", response_model=APIResponse[MCPServerSchema])
@handle_api_errors("Failed to create MCP server")
async def create_server(
    server_data: MCPServerCreateSchema,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """Create a new MCP server with comprehensive configuration."""
    log_api_call(
        "create_mcp_server", user_id=current_user.id, server_name=server_data.name
    )

    server = await mcp_service.create_server(server_data)

    return APIResponse[MCPServerSchema](
        success=True,
        message=f"MCP server '{server_data.name}' created successfully",
        data=server,
    )


@router.get("/servers/byname/{server_name}", response_model=APIResponse[MCPServerSchema])
@handle_api_errors("Failed to get MCP server")
async def get_server(
    server_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """Get detailed information about a specific MCP server by name."""
    log_api_call("get_mcp_server", user_id=current_user.id, server_name=server_name)

    server = await mcp_service.get_server(server_name)

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server '{server_name}' not found",
        )

    return APIResponse[MCPServerSchema](
        success=True,
        message=f"Retrieved MCP server '{server_name}'",
        data=server,
    )


@router.patch("/servers/byname/{server_name}", response_model=APIResponse[MCPServerSchema])
@handle_api_errors("Failed to update MCP server")
async def update_server(
    server_name: str,
    server_update: MCPServerUpdateSchema,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """Update configuration settings for an existing MCP server."""
    log_api_call("update_mcp_server", user_id=current_user.id, server_name=server_name)

    server = await mcp_service.update_server(server_name, server_update)

    return APIResponse[MCPServerSchema](
        success=True,
        message=f"MCP server '{server_name}' updated successfully",
        data=server,
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

    if deleted:
        return SuccessResponse.create(
            message=f"MCP server '{server_name}' deleted successfully"
        )
    else:
        return ErrorResponse.create(
            error_code="MCP_SERVER_NOT_FOUND",
            message=f"MCP server '{server_name}' not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


@router.get("/tools", response_model=MCPToolsResponse)
@handle_api_errors("Failed to list MCP tools")
async def list_tools(
    server: Optional[str] = Query(None, description="Filter by server name"),
    enabled_only: bool = Query(False, description="Show only enabled tools"),
    detailed: bool = Query(False, description="Include detailed information"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """List all available MCP tools with filtering and detailed information."""
    log_api_call("list_mcp_tools", user_id=current_user.id)

    mcp_service = MCPService(db)
    filters = MCPListFiltersSchema(enabled_only=enabled_only)
    if server:
        filters.server_name = server
    tools = await mcp_service.list_tools(filters)

    return MCPToolsResponse(
        success=True,
        message=f"Retrieved {len(tools)} MCP tools",
        data=tools,
    )


@router.patch("/tools/byname/{tool_name}/enable", response_model=APIResponse)
@handle_api_errors("Failed to enable MCP tool")
async def enable_tool(
    tool_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """Enable a specific MCP tool for system-wide availability."""
    log_api_call("enable_mcp_tool", user_id=current_user.id, tool_name=tool_name)

    success = await mcp_service.enable_tool(tool_name)

    if success:
        return SuccessResponse.create(
            message=f"MCP tool '{tool_name}' enabled successfully"
        )
    else:
        return ErrorResponse.create(
            error_code="MCP_TOOL_NOT_FOUND",
            message=f"MCP tool '{tool_name}' not found",
            status_code=status.HTTP_404_NOT_FOUND
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

    if success:
        return SuccessResponse.create(
            message=f"MCP tool '{tool_name}' disabled successfully"
        )
    else:
        return ErrorResponse.create(
            error_code="MCP_TOOL_NOT_FOUND",
            message=f"MCP tool '{tool_name}' not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


@router.get("/stats", response_model=APIResponse)
@handle_api_errors("Failed to get MCP statistics")
async def get_mcp_stats(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """Get comprehensive MCP usage statistics and performance analytics."""
    log_api_call("get_mcp_stats", user_id=current_user.id)

    stats = await mcp_service.get_tool_stats()

    return APIResponse(
        success=True,
        message="MCP statistics retrieved successfully",
        data=stats,
    )


@router.get("/tools/byname/{tool_name}", response_model=MCPToolsResponse)
@handle_api_errors("Failed to get MCP tool details")
async def get_tool_details(
    tool_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information about a specific MCP tool by name.

    Retrieves comprehensive details about an MCP tool including its schema,
    current status, usage statistics, and configuration parameters.
    """
    log_api_call("get_mcp_tool_details", user_id=current_user.id)

    mcp_service = MCPService(db)
    tool = await mcp_service.get_tool_by_name(tool_name)

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found"
        )

    return MCPToolsResponse(
        success=True,
        message=f"Retrieved details for tool '{tool_name}'",
        data=[tool],
    )


@router.post("/tools/byname/{tool_name}/test", response_model=APIResponse)
@handle_api_errors("Failed to test MCP tool")
async def test_tool(
    tool_name: str,
    test_params: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Test execution of a specific MCP tool with optional parameters.

    Executes a test run of the specified tool to verify functionality,
    connectivity, and parameter validation.
    """
    log_api_call("test_mcp_tool", user_id=current_user.id)

    mcp_service = MCPService(db)

    # Test the tool execution
    try:
        await mcp_service.test_tool_execution(tool_name, test_params or {})
        return SuccessResponse.create(
            message=f"Tool '{tool_name}' test completed successfully"
        )
    except Exception:
        raise


@router.get("/servers/status", response_model=MCPStatsResponse)
@handle_api_errors("Failed to get MCP server status")
async def get_servers_status(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive status information for all MCP servers.

    Returns detailed status information including connectivity, health,
    and performance metrics for all registered MCP servers.
    """
    log_api_call("get_mcp_servers_status", user_id=current_user.id)

    mcp_service = MCPService(db)
    stats = await mcp_service.get_stats()

    return MCPStatsResponse(
        success=True,
        message="Retrieved MCP server status",
        data=stats,
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
