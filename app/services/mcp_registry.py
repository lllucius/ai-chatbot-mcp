"""
MCP Registry service for managing MCP servers and tools.

This service provides functionality to manage MCP server registrations,
tool discovery, and usage statistics using dependency injection and 
Pydantic models for all operations.

Refactored to:
- Use instance methods with dependency injection
- Return Pydantic models for all operations  
- Centralize all tool/server discovery and registration
- Implement batch usage statistics
- Remove static methods and global database sessions
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.logging import get_api_logger
from ..models.mcp_server import MCPServer
from ..models.mcp_tool import MCPTool
from ..schemas.mcp import (
    MCPServerCreateSchema, MCPServerSchema, MCPServerUpdateSchema,
    MCPToolCreateSchema, MCPToolSchema, MCPToolUpdateSchema,
    MCPToolUsageStatsSchema, MCPDiscoveryResultSchema,
    MCPListFiltersSchema
)

logger = get_api_logger("mcp_registry")


class MCPRegistryService:
    """
    Service for managing MCP server and tool registrations.
    
    This service uses dependency injection for database sessions and
    returns Pydantic models for all operations to ensure type safety
    and consistent API schemas.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initialize the MCP registry service.
        
        Args:
            db_session: AsyncSession for database operations
        """
        self.db = db_session

    async def create_server(
        self,
        server_data: MCPServerCreateSchema,
        auto_discover: bool = True,
    ) -> MCPServerSchema:
        """Create a new MCP server registration and optionally discover tools."""
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

        # Trigger tool discovery for new enabled servers
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
        """Get an MCP server by name."""
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
        """List all MCP servers with optional filtering."""
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
        
        # Convert to Pydantic models with computed fields
        server_schemas = []
        for server in servers:
            server_dict = server.__dict__.copy()
            server_dict['tools_count'] = len(server.tools)
            server_schemas.append(MCPServerSchema.model_validate(server_dict))
        
        return server_schemas

    async def update_server(self, name: str, updates: MCPServerUpdateSchema) -> Optional[MCPServerSchema]:
        """Update an MCP server configuration."""
        server = await self.db.execute(select(MCPServer).where(MCPServer.name == name))
        server = server.scalar_one_or_none()

        if not server:
            return None

        # Update only provided fields
        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(server, key):
                setattr(server, key, value)

        await self.db.commit()
        await self.db.refresh(server)

        logger.info(f"Updated MCP server: {name}")
        return MCPServerSchema.model_validate(server)

    async def delete_server(self, name: str) -> bool:
        """Delete an MCP server registration."""
        server = await self.db.execute(select(MCPServer).where(MCPServer.name == name))
        server = server.scalar_one_or_none()

        if not server:
            return False

        await self.db.delete(server)
        await self.db.commit()

        logger.info(f"Deleted MCP server: {name}")
        return True

    async def enable_server(self, name: str, auto_discover: bool = True) -> Optional[MCPServerSchema]:
        """Enable an MCP server and optionally discover tools."""
        # Get current state
        server = await self.get_server(name)
        if not server:
            return None

        was_enabled = server.is_enabled

        # Update server
        updates = MCPServerUpdateSchema(is_enabled=True)
        updated_server = await self.update_server(name, updates)
        if not updated_server:
            return None

        # Trigger automatic discovery if requested
        if auto_discover:
            discovery_result = await self._auto_discover_on_server_change(
                name, was_enabled, True
            )
            if discovery_result:
                logger.info(f"Automatic tool discovery triggered for {name}: "
                          f"{discovery_result.new_tools} new, {discovery_result.updated_tools} updated")

        return updated_server

    async def disable_server(self, name: str) -> Optional[MCPServerSchema]:
        """Disable an MCP server."""
        updates = MCPServerUpdateSchema(is_enabled=False)
        return await self.update_server(name, updates)

    async def update_connection_status(
        self, name: str, is_connected: bool, increment_errors: bool = False
    ) -> Optional[MCPServerSchema]:
        """Update the connection status of an MCP server."""
        updates_dict = {
            "is_connected": is_connected,
        }

        if is_connected:
            updates_dict["last_connected_at"] = datetime.utcnow()
            updates_dict["connection_errors"] = 0
        elif increment_errors:
            # Need to get current error count and increment it
            server = await self.get_server(name)
            if server:
                updates_dict["connection_errors"] = server.connection_errors + 1

        # Convert to schema for validation
        updates = MCPServerUpdateSchema(**updates_dict)
        return await self.update_server(name, updates)

    async def register_tool(self, tool_data: MCPToolCreateSchema) -> Optional[MCPToolSchema]:
        """Register a tool for an MCP server."""
        # Get the server
        server_result = await self.db.execute(
            select(MCPServer).where(MCPServer.name == tool_data.server_name)
        )
        server = server_result.scalar_one_or_none()

        if not server:
            logger.error(f"Server not found: {tool_data.server_name}")
            return None

        # Check if tool already exists
        existing_tool = await self.db.execute(
            select(MCPTool).where(MCPTool.name == tool_data.name)
        )
        existing_tool = existing_tool.scalar_one_or_none()

        if existing_tool:
            # Update existing tool
            existing_tool.description = tool_data.description
            existing_tool.parameters = tool_data.parameters or {}
            existing_tool.is_enabled = tool_data.is_enabled
            await self.db.commit()
            await self.db.refresh(existing_tool, ["server"])
            return MCPToolSchema.model_validate(existing_tool)

        # Create new tool
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
        """Get a tool by name."""
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
        """List tools with optional filtering."""
        query = select(MCPTool).options(selectinload(MCPTool.server))

        if filters:
            filter_conditions = []
            if filters.server_name:
                # Join with server to filter by server name
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
        """Update a tool configuration."""
        tool = await self.db.execute(
            select(MCPTool)
            .options(selectinload(MCPTool.server))
            .where(MCPTool.name == tool_name)
        )
        tool = tool.scalar_one_or_none()

        if not tool:
            return None

        # Update only provided fields
        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(tool, key):
                setattr(tool, key, value)

        await self.db.commit()
        await self.db.refresh(tool, ["server"])

        logger.info(f"Updated tool: {tool_name}")
        return MCPToolSchema.model_validate(tool)

    async def enable_tool(self, tool_name: str) -> bool:
        """Enable a tool."""
        result = await self.db.execute(
            update(MCPTool).where(MCPTool.name == tool_name).values(is_enabled=True)
        )
        await self.db.commit()

        if result.rowcount > 0:
            logger.info(f"Enabled tool: {tool_name}")
            return True
        return False

    async def disable_tool(self, tool_name: str) -> bool:
        """Disable a tool."""
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
        """Record a tool usage event."""
        tool = await self.db.execute(select(MCPTool).where(MCPTool.name == tool_name))
        tool = tool.scalar_one_or_none()

        if not tool:
            return False

        tool.record_usage(success, duration_ms)
        await self.db.commit()

        return True

    async def batch_record_tool_usage(self, usage_records: List[Dict[str, Any]]) -> int:
        """
        Batch record multiple tool usage events for better performance.
        
        Args:
            usage_records: List of usage records with keys: tool_name, success, duration_ms
            
        Returns:
            Number of records successfully processed
        """
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
        """Get tool usage statistics."""
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
        """Discover tools from an MCP server and update the registry."""
        # Get the server
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
            # Import the MCP client service for tool discovery
            from .mcp_client import get_mcp_client
            
            # Get MCP client for discovery
            client_service = await get_mcp_client()
            discovered_tools = await client_service._discover_server_tools(server.url, server.timeout)

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

                    # Check if tool already exists
                    existing_tool = await self.get_tool(tool_name)

                    if existing_tool:
                        # Update existing tool (preserve enabled/disabled status)
                        updates = MCPToolUpdateSchema(
                            description=tool_data.description,
                            parameters=tool_data.parameters
                        )
                        await self.update_tool(tool_name, updates)
                        updated_tools += 1
                        logger.info(f"Updated existing tool: {tool_name}")
                    else:
                        # Create new tool
                        await self.register_tool(tool_data)
                        new_tools += 1
                        logger.info(f"Discovered new tool: {tool_name}")

                except Exception as e:
                    error_msg = f"Failed to process tool {tool_info.get('name', 'unknown')}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)

            # Update server connection status
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

            # Update server connection status
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
        """Discover tools from all enabled MCP servers."""
        # Get all enabled servers
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

            # Small delay between discoveries to avoid overwhelming servers
            await asyncio.sleep(0.5)

        return discovery_results

    async def _auto_discover_on_server_change(
        self, server_name: str, was_enabled: bool, is_enabled: bool
    ) -> Optional[MCPDiscoveryResultSchema]:
        """Automatically discover tools when a server is enabled or re-enabled."""
        if not was_enabled and is_enabled:
            # Server was just enabled - discover tools
            logger.info(f"Server {server_name} was enabled, starting automatic tool discovery")
            return await self.discover_tools_from_server(server_name)

        return None
