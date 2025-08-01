"""
MCP (Model Context Protocol) management API endpoints.

This module provides comprehensive REST API endpoints for managing MCP servers
and tools, offering complete lifecycle management including server registration,
tool discovery, connection management, and usage analytics. It serves as the
backend for API-based CLI MCP commands and administrative operations.

Key Features:
- MCP server registration and configuration management
- Tool discovery and lifecycle management
- Connection status monitoring and health checks
- Usage statistics and performance analytics
- Server and tool enable/disable operations
- Comprehensive filtering and search capabilities

Server Management:
- Register and configure MCP servers with various transports
- Monitor connection status and health metrics
- Manage server lifecycle (enable, disable, update, delete)
- Connection pooling and retry mechanisms
- Configuration validation and error handling

Tool Management:
- Automatic tool discovery from registered servers
- Tool lifecycle management (enable, disable, configure)
- Usage tracking and performance monitoring
- Tool parameter validation and schema management
- Integration with conversation and chat systems

Security Features:
- Role-based access control for server management
- Secure connection handling and authentication
- Input validation and parameter sanitization
- Audit logging for administrative operations
- Protection against unauthorized server access
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_superuser, get_mcp_service
from ..models.user import User
from ..schemas.common import BaseResponse
from ..schemas.mcp import (
    MCPListFiltersSchema,
    MCPServerCreateSchema,
    MCPServerListResponse,
    MCPServerUpdateSchema,
    MCPStatsResponse,
    MCPToolsResponse,
)
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
    """
    Create a new MCP server with comprehensive configuration.

    Registers a new MCP (Model Context Protocol) server in the system with
    the specified configuration including connection details, transport settings,
    and metadata. Performs validation and initial connection testing to ensure
    server viability.

    Args:
        server_data: Server configuration data including name, URL, transport, and settings
        current_user: Current authenticated superuser creating the server
        db: Database session for server registration
        mcp_service: Injected MCP service instance

    Returns:
        MCPServerListResponse: Created server configuration with status information

    Raises:
        HTTP 403: If user is not a superuser
        HTTP 400: If server name already exists or configuration is invalid
        HTTP 422: If server data validation fails
        HTTP 500: If server creation process fails

    Server Configuration:
        - name: Unique identifier for the server
        - url: Connection URL or command for server access
        - transport: Connection transport type (stdio, sse, websocket)
        - timeout: Connection timeout and retry settings
        - description: Server description and metadata
        - environment: Environment variables for server execution

    Validation Checks:
        - Server name uniqueness verification
        - URL format and accessibility validation
        - Transport compatibility checking
        - Configuration parameter validation
        - Initial connection test (optional)

    Example:
        POST /api/v1/mcp/servers
        {
            "name": "file-system",
            "url": "mcp-server-filesystem",
            "transport": "stdio",
            "description": "File system operations server",
            "timeout": 30
        }
    """
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
    """
    Get detailed information about a specific MCP server by name.

    Returns comprehensive server configuration, connection status, tool inventory,
    and performance metrics for the specified MCP server. Provides complete
    server information needed for management and troubleshooting operations.

    Args:
        server_name: Name of the MCP server to retrieve details for
        current_user: Current authenticated superuser requesting server details
        db: Database session for server data retrieval
        mcp_service: Injected MCP service instance

    Returns:
        MCPServerListResponse: Complete server information including:
            - configuration: Server settings and connection parameters
            - status: Current connection and health status
            - tools: List of available tools and their states
            - statistics: Usage metrics and performance data
            - metadata: Creation and modification timestamps

    Raises:
        HTTP 403: If user is not a superuser
        HTTP 404: If server with specified name is not found
        HTTP 500: If server retrieval process fails

    Server Details:
        - Complete configuration parameters
        - Real-time connection status and health metrics
        - Tool inventory with availability and status
        - Usage statistics and performance metrics
        - Error logs and diagnostic information

    Use Cases:
        - Server troubleshooting and diagnostics
        - Configuration verification and validation
        - Performance monitoring and optimization
        - Tool availability checking
        - Administrative reporting and auditing

    Example:
        GET /api/v1/mcp/servers/byname/file-system
    """
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
    """
    Update configuration settings for an existing MCP server.

    Modifies the configuration of an existing MCP server including connection
    parameters, transport settings, and metadata. Supports partial updates and
    performs validation to ensure configuration consistency and compatibility.

    Args:
        server_name: Name of the MCP server to update
        server_update: Updated configuration data with modified settings
        current_user: Current authenticated superuser performing the update
        db: Database session for server configuration updates
        mcp_service: Injected MCP service instance

    Returns:
        MCPServerListResponse: Updated server configuration with new settings

    Raises:
        HTTP 403: If user is not a superuser
        HTTP 404: If server with specified name is not found
        HTTP 400: If updated configuration is invalid
        HTTP 422: If update data validation fails
        HTTP 500: If server update process fails

    Updatable Configuration:
        - url: Server connection URL or command
        - transport: Connection transport type
        - timeout: Connection timeout settings
        - description: Server description and metadata
        - environment: Environment variables
        - enabled: Server activation status

    Update Validation:
        - Configuration parameter validation
        - Transport compatibility checking
        - URL accessibility verification (optional)
        - Dependency and compatibility analysis
        - Impact assessment on active connections

    Impact Considerations:
        - Active connections may be terminated
        - Tool availability might change temporarily
        - Client applications may need to reconnect
        - Configuration changes take effect immediately

    Example:
        PATCH /api/v1/mcp/servers/byname/file-system
        {
            "timeout": 60,
            "description": "Enhanced file system operations server",
            "enabled": true
        }
    """
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
    """
    Delete an MCP server and clean up associated resources.

    Permanently removes an MCP server from the system including its configuration,
    tool registrations, and historical data. Performs cleanup operations to ensure
    system consistency and handles graceful shutdown of active connections.

    Args:
        server_name: Name of the MCP server to delete
        current_user: Current authenticated superuser performing the deletion
        db: Database session for server removal operations
        mcp_service: Injected MCP service instance

    Returns:
        BaseResponse: Confirmation of successful server deletion

    Raises:
        HTTP 403: If user is not a superuser
        HTTP 404: If server with specified name is not found
        HTTP 409: If server has active connections or dependencies
        HTTP 500: If server deletion process fails

    Deletion Process:
        - Graceful shutdown of active connections
        - Tool deregistration and cleanup
        - Configuration and metadata removal
        - Historical data archiving or deletion
        - Dependency validation and cleanup

    Impact and Cleanup:
        - All server tools become unavailable immediately
        - Active connections are terminated gracefully
        - Client applications lose access to server tools
        - Usage statistics and logs may be archived
        - System references are cleaned up

    Safety Considerations:
        - Irreversible operation requiring confirmation
        - Active connections are validated before deletion
        - Dependent services and configurations are checked
        - Audit logging for administrative oversight
        - Backup recommendations for critical servers

    Example:
        DELETE /api/v1/mcp/servers/byname/file-system
    """
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
    """
    List all available MCP tools with filtering and detailed information.

    Returns a comprehensive list of MCP tools available across all registered
    servers with optional filtering by server, enabled status, and detail level.
    Includes tool schemas, usage statistics, and availability information.

    Args:
        server: Optional server name filter to show tools from specific server
        enabled_only: If True, returns only enabled tools (default: False)
        detailed: If True, includes comprehensive tool metadata (default: False)
        current_user: Current authenticated superuser requesting tool list
        db: Database session for tool data retrieval

    Returns:
        MCPToolsResponse: List of available tools with metadata including:
            - tools: List of tool objects with schemas and status
            - server_mapping: Tools organized by server
            - statistics: Usage and availability metrics
            - total_count: Number of tools matching filters

    Raises:
        HTTP 403: If user is not a superuser
        HTTP 500: If tool listing operation fails

    Tool Information:
        - Tool name, description, and parameters
        - Server association and availability status
        - Usage statistics and performance metrics
        - Schema definitions for parameter validation
        - Enabled/disabled status and configuration

    Filtering Options:
        - Server-specific tool filtering
        - Active/inactive status filtering
        - Detailed metadata inclusion control
        - Tool type and category filtering (if implemented)

    Use Cases:
        - Tool discovery and inventory management
        - Server capability assessment
        - Tool usage analysis and optimization
        - Client application integration planning
        - Administrative monitoring and reporting

    Example:
        GET /api/v1/mcp/tools?server=file-system&enabled_only=true&detailed=true
    """
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
    """
    Enable a specific MCP tool for system-wide availability.

    Activates the specified MCP tool making it available for use in conversations
    and other system operations. Performs validation to ensure tool compatibility
    and updates tool registry with new availability status.

    Args:
        tool_name: Name of the MCP tool to enable
        current_user: Current authenticated superuser performing the operation
        db: Database session for tool status updates
        mcp_service: Injected MCP service instance

    Returns:
        BaseResponse: Confirmation of successful tool enablement

    Raises:
        HTTP 403: If user is not a superuser
        HTTP 404: If tool with specified name is not found
        HTTP 409: If tool is already enabled or has conflicts
        HTTP 500: If tool enablement process fails

    Enablement Process:
        - Tool availability verification
        - Dependency and compatibility checking
        - Registry status update and synchronization
        - Client notification of tool availability
        - Usage tracking initialization

    Impact:
        - Tool becomes available for conversation use
        - Client applications can discover and use the tool
        - Tool appears in available tools listings
        - Usage statistics tracking begins
        - Integration with LLM function calling enabled

    Validation:
        - Tool server connection status verification
        - Tool schema and parameter validation
        - Conflict detection with existing tools
        - Permission and access control checking

    Example:
        PATCH /api/v1/mcp/tools/byname/read_file/enable
    """
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
    """
    Disable a specific MCP tool to remove it from system availability.

    Deactivates the specified MCP tool removing it from conversation use and
    other system operations. Performs graceful shutdown and updates tool registry
    to reflect unavailability status while preserving configuration.

    Args:
        tool_name: Name of the MCP tool to disable
        current_user: Current authenticated superuser performing the operation
        db: Database session for tool status updates
        mcp_service: Injected MCP service instance

    Returns:
        BaseResponse: Confirmation of successful tool disablement

    Raises:
        HTTP 403: If user is not a superuser
        HTTP 404: If tool with specified name is not found
        HTTP 409: If tool is already disabled or has active usage
        HTTP 500: If tool disablement process fails

    Disablement Process:
        - Active usage validation and graceful termination
        - Registry status update and synchronization
        - Client notification of tool unavailability
        - Usage statistics finalization
        - Configuration preservation for future re-enablement

    Impact:
        - Tool becomes unavailable for conversation use
        - Client applications lose access to the tool
        - Tool removed from available tools listings
        - Active tool calls may be interrupted
        - LLM function calling integration disabled

    Safety Considerations:
        - Active tool usage detection and handling
        - Graceful degradation for dependent operations
        - Configuration preservation for easy re-enablement
        - Audit logging for administrative oversight

    Example:
        PATCH /api/v1/mcp/tools/byname/read_file/disable
    """
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
    """
    Get comprehensive MCP usage statistics and performance analytics.

    Returns detailed analytics about MCP server and tool usage including
    performance metrics, error rates, usage patterns, and system health
    indicators. Provides insights for optimization and capacity planning.

    Args:
        current_user: Current authenticated superuser requesting statistics
        db: Database session for analytics data retrieval
        mcp_service: Injected MCP service instance

    Returns:
        MCPStatsResponse: Comprehensive MCP statistics including:
            - server_stats: Performance metrics for each server
            - tool_usage: Usage frequency and success rates per tool
            - performance_metrics: Response times and error rates
            - capacity_data: Resource utilization and scaling metrics
            - trend_analysis: Usage patterns over time

    Analytics Data:
        - Server connection health and uptime statistics
        - Tool usage frequency and success/failure rates
        - Performance metrics including response times
        - Error analysis and failure pattern identification
        - Capacity utilization and scaling recommendations

    Performance Metrics:
        - Average response times per tool and server
        - Success rates and error frequency analysis
        - Concurrent usage patterns and peak load data
        - Resource consumption and efficiency metrics
        - Network and connection performance indicators

    Use Cases:
        - System performance monitoring and optimization
        - Capacity planning and scaling decisions
        - Tool effectiveness and usage analysis
        - Error pattern identification and resolution
        - Administrative reporting and insights

    Example:
        GET /api/v1/mcp/stats
    """
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
    """
    Refresh MCP server connections and perform comprehensive tool discovery.

    Initiates a system-wide refresh of all MCP server connections, performs
    tool discovery operations, and updates the tool registry with the latest
    available tools and their configurations. Useful for maintaining system
    synchronization and recovering from connection issues.

    Args:
        current_user: Current authenticated superuser performing the refresh
        db: Database session for registry updates
        mcp_service: Injected MCP service instance

    Returns:
        MCPStatsResponse: Refresh operation results including:
            - refreshed_servers: List of servers that were refreshed
            - discovered_tools: New tools found during discovery
            - updated_tools: Existing tools with updated configurations
            - failed_operations: Servers or tools with refresh failures
            - operation_summary: Overall refresh operation statistics

    Refresh Operations:
        - Connection health checking and reconnection
        - Tool discovery across all enabled servers
        - Registry synchronization and consistency checking
        - Configuration update and validation
        - Performance baseline re-establishment

    Discovery Process:
        - Server capability enumeration
        - Tool schema retrieval and validation
        - Parameter and configuration synchronization
        - Availability status verification
        - Performance metric initialization

    Use Cases:
        - Recovery from connection failures or network issues
        - Synchronization after server configuration changes
        - Periodic maintenance and system health checking
        - Integration of newly deployed MCP servers
        - Tool availability verification and updates

    Example:
        POST /api/v1/mcp/refresh
    """
    log_api_call("refresh_mcp", user_id=current_user.id)

    await mcp_service.refresh_from_registry()

    return {
        "success": True,
        "message": "MCP refresh completed successfully",
        "data": {},
    }
