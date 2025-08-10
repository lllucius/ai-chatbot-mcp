"""MCP service for registry management, FastMCP client proxy, and tool execution.

This service provides registry CRUD operations for MCP servers and tools, FastMCP
client proxy logic for tool execution and health checking, with tool execution
featuring retry, parallelization, and API response result caching.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional

from fastmcp import Client
from fastmcp.client import StreamableHttpTransport
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.schemas.mcp import (
    MCPDiscoveryResultSchema,
    MCPHealthStatusSchema,
    MCPListFiltersSchema,
    MCPServerCreateSchema,
    MCPServerSchema,
    MCPServerUpdateSchema,
    MCPToolCreateSchema,
    MCPToolExecutionRequestSchema,
    MCPToolExecutionResultSchema,
    MCPToolResponse,
    MCPToolUpdateSchema,
    MCPToolUsageStatsSchema,
)

from ..config import settings
from ..core.exceptions import ExternalServiceError
from ..core.logging import get_api_logger
from ..models.mcp_server import MCPServer
from ..models.mcp_tool import MCPTool
from ..utils.timestamp import utcnow

logger = get_api_logger("mcp_service")


class MCPService:
    """MCP service for registry, client proxy, and tool execution.

    Pass a database session when instantiating. All registry and client operations
    as well as tool execution (with retry, parallelization, caching) are available
    on this class. This is the single entry point for all MCP tool operations.
    """

    def __init__(self, db_session: AsyncSession):
        """Initialize the MCP service.

        Args:
            db_session: Database session for MCP operations.

        """
        self.db: AsyncSession = db_session
        self.clients: Dict[str, Client] = {}
        self.is_initialized = False
        logger.info("MCPService initialized")

    async def create_server(
        self, server_data: MCPServerCreateSchema, auto_discover: bool = True
    ) -> MCPServerSchema:
        """Create a new MCP server registration.

        Args:
            server_data: Server configuration data.
            auto_discover: Whether to automatically discover tools.

        Returns:
            Created server schema.

        """
        server = MCPServer(
            name=server_data.name,
            url=server_data.url,
            description=server_data.description,
            transport=server_data.transport,
            timeout=server_data.timeout,
            config=server_data.config or {},
            is_enabled=server_data.is_enabled,
            is_connected=False,
            connection_errors=0,
        )
        self.db.add(server)
        await self.db.commit()
        await self.db.refresh(server)
        logger.info(f"Created MCP server registration: {server_data.name}")

        if server_data.is_enabled and auto_discover:
            try:
                discovery_result = await self.discover_tools_from_server(
                    server_data.name
                )
                logger.info(
                    f"Automatic tool discovery for new server {server_data.name}: "
                    f"{discovery_result.new_tools} new, {discovery_result.updated_tools} updated"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to auto-discover tools for new server {server_data.name}: {e}"
                )

        return MCPServerSchema.model_validate(server)

    async def get_server(self, name: str) -> Optional[MCPServerSchema]:
        """Get a server by name.

        Args:
            name: Name of the server to retrieve.

        Returns:
            Server schema if found, None otherwise.

        """
        result = await self.db.execute(
            select(MCPServer)
            .options(selectinload(MCPServer.tools))
            .where(MCPServer.name == name)
        )
        server = result.scalar_one_or_none()
        if server:
            # Create MCPServerSchema directly with explicit field assignment
            return MCPServerSchema(
                name=server.name,
                url=server.url,
                description=server.description,
                transport=server.transport,
                timeout=server.timeout,
                config=server.config,
                is_enabled=server.is_enabled,
                is_connected=server.is_connected,
                last_connected_at=server.last_connected_at,
                connection_errors=server.connection_errors,
                tools_count=len(server.tools),
            )
        return None

    async def list_servers(
        self, filters: Optional[MCPListFiltersSchema] = None
    ) -> List[MCPServerSchema]:
        """List all servers with optional filtering.

        Args:
            filters: Optional filters to apply.

        Returns:
            List of server schemas.

        """
        query = select(MCPServer).options(selectinload(MCPServer.tools))
        if filters:
            filter_conditions = []
            if filters.enabled_only:
                filter_conditions.append(MCPServer.is_enabled)
            if filters.connected_only:
                filter_conditions.append(MCPServer.is_connected)
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
            if filters.limit:
                query = query.limit(filters.limit)
            if filters.offset:
                query = query.offset(filters.offset)
        result = await self.db.execute(query.order_by(MCPServer.name))
        servers = result.scalars().all()
        server_schemas = []
        for server in servers:
            # Create MCPServerSchema directly with explicit field assignment
            server_schema = MCPServerSchema(
                name=server.name,
                url=server.url,
                description=server.description,
                transport=server.transport,
                timeout=server.timeout,
                config=server.config,
                is_enabled=server.is_enabled,
                is_connected=server.is_connected,
                last_connected_at=server.last_connected_at,
                connection_errors=server.connection_errors,
                tools_count=len(server.tools),
            )
            server_schemas.append(server_schema)
        return server_schemas

    async def update_server(
        self, name: str, updates: MCPServerUpdateSchema
    ) -> Optional[MCPServerSchema]:
        """Update an existing server configuration."""
        server = await self.db.execute(select(MCPServer).where(MCPServer.name == name))
        server = server.scalar_one_or_none()
        if not server:
            return None
        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(server, key):
                setattr(server, key, value)
        await self.db.commit()
        await self.db.refresh(server)
        logger.info(f"Updated MCP server: {name}")
        return MCPServerSchema.model_validate(server)

    async def delete_server(self, name: str) -> bool:
        """Delete a server and its associated tools."""
        server = await self.db.execute(select(MCPServer).where(MCPServer.name == name))
        server = server.scalar_one_or_none()
        if not server:
            return False
        await self.db.delete(server)
        await self.db.commit()
        logger.info(f"Deleted MCP server: {name}")
        return True

    async def enable_server(
        self, name: str, auto_discover: bool = True
    ) -> Optional[MCPServerSchema]:
        """Enable a server and optionally discover its tools.

        Args:
            name: Name of the server to enable.
            auto_discover: Whether to automatically discover tools.

        Returns:
            Updated server schema if successful.

        """
        server = await self.get_server(name)
        if not server:
            return None
        was_enabled = server.is_enabled
        updates = MCPServerUpdateSchema(is_enabled=True)
        updated_server = await self.update_server(name, updates)
        if not updated_server:
            return None
        if auto_discover:
            discovery_result = await self._auto_discover_on_server_change(
                name, was_enabled, True
            )
            if discovery_result:
                logger.info(
                    f"Automatic tool discovery triggered for {name}: "
                    f"{discovery_result.new_tools} new, {discovery_result.updated_tools} updated"
                )
        return updated_server

    async def disable_server(self, name: str) -> Optional[MCPServerSchema]:
        """Disable a server.

        Args:
            name: Name of the server to disable.

        Returns:
            Updated server schema if successful.

        """
        updates = MCPServerUpdateSchema(is_enabled=False)
        return await self.update_server(name, updates)

    async def update_connection_status(
        self, name: str, is_connected: bool, increment_errors: bool = False
    ) -> Optional[MCPServerSchema]:
        """Update the connection status of a server."""
        updates_dict = {
            "is_connected": is_connected,
        }
        if is_connected:
            updates_dict["last_connected_at"] = utcnow()
            updates_dict["connection_errors"] = 0
        elif increment_errors:
            server = await self.get_server(name)
            if server:
                updates_dict["connection_errors"] = server.connection_errors + 1
        updates = MCPServerUpdateSchema(**updates_dict)
        return await self.update_server(name, updates)

    async def register_tool(
        self, tool_data: MCPToolCreateSchema
    ) -> Optional[MCPToolResponse]:
        """Register a new tool for a server.

        Args:
            tool_data: Tool configuration data.

        Returns:
            Created tool schema if successful.

        """
        server_result = await self.db.execute(
            select(MCPServer).where(MCPServer.name == tool_data.server_name)
        )
        server = server_result.scalar_one_or_none()
        if not server:
            logger.error(f"Server not found: {tool_data.server_name}")
            return None
        existing_tool = await self.db.execute(
            select(MCPTool).where(MCPTool.name == tool_data.name)
        )
        existing_tool = existing_tool.scalar_one_or_none()
        if existing_tool:
            existing_tool.description = tool_data.description
            existing_tool.parameters = tool_data.parameters or {}
            existing_tool.is_enabled = tool_data.is_enabled
            await self.db.commit()
            await self.db.refresh(existing_tool, ["server"])
            return MCPToolResponse.model_validate(existing_tool)
        tool = MCPTool(
            name=tool_data.name,
            original_name=tool_data.original_name,
            server_id=server.id,
            description=tool_data.description,
            parameters=tool_data.parameters or {},
            is_enabled=tool_data.is_enabled,
        )
        self.db.add(tool)
        await self.db.commit()
        await self.db.refresh(tool, ["server"])
        logger.info(
            f"Registered tool: {tool_data.name} for server {tool_data.server_name}"
        )
        return MCPToolResponse.model_validate(tool)

    async def get_tool(self, tool_name: str) -> Optional[MCPToolResponse]:
        """Get a tool by server name and tool name."""
        result = await self.db.execute(
            select(MCPTool)
            .options(selectinload(MCPTool.server))
            .where(MCPTool.name == tool_name)
        )
        tool = result.scalar_one_or_none()
        if tool:
            return MCPToolResponse.model_validate(tool)
        return None

    async def list_tools(
        self, filters: Optional[MCPListFiltersSchema] = None
    ) -> List[MCPToolResponse]:
        """List all tools with optional filtering."""
        query = select(MCPTool).options(selectinload(MCPTool.server))
        if filters:
            filter_conditions = []
            if filters.server_name:
                query = query.join(MCPServer)
                filter_conditions.append(MCPServer.name == filters.server_name)
            if filters.enabled_only:
                filter_conditions.append(MCPTool.is_enabled)
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
            if filters.limit:
                query = query.limit(filters.limit)
            if filters.offset:
                query = query.offset(filters.offset)
        result = await self.db.execute(query.order_by(MCPTool.name))
        tools = result.scalars().all()
        return [MCPToolResponse.model_validate(tool) for tool in tools]

    async def update_tool(
        self, tool_name: str, updates: MCPToolUpdateSchema
    ) -> Optional[MCPToolResponse]:
        """Update an existing tool configuration."""
        tool = await self.db.execute(
            select(MCPTool)
            .options(selectinload(MCPTool.server))
            .where(MCPTool.name == tool_name)
        )
        tool = tool.scalar_one_or_none()
        if not tool:
            return None
        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(tool, key):
                setattr(tool, key, value)
        await self.db.commit()
        await self.db.refresh(tool, ["server"])
        logger.info(f"Updated tool: {tool_name}")
        return MCPToolResponse.model_validate(tool)

    async def enable_tool(self, tool_name: str) -> bool:
        """Enable a tool.

        Args:
            tool_name: Name of the tool to enable.

        Returns:
            True if tool was enabled successfully.

        """
        result = await self.db.execute(
            update(MCPTool).where(MCPTool.name == tool_name).values(is_enabled=True)
        )
        await self.db.commit()
        if result.rowcount > 0:
            logger.info(f"Enabled tool: {tool_name}")
            return True
        return False

    async def disable_tool(self, tool_name: str) -> bool:
        """Disable a tool.

        Args:
            tool_name: Name of the tool to disable.

        Returns:
            True if tool was disabled successfully.

        """
        result = await self.db.execute(
            update(MCPTool).where(MCPTool.name == tool_name).values(is_enabled=False)
        )
        await self.db.commit()
        if result.rowcount > 0:
            logger.info(f"Disabled tool: {tool_name}")
            return True
        return False

    async def record_tool_usage(
        self, tool_name: str, success: bool, duration_ms: Optional[int] = None
    ) -> bool:
        """Record usage statistics for a tool.

        Args:
            tool_name: Name of the tool.
            success: Whether the tool execution was successful.
            duration_ms: Duration of execution in milliseconds.

        Returns:
            True if usage was recorded successfully.

        """
        tool = await self.db.execute(select(MCPTool).where(MCPTool.name == tool_name))
        tool = tool.scalar_one_or_none()
        if not tool:
            return False
        tool.record_usage(success, duration_ms)
        await self.db.commit()
        return True

    async def batch_record_tool_usage(self, usage_records: List[Dict[str, Any]]) -> int:
        """Record usage statistics for multiple tools in batch.

        Args:
            usage_records: List of usage record dictionaries.

        Returns:
            Number of records successfully processed.

        """
        processed_count = 0
        for record in usage_records:
            try:
                tool_name = record.get("tool_name")
                success = record.get("success", True)
                duration_ms = record.get("duration_ms")
                if tool_name and await self.record_tool_usage(
                    tool_name, success, duration_ms
                ):
                    processed_count += 1
            except Exception as e:
                logger.warning(
                    f"Failed to record usage for tool {record.get('tool_name')}: {e}"
                )
        return processed_count

    async def get_tool_stats(
        self, server_name: Optional[str] = None, limit: int = 10
    ) -> List[MCPToolUsageStatsSchema]:
        """Get usage statistics for tools.

        Args:
            server_name: Optional server name to filter by.
            limit: Maximum number of results to return.

        Returns:
            List of tool usage statistics.

        """
        query = select(MCPTool).options(selectinload(MCPTool.server))
        if server_name:
            query = query.join(MCPServer).where(MCPServer.name == server_name)
        result = await self.db.execute(
            query.order_by(MCPTool.usage_count.desc()).limit(limit)
        )
        tools = result.scalars().all()
        stats = []
        for tool in tools:
            stats.append(
                MCPToolUsageStatsSchema(
                    tool_name=tool.name,
                    server_name=tool.server.name,
                    usage_count=tool.usage_count,
                    success_count=tool.success_count,
                    error_count=tool.error_count,
                    success_rate=tool.success_rate,
                    average_duration_ms=tool.average_duration_ms,
                    last_used_at=tool.last_used_at,
                    is_enabled=tool.is_enabled,
                )
            )
        return stats

    async def discover_tools_from_server(
        self, server_name: str
    ) -> MCPDiscoveryResultSchema:
        """Discover and register tools from a specific server.

        Args:
            server_name: Name of the server to discover tools from.

        Returns:
            Discovery result with counts of new and updated tools.

        """
        server_result = await self.db.execute(
            select(MCPServer).where(MCPServer.name == server_name)
        )
        server = server_result.scalar_one_or_none()
        if not server:
            logger.error(f"Server not found: {server_name}")
            return MCPDiscoveryResultSchema(
                success=False, server_name=server_name, error="Server not found"
            )
        if not server.is_enabled:
            logger.info(f"Server {server_name} is disabled, skipping discovery")
            return MCPDiscoveryResultSchema(
                success=False, server_name=server_name, error="Server is disabled"
            )
        try:
            discovered_tools = await self._discover_server_tools(
                server.url, server.timeout
            )
            new_tools = 0
            updated_tools = 0
            errors = []
            for tool_info in discovered_tools:
                try:
                    tool_name = f"{server_name}_{tool_info.get('name', 'unknown')}"
                    tool_data = MCPToolCreateSchema(
                        name=tool_name,
                        original_name=tool_info.get("name", "unknown"),
                        server_name=server_name,
                        description=tool_info.get("description"),
                        parameters=tool_info.get("parameters", {}),
                        is_enabled=True,
                    )
                    existing_tool = await self.get_tool(tool_name)
                    if existing_tool:
                        updates = MCPToolUpdateSchema(
                            description=tool_data.description,
                            parameters=tool_data.parameters,
                        )
                        await self.update_tool(tool_name, updates)
                        updated_tools += 1
                        logger.info(f"Updated existing tool: {tool_name}")
                    else:
                        await self.register_tool(tool_data)
                        new_tools += 1
                        logger.info(f"Discovered new tool: {tool_name}")
                except Exception as e:
                    error_msg = f"Failed to process tool {tool_info.get('name', 'unknown')}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            await self.update_connection_status(server_name, True, False)
            result = MCPDiscoveryResultSchema(
                success=True,
                server_name=server_name,
                new_tools=new_tools,
                updated_tools=updated_tools,
                total_discovered=len(discovered_tools),
                errors=errors,
            )
            logger.info(
                f"Tool discovery completed for {server_name}: {new_tools} new, {updated_tools} updated"
            )
            return result
        except Exception as e:
            error_msg = f"Failed to discover tools from server {server_name}: {e}"
            logger.error(error_msg)
            await self.update_connection_status(server_name, False, True)
            return MCPDiscoveryResultSchema(
                success=False,
                server_name=server_name,
                error=str(e),
                new_tools=0,
                updated_tools=0,
                total_discovered=0,
            )

    async def discover_tools_all_servers(self) -> List[MCPDiscoveryResultSchema]:
        """Discover tools from all enabled servers.

        Returns:
            List of discovery results for all servers.

        """
        filters = MCPListFiltersSchema(enabled_only=True)
        servers = await self.list_servers(filters)
        if not servers:
            logger.info("No enabled MCP servers found for tool discovery")
            return []
        logger.info(f"Starting tool discovery for {len(servers)} servers")
        discovery_results = []
        for server in servers:
            result = await self.discover_tools_from_server(server.name)
            discovery_results.append(result)
            await asyncio.sleep(0.5)
        return discovery_results

    async def _auto_discover_on_server_change(
        self, server_name: str, was_enabled: bool, is_enabled: bool
    ) -> Optional[MCPDiscoveryResultSchema]:
        if not was_enabled and is_enabled:
            logger.info(
                f"Server {server_name} was enabled, starting automatic tool discovery"
            )
            return await self.discover_tools_from_server(server_name)
        return None

    async def initialize(self):
        """Initialize the MCP service registry/client connections."""
        if not settings.mcp_enabled:
            logger.warning("MCP is disabled - cannot initialize MCP clients")
            self.is_initialized = False
            return
        self.is_initialized = True
        logger.info("MCPService initialized (no registry caching)")

    async def _connect_server(self, server: MCPServerSchema):
        try:
            transport = StreamableHttpTransport(server.url)
            client = Client(transport, timeout=server.timeout)
            async with client:
                self.clients[server.name] = client
                logger.info(f"Connected to MCP server: {server.name} ({server.url})")
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server.name}: {e}")
            self.clients.pop(server.name, None)
            raise

    async def _discover_server_tools(
        self, server_url: str, timeout: int
    ) -> List[Dict[str, Any]]:
        try:
            transport = StreamableHttpTransport(server_url)
            client = Client(transport, timeout=timeout)
            async with client:
                tools_response = await client.list_tools()
                if hasattr(tools_response, "tools"):
                    tools_list = tools_response.tools
                elif isinstance(tools_response, dict) and "tools" in tools_response:
                    tools_list = tools_response["tools"]
                elif isinstance(tools_response, list):
                    tools_list = tools_response
                else:
                    logger.warning(
                        f"Unexpected tools response format: {type(tools_response)}"
                    )
                    return []
                discovered_tools = []
                for tool_info in tools_list:
                    if hasattr(tool_info, "name"):
                        tool_name = tool_info.name
                        tool_desc = getattr(tool_info, "description", "")
                        tool_schema = getattr(tool_info, "inputSchema", None)
                    elif isinstance(tool_info, dict):
                        tool_name = tool_info.get("name", "unknown")
                        tool_desc = tool_info.get("description", "")
                        tool_schema = tool_info.get("inputSchema", None)
                    else:
                        logger.warning(
                            f"Unexpected tool info format: {type(tool_info)}"
                        )
                        continue
                    if tool_schema:
                        if hasattr(tool_schema, "model_dump"):
                            schema_dict = tool_schema.model_dump()
                        elif isinstance(tool_schema, dict):
                            schema_dict = tool_schema
                        else:
                            schema_dict = {
                                "type": "object",
                                "properties": {},
                                "required": [],
                            }
                    else:
                        schema_dict = {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        }
                    discovered_tools.append(
                        {
                            "name": tool_name,
                            "description": tool_desc,
                            "parameters": schema_dict,
                        }
                    )
                return discovered_tools
        except Exception as e:
            logger.error(f"Failed to discover tools from {server_url}: {e}")
            raise

    async def call_tool(
        self,
        request: MCPToolExecutionRequestSchema,
    ) -> MCPToolExecutionResultSchema:
        """Execute a single tool call (with MCP registry), using FastMCP client proxy.

        Does NOT apply retry or caching logic. For managed execution use 'execute_tool_call'.
        """
        #        if not self.is_initialized:
        #            raise ExternalServiceError("MCP client not initialized")
        tool = await self.get_tool(request.tool_name)
        if not tool:
            available_tools = [t.name for t in await self.list_tools()]
            raise ExternalServiceError(
                f"Tool '{request.tool_name}' not found. Available: {available_tools}"
            )
        if not tool.is_enabled:
            raise ExternalServiceError(f"Tool '{request.tool_name}' is disabled")
        server_name = tool.server.name
        if server_name not in self.clients:
            # Connect if not already connected
            server = await self.get_server(server_name)
            if not server:
                raise ExternalServiceError(f"Server '{server_name}' not found")
            await self._connect_server(server)
        client = self.clients[server_name]
        start_time = time.time()
        success = False
        try:
            async with client:
                result = await client.call_tool(
                    name=tool.original_name, arguments=request.parameters
                )
            success = True
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
            if request.record_usage:
                try:
                    duration_ms = int((time.time() - start_time) * 1000)
                    await self.record_tool_usage(
                        request.tool_name, success, duration_ms
                    )
                except Exception as e:
                    logger.warning(f"Failed to record tool usage: {e}")
        logger.info(
            f"Tool '{request.tool_name}' executed successfully on '{server_name}'"
        )
        return formatted_result

    def _format_tool_content(self, result: Any) -> List[Dict[str, Any]]:
        content = []
        if hasattr(result, "content") and result.content:
            for content_item in result.content:
                if hasattr(content_item, "text"):
                    content.append({"type": "text", "text": content_item.text})
                elif hasattr(content_item, "data"):
                    content.append(
                        {
                            "type": "data",
                            "data": content_item.data,
                            "mimeType": getattr(
                                content_item, "mimeType", "application/octet-stream"
                            ),
                        }
                    )
                elif isinstance(content_item, dict):
                    if "text" in content_item:
                        content.append({"type": "text", "text": content_item["text"]})
                    elif "data" in content_item:
                        content.append(
                            {
                                "type": "data",
                                "data": content_item["data"],
                                "mimeType": content_item.get(
                                    "mimeType", "application/octet-stream"
                                ),
                            }
                        )
        elif isinstance(result, dict) and "content" in result:
            for content_item in result["content"]:
                if isinstance(content_item, dict):
                    if "text" in content_item:
                        content.append({"type": "text", "text": content_item["text"]})
                    elif "data" in content_item:
                        content.append(
                            {
                                "type": "data",
                                "data": content_item["data"],
                                "mimeType": content_item.get(
                                    "mimeType", "application/octet-stream"
                                ),
                            }
                        )
        if not content:
            content.append({"type": "text", "text": str(result)})
        return content

    def _serialize_result(self, result: Any) -> str:
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
    ) -> List[MCPToolResponse]:
        """Return a list of available tools (from DB/registry), optionally filtered."""
        #        if not self.is_initialized:
        #            logger.warning("MCP client not initialized - returning empty tools list")
        #            return []
        tools = await self.list_tools(filters)
        if filters:
            if filters.enabled_only:
                tools = [t for t in tools if t.is_enabled and t.server.is_enabled]
            if filters.server_name:
                tools = [t for t in tools if t.server.name == filters.server_name]
        return tools

    async def get_openai_tools(
        self,
        filters: Optional[MCPListFiltersSchema] = None,
    ) -> List[Dict[str, Any]]:
        """Format available MCP tools as OpenAI-compatible function tool schemas."""
        mcp_tools = await self.get_available_tools(filters)
        openai_tools = []
        for tool in mcp_tools:
            if tool.is_enabled and tool.server.is_enabled:
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description
                        or f"Tool from {tool.server.name}",
                        "parameters": tool.parameters
                        or {"type": "object", "properties": {}},
                    },
                }
                openai_tools.append(openai_tool)
        return openai_tools

    async def execute_tool_call(
        self,
        tool_call: Dict[str, Any],
        max_retries: int = 3,
        use_cache: bool = True,
        cache_ttl: int = 300,
    ) -> Dict[str, Any]:
        """Execute a single tool call, with retry and API response caching logic.

        Args:
            tool_call: Dict with keys: id (str), name (str), arguments (dict)
            max_retries: Number of retry attempts on failure (default 3)
            use_cache: If True, cache successful results for identical arguments
            cache_ttl: TTL for result cache in seconds

        Returns:
            Dict describing the tool execution result (see below).

        """
        import time

        tool_call_id = tool_call.get("id", "")
        tool_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})

        # if use_cache:
        #    cache_key = make_cache_key("tool_call", tool_name, arguments)
        #    cached_result = await api_response_cache.get(cache_key)
        #    if cached_result is not None:
        #        logger.debug(f"Using cached result for tool call: {tool_name}")
        #        return cached_result

        last_exception = None
        for attempt in range(max_retries):
            start_time = time.time()
            try:
                logger.info(
                    f"Executing tool call '{tool_name}', attempt {attempt + 1}/{max_retries}"
                )
                req = MCPToolExecutionRequestSchema(
                    tool_name=tool_name, parameters=arguments, record_usage=True
                )
                result = await self.call_tool(req)
                execution_time = (time.time() - start_time) * 1000
                print("RESULT", result)
                result_dict = {
                    "tool_call_id": tool_call_id,
                    "tool_name": tool_name,
                    "success": result.success,
                    "content": result.content,
                    "error": getattr(result, "error", None),
                    "provider": "fastmcp",
                    "execution_time_ms": execution_time,
                }
                print("RESULTDICT", result_dict)
                # if use_cache and cache_key and result.success:
                #    await api_response_cache.set(cache_key, result_dict, ttl=cache_ttl)
                return result_dict
            except Exception as e:
                last_exception = e
                logger.warning(f"Tool execution attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                    continue

        logger.error(
            f"Tool execution failed after {max_retries} attempts: {tool_name} (error: {last_exception})"
        )
        return {
            "tool_call_id": tool_call_id,
            "tool_name": tool_name,
            "success": False,
            "content": [],
            "error": f"Tool execution failed after {max_retries} attempts: {last_exception}",
            "provider": "fastmcp",
            "execution_time_ms": None,
        }

    async def execute_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        max_retries: int = 3,
        use_cache: bool = True,
        parallel_execution: bool = True,
    ) -> List[Dict[str, Any]]:
        """Execute multiple tool calls, optionally in parallel, with retry and caching.

        Args:
            tool_calls: List of tool call dicts (see 'execute_tool_call')
            max_retries: Number of retry attempts per call
            use_cache: If True, use API response caching
            parallel_execution: If True, run tool calls concurrently

        Returns:
            List of result dicts, in the same order as tool_calls

        """
        if not tool_calls:
            return []
        logger.info(
            f"Executing {len(tool_calls)} tool calls (parallel={parallel_execution})"
        )

        if parallel_execution:
            tasks = [
                self.execute_tool_call(
                    tool_call, max_retries=max_retries, use_cache=use_cache
                )
                for tool_call in tool_calls
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(
                        {
                            "tool_call_id": tool_calls[i].get("id", ""),
                            "tool_name": tool_calls[i].get("name", ""),
                            "success": False,
                            "content": [],
                            "error": str(result),
                            "provider": "fastmcp",
                            "execution_time_ms": None,
                        }
                    )
                else:
                    processed_results.append(result)
            return processed_results
        else:
            results = []
            for tool_call in tool_calls:
                result = await self.execute_tool_call(
                    tool_call,
                    max_retries=max_retries,
                    use_cache=use_cache,
                )
                results.append(result)
            return results

    async def health_check(self) -> MCPHealthStatusSchema:
        """Perform a health check of the MCP system: registry and client connections."""
        all_servers = await self.list_servers()
        all_tools = await self.list_tools()
        health_status = MCPHealthStatusSchema(
            mcp_available=settings.mcp_enabled,
            initialized=self.is_initialized,
            total_servers=len(all_servers),
            healthy_servers=0,
            unhealthy_servers=0,
            tools_count=len(all_tools),
            server_status={},
        )
        if not self.is_initialized:
            return health_status
        for server in all_servers:
            server_name = server.name
            healthy = False
            if server_name in self.clients:
                client = self.clients[server_name]
                try:
                    async with client:
                        await asyncio.wait_for(client.list_tools(), timeout=5)
                    tools_count = len(
                        [t for t in all_tools if t.server.name == server_name]
                    )
                    health_status.server_status[server_name] = {
                        "status": "healthy",
                        "tools_count": tools_count,
                        "connected": True,
                    }
                    health_status.healthy_servers += 1
                    healthy = True
                except Exception as e:
                    health_status.server_status[server_name] = {
                        "status": "unhealthy",
                        "error": str(e),
                        "connected": False,
                    }
                    health_status.unhealthy_servers += 1
            if not healthy:
                health_status.server_status.setdefault(
                    server_name,
                    {
                        "status": "disconnected",
                        "error": "Not connected",
                        "connected": False,
                    },
                )
                health_status.unhealthy_servers += 1
        try:
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
        """Disconnect from all MCP servers and clear client state."""
        disconnected_servers = []
        for server_name, client in self.clients.items():
            try:
                await client.close()
                disconnected_servers.append(server_name)
                logger.info(f"Disconnected from MCP server: {server_name}")
            except Exception as e:
                logger.warning(f"Error disconnecting from {server_name}: {e}")
        self.clients.clear()
        self.is_initialized = False
        logger.info(f"Disconnected from {len(disconnected_servers)} MCP servers")

    async def refresh_from_registry(self):
        """Force a refresh of the MCP registry and clear all client connections."""
        logger.info("Force refreshing MCP client from registry (connections cleared)")
        await self.disconnect_all()
        await self.initialize()
