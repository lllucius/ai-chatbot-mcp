"""
Tools API endpoints for MCP tools management with registry integration.

This module provides endpoints for managing MCP (Model Context Protocol) tools
using the refactored registry service and client, with Pydantic schemas
throughout for consistent API responses.

"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_superuser
from ..models.user import User
from ..schemas.common import BaseResponse
from ..schemas.mcp import (
    MCPToolExecutionRequestSchema, MCPToolExecutionResultSchema,
    MCPToolSchema, MCPServerSchema, MCPListFiltersSchema,
    OpenAIToolSchema, MCPOpenAIToolsResponseSchema
)
from ..services.mcp_client import get_mcp_client
from ..services.mcp_registry import MCPRegistryService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["tools"])


@router.get("/", response_model=Dict[str, Any])
@handle_api_errors("Failed to list tools")
async def list_tools(
    enabled_only: bool = False,
    server_name: Optional[str] = None,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    List all available MCP tools with registry integration.

    Returns information about all configured MCP tools including their
    status, schemas, configuration details, and usage statistics from
    the registry system.

    Only available to superusers.
    """
    log_api_call("list_tools", user_id=current_user.id)

    try:
        # Get tools from registry using new service
        registry = MCPRegistryService(db)
        filters = MCPListFiltersSchema(
            enabled_only=enabled_only,
            server_name=server_name
        )
        tools = await registry.list_tools(filters)
        
        # Get servers for status info
        servers = await registry.list_servers()

        # Get MCP client for OpenAI tools format
        mcp_client = await get_mcp_client(db)
        client_tools = await mcp_client.get_available_tools(filters, db)

        # Convert to OpenAI format for enabled tools
        openai_tools = []
        for tool in tools:
            if tool.is_enabled and tool.server.is_enabled:
                openai_tool = OpenAIToolSchema(
                    type="function",
                    function={
                        "name": tool.name,
                        "description": tool.description or f"Tool from {tool.server.name}",
                        "parameters": tool.parameters or {"type": "object", "properties": {}}
                    }
                )
                openai_tools.append(openai_tool)

        # Server status summary
        server_status = []
        for server in servers:
            server_tools = [t for t in tools if t.server.name == server.name]
            server_status.append({
                "name": server.name,
                "status": "connected" if server.is_connected else "disconnected",
                "enabled": server.is_enabled,
                "url": server.url,
                "tool_count": len(server_tools),
                "last_connected": server.last_connected_at,
                "connection_errors": server.connection_errors,
            })

        # Convert tools to response format
        tool_responses = []
        for tool in tools:
            tool_responses.append({
                "name": tool.name,
                "description": tool.description or "",
                "schema": tool.parameters or {},
                "server_name": tool.server.name,
                "is_enabled": tool.is_enabled,
                "usage_count": tool.usage_count,
                "last_used_at": tool.last_used_at,
                "success_rate": tool.success_rate,
            })

        return {
            "success": True,
            "message": f"Retrieved {len(tools)} tools from {len(servers)} servers",
            "available_tools": tool_responses,
            "openai_tools": [tool.model_dump() for tool in openai_tools],
            "servers": server_status,
            "enabled_count": len([t for t in tools if t.is_enabled]),
            "total_count": len(tools),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tools: {str(e)}",
        )


