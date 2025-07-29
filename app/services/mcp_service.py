"""
Unified MCP service for registry management and FastMCP client proxy.

This service combines the registry and client logic for:
- MCP server and tool registration/discovery/updating
- Lightweight in-memory cache for active MCP server connections
- Thin proxy for tool execution and health checking

The service is initialized per-request with an AsyncSession.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastmcp import Client
from fastmcp.client import StreamableHttpTransport
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import settings
from ..core.exceptions import ExternalServiceError
from ..core.logging import get_api_logger
from ..models.mcp_server import MCPServer
from ..models.mcp_tool import MCPTool
from ..schemas.mcp import (
    MCPDiscoveryResultSchema, MCPHealthStatusSchema, MCPListFiltersSchema,
    MCPServerCreateSchema, MCPServerSchema, MCPServerUpdateSchema,
    MCPToolCreateSchema, MCPToolExecutionRequestSchema, MCPToolExecutionResultSchema,
    MCPToolSchema, MCPToolUpdateSchema, MCPToolUsageStatsSchema
)

logger = get_api_logger("mcp_service")


class MCPService:
    """
    Unified MCP service for registry and client proxy.

    Pass a database session when instantiating. All registry and client operations
    are available on this class.
    """

    def __init__(self, db_session: AsyncSession):
        self.db: AsyncSession = db_session
        self.clients: Dict[str, Client] = {}
        self._cache_timeout = 300
        self._last_refresh = 0
        self._cached_servers: Dict[str, MCPServerSchema] = {}
        self._cached_tools: Dict[str, MCPToolSchema] = {}
        self.is_initialized = False
        logger.info("MCPService initialized")

    # --- Registry methods (from MCPRegistryService) ---

    async def create_server(self, server_data: MCPServerCreateSchema, auto_discover: bool = True) -> MCPServerSchema:
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
                discovery_result = await self.discover_tools_from_server(server_data.name)
                logger.info(
                    f"Automatic tool discovery for new server {server_data.name}: "
                    f"{discovery_result.new_tools} new, {discovery_result.updated_tools} updated"
                )
            except Exception as e:
                logger.warning(f"Failed to auto-discover tools for new server {server_data.name}: {e}")

        return MCPServerSchema.model_validate(server)

    async def get_server(self, name: str) -> Optional[MCPServerSchema]:
        result = await self.db.execute(
            select(MCPServer)
            .options(selectinload(MCPServer.tools))
            .where(MCPServer.name == name)
        )
        server = result.scalar_one_or_none()
        if server:
            server_dict = server.__dict__.copy()
            server_dict['tools_count'] = len(server.tools)
            return MCPServerSchema.model_validate(server_dict)
        return None

    async def list_servers(self, filters: Optional[MCPListFiltersSchema] = None) -> List[MCPServerSchema]:
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
            server_dict = server.__dict__.copy()
            server_dict['tools_count'] = len(server.tools)
            server_schemas.append(MCPServerSchema.model_validate(server_dict))
        return server_schemas

    async def update_server(self, name: str, updates: MCPServerUpdateSchema) -> Optional[MCPServerSchema]:
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
        server = await self.db.execute(select(MCPServer).where(MCPServer.name == name))
        server = server.scalar_one_or_none()
        if not server:
            return False
        await self.db.delete(server)
        await self.db.commit()
        logger.info(f"Deleted MCP server: {name}")
        return True

    async def enable_server(self, name: str, auto_discover: bool = True) -> Optional[MCPServerSchema]:
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
                logger.info(f"Automatic tool discovery triggered for {name}: "
                          f"{discovery_result.new_tools} new, {discovery_result.updated_tools} updated")
        return updated_server

    async def disable_server(self, name: str) -> Optional[MCPServerSchema]:
        updates = MCPServerUpdateSchema(is_enabled=False)
        return await self.update_server(name, updates)

    async def update_connection_status(
        self, name: str, is_connected: bool, increment_errors: bool = False
    ) -> Optional[MCPServerSchema]:
        updates_dict = {
            "is_connected": is_connected,
        }
        if is_connected:
            updates_dict["last_connected_at"] = datetime.utcnow()
            updates_dict["connection_errors"] = 0
        elif increment_errors:
            server = await self.get_server(name)
            if server:
                updates_dict["connection_errors"] = server.connection_errors + 1
        updates = MCPServerUpdateSchema(**updates_dict)
        return await self.update_server(name, updates)

    async def register_tool(self, tool_data: MCPToolCreateSchema) -> Optional[MCPToolSchema]:
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
            return MCPToolSchema.model_validate(existing_tool)
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
        logger.info(f"Registered tool: {tool_data.name} for server {tool_data.server_name}")
        return MCPToolSchema.model_validate(tool)

    async def get_tool(self, tool_name: str) -> Optional[MCPToolSchema]:
        result = await self.db.execute(
            select(MCPTool)
            .options(selectinload(MCPTool.server))
            .where(MCPTool.name == tool_name)
        )
        tool = result.scalar_one_or_none()
        if tool:
            return MCPToolSchema.model_validate(tool)
        return None

    async def list_tools(self, filters: Optional[MCPListFiltersSchema] = None) -> List[MCPToolSchema]:
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
        return [MCPToolSchema.model_validate(tool) for tool in tools]

    async def update_tool(self, tool_name: str, updates: MCPToolUpdateSchema) -> Optional[MCPToolSchema]:
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
        return MCPToolSchema.model_validate(tool)

    async def enable_tool(self, tool_name: str) -> bool:
        result = await self.db.execute(
            update(MCPTool).where(MCPTool.name == tool_name).values(is_enabled=True)
        )
        await self.db.commit()
        if result.rowcount > 0:
            logger.info(f"Enabled tool: {tool_name}")
            return True
        return False

    async def disable_tool(self, tool_name: str) -> bool:
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
        tool = await self.db.execute(select(MCPTool).where(MCPTool.name == tool_name))
        tool = tool.scalar_one_or_none()
        if not tool:
            return False
        tool.record_usage(success, duration_ms)
        await self.db.commit()
        return True

    async def batch_record_tool_usage(self, usage_records: List[Dict[str, Any]]) -> int:
        processed_count = 0
        for record in usage_records:
            try:
                tool_name = record.get("tool_name")
                success = record.get("success", True)
                duration_ms = record.get("duration_ms")
                if tool_name and await self.record_tool_usage(tool_name, success, duration_ms):
                    processed_count += 1
            except Exception as e:
                logger.warning(f"Failed to record usage for tool {record.get('tool_name')}: {e}")
        return processed_count

    async def get_tool_stats(
        self, server_name: Optional[str] = None, limit: int = 10
    ) -> List[MCPToolUsageStatsSchema]:
        query = select(MCPTool).options(selectinload(MCPTool.server))
        if server_name:
            query = query.join(MCPServer).where(MCPServer.name == server_name)
        result = await self.db.execute(query.order_by(MCPTool.usage_count.desc()).limit(limit))
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

    async def discover_tools_from_server(self, server_name: str) -> MCPDiscoveryResultSchema:
        server_result = await self.db.execute(select(MCPServer).where(MCPServer.name == server_name))
        server = server_result.scalar_one_or_none()
        if not server:
            logger.error(f"Server not found: {server_name}")
            return MCPDiscoveryResultSchema(
                success=False,
                server_name=server_name,
                error="Server not found"
            )
        if not server.is_enabled:
            logger.info(f"Server {server_name} is disabled, skipping discovery")
            return MCPDiscoveryResultSchema(
                success=False,
                server_name=server_name,
                error="Server is disabled"
            )
        try:
            discovered_tools = await self._discover_server_tools(server.url, server.timeout)
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
                        is_enabled=True
                    )
                    existing_tool = await self.get_tool(tool_name)
                    if existing_tool:
                        updates = MCPToolUpdateSchema(
                            description=tool_data.description,
                            parameters=tool_data.parameters
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
            logger.info(f"Server {server_name} was enabled, starting automatic tool discovery")
            return await self.discover_tools_from_server(server_name)
        return None

    # --- MCP client proxy methods (from FastMCPClientService, using registry via self) ---

    async def _should_refresh_cache(self) -> bool:
        return (time.time() - self._last_refresh) > self._cache_timeout

    async def _refresh_from_registry(self):
        if not settings.mcp_enabled:
            logger.info("MCP is disabled, skipping registry refresh")
            return
        try:
            filters = MCPListFiltersSchema(enabled_only=True)
            servers = await self.list_servers(filters)
            self._cached_servers = {server.name: server for server in servers}
            tools = await self.list_tools(filters)
            self._cached_tools = {tool.name: tool for tool in tools if tool.server.is_enabled}
            self._last_refresh = time.time()
            logger.info(
                f"Refreshed from registry: {len(self._cached_servers)} servers, "
                f"{len(self._cached_tools)} tools"
            )
        except Exception as e:
            logger.error(f"Failed to refresh from registry: {e}")
            raise ExternalServiceError(f"Registry refresh failed: {e}")

    async def initialize(self):
        if not settings.mcp_enabled:
            logger.warning("MCP is disabled - cannot initialize MCP clients")
            self.is_initialized = False
            return
        try:
            await self._refresh_from_registry()
            if not self._cached_servers:
                logger.warning("No enabled MCP servers found in registry")
                self.is_initialized = False
                return
            successful_connections = 0
            for server_name, server in self._cached_servers.items():
                try:
                    await self._connect_server(server)
                    successful_connections += 1
                    logger.info(f"✅ Connected to MCP server: {server_name}")
                except Exception as e:
                    logger.error(f"❌ Failed to connect to MCP server {server_name}: {e}")
            tools_count = len([t for t in self._cached_tools.values() if t.server.name in self.clients])
            self.is_initialized = True
            logger.info(
                f"MCPService initialization completed: {successful_connections}/"
                f"{len(self._cached_servers)} servers, {tools_count} tools available"
            )
        except Exception as e:
            logger.error(f"MCPService initialization failed: {e}")
            logger.warning("Continuing without MCP integration")
            self.is_initialized = False

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

    async def _discover_server_tools(self, server_url: str, timeout: int) -> List[Dict[str, Any]]:
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
                    logger.warning(f"Unexpected tools response format: {type(tools_response)}")
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
                        logger.warning(f"Unexpected tool info format: {type(tool_info)}")
                        continue
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
    ) -> MCPToolExecutionResultSchema:
        if not self.is_initialized:
            raise ExternalServiceError("MCP client not initialized")
        if await self._should_refresh_cache():
            await self._refresh_from_registry()
        tool = self._cached_tools.get(request.tool_name)
        if not tool:
            available_tools = list(self._cached_tools.keys())
            raise ExternalServiceError(
                f"Tool '{request.tool_name}' not found. Available: {available_tools}"
            )
        if not tool.is_enabled:
            raise ExternalServiceError(f"Tool '{request.tool_name}' is disabled")
        server_name = tool.server.name
        if server_name not in self.clients:
            raise ExternalServiceError(f"Server '{server_name}' not connected")
        client = self.clients[server_name]
        start_time = time.time()
        success = False
        try:
            async with client:
                result = await client.call_tool(
                    name=tool.original_name,
                    arguments=request.parameters
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
                    await self.record_tool_usage(request.tool_name, success, duration_ms)
                except Exception as e:
                    logger.warning(f"Failed to record tool usage: {e}")
        logger.info(f"Tool '{request.tool_name}' executed successfully on '{server_name}'")
        return formatted_result

    def _format_tool_content(self, result: Any) -> List[Dict[str, Any]]:
        content = []
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
    ) -> List[MCPToolSchema]:
        if not self.is_initialized:
            logger.warning("MCP client not initialized - returning empty tools list")
            return []
        if await self._should_refresh_cache():
            await self._refresh_from_registry()
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
    ) -> List[MCPToolExecutionResultSchema]:
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
                result = await self.call_tool(request)
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

    async def health_check(self) -> MCPHealthStatusSchema:
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
        for server_name, client in self.clients.items():
            try:
                async with client:
                    await asyncio.wait_for(client.list_tools(), timeout=5)
                tools_count = len([t for t in self._cached_tools.values() if t.server.name == server_name])
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
        for server_name in self._cached_servers:
            if server_name not in self.clients:
                health_status.server_status[server_name] = {
                    "status": "disconnected",
                    "error": "Failed to connect",
                    "connected": False,
                }
                health_status.unhealthy_servers += 1
        try:
            all_servers = await self.list_servers()
            all_tools = await self.list_tools()
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
        disconnected_servers = []
        for server_name, client in self.clients.items():
            try:
                await client.close()
                disconnected_servers.append(server_name)
                logger.info(f"Disconnected from MCP server: {server_name}")
            except Exception as e:
                logger.warning(f"Error disconnecting from {server_name}: {e}")
        self.clients.clear()
        self._cached_servers.clear()
        self._cached_tools.clear()
        self._last_refresh = 0
        self.is_initialized = False
        logger.info(f"Disconnected from {len(disconnected_servers)} MCP servers")

    async def refresh_from_registry(self):
        logger.info("Force refreshing MCP client from registry")
        await self.disconnect_all()
        await self.initialize()