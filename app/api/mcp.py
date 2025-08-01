"""
MCP management API endpoints.

This module provides REST API endpoints for managing MCP servers and tools,
providing the backend for the API-based CLI MCP commands.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_superuser, get_mcp_service
from ..models.user import User
from ..schemas.common import BaseResponse
from ..schemas.mcp import (MCPListFiltersSchema, MCPServerCreateSchema,
                           MCPServerListResponse, MCPServerUpdateSchema, MCPToolsResponse)
from ..services.mcp_service import MCPService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["mcp"])


@router.get("/servers", response_model=MCPServerListResponse)
@handle_api_errors("Failed to list MCP servers")
async def list_servers(
    enabled_only: bool = Query(False, description="Show only enabled servers"),
    connected_only: bool = Query(False, description="Show only connected servers"),
    detailed: bool = Query(False, description="Include detailed information"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """
    List all registered MCP servers with optional filtering.

    Returns a list of MCP servers configured in the system with their
    connection status, configuration details, and metadata. Supports
    filtering by enabled/connected status and includes detailed information
    when requested.

    Args:
        enabled_only: If True, returns only enabled servers
        connected_only: If True, returns only currently connected servers
        detailed: If True, includes additional server metadata
        current_user: Current authenticated superuser
        db: Database session
        mcp_service: MCP service instance

    Returns:
        MCPServerListResponse: List of servers with metadata

    Raises:
        HTTP 403: If user is not a superuser
        HTTP 500: If server listing fails

    Note:
        This endpoint requires superuser privileges as it exposes
        system configuration details.
    """
    log_api_call("list_mcp_servers", user_id=current_user.id)

    filters = MCPListFiltersSchema(
        enabled_only=enabled_only, connected_only=connected_only
    )

    servers = await mcp_service.list_servers(filters)

    return {
        "success": True,
        "message": f"Retrieved {len(servers)} MCP servers",
        "data": servers,
    }


@router.post("/servers", response_model=MCPServerListResponse)
@handle_api_errors("Failed to create MCP server")
async def create_server(
    server_data: MCPServerCreateSchema,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """Create a new MCP server."""
    log_api_call(
        "create_mcp_server", user_id=current_user.id, server_name=server_data.name
    )

    server = await mcp_service.create_server(server_data)

    return {
        "success": True,
        "message": f"MCP server '{server_data.name}' created successfully",
        "data": server,
    }


@router.get("/servers/byname/{server_name}", response_model=MCPServerListResponse)
@handle_api_errors("Failed to get MCP server")
async def get_server(
    server_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """Get details of a specific MCP server."""
    log_api_call("get_mcp_server", user_id=current_user.id, server_name=server_name)

    server = await mcp_service.get_server(server_name)

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server '{server_name}' not found",
        )

    return {
        "success": True,
        "message": f"Retrieved MCP server '{server_name}'",
        "data": server,
    }


@router.patch("/servers/byname/{server_name}", response_model=MCPServerListResponse)
@handle_api_errors("Failed to update MCP server")
async def update_server(
    server_name: str,
    server_update: MCPServerUpdateSchema,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """Update an MCP server."""
    log_api_call("update_mcp_server", user_id=current_user.id, server_name=server_name)

    server = await mcp_service.update_server(server_name, server_update)

    return {
        "success": True,
        "message": f"MCP server '{server_name}' updated successfully",
        "data": server,
    }


@router.delete("/servers/byname/{server_name}", response_model=BaseResponse)
@handle_api_errors("Failed to delete MCP server")
async def delete_server(
    server_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """Delete an MCP server."""
    log_api_call("delete_mcp_server", user_id=current_user.id, server_name=server_name)

    deleted = await mcp_service.delete_server(server_name)

    if deleted:
        return BaseResponse(
            success=True, message=f"MCP server '{server_name}' deleted successfully"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server '{server_name}' not found",
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
    """List all available MCP tools."""
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


@router.patch("/tools/byname/{tool_name}/enable", response_model=BaseResponse)
@handle_api_errors("Failed to enable MCP tool")
async def enable_tool(
    tool_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """Enable an MCP tool."""
    log_api_call("enable_mcp_tool", user_id=current_user.id, tool_name=tool_name)

    success = await mcp_service.enable_tool(tool_name)

    if success:
        return BaseResponse(
            success=True, message=f"MCP tool '{tool_name}' enabled successfully"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP tool '{tool_name}' not found",
        )


@router.patch("/tools/byname/{tool_name}/disable", response_model=BaseResponse)
@handle_api_errors("Failed to disable MCP tool")
async def disable_tool(
    tool_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """Disable an MCP tool."""
    log_api_call("disable_mcp_tool", user_id=current_user.id, tool_name=tool_name)

    success = await mcp_service.disable_tool(tool_name)

    if success:
        return BaseResponse(
            success=True, message=f"MCP tool '{tool_name}' disabled successfully"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP tool '{tool_name}' not found",
        )


@router.get("/stats", response_model=MCPStatsResponse)
@handle_api_errors("Failed to get MCP statistics")
async def get_mcp_stats(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """Get MCP usage statistics."""
    log_api_call("get_mcp_stats", user_id=current_user.id)

    stats = await mcp_service.get_tool_stats()

    return {
        "success": True,
        "message": "MCP statistics retrieved successfully",
        "data": [s.model_dump() for s in stats],
    }


@router.post("/refresh", response_model=MCPStatsResponse)
@handle_api_errors("Failed to refresh MCP")
async def refresh_mcp(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """Refresh MCP server connections and tool discovery."""
    log_api_call("refresh_mcp", user_id=current_user.id)

    await mcp_service.refresh_from_registry()

    return {
        "success": True,
        "message": "MCP refresh completed successfully",
        "data": {},
    }
