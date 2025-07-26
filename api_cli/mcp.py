"""
MCP management API CLI commands.

This module provides comprehensive MCP server and tool management functionality
through the API-based command line interface.
"""

import asyncio
from typing import Any, Dict, List, Optional

import typer
from rich import box
from rich.panel import Panel
from rich.table import Table

from .base import APIClient, console, error_message, info_message, success_message, warning_message

# Create the MCP management app
mcp_app = typer.Typer(help="🔌 MCP server and tool management commands", rich_markup_mode="rich")


@mcp_app.command("list-servers")
def list_servers(
    enabled_only: bool = typer.Option(False, "--enabled-only", help="Show only enabled servers"),
    connected_only: bool = typer.Option(
        False, "--connected-only", help="Show only connected servers"
    ),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information"),
):
    """List all registered MCP servers."""

    async def _list_servers():
        try:
            client = APIClient()
            
            # Build query parameters
            params = {}
            if enabled_only:
                params["enabled_only"] = "true"
            if connected_only:
                params["connected_only"] = "true"
            if detailed:
                params["detailed"] = "true"
            
            # Get servers from API
            response = await client.get("/api/v1/mcp/servers", params=params)
            
            if not response or not response.get("success"):
                error_message("Failed to retrieve MCP servers")
                return
            
            servers = response.get("data", [])
            
            if not servers:
                info_message("No MCP servers found")
                return

            if detailed:
                # Show detailed information
                for server in servers:
                    _display_server_details(server)
            else:
                # Show summary table
                _display_servers_table(servers)

        except Exception as e:
            error_message(f"Failed to list MCP servers: {str(e)}")

    asyncio.run(_list_servers())


@mcp_app.command("add-server")
def add_server(
    name: str = typer.Argument(..., help="Server name"),
    url: str = typer.Argument(..., help="Server URL"),
    description: str = typer.Option("", "--description", "-d", help="Server description"),
    enabled: bool = typer.Option(True, "--enabled/--disabled", help="Enable server after creation"),
    transport: str = typer.Option("http", "--transport", help="Transport type (http, websocket)"),
):
    """Add a new MCP server."""

    async def _add_server():
        try:
            client = APIClient()
            
            server_data = {
                "name": name,
                "url": url,
                "description": description,
                "enabled": enabled,
                "transport": transport,
            }
            
            response = await client.post("/api/v1/mcp/servers", json=server_data)
            
            if response and response.get("success"):
                success_message(f"MCP server '{name}' added successfully")
                if response.get("data"):
                    _display_server_details(response["data"])
            else:
                error_message(f"Failed to add MCP server: {response.get('message', 'Unknown error')}")

        except Exception as e:
            error_message(f"Failed to add MCP server: {str(e)}")

    asyncio.run(_add_server())


@mcp_app.command("remove-server")
def remove_server(
    name: str = typer.Argument(..., help="Server name to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Force removal without confirmation"),
):
    """Remove an MCP server."""

    async def _remove_server():
        try:
            if not force:
                confirmed = typer.confirm(f"Are you sure you want to remove MCP server '{name}'?")
                if not confirmed:
                    info_message("Operation cancelled")
                    return

            client = APIClient()
            response = await client.delete(f"/api/v1/mcp/servers/{name}")
            
            if response and response.get("success"):
                success_message(f"MCP server '{name}' removed successfully")
            else:
                error_message(f"Failed to remove MCP server: {response.get('message', 'Unknown error')}")

        except Exception as e:
            error_message(f"Failed to remove MCP server: {str(e)}")

    asyncio.run(_remove_server())


@mcp_app.command("enable-server")
def enable_server(name: str = typer.Argument(..., help="Server name to enable")):
    """Enable an MCP server."""

    async def _enable_server():
        try:
            client = APIClient()
            response = await client.patch(f"/api/v1/mcp/servers/{name}", json={"enabled": True})
            
            if response and response.get("success"):
                success_message(f"MCP server '{name}' enabled successfully")
            else:
                error_message(f"Failed to enable MCP server: {response.get('message', 'Unknown error')}")

        except Exception as e:
            error_message(f"Failed to enable MCP server: {str(e)}")

    asyncio.run(_enable_server())