@router.get("/{tool_name}", response_model=Dict[str, Any])
@handle_api_errors("Failed to get tool details")
async def get_tool_details(
    tool_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information about a specific tool with registry integration.

    Returns the complete schema, configuration, status information,
    and usage statistics for the specified tool.
    """
    log_api_call("get_tool_details", user_id=current_user.id, tool_name=tool_name)

    try:
        registry = MCPRegistryService(db)
        tool = await registry.get_tool(tool_name)

        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found in registry",
            )

        return {
            "success": True,
            "data": {
                "name": tool.name,
                "original_name": tool.original_name,
                "server": tool.server.name,
                "description": tool.description,
                "parameters": tool.parameters,
                "is_enabled": tool.is_enabled,
                "usage_statistics": {
                    "usage_count": tool.usage_count,
                    "success_count": tool.success_count,
                    "error_count": tool.error_count,
                    "success_rate": tool.success_rate,
                    "average_duration_ms": tool.average_duration_ms,
                    "last_used_at": tool.last_used_at,
                },
                "server_info": {
                    "server_name": tool.server.name,
                    "server_url": tool.server.url,
                    "server_enabled": tool.server.is_enabled,
                    "server_connected": tool.server.is_connected,
                },
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool details: {str(e)}",
        )


@router.post("/{tool_name}/test", response_model=Dict[str, Any])
@handle_api_errors("Failed to test tool")
async def test_tool(
    tool_name: str,
    test_params: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Test a tool with optional parameters using registry integration.

    Executes the tool with provided test parameters to verify
    it's working correctly.
    """
    log_api_call("test_tool", user_id=current_user.id, tool_name=tool_name)

    try:
        registry = MCPRegistryService(db)
        tool = await registry.get_tool(tool_name)
        
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found in registry",
            )

        if not tool.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tool '{tool_name}' is disabled",
            )

        # Use empty parameters if none provided
        if test_params is None:
            test_params = {}

        # Execute the tool
        mcp_client = await get_mcp_client(db)
        request = MCPToolExecutionRequestSchema(
            tool_name=tool_name,
            parameters=test_params,
            record_usage=True
        )
        result = await mcp_client.call_tool(request, db)

        return {
            "success": True,
            "data": {
                "tool_name": tool_name,
                "test_parameters": test_params,
                "result": result.model_dump(),
                "status": "success" if result.success else "error",
                "usage_recorded": True,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "data": {
                "tool_name": tool_name,
                "test_parameters": test_params,
                "error": str(e),
                "status": "error",
            },
        }


@router.post("/refresh", response_model=BaseResponse)
@handle_api_errors("Failed to refresh tools")
async def refresh_tools(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh tool discovery and reconnect to MCP servers with registry integration.

    Triggers a fresh discovery of all available tools from configured MCP servers
    and updates the registry with new tool information.
    """
    log_api_call("refresh_tools", user_id=current_user.id)

    try:
        registry = MCPRegistryService(db)
        results = await registry.discover_tools_all_servers()

        if not results:
            return BaseResponse(success=True, message="No enabled servers found for tool discovery")

        # Summarize results
        total_new = sum(r.new_tools for r in results if r.success)
        total_updated = sum(r.updated_tools for r in results if r.success)
        failed_servers = [r.server_name for r in results if not r.success]

        message = f"Tools refreshed successfully: {total_new} new, {total_updated} updated"
        if failed_servers:
            message += f". Failed servers: {', '.join(failed_servers)}"

        # Also refresh the MCP client cache
        mcp_client = await get_mcp_client(db)
        await mcp_client.refresh_from_registry(db)

        return BaseResponse(success=True, message=message)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh tools: {str(e)}",
        )


@router.post("/{tool_name}/enable", response_model=BaseResponse)
@handle_api_errors("Failed to enable tool")
async def enable_tool(
    tool_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Enable a specific tool in the registry.

    Enables the tool for use in conversations and tool calling.
    """
    log_api_call("enable_tool", user_id=current_user.id, tool_name=tool_name)

    registry = MCPRegistryService(db)
    success = await registry.enable_tool(tool_name)

    if success:
        return BaseResponse(success=True, message=f"Tool '{tool_name}' enabled successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found",
        )


@router.post("/{tool_name}/disable", response_model=BaseResponse)
@handle_api_errors("Failed to disable tool")
async def disable_tool(
    tool_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Disable a specific tool in the registry.

    Disables the tool from being used in conversations and tool calling.
    """
    log_api_call("disable_tool", user_id=current_user.id, tool_name=tool_name)

    registry = MCPRegistryService(db)
    success = await registry.disable_tool(tool_name)

    if success:
        return BaseResponse(success=True, message=f"Tool '{tool_name}' disabled successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found",
        )


@router.get("/servers/status", response_model=Dict[str, Any])
@handle_api_errors("Failed to get server status")
async def get_server_status(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Get status of all configured MCP servers with registry integration.

    Returns connection status, tool counts, and health information
    for all configured MCP servers from the registry.
    """
    log_api_call("get_server_status", user_id=current_user.id)

    try:
        registry = MCPRegistryService(db)
        servers = await registry.list_servers()

        if not servers:
            return {
                "success": True,
                "data": {
                    "servers": {},
                    "total_servers": 0,
                    "connected_servers": 0,
                    "enabled_servers": 0,
                    "mcp_enabled": True,
                },
            }

        server_status = {}
        connected_count = 0
        enabled_count = 0

        for server in servers:
            # Get tools for this server
            filters = MCPListFiltersSchema(server_name=server.name)
            tools = await registry.list_tools(filters)

            server_status[server.name] = {
                "name": server.name,
                "url": server.url,
                "status": "connected" if server.is_connected else "disconnected",
                "enabled": server.is_enabled,
                "last_connected": server.last_connected_at,
                "connection_errors": server.connection_errors,
                "tool_count": len(tools),
                "enabled_tools": len([t for t in tools if t.is_enabled]),
                "transport": server.transport,
                "timeout": server.timeout,
                "description": server.description,
            }

            if server.is_connected:
                connected_count += 1
            if server.is_enabled:
                enabled_count += 1

        return {
            "success": True,
            "data": {
                "servers": server_status,
                "total_servers": len(servers),
                "connected_servers": connected_count,
                "enabled_servers": enabled_count,
                "mcp_enabled": True,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get server status: {str(e)}",
        )
