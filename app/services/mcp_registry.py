"""
MCP Registry service for managing MCP servers and tools.

This service provides functionality to manage MCP server registrations,
tool discovery, and usage statistics.

Current Date and Time (UTC): 2025-07-23 03:30:00
Current User: lllucius / assistant
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.orm import selectinload

from ..database import AsyncSessionLocal
from ..models.mcp_server import MCPServer
from ..models.mcp_tool import MCPTool
from ..utils.logging import get_api_logger

logger = get_api_logger("mcp_registry")


class MCPRegistryService:
    """Service for managing MCP server and tool registrations."""

    @staticmethod
    async def create_server(
        name: str,
        url: str,
        description: Optional[str] = None,
        transport: str = "http",
        timeout: int = 30,
        config: Optional[dict] = None,
        is_enabled: bool = True,
        auto_discover: bool = True,
    ) -> MCPServer:
        """Create a new MCP server registration and optionally discover tools."""
        async with AsyncSessionLocal() as db:
            server = MCPServer(
                name=name,
                url=url,
                description=description,
                transport=transport,
                timeout=timeout,
                config=config or {},
                is_enabled=is_enabled,
                is_connected=False,
                connection_errors=0,
            )

            db.add(server)
            await db.commit()
            await db.refresh(server)

            logger.info(f"Created MCP server registration: {name}")

            # Trigger tool discovery for new enabled servers
            if is_enabled and auto_discover:
                try:
                    discovery_result = (
                        await MCPRegistryService.discover_tools_from_server(name)
                    )
                    logger.info(
                        f"Automatic tool discovery for new server {name}: {discovery_result}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to auto-discover tools for new server {name}: {e}"
                    )

            return server

    @staticmethod
    async def get_server(name: str) -> Optional[MCPServer]:
        """Get an MCP server by name."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(MCPServer).where(MCPServer.name == name))
            return result.scalar_one_or_none()

    @staticmethod
    async def list_servers(
        enabled_only: bool = False, connected_only: bool = False
    ) -> List[MCPServer]:
        """List all MCP servers with optional filtering."""
        async with AsyncSessionLocal() as db:
            query = select(MCPServer).options(selectinload(MCPServer.tools))

            filters = []
            if enabled_only:
                filters.append(MCPServer.is_enabled == True)
            if connected_only:
                filters.append(MCPServer.is_connected == True)

            if filters:
                query = query.where(and_(*filters))

            result = await db.execute(query.order_by(MCPServer.name))
            return list(result.scalars().all())

    @staticmethod
    async def update_server(name: str, **updates) -> Optional[MCPServer]:
        """Update an MCP server configuration."""
        async with AsyncSessionLocal() as db:
            server = await db.execute(select(MCPServer).where(MCPServer.name == name))
            server = server.scalar_one_or_none()

            if not server:
                return None

            for key, value in updates.items():
                if hasattr(server, key):
                    setattr(server, key, value)

            await db.commit()
            await db.refresh(server)

            logger.info(f"Updated MCP server: {name}")
            return server

    @staticmethod
    async def delete_server(name: str) -> bool:
        """Delete an MCP server registration."""
        async with AsyncSessionLocal() as db:
            server = await db.execute(select(MCPServer).where(MCPServer.name == name))
            server = server.scalar_one_or_none()

            if not server:
                return False

            await db.delete(server)
            await db.commit()

            logger.info(f"Deleted MCP server: {name}")
            return True

    @staticmethod
    async def enable_server(name: str, auto_discover: bool = True) -> bool:
        """Enable an MCP server and optionally discover tools."""
        # Get current state
        server = await MCPRegistryService.get_server(name)
        if not server:
            return False

        was_enabled = server.is_enabled

        # Update server
        updated_server = await MCPRegistryService.update_server(name, is_enabled=True)
        if not updated_server:
            return False

        # Trigger automatic discovery if requested
        if auto_discover:
            discovery_result = await MCPRegistryService.auto_discover_on_server_change(
                name, was_enabled, True
            )
            if discovery_result:
                logger.info(
                    f"Automatic tool discovery triggered for {name}: {discovery_result}"
                )

        return True

    @staticmethod
    async def disable_server(name: str) -> bool:
        """Disable an MCP server."""
        return (
            await MCPRegistryService.update_server(name, is_enabled=False) is not None
        )

    @staticmethod
    async def update_connection_status(
        name: str, is_connected: bool, increment_errors: bool = False
    ) -> bool:
        """Update the connection status of an MCP server."""
        updates = {
            "is_connected": is_connected,
        }

        if is_connected:
            updates["last_connected_at"] = datetime.utcnow()
            updates["connection_errors"] = 0
        elif increment_errors:
            # Need to get current error count and increment it
            server = await MCPRegistryService.get_server(name)
            if server:
                updates["connection_errors"] = server.connection_errors + 1

        return await MCPRegistryService.update_server(name, **updates) is not None

    @staticmethod
    async def register_tool(
        server_name: str,
        tool_name: str,
        original_name: str,
        description: Optional[str] = None,
        parameters: Optional[dict] = None,
        is_enabled: bool = True,
    ) -> Optional[MCPTool]:
        """Register a tool for an MCP server."""
        async with AsyncSessionLocal() as db:
            # Get the server
            server_result = await db.execute(
                select(MCPServer).where(MCPServer.name == server_name)
            )
            server = server_result.scalar_one_or_none()

            if not server:
                logger.error(f"Server not found: {server_name}")
                return None

            # Check if tool already exists
            existing_tool = await db.execute(
                select(MCPTool).where(MCPTool.name == tool_name)
            )
            existing_tool = existing_tool.scalar_one_or_none()

            if existing_tool:
                # Update existing tool
                existing_tool.description = description
                existing_tool.parameters = parameters or {}
                existing_tool.is_enabled = is_enabled
                await db.commit()
                await db.refresh(existing_tool)
                return existing_tool

            # Create new tool
            tool = MCPTool(
                name=tool_name,
                original_name=original_name,
                server_id=server.id,
                description=description,
                parameters=parameters or {},
                is_enabled=is_enabled,
            )

            db.add(tool)
            await db.commit()
            await db.refresh(tool)

            logger.info(f"Registered tool: {tool_name} for server {server_name}")
            return tool

    @staticmethod
    async def get_tool(tool_name: str) -> Optional[MCPTool]:
        """Get a tool by name."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(MCPTool)
                .options(selectinload(MCPTool.server))
                .where(MCPTool.name == tool_name)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def list_tools(
        server_name: Optional[str] = None, enabled_only: bool = False
    ) -> List[MCPTool]:
        """List tools with optional filtering."""
        async with AsyncSessionLocal() as db:
            query = select(MCPTool).options(selectinload(MCPTool.server))

            filters = []
            if server_name:
                # Join with server to filter by server name
                query = query.join(MCPServer)
                filters.append(MCPServer.name == server_name)
            if enabled_only:
                filters.append(MCPTool.is_enabled == True)

            if filters:
                query = query.where(and_(*filters))

            result = await db.execute(query.order_by(MCPTool.name))
            return list(result.scalars().all())

    @staticmethod
    async def enable_tool(tool_name: str) -> bool:
        """Enable a tool."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                update(MCPTool).where(MCPTool.name == tool_name).values(is_enabled=True)
            )
            await db.commit()

            if result.rowcount > 0:
                logger.info(f"Enabled tool: {tool_name}")
                return True
            return False

    @staticmethod
    async def disable_tool(tool_name: str) -> bool:
        """Disable a tool."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                update(MCPTool)
                .where(MCPTool.name == tool_name)
                .values(is_enabled=False)
            )
            await db.commit()

            if result.rowcount > 0:
                logger.info(f"Disabled tool: {tool_name}")
                return True
            return False

    @staticmethod
    async def record_tool_usage(
        tool_name: str, success: bool, duration_ms: Optional[int] = None
    ) -> bool:
        """Record a tool usage event."""
        async with AsyncSessionLocal() as db:
            tool = await db.execute(select(MCPTool).where(MCPTool.name == tool_name))
            tool = tool.scalar_one_or_none()

            if not tool:
                return False

            tool.record_usage(success, duration_ms)
            await db.commit()

            return True

    @staticmethod
    async def get_tool_stats(
        server_name: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get tool usage statistics."""
        async with AsyncSessionLocal() as db:
            query = select(MCPTool).options(selectinload(MCPTool.server))

            if server_name:
                query = query.join(MCPServer).where(MCPServer.name == server_name)

            result = await db.execute(
                query.order_by(MCPTool.usage_count.desc()).limit(limit)
            )
            tools = result.scalars().all()

            stats = []
            for tool in tools:
                stats.append(
                    {
                        "name": tool.name,
                        "server": tool.server.name,
                        "usage_count": tool.usage_count,
                        "success_count": tool.success_count,
                        "error_count": tool.error_count,
                        "success_rate": tool.success_rate,
                        "average_duration_ms": tool.average_duration_ms,
                        "last_used_at": tool.last_used_at,
                        "is_enabled": tool.is_enabled,
                    }
                )

            return stats

    @staticmethod
    async def discover_tools_from_server(server_name: str) -> Dict[str, Any]:
        """Discover tools from an MCP server and update the registry."""
        async with AsyncSessionLocal() as db:
            # Get the server
            server_result = await db.execute(
                select(MCPServer).where(MCPServer.name == server_name)
            )
            server = server_result.scalar_one_or_none()

            if not server:
                logger.error(f"Server not found: {server_name}")
                return {"success": False, "error": "Server not found"}

            if not server.is_enabled:
                logger.info(f"Server {server_name} is disabled, skipping discovery")
                return {"success": False, "error": "Server is disabled"}

            try:
                # Import the MCP client service
                from .mcp_client import FastMCPClientService

                # Create a temporary client to discover tools
                client_service = FastMCPClientService()
                discovered_tools = await client_service.discover_tools(
                    server.url, server.timeout
                )

                new_tools = 0
                updated_tools = 0
                errors = []

                for tool_info in discovered_tools:
                    try:
                        tool_name = f"{server_name}_{tool_info.get('name', 'unknown')}"
                        original_name = tool_info.get("name", "unknown")

                        # Check if tool already exists
                        existing_tool = await db.execute(
                            select(MCPTool).where(MCPTool.name == tool_name)
                        )
                        existing_tool = existing_tool.scalar_one_or_none()

                        if existing_tool:
                            # Update existing tool (preserve enabled/disabled status)
                            existing_tool.description = tool_info.get("description")
                            existing_tool.parameters = tool_info.get("parameters", {})
                            updated_tools += 1
                            logger.info(f"Updated existing tool: {tool_name}")
                        else:
                            # Create new tool
                            new_tool = MCPTool(
                                name=tool_name,
                                original_name=original_name,
                                server_id=server.id,
                                description=tool_info.get("description"),
                                parameters=tool_info.get("parameters", {}),
                                is_enabled=True,  # New tools are enabled by default
                            )
                            db.add(new_tool)
                            new_tools += 1
                            logger.info(f"Discovered new tool: {tool_name}")

                    except Exception as e:
                        error_msg = f"Failed to process tool {tool_info.get('name', 'unknown')}: {e}"
                        errors.append(error_msg)
                        logger.error(error_msg)

                # Update server connection status
                await MCPRegistryService.update_connection_status(
                    server_name, True, False
                )

                await db.commit()

                result = {
                    "success": True,
                    "server": server_name,
                    "new_tools": new_tools,
                    "updated_tools": updated_tools,
                    "total_discovered": len(discovered_tools),
                    "errors": errors,
                }

                logger.info(
                    f"Tool discovery completed for {server_name}: {new_tools} new, {updated_tools} updated"
                )
                return result

            except Exception as e:
                error_msg = f"Failed to discover tools from server {server_name}: {e}"
                logger.error(error_msg)

                # Update server connection status
                await MCPRegistryService.update_connection_status(
                    server_name, False, True
                )

                return {
                    "success": False,
                    "server": server_name,
                    "error": str(e),
                    "new_tools": 0,
                    "updated_tools": 0,
                    "total_discovered": 0,
                }

    @staticmethod
    async def discover_tools_all_servers() -> List[Dict[str, Any]]:
        """Discover tools from all enabled MCP servers."""
        async with AsyncSessionLocal() as db:
            # Get all enabled servers
            result = await db.execute(
                select(MCPServer).where(MCPServer.is_enabled == True)
            )
            servers = result.scalars().all()

            if not servers:
                logger.info("No enabled MCP servers found for tool discovery")
                return []

            logger.info(f"Starting tool discovery for {len(servers)} servers")
            discovery_results = []

            for server in servers:
                result = await MCPRegistryService.discover_tools_from_server(
                    server.name
                )
                discovery_results.append(result)

                # Small delay between discoveries to avoid overwhelming servers
                await asyncio.sleep(0.5)

            return discovery_results

    @staticmethod
    async def auto_discover_on_server_change(
        server_name: str, was_enabled: bool, is_enabled: bool
    ) -> Optional[Dict[str, Any]]:
        """Automatically discover tools when a server is enabled or re-enabled."""
        if not was_enabled and is_enabled:
            # Server was just enabled - discover tools
            logger.info(
                f"Server {server_name} was enabled, starting automatic tool discovery"
            )
            return await MCPRegistryService.discover_tools_from_server(server_name)

        return None
