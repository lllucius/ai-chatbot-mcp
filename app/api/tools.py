"""
Tools API endpoints for comprehensive MCP tools management with advanced registry integration.

This module provides endpoints for managing MCP (Model Context Protocol) tools using
the MCPService for both registry management and client operations. It implements
comprehensive tool lifecycle management, discovery, testing, and integration
capabilities for enhanced AI assistant functionality.

Key Features:
- Comprehensive MCP tool discovery and listing with advanced filtering
- Tool lifecycle management (enable, disable, refresh, test)
- Server status monitoring and health checking
- Tool execution testing and validation
- OpenAI-compatible tool schema generation
- Registry integration for centralized tool management

Tool Management:
- List all available tools with filtering by enabled status and server
- Enable and disable tools for conversation use
- Test tool execution with parameter validation
- Refresh tool registry and update tool definitions
- Monitor tool performance and usage statistics

Server Integration:
- Monitor MCP server status and connectivity
- Manage server-specific tool collections
- Handle server failures and reconnection
- Validate server capabilities and tool availability
- Integrate with multiple MCP server instances

Tool Discovery:
- Automatic tool discovery from registered MCP servers
- Schema validation and OpenAI compatibility checking
- Tool categorization and metadata management
- Usage statistics and performance tracking
- Tool dependency analysis and validation

Administrative Features:
- Administrative control over tool availability
- Tool testing and validation capabilities
- Server management and monitoring
- Usage analytics and performance insights
- Tool configuration and parameter management

Security and Access Control:
- Superuser-only access for tool management operations
- Tool execution validation and parameter sanitization
- Server authentication and secure communication
- Audit logging for all tool management activities
- Protection against unauthorized tool access
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_superuser, get_mcp_service
from ..models.user import User
from ..schemas.admin import ServerStatusResponse, ToolResponse, ToolTestResponse
from ..schemas.common import BaseResponse
from ..schemas.mcp import (
    MCPListFiltersSchema,
    MCPToolExecutionRequestSchema,
    MCPToolListResponse,
    OpenAIToolSchema,
)
from ..services.mcp_service import MCPService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["tools"])


@router.get("/", response_model=MCPToolListResponse)
@handle_api_errors("Failed to list tools")
async def list_tools(
    enabled_only: bool = False,
    server_name: Optional[str] = None,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """
    List all available MCP tools with comprehensive registry integration and filtering.

    Returns a detailed list of all MCP tools available through registered servers,
    including their schemas, usage statistics, OpenAI-compatible function definitions,
    and server status information. Provides comprehensive tool discovery and
    management capabilities for administrative oversight and integration.

    Args:
        enabled_only: If True, filters to show only enabled tools from enabled servers
        server_name: Optional server name filter to show tools from specific server only
        current_user: Current authenticated superuser requesting tool information
        db: Database session for tool and server data retrieval
        mcp_service: Injected MCP service instance for tool operations

    Returns:
        MCPToolListResponse: Comprehensive tool listing including:
            - available_tools: Complete tool definitions with metadata and schemas
            - openai_tools: Tools formatted for OpenAI function calling integration
            - servers: Server status information and tool count statistics
            - enabled_count: Number of enabled tools available for use
            - total_count: Total number of tools across all servers

    Raises:
        HTTP 403: If user is not a superuser
        HTTP 500: If tool discovery or listing operation fails

    Tool Information:
        - Tool name, description, and parameter schemas
        - Server association and availability status
        - Usage statistics and performance metrics
        - OpenAI-compatible function definitions for integration
        - Enable/disable status for conversation use

    Server Information:
        - Server connection status and health monitoring
        - Tool count per server for capacity assessment
        - Last connection timestamps for monitoring
        - Server configuration and endpoint information
        - Enable/disable status for server management

    Use Cases:
        - Tool discovery and inventory management for administrators
        - Integration planning and capability assessment
        - Tool availability monitoring and troubleshooting
        - OpenAI function calling setup and configuration
        - Administrative oversight of tool ecosystem

    Security Notes:
        - Requires superuser privileges for comprehensive tool access
        - Tool discovery may trigger server connections and validation
        - Administrative logging for all tool management activities
        - Secure handling of tool schemas and server information

    Example:
        GET /api/v1/tools/?enabled_only=true&server_name=file-system
    """
    log_api_call("list_tools", user_id=current_user.id)

    try:
        filters = MCPListFiltersSchema(
            enabled_only=enabled_only, server_name=server_name
        )
        tools = await mcp_service.list_tools(filters)
        servers = await mcp_service.list_servers()

        await mcp_service.get_available_tools(filters)

        openai_tools = []
        for tool in tools:
            if tool.is_enabled and tool.server.is_enabled:
                openai_tool = OpenAIToolSchema(
                    type="function",
                    function={
                        "name": tool.name,
                        "description": tool.description
                        or f"Tool from {tool.server.name}",
                        "parameters": tool.parameters
                        or {"type": "object", "properties": {}},
                    },
                )
                openai_tools.append(openai_tool)

        server_status = []
        for server in servers:
            server_tools = [t for t in tools if t.server.name == server.name]
            server_status.append(
                {
                    "name": server.name,
                    "status": "connected" if server.is_connected else "disconnected",
                    "enabled": server.is_enabled,
                    "url": server.url,
                    "tool_count": len(server_tools),
                    "last_connected": server.last_connected_at,
                    "connection_errors": server.connection_errors,
                }
            )

        tool_responses = []
        for tool in tools:
            tool_responses.append(
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "schema": tool.parameters or {},
                    "server_name": tool.server.name,
                    "is_enabled": tool.is_enabled,
                    "usage_count": tool.usage_count,
                    "last_used_at": tool.last_used_at,
                    "success_rate": tool.success_rate,
                }
            )

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


@router.get("/byname/{tool_name}", response_model=ToolResponse)
@handle_api_errors("Failed to get tool details")
async def get_tool_details(
    tool_name: str,
    current_user: User = Depends(get_current_superuser),
    mcp_service: MCPService = Depends(get_mcp_service),
) -> ToolResponse:
    """
    Get detailed information about a specific tool with registry integration.
    """
    log_api_call("get_tool_details", user_id=current_user.id, tool_name=tool_name)

    try:
        tool = await mcp_service.get_tool(tool_name)

        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found in registry",
            )

        return ToolResponse(
            success=True,
            tool_name=tool.name,
            tool_info={
                "name": tool.name,
                "original_name": tool.original_name,
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
            },
            server_info={
                "server_name": tool.server.name,
                "server_url": tool.server.url,
                "server_enabled": tool.server.is_enabled,
                "server_connected": tool.server.is_connected,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool details: {str(e)}",
        )


@router.post("/byname/{tool_name}/test", response_model=ToolTestResponse)
@handle_api_errors("Failed to test tool")
async def test_tool(
    tool_name: str,
    test_params: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_superuser),
    mcp_service: MCPService = Depends(get_mcp_service),
) -> ToolTestResponse:
    """
    Test a tool with optional parameters using registry integration.
    """
    log_api_call("test_tool", user_id=current_user.id, tool_name=tool_name)

    import time
    start_time = time.time()

    try:
        tool = await mcp_service.get_tool(tool_name)
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
        if test_params is None:
            test_params = {}
        request = MCPToolExecutionRequestSchema(
            tool_name=tool_name, parameters=test_params, record_usage=True
        )
        result = await mcp_service.call_tool(request)
        execution_time = time.time() - start_time

        return ToolTestResponse(
            success=True,
            tool_name=tool_name,
            test_result={
                "tool_name": tool_name,
                "test_parameters": test_params,
                "result": result.model_dump(),
                "status": "success" if result.success else "error",
                "usage_recorded": True,
            },
            execution_time=execution_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        execution_time = time.time() - start_time
        return ToolTestResponse(
            success=False,
            tool_name=tool_name,
            test_result={
                "tool_name": tool_name,
                "test_parameters": test_params,
                "error": str(e),
                "status": "error",
            },
            execution_time=execution_time,
        )


@router.post("/refresh", response_model=BaseResponse)
@handle_api_errors("Failed to refresh tools")
async def refresh_tools(
    current_user: User = Depends(get_current_superuser),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """
    Refresh tool discovery and reconnect to MCP servers with registry integration.
    """
    log_api_call("refresh_tools", user_id=current_user.id)

    try:
        results = await mcp_service.discover_tools_all_servers()

        if not results:
            return BaseResponse(
                success=True, message="No enabled servers found for tool discovery"
            )

        total_new = sum(r.new_tools for r in results if r.success)
        total_updated = sum(r.updated_tools for r in results if r.success)
        failed_servers = [r.server_name for r in results if not r.success]

        message = (
            f"Tools refreshed successfully: {total_new} new, {total_updated} updated"
        )
        if failed_servers:
            message += f". Failed servers: {', '.join(failed_servers)}"

        await mcp_service.refresh_from_registry()

        return BaseResponse(success=True, message=message)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh tools: {str(e)}",
        )


@router.post("/byname/{tool_name}/enable", response_model=BaseResponse)
@handle_api_errors("Failed to enable tool")
async def enable_tool(
    tool_name: str,
    current_user: User = Depends(get_current_superuser),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """
    Enable a specific tool in the registry.
    """
    log_api_call("enable_tool", user_id=current_user.id, tool_name=tool_name)

    success = await mcp_service.enable_tool(tool_name)

    if success:
        return BaseResponse(
            success=True, message=f"Tool '{tool_name}' enabled successfully"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found",
        )


@router.post("/byname/{tool_name}/disable", response_model=BaseResponse)
@handle_api_errors("Failed to disable tool")
async def disable_tool(
    tool_name: str,
    current_user: User = Depends(get_current_superuser),
    mcp_service: MCPService = Depends(get_mcp_service),
):
    """
    Disable a specific tool in the registry.
    """
    log_api_call("disable_tool", user_id=current_user.id, tool_name=tool_name)

    success = await mcp_service.disable_tool(tool_name)

    if success:
        return BaseResponse(
            success=True, message=f"Tool '{tool_name}' disabled successfully"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found",
        )


@router.get("/servers/status", response_model=ServerStatusResponse)
@handle_api_errors("Failed to get server status")
async def get_server_status(
    current_user: User = Depends(get_current_superuser),
    mcp_service: MCPService = Depends(get_mcp_service),
) -> ServerStatusResponse:
    """
    Get status of all configured MCP servers with registry integration.
    """
    log_api_call("get_server_status", user_id=current_user.id)

    try:
        servers = await mcp_service.list_servers()

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
            filters = MCPListFiltersSchema(server_name=server.name)
            tools = await mcp_service.list_tools(filters)

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

        return ServerStatusResponse(
            success=True,
            servers=server_status,
            total_servers=len(servers),
            healthy_servers=connected_count,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get server status: {str(e)}",
        )
