"""
FastMCP client service for tool integration and external function execution.

This service provides integration with MCP servers using the FastMCP client
for tool calling and external function execution capabilities.

Updated to use HTTP transport for all server connections.

Current Date and Time (UTC): 2025-07-21 04:22:44
Updated on: 2025-07-21 04:22:44 UTC
Current User: lllucius / assistant
"""

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from fastmcp import Client
from fastmcp.client import SSETransport

from ..config import settings
from ..core.exceptions import ExternalServiceError
from ..utils.api_errors import handle_api_errors
from ..utils.tool_middleware import tool_operation, RetryConfig
from ..utils.logging import get_api_logger

logger = get_api_logger("mcp_client")


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""

    name: str
    url: str
    timeout: int = 30


class FastMCPClientService:
    """
    FastMCP client service for tool calling and external integrations.

    This service manages connections to MCP servers using FastMCP and provides
    an interface for tool discovery and execution with unified error handling.

    Key Features:
    - Consistent error handling via @handle_api_errors decorator
    - Retry logic and caching through middleware decorators
    - Structured logging for all tool operations
    - Integration with UnifiedToolExecutor for consistent tool calling patterns
    - Automatic server connection management and health monitoring

    Architecture:
    - Uses decorators instead of manual try/catch blocks
    - Centralized retry and caching logic through middleware
    - Full async/await support throughout
    - Proper exception handling and logging

    Tool Operations:
    - call_tool(): Execute individual tools with unified patterns
    - execute_tool_calls(): Batch tool execution for OpenAI integration
    - Automatic tool discovery and schema management
    - Health checking and connection monitoring
    """

    def __init__(self):
        """Initialize FastMCP client service."""
        self.clients: Dict[str, Client] = {}
        self.servers: Dict[str, MCPServerConfig] = {}
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.is_initialized = False

        # Parse server configurations
        self._parse_server_configs()

        logger.info("FastMCP client service initialized")

    def _parse_server_configs(self):
        """Parse MCP server configurations from settings."""
        try:
            # Get server configurations from settings
            mcp_servers_config = settings.mcp_servers

            for server_name, config in mcp_servers_config.items():
                # All servers must provide a 'url' key for SSETransport
                url = config.get("url")
                if not url:
                    # Default to localhost with server name as port for demo
                    # You may customize this per your deployment!
                    port = 8000 + len(self.servers)  # Example: http://localhost:8000, 8001, etc.
                    url = f"http://localhost:{port}"
                server = MCPServerConfig(
                    name=server_name,
                    url=url,
                    timeout=config.get("timeout", settings.mcp_timeout),
                )
                self.servers[server.name] = server

            logger.info(
                f"Configured {len(self.servers)} MCP servers (HTTP): {list(self.servers.keys())}"
            )

        except Exception as e:
            logger.error(f"Failed to parse MCP server configs: {e}")
            raise ExternalServiceError(f"MCP configuration failed: {e}")

    @handle_api_errors("MCP initialization failed", log_errors=False)
    async def initialize(self):
        """
        Initialize connections to MCP servers with improved error handling.
        """
        if not self.servers:
            logger.warning("No MCP servers configured - cannot initialize MCP clients")
            self.is_initialized = False
            return

        try:
            successful_connections = 0

            # Try to connect to configured servers
            for server_name, server in self.servers.items():
                try:
                    await self._connect_server(server_name, server)
                    successful_connections += 1
                    logger.info(f"✅ Connected to MCP server (HTTP): {server_name}")
                except Exception as e:
                    logger.error(
                        f"❌ Failed to connect to MCP server {server_name}: {e}"
                    )
                    # Don't fail completely - continue with other servers

            # Discover available tools from connected clients
            await self._discover_tools()

            if not self.tools:
                logger.warning("⚠️  No tools discovered from MCP servers")
            else:
                logger.info(f"🛠️  Discovered {len(self.tools)} tools from MCP servers")

            self.is_initialized = True
            logger.info(
                f"FastMCP initialization completed: {successful_connections}/{len(self.servers)} servers connected"
            )

        except Exception as e:
            logger.error(f"FastMCP client initialization failed: {e}")
            # Don't raise - MCP is optional for basic functionality
            logger.warning("Continuing without MCP integration")
            self.is_initialized = False

    async def _connect_server(self, server_name: str, server: MCPServerConfig):
        """Connect to a specific MCP server using SSETransport."""
        try:
            # Create FastMCP client with HTTP transport
            transport = SSETransport(server.url)
            client = Client(transport)

            # Test connection with timeout
            async with asyncio.timeout(server.timeout):
                # Store client first
                self.clients[server_name] = client
                logger.info(f"Successfully configured MCP HTTP server: {server_name} ({server.url})")

        except asyncio.TimeoutError:
            logger.error(
                f"Timeout connecting to MCP server {server_name} after {server.timeout}s"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server_name}: {e}")
            # Remove client if it was added
            self.clients.pop(server_name, None)
            raise

    async def _discover_tools(self):
        """Discover available tools from connected servers."""
        for server_name, client in self.clients.items():
            try:
                async with client:
                    # List available tools from the server
                    tools_response = await client.list_tools()
                    server_tools = []

                    # Handle the tools response structure
                    if hasattr(tools_response, "tools"):
                        tools_list = tools_response.tools
                    elif isinstance(tools_response, dict) and "tools" in tools_response:
                        tools_list = tools_response["tools"]
                    elif isinstance(tools_response, list):
                        tools_list = tools_response
                    else:
                        logger.warning(
                            f"Unexpected tools response format from {server_name}: {type(tools_response)}"
                        )
                        continue

                    for tool_info in tools_list:
                        # Handle different tool info structures
                        if hasattr(tool_info, "name"):
                            tool_name_attr = tool_info.name
                            tool_desc = getattr(
                                tool_info, "description", f"Tool from {server_name}"
                            )
                            tool_schema = getattr(tool_info, "inputSchema", None)
                        elif isinstance(tool_info, dict):
                            tool_name_attr = tool_info.get(
                                "name", f"unknown_tool_{len(server_tools)}"
                            )
                            tool_desc = tool_info.get(
                                "description", f"Tool from {server_name}"
                            )
                            tool_schema = tool_info.get("inputSchema", None)
                        else:
                            logger.warning(
                                f"Unexpected tool info format from {server_name}: {type(tool_info)}"
                            )
                            continue

                        tool_name = f"{server_name}_{tool_name_attr}"

                        # Process tool schema
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

                        self.tools[tool_name] = {
                            "name": tool_name,
                            "original_name": tool_name_attr,
                            "description": tool_desc,
                            "server": server_name,
                            "parameters": schema_dict,
                        }
                        server_tools.append(tool_name)

                    logger.info(
                        f"Discovered {len(server_tools)} tools from {server_name}: {server_tools}"
                    )

            except Exception as e:
                logger.warning(f"Failed to discover tools from {server_name}: {e}")

        logger.info(f"Total discovered tools: {len(self.tools)}")

    @handle_api_errors("MCP tool call failed")
    @tool_operation(
        retry_config=RetryConfig(max_retries=3),
        cache_ttl=300,
        enable_caching=True,
        log_details=True,
    )
    async def call_tool(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call a tool on an MCP server using FastMCP with unified patterns.

        Args:
            tool_name: Name of the tool to call (format: server_toolname)
            parameters: Parameters to pass to the tool

        Returns:
            dict: Tool execution result
        """
        if not self.is_initialized:
            raise ExternalServiceError("MCP client not initialized")

        if tool_name not in self.tools:
            available_tools = list(self.tools.keys())
            raise ExternalServiceError(
                f"Tool '{tool_name}' not found. Available tools: {available_tools}"
            )

        tool = self.tools[tool_name]
        server_name = tool["server"]
        original_tool_name = tool["original_name"]

        if server_name not in self.clients:
            raise ExternalServiceError(f"Server '{server_name}' not connected")

        client = self.clients[server_name]

        # Call the tool using FastMCP
        async with client:
            result = await client.call_tool(
                name=original_tool_name, arguments=parameters
            )

        # Format the response
        formatted_result = {
            "success": True,
            "tool_name": tool_name,
            "server": server_name,
            "content": [],
            "raw_result": self._serialize_result(result),
        }

        # Process result content
        if hasattr(result, "content") and result.content:
            for content_item in result.content:
                if hasattr(content_item, "text"):
                    formatted_result["content"].append(
                        {"type": "text", "text": content_item.text}
                    )
                elif hasattr(content_item, "data"):
                    formatted_result["content"].append(
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
                        formatted_result["content"].append(
                            {"type": "text", "text": content_item["text"]}
                        )
                    elif "data" in content_item:
                        formatted_result["content"].append(
                            {
                                "type": "data",
                                "data": content_item["data"],
                                "mimeType": content_item.get(
                                    "mimeType", "application/octet-stream"
                                ),
                            }
                        )
        elif isinstance(result, dict) and "content" in result:
            # Handle dict-based result
            for content_item in result["content"]:
                if isinstance(content_item, dict):
                    if "text" in content_item:
                        formatted_result["content"].append(
                            {"type": "text", "text": content_item["text"]}
                        )
                    elif "data" in content_item:
                        formatted_result["content"].append(
                            {
                                "type": "data",
                                "data": content_item["data"],
                                "mimeType": content_item.get(
                                    "mimeType", "application/octet-stream"
                                ),
                            }
                        )

        # If no content was found, add the raw result as text
        if not formatted_result["content"]:
            formatted_result["content"].append({"type": "text", "text": str(result)})

        logger.info(
            f"Tool '{tool_name}' executed successfully on server '{server_name}'"
        )

        return formatted_result

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

    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Get list of available tools.

        Returns:
            dict: Available tools and their schemas
        """
        if not self.is_initialized:
            logger.warning("MCP client not initialized - returning empty tools list")
            return {}

        return self.tools.copy()

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get schema for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            dict: Tool schema or None if not found
        """
        return self.tools.get(tool_name)

    def get_tools_for_openai(self) -> List[Dict[str, Any]]:
        """
        Get tools formatted for OpenAI function calling.

        Returns:
            list: Tools in OpenAI format
        """
        if not self.is_initialized:
            logger.warning(
                "MCP client not initialized - returning empty tools list for OpenAI"
            )
            return []

        openai_tools = []

        for tool_name, tool in self.tools.items():
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            }
            openai_tools.append(openai_tool)

        return openai_tools

    @handle_api_errors("MCP tool calls execution failed")
    async def execute_tool_calls(
        self, tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tool calls from OpenAI function calling.

        Args:
            tool_calls: List of tool calls from OpenAI

        Returns:
            list: Results from tool executions
        """
        if not self.is_initialized:
            raise ExternalServiceError(
                "MCP client not initialized - cannot execute tool calls"
            )

        results = []
        for tool_call in tool_calls:
            try:
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])

                result = await self.call_tool(function_name, function_args)
                results.append(result)
            except Exception as e:
                logger.error(
                    f"Failed to execute tool call {tool_call.get('id', 'unknown')}: {e}"
                )
                results.append(
                    {
                        "tool_call_id": tool_call.get("id", "unknown"),
                        "function_name": tool_call.get("function", {}).get(
                            "name", "unknown"
                        ),
                        "success": False,
                        "error": str(e),
                    }
                )

        return results

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of MCP servers using FastMCP.

        Returns:
            dict: Health status of all servers
        """
        health_status = {
            "fastmcp_available": True,
            "total_servers": len(self.servers),
            "healthy_servers": 0,
            "unhealthy_servers": 0,
            "server_status": {},
            "initialized": self.is_initialized,
            "tools_count": len(self.tools),
        }

        for server_name, client in self.clients.items():
            try:
                # Try to ping the server by listing tools
                await asyncio.wait_for(client.list_tools(), timeout=5)

                tools_count = len(
                    [t for t in self.tools.values() if t["server"] == server_name]
                )

                health_status["server_status"][server_name] = {
                    "status": "healthy",
                    "tools_count": tools_count,
                    "connected": True,
                }
                health_status["healthy_servers"] += 1

            except Exception as e:
                health_status["server_status"][server_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "connected": False,
                }
                health_status["unhealthy_servers"] += 1

        # Add servers that failed to connect
        for server_name in self.servers:
            if server_name not in self.clients:
                health_status["server_status"][server_name] = {
                    "status": "disconnected",
                    "error": "Failed to connect",
                    "connected": False,
                }
                health_status["unhealthy_servers"] += 1

        return health_status

    async def disconnect_all(self):
        """Disconnect from all MCP servers."""
        disconnected_servers = []

        for server_name, client in self.clients.items():
            try:
                await client.close()
                disconnected_servers.append(server_name)
                logger.info(f"Disconnected from MCP server: {server_name}")
            except Exception as e:
                logger.warning(f"Error disconnecting from {server_name}: {e}")

        self.clients.clear()
        self.tools.clear()
        self.is_initialized = False

        logger.info(f"Disconnected from {len(disconnected_servers)} MCP servers")

    async def list_resources(self, server_name: Optional[str] = None) -> Dict[str, Any]:
        """
        List available resources from MCP servers.

        Args:
            server_name: Optional specific server name

        Returns:
            dict: Available resources
        """
        if not self.is_initialized:
            raise ExternalServiceError("MCP client not initialized")

        resources = {}

        clients_to_check = {}
        if server_name and server_name in self.clients:
            clients_to_check[server_name] = self.clients[server_name]
        else:
            clients_to_check = self.clients

        for srv_name, client in clients_to_check.items():
            try:
                resources_response = await client.list_resources()

                # Handle different response formats
                if hasattr(resources_response, "resources"):
                    resources_list = resources_response.resources
                elif (
                    isinstance(resources_response, dict)
                    and "resources" in resources_response
                ):
                    resources_list = resources_response["resources"]
                elif isinstance(resources_response, list):
                    resources_list = resources_response
                else:
                    resources_list = []

                formatted_resources = []
                for resource in resources_list:
                    if hasattr(resource, "uri"):
                        formatted_resources.append(
                            {
                                "uri": resource.uri,
                                "name": getattr(resource, "name", resource.uri),
                                "description": getattr(resource, "description", ""),
                                "mimeType": getattr(resource, "mimeType", None),
                            }
                        )
                    elif isinstance(resource, dict):
                        formatted_resources.append(
                            {
                                "uri": resource.get("uri", ""),
                                "name": resource.get("name", resource.get("uri", "")),
                                "description": resource.get("description", ""),
                                "mimeType": resource.get("mimeType", None),
                            }
                        )

                resources[srv_name] = formatted_resources

            except Exception as e:
                logger.warning(f"Failed to list resources from {srv_name}: {e}")
                resources[srv_name] = []

        return {"resources": resources}

    async def read_resource(self, server_name: str, uri: str) -> Dict[str, Any]:
        """
        Read a specific resource from an MCP server.

        Args:
            server_name: Name of the server
            uri: URI of the resource to read

        Returns:
            dict: Resource content
        """
        if not self.is_initialized:
            raise ExternalServiceError("MCP client not initialized")

        if server_name not in self.clients:
            raise ExternalServiceError(f"Server '{server_name}' not connected")

        try:
            client = self.clients[server_name]
            result = await client.read_resource(uri=uri)

            formatted_result = {
                "success": True,
                "uri": uri,
                "server": server_name,
                "content": [],
            }

            # Handle different result formats
            if hasattr(result, "contents"):
                contents_list = result.contents
            elif isinstance(result, dict) and "contents" in result:
                contents_list = result["contents"]
            else:
                contents_list = [result] if result else []

            for content_item in contents_list:
                if hasattr(content_item, "text"):
                    formatted_result["content"].append(
                        {"type": "text", "text": content_item.text, "uri": uri}
                    )
                elif hasattr(content_item, "blob"):
                    formatted_result["content"].append(
                        {
                            "type": "blob",
                            "data": content_item.blob,
                            "mimeType": getattr(
                                content_item, "mimeType", "application/octet-stream"
                            ),
                            "uri": uri,
                        }
                    )
                elif isinstance(content_item, dict):
                    if "text" in content_item:
                        formatted_result["content"].append(
                            {"type": "text", "text": content_item["text"], "uri": uri}
                        )
                    elif "blob" in content_item:
                        formatted_result["content"].append(
                            {
                                "type": "blob",
                                "data": content_item["blob"],
                                "mimeType": content_item.get(
                                    "mimeType", "application/octet-stream"
                                ),
                                "uri": uri,
                            }
                        )

            return formatted_result

        except Exception as e:
            logger.error(f"Failed to read resource {uri} from {server_name}: {e}")
            raise ExternalServiceError(f"Failed to read resource: {e}")


# Global instance (created when needed)
_mcp_client_instance: Optional[FastMCPClientService] = None


async def get_mcp_client() -> FastMCPClientService:
    """Get or create the global MCP client instance."""
    global _mcp_client_instance

    if _mcp_client_instance is None:
        _mcp_client_instance = FastMCPClientService()
        await _mcp_client_instance.initialize()

    return _mcp_client_instance


async def cleanup_mcp_client():
    """Cleanup the global MCP client instance."""
    global _mcp_client_instance

    if _mcp_client_instance is not None:
        await _mcp_client_instance.disconnect_all()
        _mcp_client_instance = None