@mcp_app.command("disable-server")
def disable_server(name: str = typer.Argument(..., help="Server name to disable")):
    """Disable an MCP server."""

    async def _disable_server():
        try:
            client = APIClient()
            response = await client.patch(f"/api/v1/mcp/servers/{name}", json={"enabled": False})
            
            if response and response.get("success"):
                success_message(f"MCP server '{name}' disabled successfully")
            else:
                error_message(f"Failed to disable MCP server: {response.get('message', 'Unknown error')}")

        except Exception as e:
            error_message(f"Failed to disable MCP server: {str(e)}")

    asyncio.run(_disable_server())


@mcp_app.command("test-server")
def test_server(name: str = typer.Argument(..., help="Server name to test")):
    """Test connection to an MCP server."""

    async def _test_server():
        try:
            client = APIClient()
            response = await client.post(f"/api/v1/mcp/servers/{name}/test")
            
            if response and response.get("success"):
                test_result = response.get("data", {})
                if test_result.get("connected"):
                    success_message(f"MCP server '{name}' connection test passed")
                    _display_connection_details(test_result)
                else:
                    warning_message(f"MCP server '{name}' connection test failed")
                    if test_result.get("error"):
                        error_message(f"Error: {test_result['error']}")
            else:
                error_message(f"Failed to test MCP server: {response.get('message', 'Unknown error')}")

        except Exception as e:
            error_message(f"Failed to test MCP server: {str(e)}")

    asyncio.run(_test_server())


