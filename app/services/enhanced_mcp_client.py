"""
Enhanced MCP Client service that integrates with the registry system.

This service extends the existing MCP client to work with the database registry,
providing usage tracking and enabled/disabled server/tool management.

Current Date and Time (UTC): 2025-07-23 03:50:00
Current User: lllucius / assistant
"""

import time
from typing import Any, Dict, List, Optional

from ..utils.logging import get_api_logger
from .mcp_client import get_mcp_client
from .mcp_registry import MCPRegistryService

logger = get_api_logger("enhanced_mcp_client")


class EnhancedMCPClientService:
    """Enhanced MCP client that integrates with the registry system."""

    def __init__(self):
        """Initialize the enhanced MCP client."""
        self._mcp_client = None
        self._initialized = False

    async def initialize(self):
        """Initialize the enhanced client and sync with registry."""
        if self._initialized:
            return

        # Get the original MCP client
        self._mcp_client = await get_mcp_client()
        
        # Sync servers from settings with registry
        await self._sync_servers_with_registry()
        
        # Sync tools from discovered tools with registry
        await self._sync_tools_with_registry()
        
        self._initialized = True
        logger.info("Enhanced MCP client initialized with registry integration")

    async def _sync_servers_with_registry(self):
        """Sync configured servers with the registry."""
        if not self._mcp_client:
            return

        # Get servers from registry
        registered_servers = await MCPRegistryService.list_servers()
        registered_names = {server.name for server in registered_servers}

        # Register any servers from settings that aren't in registry
        for server_name, server_config in self._mcp_client.servers.items():
            if server_name not in registered_names:
                try:
                    await MCPRegistryService.create_server(
                        name=server_name,
                        url=server_config.url,
                        description="Auto-registered server from configuration",
                        transport="http",
                        timeout=server_config.timeout,
                        is_enabled=True
                    )
                    logger.info(f"Auto-registered server: {server_name}")
                except Exception as e:
                    logger.warning(f"Failed to auto-register server {server_name}: {e}")

        # Update connection status for registered servers
        for server_name in self._mcp_client.servers.keys():
            is_connected = server_name in self._mcp_client.clients
            await MCPRegistryService.update_connection_status(
                server_name, is_connected
            )

    async def _sync_tools_with_registry(self):
        """Sync discovered tools with the registry."""
        if not self._mcp_client:
            return

        # Register discovered tools that aren't in registry
        for tool_name, tool_info in self._mcp_client.tools.items():
            try:
                await MCPRegistryService.register_tool(
                    server_name=tool_info["server"],
                    tool_name=tool_name,
                    original_name=tool_info["original_name"],
                    description=tool_info.get("description"),
                    parameters=tool_info.get("parameters"),
                    is_enabled=True
                )
            except Exception as e:
                logger.debug(f"Tool {tool_name} already registered or failed: {e}")

    async def call_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any],
        record_usage: bool = True
    ) -> Dict[str, Any]:
        """
        Call a tool with registry integration for usage tracking and enabled/disabled checks.
        
        Args:
            tool_name: Name of the tool to call
            parameters: Parameters to pass to the tool
            record_usage: Whether to record usage statistics
            
        Returns:
            dict: Tool execution result
        """
        if not self._initialized:
            await self.initialize()

        # Check if tool is enabled in registry
        tool = await MCPRegistryService.get_tool(tool_name)
        if tool and not tool.is_enabled:
            raise Exception(f"Tool '{tool_name}' is disabled")

        # Check if server is enabled in registry
        if tool:
            server = await MCPRegistryService.get_server(tool.server.name)
            if server and not server.is_enabled:
                raise Exception(f"Server '{tool.server.name}' is disabled")

        # Record start time for duration tracking
        start_time = time.time()
        success = False
        
        try:
            # Call the tool using the original client
            result = await self._mcp_client.call_tool(tool_name, parameters)
            success = True
            return result
            
        except Exception:
            success = False
            raise
            
        finally:
            # Record usage if requested and tool exists in registry
            if record_usage and tool:
                duration_ms = int((time.time() - start_time) * 1000)
                await MCPRegistryService.record_tool_usage(
                    tool_name, success, duration_ms
                )

    async def get_available_tools(self, enabled_only: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Get available tools, optionally filtering by enabled status.
        
        Args:
            enabled_only: Whether to only return enabled tools
            
        Returns:
            dict: Available tools and their schemas
        """
        if not self._initialized:
            await self.initialize()

        # Get tools from registry with filtering
        registry_tools = await MCPRegistryService.list_tools(enabled_only=enabled_only)
        
        # Convert to the format expected by the original client
        available_tools = {}
        for tool in registry_tools:
            # Only include if the server is also enabled
            if enabled_only and not tool.server.is_enabled:
                continue
                
            available_tools[tool.name] = {
                "name": tool.name,
                "original_name": tool.original_name,
                "description": tool.description,
                "server": tool.server.name,
                "parameters": tool.parameters or {},
                "is_enabled": tool.is_enabled,
                "usage_count": tool.usage_count,
                "success_rate": tool.success_rate
            }
        
        return available_tools

    async def get_tools_for_openai(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get tools formatted for OpenAI function calling, with registry filtering.
        
        Args:
            enabled_only: Whether to only return enabled tools
            
        Returns:
            list: Tools in OpenAI format
        """
        available_tools = await self.get_available_tools(enabled_only=enabled_only)
        
        openai_tools = []
        for tool_name, tool in available_tools.items():
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool["description"] or f"Tool from {tool['server']}",
                    "parameters": tool["parameters"],
                },
            }
            openai_tools.append(openai_tool)

        return openai_tools

    async def execute_tool_calls(
        self, 
        tool_calls: List[Dict[str, Any]],
        record_usage: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tool calls with registry integration.
        
        Args:
            tool_calls: List of tool calls from OpenAI
            record_usage: Whether to record usage statistics
            
        Returns:
            list: Results from tool executions
        """
        results = []
        for tool_call in tool_calls:
            try:
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])

                result = await self.call_tool(
                    function_name, function_args, record_usage=record_usage
                )
                results.append(result)
                
            except Exception as e:
                logger.error(
                    f"Failed to execute tool call {tool_call.get('id', 'unknown')}: {e}"
                )
                results.append({
                    "tool_call_id": tool_call.get("id", "unknown"),
                    "function_name": tool_call.get("function", {}).get("name", "unknown"),
                    "success": False,
                    "error": str(e),
                })

        return results

    async def health_check(self) -> Dict[str, Any]:
        """Enhanced health check that includes registry information."""
        if not self._initialized:
            await self.initialize()

        # Get original health check
        health = await self._mcp_client.health_check()
        
        # Add registry statistics
        servers = await MCPRegistryService.list_servers()
        tools = await MCPRegistryService.list_tools()
        
        enabled_servers = sum(1 for s in servers if s.is_enabled)
        enabled_tools = sum(1 for t in tools if t.is_enabled)
        
        health.update({
            "registry": {
                "total_servers": len(servers),
                "enabled_servers": enabled_servers,
                "disabled_servers": len(servers) - enabled_servers,
                "total_tools": len(tools),
                "enabled_tools": enabled_tools,
                "disabled_tools": len(tools) - enabled_tools,
            }
        })
        
        return health


# Global instance
_enhanced_mcp_client_instance: Optional[EnhancedMCPClientService] = None


async def get_enhanced_mcp_client() -> EnhancedMCPClientService:
    """Get or create the global enhanced MCP client instance."""
    global _enhanced_mcp_client_instance

    if _enhanced_mcp_client_instance is None:
        _enhanced_mcp_client_instance = EnhancedMCPClientService()
        await _enhanced_mcp_client_instance.initialize()

    return _enhanced_mcp_client_instance


async def cleanup_enhanced_mcp_client():
    """Cleanup the global enhanced MCP client instance."""
    global _enhanced_mcp_client_instance
    _enhanced_mcp_client_instance = None