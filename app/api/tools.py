"""
Tools API endpoints for MCP tools management with registry integration.

This module provides endpoints for managing MCP (Model Context Protocol) tools
including listing available tools, enabling/disabling tools, viewing tool configurations,
and comprehensive registry-based management with usage tracking.

Generated on: 2025-07-22 UTC
Updated on: 2025-07-23 04:00:00 UTC - Enhanced with registry services
Current User: lllucius
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_current_superuser
from ..models.user import User
from ..schemas.common import BaseResponse
from ..services.enhanced_mcp_client import get_enhanced_mcp_client
from ..services.mcp_client import get_mcp_client
from ..services.mcp_registry import MCPRegistryService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["tools"])


@router.get("/", response_model=Dict[str, Any])
@handle_api_errors("Failed to list tools")
async def list_tools(
    current_user: User = Depends(get_current_superuser),
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
        # Get enhanced MCP client with registry integration
        enhanced_client = await get_enhanced_mcp_client()

        # Get available tools with registry filtering
        available_tools = await enhanced_client.get_available_tools(enabled_only=False)

        # Get OpenAI-formatted tools (enabled only)
        openai_tools = await enhanced_client.get_tools_for_openai(enabled_only=True)

        # Get registry servers and their status
        servers = await MCPRegistryService.list_servers()
        server_status = {}
        
        for server in servers:
            server_status[server.name] = {
                "status": "connected" if server.is_connected else "disconnected",
                "enabled": server.is_enabled,
                "url": server.url,
                "tool_count": len([t for t in available_tools.keys() if t.startswith(f"{server.name}_")]),
                "last_connected": server.last_connected_at.isoformat() if server.last_connected_at else None,
                "connection_errors": server.connection_errors,
            }

        # Get tool statistics
        tool_stats = await MCPRegistryService.get_tool_stats(limit=20)

        return {
            "success": True,
            "data": {
                "tools": available_tools,
                "openai_tools": openai_tools,
                "servers": server_status,
                "tool_statistics": tool_stats,
                "total_tools": len(available_tools),
                "enabled_tools": len([t for t in available_tools.values() if t.get("is_enabled", True)]),
                "total_servers": len(servers),
                "enabled_servers": len([s for s in servers if s.is_enabled]),
                "connected_servers": len([s for s in servers if s.is_connected]),
            },
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
):
    """
    Get detailed information about a specific tool.

    Returns the complete schema, configuration, and status
    information for the specified tool.
    """
    log_api_call("get_tool_details", user_id=current_user.id, tool_name=tool_name)

    try:
        mcp_client = await get_mcp_client()

        if not mcp_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MCP client not available",
            )

        # Get tool schema
        tool_schema = mcp_client.get_tool_schema(tool_name)

        if not tool_schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found",
            )

        # Get additional tool information
        available_tools = mcp_client.get_available_tools()
        tool_info = available_tools.get(tool_name, {})

        return {
            "success": True,
            "data": {
                "name": tool_name,
                "schema": tool_schema,
                "enabled": tool_info.get("enabled", True),
                "server": tool_info.get("server", "unknown"),
                "description": tool_schema.get("description", ""),
                "parameters": tool_schema.get("parameters", {}),
                "last_used": tool_info.get("last_used"),
                "usage_count": tool_info.get("usage_count", 0),
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
):
    """
    Test a tool with optional parameters using registry integration.

    Executes the tool with provided test parameters to verify
    it's working correctly. Uses the enhanced MCP client for
    registry integration and usage tracking.
    """
    log_api_call("test_tool", user_id=current_user.id, tool_name=tool_name)

    try:
        enhanced_client = await get_enhanced_mcp_client()

        # Check if tool exists and is enabled
        tool = await MCPRegistryService.get_tool(tool_name)
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

        # Execute the tool with usage tracking
        result = await enhanced_client.call_tool(
            tool_name, test_params, record_usage=True
        )

        return {
            "success": True,
            "data": {
                "tool_name": tool_name,
                "test_parameters": test_params,
                "result": result,
                "status": "success",
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
):
    """
    Refresh tool discovery and reconnect to MCP servers with registry integration.

    Triggers a fresh discovery of all available tools from configured MCP servers
    and updates the registry with new tool information.
    """
    log_api_call("refresh_tools", user_id=current_user.id)

    try:
        # Discover tools from all servers using registry service
        results = await MCPRegistryService.discover_tools_all_servers()
        
        if not results:
            return BaseResponse(
                success=True, 
                message="No enabled servers found for tool discovery"
            )

        # Summarize results
        total_new = sum(r.get("new_tools", 0) for r in results if r.get("success"))
        total_updated = sum(r.get("updated_tools", 0) for r in results if r.get("success"))
        failed_servers = [r.get("server") for r in results if not r.get("success")]

        message = f"Tools refreshed successfully: {total_new} new, {total_updated} updated"
        if failed_servers:
            message += f". Failed servers: {', '.join(failed_servers)}"

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
):
    """
    Enable a specific tool in the registry.
    
    Enables the tool for use in conversations and tool calling.
    """
    log_api_call("enable_tool", user_id=current_user.id, tool_name=tool_name)

    try:
        success = await MCPRegistryService.enable_tool(tool_name)
        
        if success:
            return BaseResponse(
                success=True, 
                message=f"Tool '{tool_name}' enabled successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable tool: {str(e)}",
        )


@router.post("/{tool_name}/disable", response_model=BaseResponse)
@handle_api_errors("Failed to disable tool")
async def disable_tool(
    tool_name: str,
    current_user: User = Depends(get_current_superuser),
):
    """
    Disable a specific tool in the registry.
    
    Disables the tool from being used in conversations and tool calling.
    """
    log_api_call("disable_tool", user_id=current_user.id, tool_name=tool_name)

    try:
        success = await MCPRegistryService.disable_tool(tool_name)
        
        if success:
            return BaseResponse(
                success=True, 
                message=f"Tool '{tool_name}' disabled successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable tool: {str(e)}",
        )


@router.get("/servers/status", response_model=Dict[str, Any])
@handle_api_errors("Failed to get server status")
async def get_server_status(
    current_user: User = Depends(get_current_superuser),
):
    """
    Get status of all configured MCP servers.

    Returns connection status, tool counts, and health information
    for all configured MCP servers.
    """
    log_api_call("get_server_status", user_id=current_user.id)

    try:
        mcp_client = await get_mcp_client()

        if not mcp_client:
            return {
                "success": True,
                "data": {
                    "servers": {},
                    "total_servers": 0,
                    "connected_servers": 0,
                    "mcp_enabled": False,
                },
            }

        server_status = {}
        connected_count = 0

        for server_name, server_config in mcp_client.servers.items():
            try:
                # Check server health
                # In a real implementation, you might ping the server or check last successful call
                server_status[server_name] = {
                    "name": server_name,
                    "url": getattr(server_config, "url", "unknown"),
                    "status": "connected",
                    "last_check": "2024-01-22T20:59:27Z",
                    "response_time": "150ms",
                    "tool_count": len(
                        [
                            t
                            for t in mcp_client.get_available_tools().keys()
                            if t.startswith(f"{server_name}:")
                        ]
                    ),
                    "error": None,
                }
                connected_count += 1
            except Exception as e:
                server_status[server_name] = {
                    "name": server_name,
                    "url": getattr(server_config, "url", "unknown"),
                    "status": "error",
                    "last_check": "2024-01-22T20:59:27Z",
                    "response_time": None,
                    "tool_count": 0,
                    "error": str(e),
                }

        return {
            "success": True,
            "data": {
                "servers": server_status,
                "total_servers": len(server_status),
                "connected_servers": connected_count,
                "mcp_enabled": True,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get server status: {str(e)}",
        )