@mcp_app.command("list-tools")
def list_tools(
    server: Optional[str] = typer.Option(None, "--server", "-s", help="Filter by server name"),
    enabled_only: bool = typer.Option(False, "--enabled-only", help="Show only enabled tools"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information"),
):
    """List all available MCP tools."""

    async def _list_tools():
        try:
            client = APIClient()
            
            # Build query parameters
            params = {}
            if server:
                params["server"] = server
            if enabled_only:
                params["enabled_only"] = "true"
            if detailed:
                params["detailed"] = "true"
            
            response = await client.get("/api/v1/mcp/tools", params=params)
            
            if not response or not response.get("success"):
                error_message("Failed to retrieve MCP tools")
                return
            
            tools = response.get("data", [])
            
            if not tools:
                info_message("No MCP tools found")
                return

            if detailed:
                # Show detailed information
                for tool in tools:
                    _display_tool_details(tool)
            else:
                # Show summary table
                _display_tools_table(tools)

        except Exception as e:
            error_message(f"Failed to list MCP tools: {str(e)}")

    asyncio.run(_list_tools())


@mcp_app.command("enable-tool")
def enable_tool(
    tool_name: str = typer.Argument(..., help="Tool name to enable"),
    server: Optional[str] = typer.Option(None, "--server", "-s", help="Server name"),
):
    """Enable an MCP tool."""

    async def _enable_tool():
        try:
            client = APIClient()
            
            params = {}
            if server:
                params["server"] = server
                
            response = await client.patch(f"/api/v1/mcp/tools/{tool_name}/enable", params=params)
            
            if response and response.get("success"):
                success_message(f"MCP tool '{tool_name}' enabled successfully")
            else:
                error_message(f"Failed to enable MCP tool: {response.get('message', 'Unknown error')}")

        except Exception as e:
            error_message(f"Failed to enable MCP tool: {str(e)}")

    asyncio.run(_enable_tool())


@mcp_app.command("disable-tool")
def disable_tool(
    tool_name: str = typer.Argument(..., help="Tool name to disable"),
    server: Optional[str] = typer.Option(None, "--server", "-s", help="Server name"),
):
    """Disable an MCP tool."""

    async def _disable_tool():
        try:
            client = APIClient()
            
            params = {}
            if server:
                params["server"] = server
                
            response = await client.patch(f"/api/v1/mcp/tools/{tool_name}/disable", params=params)
            
            if response and response.get("success"):
                success_message(f"MCP tool '{tool_name}' disabled successfully")
            else:
                error_message(f"Failed to disable MCP tool: {response.get('message', 'Unknown error')}")

        except Exception as e:
            error_message(f"Failed to disable MCP tool: {str(e)}")

    asyncio.run(_disable_tool())


@mcp_app.command("stats")
def stats():
    """Show MCP usage statistics."""

    async def _stats():
        try:
            client = APIClient()
            response = await client.get("/api/v1/mcp/stats")
            
            if not response or not response.get("success"):
                error_message("Failed to retrieve MCP statistics")
                return
            
            stats_data = response.get("data", {})
            _display_stats(stats_data)

        except Exception as e:
            error_message(f"Failed to get MCP statistics: {str(e)}")

    asyncio.run(_stats())


@mcp_app.command("refresh")
def refresh(
    server: Optional[str] = typer.Option(None, "--server", "-s", help="Refresh specific server"),
):
    """Refresh MCP server connections and tool discovery."""

    async def _refresh():
        try:
            client = APIClient()
            
            endpoint = "/api/v1/mcp/refresh"
            params = {}
            if server:
                params["server"] = server
            
            response = await client.post(endpoint, params=params)
            
            if response and response.get("success"):
                success_message("MCP refresh completed successfully")
                refresh_data = response.get("data", {})
                if refresh_data.get("servers_refreshed"):
                    info_message(f"Refreshed {refresh_data['servers_refreshed']} servers")
                if refresh_data.get("tools_discovered"):
                    info_message(f"Discovered {refresh_data['tools_discovered']} tools")
            else:
                error_message(f"Failed to refresh MCP: {response.get('message', 'Unknown error')}")

        except Exception as e:
            error_message(f"Failed to refresh MCP: {str(e)}")

    asyncio.run(_refresh())


def _display_servers_table(servers: List[Dict[str, Any]]):
    """Display servers in a table format."""
    table = Table(title="MCP Servers", box=box.ROUNDED)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("URL", style="blue")
    table.add_column("Status", style="green")
    table.add_column("Transport", style="yellow")
    table.add_column("Tools", style="magenta")

    for server in servers:
        status = "🟢 Enabled" if server.get("enabled") else "🔴 Disabled"
        if server.get("connected"):
            status += " (Connected)"
        elif server.get("enabled"):
            status += " (Disconnected)"

        table.add_row(
            server.get("name", "Unknown"),
            server.get("url", ""),
            status,
            server.get("transport", "http"),
            str(server.get("tool_count", 0)),
        )

    console.print(table)


def _display_server_details(server: Dict[str, Any]):
    """Display detailed server information."""
    name = server.get("name", "Unknown")
    status = "🟢 Enabled" if server.get("enabled") else "🔴 Disabled"
    
    details = [
        f"Name: [cyan]{name}[/cyan]",
        f"URL: [blue]{server.get('url', '')}[/blue]",
        f"Status: {status}",
        f"Transport: [yellow]{server.get('transport', 'http')}[/yellow]",
        f"Connected: {'🟢 Yes' if server.get('connected') else '🔴 No'}",
        f"Tools: [magenta]{server.get('tool_count', 0)}[/magenta]",
    ]
    
    if server.get("description"):
        details.append(f"Description: {server['description']}")
    
    if server.get("last_connected"):
        details.append(f"Last Connected: {server['last_connected']}")
    
    if server.get("error"):
        details.append(f"Error: [red]{server['error']}[/red]")

    panel = Panel(
        "\n".join(details),
        title=f"🔌 MCP Server: {name}",
        border_style="bright_blue",
    )
    console.print(panel)


def _display_tools_table(tools: List[Dict[str, Any]]):
    """Display tools in a table format."""
    table = Table(title="MCP Tools", box=box.ROUNDED)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Server", style="blue")
    table.add_column("Description", style="white")
    table.add_column("Status", style="green")

    for tool in tools:
        status = "🟢 Enabled" if tool.get("enabled") else "🔴 Disabled"
        
        table.add_row(
            tool.get("name", "Unknown"),
            tool.get("server_name", ""),
            tool.get("description", "")[:50] + "..." if len(tool.get("description", "")) > 50 else tool.get("description", ""),
            status,
        )

    console.print(table)


def _display_tool_details(tool: Dict[str, Any]):
    """Display detailed tool information."""
    name = tool.get("name", "Unknown")
    status = "🟢 Enabled" if tool.get("enabled") else "🔴 Disabled"
    
    details = [
        f"Name: [cyan]{name}[/cyan]",
        f"Server: [blue]{tool.get('server_name', '')}[/blue]",
        f"Status: {status}",
        f"Description: {tool.get('description', 'No description')}",
    ]
    
    if tool.get("parameters"):
        details.append(f"Parameters: {len(tool['parameters'])} defined")
    
    if tool.get("usage_count"):
        details.append(f"Usage Count: {tool['usage_count']}")

    panel = Panel(
        "\n".join(details),
        title=f"🔧 MCP Tool: {name}",
        border_style="bright_green",
    )
    console.print(panel)


def _display_connection_details(test_result: Dict[str, Any]):
    """Display connection test details."""
    details = [
        f"Connection: {'🟢 Success' if test_result.get('connected') else '🔴 Failed'}",
        f"Response Time: {test_result.get('response_time', 'N/A')}ms",
        f"Server Version: {test_result.get('server_version', 'Unknown')}",
        f"Capabilities: {', '.join(test_result.get('capabilities', []))}",
    ]
    
    if test_result.get("tools_available"):
        details.append(f"Tools Available: {test_result['tools_available']}")

    panel = Panel(
        "\n".join(details),
        title="🔍 Connection Test Results",
        border_style="bright_cyan",
    )
    console.print(panel)


def _display_stats(stats_data: Dict[str, Any]):
    """Display MCP statistics."""
    servers_stats = stats_data.get("servers", {})
    tools_stats = stats_data.get("tools", {})
    usage_stats = stats_data.get("usage", {})
    
    # Create servers stats table
    servers_table = Table(title="Server Statistics", box=box.ROUNDED)
    servers_table.add_column("Metric", style="cyan")
    servers_table.add_column("Value", style="white")
    
    servers_table.add_row("Total Servers", str(servers_stats.get("total", 0)))
    servers_table.add_row("Enabled", str(servers_stats.get("enabled", 0)))
    servers_table.add_row("Connected", str(servers_stats.get("connected", 0)))
    servers_table.add_row("Disconnected", str(servers_stats.get("disconnected", 0)))
    
    # Create tools stats table
    tools_table = Table(title="Tool Statistics", box=box.ROUNDED)
    tools_table.add_column("Metric", style="cyan")
    tools_table.add_column("Value", style="white")
    
    tools_table.add_row("Total Tools", str(tools_stats.get("total", 0)))
    tools_table.add_row("Enabled", str(tools_stats.get("enabled", 0)))
    tools_table.add_row("Used Today", str(usage_stats.get("today", 0)))
    tools_table.add_row("Used This Week", str(usage_stats.get("week", 0)))
    tools_table.add_row("Used This Month", str(usage_stats.get("month", 0)))
    
    console.print(servers_table)
    console.print()
    console.print(tools_table)
    
    # Show top used tools if available
    if usage_stats.get("top_tools"):
        top_tools_table = Table(title="Top Used Tools", box=box.ROUNDED)
        top_tools_table.add_column("Tool", style="cyan")
        top_tools_table.add_column("Server", style="blue")
        top_tools_table.add_column("Usage Count", style="green")
        
        for tool in usage_stats["top_tools"][:5]:  # Show top 5
            top_tools_table.add_row(
                tool.get("name", "Unknown"),
                tool.get("server", "Unknown"),
                str(tool.get("count", 0))
            )
        
        console.print()
        console.print(top_tools_table)