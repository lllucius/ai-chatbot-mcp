"""
MCP management API endpoints.

This module provides REST API endpoints for managing MCP servers and tools,
providing the backend for the API-based CLI MCP commands.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_superuser
from ..models.user import User
from ..schemas.common import BaseResponse
from ..schemas.mcp import (MCPListFiltersSchema, MCPServerCreateSchema,
                           MCPServerUpdateSchema)
from ..services.mcp_registry import MCPRegistryService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["mcp"])


@router.get("/servers")
@handle_api_errors("Failed to list MCP servers")
async def list_servers(
    enabled_only: bool = Query(False, description="Show only enabled servers"),
    connected_only: bool = Query(False, description="Show only connected servers"),
    detailed: bool = Query(False, description="Include detailed information"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """List all registered MCP servers."""
    log_api_call("list_mcp_servers", user_id=current_user.id)

    registry = MCPRegistryService(db)
    filters = MCPListFiltersSchema(
        enabled_only=enabled_only,
        connected_only=connected_only
    )
    
    servers = await registry.list_servers(filters)
    
    return {
        "success": True,
        "message": f"Retrieved {len(servers)} MCP servers",
        "data": servers
    }


@router.post("/servers")
@handle_api_errors("Failed to create MCP server")
async def create_server(
    server_data: MCPServerCreateSchema,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Create a new MCP server."""
    log_api_call("create_mcp_server", user_id=current_user.id, server_name=server_data.name)

    registry = MCPRegistryService(db)
    server = await registry.add_server(server_data)
    
    return {
        "success": True,
        "message": f"MCP server '{server_data.name}' created successfully",
        "data": server
    }


@router.get("/servers/byname/{server_name}")
@handle_api_errors("Failed to get MCP server")
async def get_server(
    server_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific MCP server."""
    log_api_call("get_mcp_server", user_id=current_user.id, server_name=server_name)

    registry = MCPRegistryService(db)
    server = await registry.get_server(server_name)
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server '{server_name}' not found"
        )
    
    return {
        "success": True,
        "message": f"Retrieved MCP server '{server_name}'",
        "data": server
    }


@router.patch("/servers/byname/{server_name}")
@handle_api_errors("Failed to update MCP server")
async def update_server(
    server_name: str,
    server_update: MCPServerUpdateSchema,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Update an MCP server."""
    log_api_call("update_mcp_server", user_id=current_user.id, server_name=server_name)

    registry = MCPRegistryService(db)
    server = await registry.update_server(server_name, server_update)
    
    return {
        "success": True,
        "message": f"MCP server '{server_name}' updated successfully",
        "data": server
    }


@router.delete("/servers/byname/{server_name}", response_model=BaseResponse)
@handle_api_errors("Failed to delete MCP server")
async def delete_server(
    server_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Delete an MCP server."""
    log_api_call("delete_mcp_server", user_id=current_user.id, server_name=server_name)

    registry = MCPRegistryService(db)
    await registry.remove_server(server_name)
    
    return BaseResponse(
        success=True,
        message=f"MCP server '{server_name}' deleted successfully"
    )


@router.post("/servers/byname/{server_name}/test")
@handle_api_errors("Failed to test MCP server connection")
async def test_server_connection(
    server_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Test connection to an MCP server."""
    log_api_call("test_mcp_server", user_id=current_user.id, server_name=server_name)

    registry = MCPRegistryService(db)
    test_result = await registry.test_connection(server_name)
    
    return {
        "success": True,
        "message": f"Connection test completed for '{server_name}'",
        "data": test_result
    }


@router.get("/tools")
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

    registry = MCPRegistryService(db)
    
    # Build filters
    filters = MCPListFiltersSchema(enabled_only=enabled_only)
    if server:
        filters.server_name = server
    
    tools = await registry.list_tools(filters)
    
    return {
        "success": True,
        "message": f"Retrieved {len(tools)} MCP tools",
        "data": tools
    }


@router.patch("/tools/byname/{tool_name}/enable", response_model=BaseResponse)
@handle_api_errors("Failed to enable MCP tool")
async def enable_tool(
    tool_name: str,
    server: Optional[str] = Query(None, description="Server name"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Enable an MCP tool."""
    log_api_call("enable_mcp_tool", user_id=current_user.id, tool_name=tool_name)

    registry = MCPRegistryService(db)
    await registry.enable_tool(tool_name, server_name=server)
    
    return BaseResponse(
        success=True,
        message=f"MCP tool '{tool_name}' enabled successfully"
    )


@router.patch("/tools/byname/{tool_name}/disable", response_model=BaseResponse)
@handle_api_errors("Failed to disable MCP tool")
async def disable_tool(
    tool_name: str,
    server: Optional[str] = Query(None, description="Server name"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Disable an MCP tool."""
    log_api_call("disable_mcp_tool", user_id=current_user.id, tool_name=tool_name)

    registry = MCPRegistryService(db)
    await registry.disable_tool(tool_name, server_name=server)
    
    return BaseResponse(
        success=True,
        message=f"MCP tool '{tool_name}' disabled successfully"
    )


@router.get("/stats")
@handle_api_errors("Failed to get MCP statistics")
async def get_mcp_stats(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Get MCP usage statistics."""
    log_api_call("get_mcp_stats", user_id=current_user.id)

    registry = MCPRegistryService(db)
    stats = await registry.get_statistics()
    
    return {
        "success": True,
        "message": "MCP statistics retrieved successfully",
        "data": stats
    }


@router.post("/refresh")
@handle_api_errors("Failed to refresh MCP")
async def refresh_mcp(
    server: Optional[str] = Query(None, description="Refresh specific server"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """Refresh MCP server connections and tool discovery."""
    log_api_call("refresh_mcp", user_id=current_user.id, server=server)

    registry = MCPRegistryService(db)
    
    if server:
        # Refresh specific server
        result = await registry.refresh_server(server)
        servers_refreshed = 1 if result else 0
        tools_discovered = len(result.get("tools", [])) if result else 0
    else:
        # Refresh all servers
        result = await registry.refresh_all_servers()
        servers_refreshed = result.get("servers_refreshed", 0)
        tools_discovered = result.get("tools_discovered", 0)
    
    return {
        "success": True,
        "message": "MCP refresh completed successfully",
        "data": {
            "servers_refreshed": servers_refreshed,
            "tools_discovered": tools_discovered,
        }
    }
