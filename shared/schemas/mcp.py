"""Pydantic schemas for MCP (Model Context Protocol) APIs.

This module provides comprehensive Pydantic models for all MCP-related
API operations, ensuring type safety and consistent validation.
All fields have an explicit 'description' argument.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .base import BaseModelSchema
from .common import utcnow


class MCPServerCreateSchema(BaseModel):
    """Schema for creating a new MCP server."""

    model_config = ConfigDict(from_attributes=True)
    name: str = Field(..., description="Unique name for the MCP server")
    url: str = Field(..., description="Connection URL for the server")
    description: Optional[str] = Field(
        None, description="Optional description of the server"
    )
    transport: str = Field(
        default="http", description="Transport protocol (http, stdio, etc.)"
    )
    timeout: int = Field(
        default=30, ge=1, le=300, description="Connection timeout in seconds"
    )
    config: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional server configuration"
    )
    is_enabled: bool = Field(default=True, description="Whether the server is enabled")


class MCPServerUpdateSchema(BaseModel):
    """Schema for updating an MCP server."""

    model_config = ConfigDict(from_attributes=True)
    url: Optional[str] = Field(None, description="New connection URL")
    description: Optional[str] = Field(None, description="New description")
    transport: Optional[str] = Field(None, description="New transport protocol")
    timeout: Optional[int] = Field(
        None, ge=1, le=300, description="New timeout in seconds"
    )
    config: Optional[Dict[str, Any]] = Field(None, description="New configuration")
    is_enabled: Optional[bool] = Field(None, description="New enabled status")


class MCPServerSchema(BaseModelSchema):
    """Schema for MCP server responses."""

    name: str = Field(..., description="Server name")
    url: str = Field(..., description="Connection URL")
    description: Optional[str] = Field(None, description="Server description")
    transport: str = Field(..., description="Transport protocol")
    timeout: int = Field(..., description="Connection timeout in seconds")
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Server configuration"
    )
    is_enabled: bool = Field(..., description="Whether the server is enabled")
    is_connected: bool = Field(..., description="Current connection status")
    last_connected_at: Optional[datetime] = Field(
        None, description="Last successful connection time"
    )
    connection_errors: int = Field(
        ..., description="Number of recent connection errors"
    )
    tools_count: Optional[int] = Field(
        None, description="Number of tools from this server"
    )


class MCPToolCreateSchema(BaseModel):
    """Schema for creating/registering a new MCP tool."""

    model_config = ConfigDict(from_attributes=True)
    name: str = Field(..., description="Full name of the tool (server_toolname)")
    original_name: str = Field(..., description="Original tool name from the server")
    server_name: str = Field(
        ..., description="Name of the MCP server providing this tool"
    )
    description: Optional[str] = Field(None, description="Tool description")
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Tool parameters schema"
    )
    is_enabled: bool = Field(default=True, description="Whether the tool is enabled")


class MCPToolUpdateSchema(BaseModel):
    """Schema for updating an MCP tool."""

    model_config = ConfigDict(from_attributes=True)
    description: Optional[str] = Field(None, description="New description")
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="New parameters schema"
    )
    is_enabled: Optional[bool] = Field(None, description="New enabled status")


class MCPToolResponse(BaseModelSchema):
    """Schema for MCP tool responses."""

    name: str = Field(..., description="Full tool name")
    original_name: str = Field(..., description="Original tool name from server")
    description: Optional[str] = Field(None, description="Tool description")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Tool parameters schema"
    )
    is_enabled: bool = Field(..., description="Whether the tool is enabled")
    usage_count: int = Field(default=0, description="Total usage count")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    success_count: int = Field(default=0, description="Successful executions count")
    error_count: int = Field(default=0, description="Failed executions count")
    success_rate: float = Field(default=0.0, description="Success rate percentage")
    average_duration_ms: Optional[int] = Field(
        None, description="Average execution duration in ms"
    )
    server: MCPServerSchema = Field(..., description="Associated MCP server")


class MCPToolExecutionRequestSchema(BaseModel):
    """Schema for tool execution requests."""

    model_config = ConfigDict(from_attributes=True)
    tool_name: str = Field(..., description="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Tool parameters"
    )
    record_usage: bool = Field(
        default=True, description="Whether to record usage statistics"
    )


class MCPToolExecutionResultSchema(BaseModel):
    """Schema for tool execution results."""

    model_config = ConfigDict(from_attributes=True)
    success: bool = Field(..., description="Whether execution was successful")
    tool_name: str = Field(..., description="Name of the executed tool")
    server: str = Field(..., description="Server that executed the tool")
    content: List[Dict[str, Any]] = Field(
        default_factory=list, description="Execution result content"
    )
    error: Optional[str] = Field(None, description="Error message if execution failed")
    duration_ms: Optional[int] = Field(
        None, description="Execution duration in milliseconds"
    )
    raw_result: Optional[str] = Field(None, description="Raw result for debugging")


class MCPToolUsageStatsSchema(BaseModel):
    """Schema for tool usage statistics."""

    model_config = ConfigDict(from_attributes=True)
    tool_name: str = Field(..., description="Tool name")
    server_name: str = Field(..., description="Server name")
    usage_count: int = Field(..., description="Total usage count")
    success_count: int = Field(..., description="Successful executions")
    error_count: int = Field(..., description="Failed executions")
    success_rate: float = Field(..., description="Success rate percentage")
    average_duration_ms: Optional[int] = Field(
        None, description="Average duration in ms"
    )
    last_used_at: Optional[datetime] = Field(None, description="Last usage time")


class MCPServerListResponse(BaseModel):
    """Response schema for listing MCP servers."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(
        default=True, description="Whether the request was successful"
    )
    message: str = Field(..., description="Response message")
    data: List[MCPServerSchema] = Field(..., description="List of MCP servers")


