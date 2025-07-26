"""
FastMCP client service for tool integration and external function execution.

This service provides a thin, stateless proxy for MCP servers that loads
enabled servers/tools from the registry on demand. All tool/server metadata
is managed by the registry, with minimal in-memory caching for performance.

Refactored to:
- Remove all persistent tool/server state except lightweight caching
- Load enabled servers/tools from registry only
- Remove all persistence/sync logic and decorators
- Be a thin proxy to registry data for tool execution
- Remove OpenAI-specific formatting (handled in API layer)
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Tuple

from fastmcp import Client
from fastmcp.client import StreamableHttpTransport
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..core.exceptions import ExternalServiceError
from ..core.logging import get_api_logger
from ..schemas.mcp import (
    MCPServerSchema, MCPToolSchema, MCPToolExecutionRequestSchema,
    MCPToolExecutionResultSchema, MCPHealthStatusSchema, MCPListFiltersSchema
)

logger = get_api_logger("mcp_client")


class FastMCPClientService:
    """
    Simplified FastMCP client service for tool calling and external integrations.

    This service is now a thin, stateless proxy that:
    - Loads enabled servers/tools from registry on startup and on-demand
    - Maintains minimal in-memory cache for performance
    - Focuses solely on tool execution, not persistence
    - Delegates all tool/server management to MCPRegistryService
    
    Key Features:
    - Lightweight in-memory caching of active connections
    - On-demand loading from registry
    - Simplified error handling without decorators
    - No tool/server registration or discovery
    - Clean separation of concerns
    """

    def __init__(self, registry_service=None):
        """
        Initialize FastMCP client service.
        
        Args:
            registry_service: Optional MCPRegistryService instance for testing
        """
        self.clients: Dict[str, Client] = {}
        self._cache_timeout = 300  # 5 minutes cache timeout
        self._last_refresh = 0
        self._cached_servers: Dict[str, MCPServerSchema] = {}
        self._cached_tools: Dict[str, MCPToolSchema] = {}
        self.is_initialized = False
        self._registry_service = registry_service

        logger.info("FastMCP client service initialized")

    async def _get_registry_service(self, db_session: Optional[AsyncSession] = None):
        """Get registry service instance with dependency injection."""
        if self._registry_service:
            return self._registry_service
            
        if not db_session:
            from ..database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                from .mcp_registry import MCPRegistryService
                return MCPRegistryService(db)
        else:
            from .mcp_registry import MCPRegistryService
            return MCPRegistryService(db_session)

    async def _should_refresh_cache(self) -> bool:
        """Check if cache should be refreshed."""
        return (time.time() - self._last_refresh) > self._cache_timeout

    async def _refresh_from_registry(self, db_session: Optional[AsyncSession] = None):
        """Refresh servers and tools from registry."""
        if not settings.mcp_enabled:
            logger.info("MCP is disabled, skipping registry refresh")
            return

        try:
            registry = await self._get_registry_service(db_session)
            
            # Load enabled servers
            filters = MCPListFiltersSchema(enabled_only=True)
            servers = await registry.list_servers(filters)
            
            # Update cache
            self._cached_servers = {server.name: server for server in servers}
            
            # Load enabled tools for enabled servers
            tools = await registry.list_tools(filters)
            self._cached_tools = {tool.name: tool for tool in tools if tool.server.is_enabled}
            
            self._last_refresh = time.time()
            
            logger.info(
                f"Refreshed from registry: {len(self._cached_servers)} servers, "
                f"{len(self._cached_tools)} tools"
            )
            
        except Exception as e:
            logger.error(f"Failed to refresh from registry: {e}")
            raise ExternalServiceError(f"Registry refresh failed: {e}")

    async def initialize(self, db_session: Optional[AsyncSession] = None):
        """Initialize connections to MCP servers from registry."""
        if not settings.mcp_enabled:
            logger.warning("MCP is disabled - cannot initialize MCP clients")
            self.is_initialized = False
            return

        try:
            # Refresh from registry
            await self._refresh_from_registry(db_session)
            
            if not self._cached_servers:
                logger.warning("No enabled MCP servers found in registry")
                self.is_initialized = False
                return

            # Connect to enabled servers
            successful_connections = 0
            for server_name, server in self._cached_servers.items():
                try:
                    await self._connect_server(server)
                    successful_connections += 1
                    logger.info(f"✅ Connected to MCP server: {server_name}")
                except Exception as e:
                    logger.error(f"❌ Failed to connect to MCP server {server_name}: {e}")

            tools_count = len([t for t in self._cached_tools.values() 
                             if t.server.name in self.clients])
            
            self.is_initialized = True
            logger.info(
                f"FastMCP initialization completed: {successful_connections}/"
                f"{len(self._cached_servers)} servers, {tools_count} tools available"
            )

        except Exception as e:
            logger.error(f"FastMCP client initialization failed: {e}")
            logger.warning("Continuing without MCP integration")
            self.is_initialized = False

    async def _connect_server(self, server: MCPServerSchema):
        """Connect to a specific MCP server."""
        try:
            # Create FastMCP client with HTTP transport
            transport = StreamableHttpTransport(server.url)
            client = Client(transport, timeout=server.timeout)

            # Test connection
            async with client:
                # Store client
                self.clients[server.name] = client
                logger.info(f"Connected to MCP server: {server.name} ({server.url})")

        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server.name}: {e}")
            # Remove client if it was added
            self.clients.pop(server.name, None)
            raise

    async def _discover_server_tools(self, server_url: str, timeout: int) -> List[Dict[str, Any]]:
        """
        Discover tools from a server URL for registry use.
        
        This is a utility method used by the registry for tool discovery.
        """
        try:
            transport = StreamableHttpTransport(server_url)
            client = Client(transport, timeout=timeout)
            
            async with client:
                tools_response = await client.list_tools()
                
                # Handle different response formats
                if hasattr(tools_response, "tools"):
                    tools_list = tools_response.tools
                elif isinstance(tools_response, dict) and "tools" in tools_response:
                    tools_list = tools_response["tools"]
                elif isinstance(tools_response, list):
                    tools_list = tools_response
                else:
                    logger.warning(f"Unexpected tools response format: {type(tools_response)}")
                    return []

                discovered_tools = []
                for tool_info in tools_list:
                    # Handle different tool info structures
                    if hasattr(tool_info, "name"):
                        tool_name = tool_info.name
                        tool_desc = getattr(tool_info, "description", "")
                        tool_schema = getattr(tool_info, "inputSchema", None)
                    elif isinstance(tool_info, dict):
                        tool_name = tool_info.get("name", "unknown")
                        tool_desc = tool_info.get("description", "")
                        tool_schema = tool_info.get("inputSchema", None)
                    else:
                        logger.warning(f"Unexpected tool info format: {type(tool_info)}")
                        continue

                    # Process schema
                    if tool_schema:
                        if hasattr(tool_schema, "model_dump"):
                            schema_dict = tool_schema.model_dump()
                        elif isinstance(tool_schema, dict):
                            schema_dict = tool_schema
                        else:
                            schema_dict = {"type": "object", "properties": {}, "required": []}
                    else:
                        schema_dict = {"type": "object", "properties": {}, "required": []}

                    discovered_tools.append({
                        "name": tool_name,
                        "description": tool_desc,
                        "parameters": schema_dict,
                    })

                return discovered_tools

        except Exception as e:
            logger.error(f"Failed to discover tools from {server_url}: {e}")
            raise

    async def call_tool(
        self, 
        request: MCPToolExecutionRequestSchema,
        db_session: Optional[AsyncSession] = None
    ) -> MCPToolExecutionResultSchema:
        """
        Execute a tool on an MCP server.

        Args:
            request: Tool execution request
            db_session: Optional database session for registry operations

        Returns:
            Tool execution result
        """
        if not self.is_initialized:
            raise ExternalServiceError("MCP client not initialized")

        # Refresh cache if needed
        if await self._should_refresh_cache():
            await self._refresh_from_registry(db_session)

        # Get tool from cache
        tool = self._cached_tools.get(request.tool_name)
        if not tool:
            available_tools = list(self._cached_tools.keys())
            raise ExternalServiceError(
                f"Tool '{request.tool_name}' not found. Available: {available_tools}"
            )

        # Check if tool is enabled
        if not tool.is_enabled:
            raise ExternalServiceError(f"Tool '{request.tool_name}' is disabled")

        # Check if server is connected
        server_name = tool.server.name
        if server_name not in self.clients:
            raise ExternalServiceError(f"Server '{server_name}' not connected")

        client = self.clients[server_name]
        start_time = time.time()
        success = False

        try:
            # Execute the tool
            async with client:
                result = await client.call_tool(
                    name=tool.original_name, 
                    arguments=request.parameters
                )
            success = True
            
            # Format the response
            formatted_result = MCPToolExecutionResultSchema(
                success=True,
                tool_name=request.tool_name,
                server=server_name,
                content=self._format_tool_content(result),
                duration_ms=int((time.time() - start_time) * 1000),
                raw_result=self._serialize_result(result),
            )

        except Exception as e:
            success = False
            formatted_result = MCPToolExecutionResultSchema(
                success=False,
                tool_name=request.tool_name,
                server=server_name,
                content=[],
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )
            raise ExternalServiceError(f"Tool execution failed: {e}")

        finally:
            # Record usage if requested
            if request.record_usage:
                try:
                    duration_ms = int((time.time() - start_time) * 1000)
                    registry = await self._get_registry_service(db_session)
                    await registry.record_tool_usage(request.tool_name, success, duration_ms)
                except Exception as e:
                    logger.warning(f"Failed to record tool usage: {e}")

        logger.info(f"Tool '{request.tool_name}' executed successfully on '{server_name}'")
        return formatted_result

    def _format_tool_content(self, result: Any) -> List[Dict[str, Any]]:
        """Format tool execution content."""
        content = []
        
        # Process result content
        if hasattr(result, "content") and result.content:
            for content_item in result.content:
                if hasattr(content_item, "text"):
                    content.append({"type": "text", "text": content_item.text})
                elif hasattr(content_item, "data"):
                    content.append({
                        "type": "data",
                        "data": content_item.data,
                        "mimeType": getattr(content_item, "mimeType", "application/octet-stream"),
                    })
                elif isinstance(content_item, dict):
                    if "text" in content_item:
                        content.append({"type": "text", "text": content_item["text"]})
                    elif "data" in content_item:
                        content.append({
                            "type": "data",
                            "data": content_item["data"],
                            "mimeType": content_item.get("mimeType", "application/octet-stream"),
                        })
        elif isinstance(result, dict) and "content" in result:
            for content_item in result["content"]:
                if isinstance(content_item, dict):
                    if "text" in content_item:
                        content.append({"type": "text", "text": content_item["text"]})
                    elif "data" in content_item:
                        content.append({
                            "type": "data",
                            "data": content_item["data"],
                            "mimeType": content_item.get("mimeType", "application/octet-stream"),
                        })

        # If no content was found, add the raw result as text
        if not content:
            content.append({"type": "text", "text": str(result)})
            
        return content

    def _serialize_result(self, result: Any) -> str:
        """Serialize result for logging/debugging."""
        try:
            if hasattr(result, "model_dump"):
                return json.dumps(result.model_dump(), indent=2)
            elif isinstance(result, (dict, list)):
                return json.dumps(result, indent=2)
            else:
                return str(result)
        except Exception:
            return str(result)

    async def get_available_tools(
        self, 
        filters: Optional[MCPListFiltersSchema] = None,
        db_session: Optional[AsyncSession] = None
    ) -> List[MCPToolSchema]:
        """
        Get available tools from registry.

        Args:
            filters: Optional filters for tools
            db_session: Optional database session

        Returns:
            List of available tools
        """
        if not self.is_initialized:
            logger.warning("MCP client not initialized - returning empty tools list")
            return []

        # Refresh cache if needed
        if await self._should_refresh_cache():
            await self._refresh_from_registry(db_session)

        # Apply filters to cached tools
        tools = list(self._cached_tools.values())
        
        if filters:
            if filters.enabled_only:
                tools = [t for t in tools if t.is_enabled and t.server.is_enabled]
            if filters.server_name:
                tools = [t for t in tools if t.server.name == filters.server_name]

        return tools

    async def execute_tool_calls(
        self, 
        tool_calls: List[Dict[str, Any]],
        db_session: Optional[AsyncSession] = None
    ) -> List[MCPToolExecutionResultSchema]:
        """
        Execute multiple tool calls (for OpenAI compatibility).

        Args:
            tool_calls: List of tool calls from OpenAI format
            db_session: Optional database session

        Returns:
            List of execution results
        """
        if not self.is_initialized:
            raise ExternalServiceError("MCP client not initialized")

        results = []
        for tool_call in tool_calls:
            try:
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])

                request = MCPToolExecutionRequestSchema(
                    tool_name=function_name,
                    parameters=function_args,
                    record_usage=True
                )
                
                result = await self.call_tool(request, db_session)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to execute tool call {tool_call.get('id', 'unknown')}: {e}")
                error_result = MCPToolExecutionResultSchema(
                    success=False,
                    tool_name=tool_call.get("function", {}).get("name", "unknown"),
                    server="unknown",
                    content=[],
                    error=str(e)
                )
                results.append(error_result)

        return results

    async def health_check(
        self, 
        db_session: Optional[AsyncSession] = None
    ) -> MCPHealthStatusSchema:
        """
        Check health of MCP servers.

        Args:
            db_session: Optional database session for registry access

        Returns:
            Health status
        """
        health_status = MCPHealthStatusSchema(
            mcp_available=settings.mcp_enabled,
            initialized=self.is_initialized,
            total_servers=len(self._cached_servers),
            healthy_servers=0,
            unhealthy_servers=0,
            tools_count=len(self._cached_tools),
            server_status={}
        )

        if not self.is_initialized:
            return health_status

        # Check each connected server
        for server_name, client in self.clients.items():
            try:
                async with client:
                    await asyncio.wait_for(client.list_tools(), timeout=5)

                tools_count = len([t for t in self._cached_tools.values() 
                                 if t.server.name == server_name])

                health_status.server_status[server_name] = {
                    "status": "healthy",
                    "tools_count": tools_count,
                    "connected": True,
                }
                health_status.healthy_servers += 1

            except Exception as e:
                health_status.server_status[server_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "connected": False,
                }
                health_status.unhealthy_servers += 1

        # Add servers that failed to connect
        for server_name in self._cached_servers:
            if server_name not in self.clients:
                health_status.server_status[server_name] = {
                    "status": "disconnected",
                    "error": "Failed to connect",
                    "connected": False,
                }
                health_status.unhealthy_servers += 1

        # Add registry statistics
        try:
            registry = await self._get_registry_service(db_session)
            all_servers = await registry.list_servers()
            all_tools = await registry.list_tools()

            enabled_servers = sum(1 for s in all_servers if s.is_enabled)
            enabled_tools = sum(1 for t in all_tools if t.is_enabled)

            health_status.registry_stats = {
                "total_servers": len(all_servers),
                "enabled_servers": enabled_servers,
                "disabled_servers": len(all_servers) - enabled_servers,
                "total_tools": len(all_tools),
                "enabled_tools": enabled_tools,
                "disabled_tools": len(all_tools) - enabled_tools,
            }
        except Exception as e:
            logger.warning(f"Failed to get registry statistics: {e}")
            health_status.registry_stats = {"error": "Registry unavailable"}

        return health_status

    async def disconnect_all(self):
        """Disconnect from all MCP servers and clear cache."""
        disconnected_servers = []

        for server_name, client in self.clients.items():
            try:
                await client.close()
                disconnected_servers.append(server_name)
                logger.info(f"Disconnected from MCP server: {server_name}")
            except Exception as e:
                logger.warning(f"Error disconnecting from {server_name}: {e}")

        # Clear all state
        self.clients.clear()
        self._cached_servers.clear()
        self._cached_tools.clear()
        self._last_refresh = 0
        self.is_initialized = False

        logger.info(f"Disconnected from {len(disconnected_servers)} MCP servers")

    async def refresh_from_registry(self, db_session: Optional[AsyncSession] = None):
        """
        Force refresh from registry and reconnect to servers.
        
        Args:
            db_session: Optional database session
        """
        logger.info("Force refreshing MCP client from registry")
        
        # Disconnect existing clients
        await self.disconnect_all()
        
        # Re-initialize from registry
        await self.initialize(db_session)


# Global instance management (simplified)
_mcp_client_instance: Optional[FastMCPClientService] = None


async def get_mcp_client(
    db_session: Optional[AsyncSession] = None,
    force_reinit: bool = False
) -> FastMCPClientService:
    """
    Get or create the global MCP client instance.
    
    Args:
        db_session: Optional database session for initialization
        force_reinit: Force re-initialization even if already initialized
        
    Returns:
        FastMCPClientService instance
    """
    global _mcp_client_instance

    if _mcp_client_instance is None or force_reinit:
        _mcp_client_instance = FastMCPClientService()
        await _mcp_client_instance.initialize(db_session)

    return _mcp_client_instance


async def cleanup_mcp_client():
    """Cleanup the global MCP client instance."""
    global _mcp_client_instance

    if _mcp_client_instance is not None:
        await _mcp_client_instance.disconnect_all()
        _mcp_client_instance = None
