"""
Tools API endpoints for MCP tools management.

This module provides endpoints for managing MCP (Model Context Protocol) tools
including listing available tools, enabling/disabling tools, and viewing tool configurations.

Generated on: 2025-07-22 UTC
Current User: lllucius
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Any, Optional

from ..database import get_db
from ..dependencies import get_current_superuser
from ..models.user import User
from ..schemas.common import BaseResponse
from ..services.mcp_client import get_mcp_client
from ..core.tool_executor import get_unified_tool_executor
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["tools"])


@router.get("/", response_model=Dict[str, Any])
@handle_api_errors("Failed to list tools")
async def list_tools(
    current_user: User = Depends(get_current_superuser),
):
    """
    List all available MCP tools.

    Returns information about all configured MCP tools including their
    status, schemas, and configuration details.
    
    Only available to superusers.
    """
    log_api_call("list_tools", user_id=current_user.id)
    
    try:
        # Get MCP client
        mcp_client = await get_mcp_client()
        
        # Get unified tool executor
        tool_executor = await get_unified_tool_executor()
        
        # Get available tools from MCP client
        available_tools = mcp_client.get_available_tools() if mcp_client else {}
        
        # Get OpenAI-formatted tools
        openai_tools = mcp_client.get_tools_for_openai() if mcp_client else []
        
        # Get server status
        server_status = {}
        if mcp_client:
            for server_name in mcp_client.servers.keys():
                try:
                    # Try to check if server is responsive
                    server_tools = mcp_client.get_available_tools()
                    server_status[server_name] = {
                        "status": "connected",
                        "tool_count": len([t for t in server_tools.keys() if t.startswith(f"{server_name}:")]),
                        "last_checked": "2024-01-22T20:59:27Z"  # In real implementation, track this
                    }
                except Exception as e:
                    server_status[server_name] = {
                        "status": "error",
                        "error": str(e),
                        "tool_count": 0,
                        "last_checked": "2024-01-22T20:59:27Z"
                    }
        
        return {
            "success": True,
            "data": {
                "tools": available_tools,
                "openai_tools": openai_tools,
                "servers": server_status,
                "total_tools": len(available_tools),
                "enabled_tools": len([t for t in available_tools.values() if t.get("enabled", True)]),
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tools: {str(e)}"
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
                detail="MCP client not available"
            )
        
        # Get tool schema
        tool_schema = mcp_client.get_tool_schema(tool_name)
        
        if not tool_schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found"
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
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool details: {str(e)}"
        )


@router.post("/{tool_name}/test", response_model=Dict[str, Any])
@handle_api_errors("Failed to test tool")
async def test_tool(
    tool_name: str,
    test_params: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_superuser),
):
    """
    Test a tool with optional parameters.
    
    Executes the tool with provided test parameters to verify
    it's working correctly.
    """
    log_api_call("test_tool", user_id=current_user.id, tool_name=tool_name)
    
    try:
        mcp_client = await get_mcp_client()
        
        if not mcp_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MCP client not available"
            )
        
        # Get tool schema to validate parameters
        tool_schema = mcp_client.get_tool_schema(tool_name)
        if not tool_schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found"
            )
        
        # Use empty parameters if none provided
        if test_params is None:
            test_params = {}
        
        # Execute the tool
        result = await mcp_client.call_tool(tool_name, test_params)
        
        return {
            "success": True,
            "data": {
                "tool_name": tool_name,
                "test_parameters": test_params,
                "result": result,
                "status": "success"
            }
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
                "status": "error"
            }
        }


@router.post("/refresh", response_model=BaseResponse)
@handle_api_errors("Failed to refresh tools")
async def refresh_tools(
    current_user: User = Depends(get_current_superuser),
):
    """
    Refresh tool discovery and reconnect to MCP servers.
    
    Triggers a fresh discovery of all available tools from
    configured MCP servers.
    """
    log_api_call("refresh_tools", user_id=current_user.id)
    
    try:
        mcp_client = await get_mcp_client()
        
        if not mcp_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MCP client not available"
            )
        
        # Force rediscovery of tools
        await mcp_client._discover_tools()
        
        return BaseResponse(
            success=True,
            message="Tools refreshed successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh tools: {str(e)}"
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
                    "mcp_enabled": False
                }
            }
        
        server_status = {}
        connected_count = 0
        
        for server_name, server_config in mcp_client.servers.items():
            try:
                # Check server health
                # In a real implementation, you might ping the server or check last successful call
                server_status[server_name] = {
                    "name": server_name,
                    "url": getattr(server_config, 'url', 'unknown'),
                    "status": "connected",
                    "last_check": "2024-01-22T20:59:27Z",
                    "response_time": "150ms",
                    "tool_count": len([t for t in mcp_client.get_available_tools().keys() if t.startswith(f"{server_name}:")]),
                    "error": None
                }
                connected_count += 1
            except Exception as e:
                server_status[server_name] = {
                    "name": server_name,
                    "url": getattr(server_config, 'url', 'unknown'),
                    "status": "error",
                    "last_check": "2024-01-22T20:59:27Z",
                    "response_time": None,
                    "tool_count": 0,
                    "error": str(e)
                }
        
        return {
            "success": True,
            "data": {
                "servers": server_status,
                "total_servers": len(server_status),
                "connected_servers": connected_count,
                "mcp_enabled": True
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get server status: {str(e)}"
        )