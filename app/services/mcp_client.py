"Service layer for mcp_client business logic."

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from fastmcp import Client
from fastmcp.client import StreamableHttpTransport
from ..config import settings
from ..core.exceptions import ExternalServiceError
from ..utils.api_errors import handle_api_errors
from ..utils.logging import get_api_logger
from ..utils.tool_middleware import RetryConfig, tool_operation

logger = get_api_logger("mcp_client")


@dataclass
class MCPServerConfig:
    "MCPServerConfig class for specialized functionality."

    name: str
    url: str
    timeout: int = 30


class FastMCPClientService:
    "FastMCPClient service for business logic operations."

    def __init__(self):
        "Initialize class instance."
        self.clients: Dict[(str, Client)] = {}
        self.servers: Dict[(str, MCPServerConfig)] = {}
        self.tools: Dict[(str, Dict[(str, Any)])] = {}
        self.is_initialized = False
        logger.info("FastMCP client service initialized")

    async def _parse_server_configs(self):
        "Parse Server Configs operation."
        from .mcp_registry import MCPRegistryService

        if not settings.mcp_enabled:
            return
        try:
            registry_servers = await MCPRegistryService.list_servers(enabled_only=True)
            for server in registry_servers:
                server_config = MCPServerConfig(
                    name=server.name, url=server.url, timeout=server.timeout
                )
                self.servers[server.name] = server_config
            logger.info(
                f"Loaded {len(self.servers)} MCP servers from registry: {list(self.servers.keys())}"
            )
            if not self.servers:
                logger.warning(
                    "No enabled MCP servers found in registry. Use the registry API to register MCP servers."
                )
        except Exception as e:
            logger.error(f"Failed to load MCP server configs from registry: {e}")
            raise ExternalServiceError(f"MCP registry configuration failed: {e}")

    @handle_api_errors("MCP initialization failed", log_errors=False)
    async def initialize(self):
        "Initialize operation."
        (await self._parse_server_configs())
        if not self.servers:
            logger.warning(
                "No MCP servers found in registry - cannot initialize MCP clients"
            )
            self.is_initialized = False
            return
        try:
            successful_connections = 0
            for server_name, server in self.servers.items():
                try:
                    (await self._connect_server(server_name, server))
                    successful_connections += 1
                    logger.info(f"✅ Connected to MCP server (HTTP): {server_name}")
                except Exception as e:
                    logger.error(
                        f"❌ Failed to connect to MCP server {server_name}: {e}"
                    )
            (await self._discover_tools())
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
            logger.warning("Continuing without MCP integration")
            self.is_initialized = False

    async def _connect_server(self, server_name: str, server: MCPServerConfig):
        "Connect Server operation."
        from .mcp_registry import MCPRegistryService

        try:
            transport = StreamableHttpTransport(server.url)
            client = Client(transport, timeout=1)
            async with client:
                self.clients[server_name] = client
                (await MCPRegistryService.update_connection_status(server_name, True))
                logger.info(
                    f"Successfully configured MCP HTTP server: {server_name} ({server.url})"
                )
        except asyncio.TimeoutError:
            logger.error(
                f"Timeout connecting to MCP server {server_name} after {server.timeout}s"
            )
            (
                await MCPRegistryService.update_connection_status(
                    server_name, False, increment_errors=True
                )
            )
            raise
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server_name}: {e}")
            self.clients.pop(server_name, None)
            (
                await MCPRegistryService.update_connection_status(
                    server_name, False, increment_errors=True
                )
            )
            raise

    async def _discover_tools(self):
        "Discover Tools operation."
        from .mcp_registry import MCPRegistryService

        for server_name, client in self.clients.items():
            try:
                async with client:
                    tools_response = await client.list_tools()
                    server_tools = []
                    if hasattr(tools_response, "tools"):
                        tools_list = tools_response.tools
                    elif isinstance(tools_response, dict) and (
                        "tools" in tools_response
                    ):
                        tools_list = tools_response["tools"]
                    elif isinstance(tools_response, list):
                        tools_list = tools_response
                    else:
                        logger.warning(
                            f"Unexpected tools response format from {server_name}: {type(tools_response)}"
                        )
                        continue
                    for tool_info in tools_list:
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
                        try:
                            (
                                await MCPRegistryService.register_tool(
                                    server_name=server_name,
                                    tool_name=tool_name,
                                    original_name=tool_name_attr,
                                    description=tool_desc,
                                    parameters=schema_dict,
                                    is_enabled=True,
                                )
                            )
                        except Exception as e:
                            logger.debug(
                                f"Tool {tool_name} already registered or registration failed: {e}"
                            )
                    logger.info(
                        f"Discovered {len(server_tools)} tools from {server_name}: {server_tools}"
                    )
            except Exception as e:
                logger.warning(f"Failed to discover tools from {server_name}: {e}")
        logger.info(f"Total discovered tools: {len(self.tools)}")
        (await self._sync_servers_with_registry())
        (await self._sync_tools_with_registry())

    async def _sync_servers_with_registry(self):
        "Sync Servers With Registry operation."
        from .mcp_registry import MCPRegistryService

        try:
            registered_servers = await MCPRegistryService.list_servers()
            registered_names = {server.name for server in registered_servers}
            for server_name, server_config in self.servers.items():
                if server_name not in registered_names:
                    try:
                        (
                            await MCPRegistryService.create_server(
                                name=server_name,
                                url=server_config.url,
                                description="Auto-registered server from configuration",
                                transport="http",
                                timeout=server_config.timeout,
                                is_enabled=True,
                            )
                        )
                        logger.info(f"Auto-registered server: {server_name}")
                    except Exception as e:
                        logger.warning(
                            f"Failed to auto-register server {server_name}: {e}"
                        )
            for server_name in self.servers.keys():
                is_connected = server_name in self.clients
                (
                    await MCPRegistryService.update_connection_status(
                        server_name, is_connected
                    )
                )
        except Exception as e:
            logger.warning(f"Failed to sync servers with registry: {e}")

    async def _sync_tools_with_registry(self):
        "Sync Tools With Registry operation."
        from .mcp_registry import MCPRegistryService

        for tool_name, tool_info in self.tools.items():
            try:
                (
                    await MCPRegistryService.register_tool(
                        server_name=tool_info["server"],
                        tool_name=tool_name,
                        original_name=tool_info["original_name"],
                        description=tool_info.get("description"),
                        parameters=tool_info.get("parameters"),
                        is_enabled=True,
                    )
                )
            except Exception as e:
                logger.debug(f"Tool {tool_name} already registered or failed: {e}")

    @handle_api_errors("MCP tool call failed")
    @tool_operation(
        retry_config=RetryConfig(max_retries=3),
        cache_ttl=300,
        enable_caching=True,
        log_details=True,
    )
    async def call_tool(
        self, tool_name: str, parameters: Dict[(str, Any)], record_usage: bool = True
    ) -> Dict[(str, Any)]:
        "Call Tool operation."
        if not self.is_initialized:
            raise ExternalServiceError("MCP client not initialized")
        from .mcp_registry import MCPRegistryService

        tool_from_registry = None
        try:
            tool_from_registry = await MCPRegistryService.get_tool(tool_name)
            if tool_from_registry and (not tool_from_registry.is_enabled):
                raise ExternalServiceError(f"Tool '{tool_name}' is disabled")
            if tool_from_registry:
                server = await MCPRegistryService.get_server(
                    tool_from_registry.server.name
                )
                if server and (not server.is_enabled):
                    raise ExternalServiceError(
                        f"Server '{tool_from_registry.server.name}' is disabled"
                    )
        except Exception as e:
            logger.warning(f"Registry check failed for tool {tool_name}: {e}")
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
        start_time = time.time()
        success = False
        try:
            async with client:
                result = await client.call_tool(
                    name=original_tool_name, arguments=parameters
                )
            success = True
        except Exception as e:
            success = False
            raise
        finally:
            if record_usage and tool_from_registry:
                try:
                    duration_ms = int(((time.time() - start_time) * 1000))
                    (
                        await MCPRegistryService.record_tool_usage(
                            tool_name, success, duration_ms
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed to record tool usage: {e}")
        formatted_result = {
            "success": True,
            "tool_name": tool_name,
            "server": server_name,
            "content": [],
            "raw_result": self._serialize_result(result),
        }
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
        elif isinstance(result, dict) and ("content" in result):
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
        if not formatted_result["content"]:
            formatted_result["content"].append({"type": "text", "text": str(result)})
        logger.info(
            f"Tool '{tool_name}' executed successfully on server '{server_name}'"
        )
        return formatted_result

    def _serialize_result(self, result: Any) -> str:
        "Serialize Result operation."
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
        self, enabled_only: bool = False
    ) -> Dict[(str, Dict[(str, Any)])]:
        "Get available tools data."
        if not self.is_initialized:
            logger.warning("MCP client not initialized - returning empty tools list")
            return {}
        if not enabled_only:
            return self.tools.copy()
        from .mcp_registry import MCPRegistryService

        try:
            registry_tools = await MCPRegistryService.list_tools(
                enabled_only=enabled_only
            )
            available_tools = {}
            for tool in registry_tools:
                if enabled_only and (not tool.server.is_enabled):
                    continue
                if tool.name not in self.tools:
                    continue
                local_tool = self.tools[tool.name]
                available_tools[tool.name] = {
                    "name": tool.name,
                    "original_name": tool.original_name,
                    "description": (tool.description or local_tool.get("description")),
                    "server": tool.server.name,
                    "parameters": (tool.parameters or local_tool.get("parameters", {})),
                    "is_enabled": tool.is_enabled,
                    "usage_count": tool.usage_count,
                    "success_rate": tool.success_rate,
                }
            return available_tools
        except Exception as e:
            logger.warning(f"Failed to get enhanced tools list: {e}")
            return self.tools.copy()

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[(str, Any)]]:
        "Get tool schema data."
        return self.tools.get(tool_name)

    async def get_tools_for_openai(
        self, enabled_only: bool = False
    ) -> List[Dict[(str, Any)]]:
        "Get tools for openai data."
        available_tools = await self.get_available_tools(enabled_only=enabled_only)
        openai_tools = []
        for tool_name, tool in available_tools.items():
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": (
                        tool["description"] or f"Tool from {tool['server']}"
                    ),
                    "parameters": tool["parameters"],
                },
            }
            openai_tools.append(openai_tool)
        return openai_tools

    @handle_api_errors("MCP tool calls execution failed")
    async def execute_tool_calls(
        self, tool_calls: List[Dict[(str, Any)]]
    ) -> List[Dict[(str, Any)]]:
        "Execute Tool Calls operation."
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

    async def health_check(self) -> Dict[(str, Any)]:
        "Health Check operation."
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
                (await asyncio.wait_for(client.list_tools(), timeout=5))
                tools_count = len(
                    [t for t in self.tools.values() if (t["server"] == server_name)]
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
        for server_name in self.servers:
            if server_name not in self.clients:
                health_status["server_status"][server_name] = {
                    "status": "disconnected",
                    "error": "Failed to connect",
                    "connected": False,
                }
                health_status["unhealthy_servers"] += 1
        try:
            from .mcp_registry import MCPRegistryService

            servers = await MCPRegistryService.list_servers()
            tools = await MCPRegistryService.list_tools()
            enabled_servers = sum((1 for s in servers if s.is_enabled))
            enabled_tools = sum((1 for t in tools if t.is_enabled))
            health_status.update(
                {
                    "registry": {
                        "total_servers": len(servers),
                        "enabled_servers": enabled_servers,
                        "disabled_servers": (len(servers) - enabled_servers),
                        "total_tools": len(tools),
                        "enabled_tools": enabled_tools,
                        "disabled_tools": (len(tools) - enabled_tools),
                    }
                }
            )
        except Exception as e:
            logger.warning(f"Failed to get registry statistics: {e}")
            health_status["registry"] = {"error": "Registry unavailable"}
        return health_status

    async def disconnect_all(self):
        "Disconnect All operation."
        disconnected_servers = []
        for server_name, client in self.clients.items():
            try:
                (await client.close())
                disconnected_servers.append(server_name)
                logger.info(f"Disconnected from MCP server: {server_name}")
            except Exception as e:
                logger.warning(f"Error disconnecting from {server_name}: {e}")
        self.clients.clear()
        self.tools.clear()
        self.is_initialized = False
        logger.info(f"Disconnected from {len(disconnected_servers)} MCP servers")

    async def list_resources(
        self, server_name: Optional[str] = None
    ) -> Dict[(str, Any)]:
        "List resources entries."
        if not self.is_initialized:
            raise ExternalServiceError("MCP client not initialized")
        resources = {}
        clients_to_check = {}
        if server_name and (server_name in self.clients):
            clients_to_check[server_name] = self.clients[server_name]
        else:
            clients_to_check = self.clients
        for srv_name, client in clients_to_check.items():
            try:
                resources_response = await client.list_resources()
                if hasattr(resources_response, "resources"):
                    resources_list = resources_response.resources
                elif isinstance(resources_response, dict) and (
                    "resources" in resources_response
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

    async def read_resource(self, server_name: str, uri: str) -> Dict[(str, Any)]:
        "Read Resource operation."
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
            if hasattr(result, "contents"):
                contents_list = result.contents
            elif isinstance(result, dict) and ("contents" in result):
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


_mcp_client_instance: Optional[FastMCPClientService] = None


async def get_mcp_client() -> FastMCPClientService:
    "Get mcp client data."
    global _mcp_client_instance
    if _mcp_client_instance is None:
        _mcp_client_instance = FastMCPClientService()
        (await _mcp_client_instance.initialize())
    return _mcp_client_instance


async def cleanup_mcp_client():
    "Cleanup Mcp Client operation."
    global _mcp_client_instance
    if _mcp_client_instance is not None:
        (await _mcp_client_instance.disconnect_all())
        _mcp_client_instance = None