class MCPToolListResponse(BaseModel):
    """Response schema for listing MCP tools."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(
        default=True, description="Whether the request was successful"
    )
    message: str = Field(..., description="Response message")
    available_tools: List[MCPToolResponse] = Field(
        ..., description="List of available tools"
    )
    openai_tools: List[Dict[str, Any]] = Field(
        ..., description="Tools in OpenAI format"
    )
    servers: List[Dict[str, Any]] = Field(..., description="Server status information")
    enabled_count: int = Field(..., description="Number of enabled tools")
    total_count: int = Field(..., description="Total number of tools")


class MCPToolsResponse(BaseModel):
    """Response schema for simple MCP tools list."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(
        default=True, description="Whether the request was successful"
    )
    message: str = Field(..., description="Response message")
    data: List[MCPToolResponse] = Field(..., description="List of MCP tools")


class MCPStatsResponse(BaseModel):
    """Response schema for MCP statistics."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(
        default=True, description="Whether the request was successful"
    )
    message: str = Field(..., description="Response message")
    data: Dict[str, Any] = Field(..., description="Statistics data")
    is_enabled: bool = Field(..., description="Tool enabled status")


class MCPDiscoveryRequestSchema(BaseModel):
    """Schema for tool discovery requests."""

    model_config = ConfigDict(from_attributes=True)
    server_name: Optional[str] = Field(
        None, description="Specific server to discover from"
    )
    force_refresh: bool = Field(
        default=False, description="Force refresh even if disabled"
    )


class MCPDiscoveryResultSchema(BaseModel):
    """Schema for tool discovery results."""

    model_config = ConfigDict(from_attributes=True)
    success: bool = Field(..., description="Whether discovery was successful")
    server_name: str = Field(..., description="Server name")
    new_tools: int = Field(default=0, description="Number of new tools discovered")
    updated_tools: int = Field(default=0, description="Number of tools updated")
    total_discovered: int = Field(default=0, description="Total tools found")
    errors: List[str] = Field(default_factory=list, description="Discovery errors")
    error: Optional[str] = Field(None, description="Main error message if failed")


class MCPHealthStatusSchema(BaseModel):
    """Schema for MCP health status."""

    model_config = ConfigDict(from_attributes=True)
    mcp_available: bool = Field(..., description="Whether MCP is available")
    initialized: bool = Field(..., description="Whether MCP client is initialized")
    total_servers: int = Field(..., description="Total configured servers")
    healthy_servers: int = Field(..., description="Number of healthy servers")
    unhealthy_servers: int = Field(..., description="Number of unhealthy servers")
    tools_count: int = Field(..., description="Total available tools")
    server_status: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Detailed status for each server"
    )
    registry_stats: Optional[Dict[str, Any]] = Field(
        None, description="Registry statistics"
    )


class MCPConnectionStatusSchema(BaseModel):
    """Schema for connection status updates."""

    model_config = ConfigDict(from_attributes=True)
    server_name: str = Field(..., description="Server name")
    is_connected: bool = Field(..., description="Connection status")
    connected_at: Optional[datetime] = Field(None, description="Connection timestamp")
    error_message: Optional[str] = Field(
        None, description="Error message if connection failed"
    )


class MCPBatchUsageSchema(BaseModel):
    """Schema for batch usage statistics updates."""

    model_config = ConfigDict(from_attributes=True)
    tool_usages: List[Dict[str, Any]] = Field(
        ..., description="List of tool usage records to batch update"
    )


class MCPConnectionTestSchema(BaseModel):
    """Schema for MCP server connection test results."""

    model_config = ConfigDict(from_attributes=True)
    connected: bool = Field(..., description="Whether connection was successful")
    server_name: str = Field(..., description="Server name")
    response_time: Optional[int] = Field(
        None, description="Response time in milliseconds"
    )
    server_version: Optional[str] = Field(
        None, description="Server version if available"
    )
    capabilities: List[str] = Field(
        default_factory=list, description="Server capabilities"
    )
    tools_available: Optional[int] = Field(
        None, description="Number of tools available"
    )
    error: Optional[str] = Field(None, description="Error message if connection failed")
    tested_at: datetime = Field(
        default_factory=utcnow, description="Test timestamp"
    )


class MCPListFiltersSchema(BaseModel):
    """Schema for list operation filters."""

    model_config = ConfigDict(from_attributes=True)
    enabled_only: bool = Field(
        default=False, description="Filter to enabled items only"
    )
    connected_only: bool = Field(
        default=False, description="Filter to connected servers only"
    )
    server_name: Optional[str] = Field(
        None, description="Filter by specific server name"
    )
    limit: Optional[int] = Field(
        None, ge=1, le=1000, description="Maximum number of results"
    )
    offset: Optional[int] = Field(None, ge=0, description="Offset for pagination")


class OpenAIToolSchema(BaseModel):
    """OpenAI-compatible tool schema."""

    model_config = ConfigDict(from_attributes=True)
    type: str = Field(default="function", description="Tool type")
    function: Dict[str, Any] = Field(..., description="Function definition")


class OpenAIToolCallSchema(BaseModel):
    """OpenAI tool call schema."""

    model_config = ConfigDict(from_attributes=True)
    id: str = Field(..., description="Tool call ID")
    type: str = Field(default="function", description="Call type")
    function: Dict[str, Any] = Field(..., description="Function call details")


class MCPOpenAIToolsResponseSchema(BaseModel):
    """Schema for OpenAI-compatible tools response."""

    model_config = ConfigDict(from_attributes=True)
    tools: List[OpenAIToolSchema] = Field(
        ..., description="Available tools in OpenAI format"
    )
    total_count: int = Field(..., description="Total number of available tools")
    enabled_count: int = Field(..., description="Number of enabled tools")
