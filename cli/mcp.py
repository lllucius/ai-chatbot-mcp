"""
MCP management API CLI commands.

This module provides comprehensive MCP server and tool management functionality
through the API-based command line interface using the AI Chatbot SDK.
All commands are async.
"""

from async_typer import AsyncTyper
from typer import Option, Argument
from typing import Optional
from .base import get_sdk_with_auth, console, error_message, info_message, success_message, warning_message

mcp_app = AsyncTyper(help="🔌 MCP server and tool management commands", rich_markup_mode="rich")


@mcp_app.async_command("list-servers")
async def list_servers(
    enabled_only: bool = Option(False, "--enabled-only", help="Show only enabled servers"),
    connected_only: bool = Option(False, "--connected-only", help="Show only connected servers"),
    detailed: bool = Option(False, "--detailed", "-d", help="Show detailed information"),
):
    """List all registered MCP servers."""
    try:
        sdk = await get_sdk_with_auth()
        response = await sdk.mcp.list_servers(
            enabled_only=enabled_only,
            connected_only=connected_only,
            detailed=detailed
        )
        if not response or not response.get("success"):
            error_message("Failed to retrieve MCP servers")
            return
        servers = response.get("data", [])
        if not servers:
            info_message("No MCP servers found")
            return
        if detailed:
            for server in servers:
                _display_server_details(server)
        else:
            _display_servers_table(servers)
    except Exception as e:
        error_message(f"Failed to list MCP servers: {str(e)}")


@mcp_app.async_command("add-server")
async def add_server(
    name: str = Argument(..., help="Server name"),
    url: str = Argument(..., help="Server URL"),
    description: str = Option("", "--description", "-d", help="Server description"),
    enabled: bool = Option(True, "--enabled/--disabled", help="Enable server after creation"),
    transport: str = Option("http", "--transport", help="Transport type (http, websocket)"),
):
    """Add a new MCP server."""
    try:
        sdk = await get_sdk_with_auth()
        response = await sdk.mcp.add_server(
            name=name,
            url=url,
            description=description,
            enabled=enabled,
            transport=transport
        )
        if response and response.get("success"):
            success_message(f"MCP server '{name}' added successfully")
            if response.get("data"):
                _display_server_details(response["data"])
        else:
            error_message(f"Failed to add MCP server: {response.get('message', 'Unknown error')}")
    except Exception as e:
        error_message(f"Failed to add MCP server: {str(e)}")


@mcp_app.async_command("remove-server")
async def remove_server(
    name: str = Argument(..., help="Server name to remove"),
    force: bool = Option(False, "--force", "-f", help="Force removal without confirmation"),
):
    """Remove an MCP server."""
    try:
        if not force:
            from .base import confirm_action
            confirmed = confirm_action(f"Are you sure you want to remove MCP server '{name}'?")
            if not confirmed:
                info_message("Operation cancelled")
                return
        sdk = await get_sdk_with_auth()
        response = await sdk.mcp.remove_server(name)
        if getattr(response, "success", False):
            success_message(f"MCP server '{name}' removed successfully")
        else:
            error_message(f"Failed to remove MCP server: {getattr(response, 'message', 'Unknown error')}")
    except Exception as e:
        error_message(f"Failed to remove MCP server: {str(e)}")


@mcp_app.async_command("enable-server")
async def enable_server(
    name: str = Argument(..., help="Server name to enable")
):
    """Enable an MCP server."""
    try:
        sdk = await get_sdk_with_auth()
        response = await sdk.mcp.enable_server(name)
        if response and response.get("success"):
            success_message(f"MCP server '{name}' enabled successfully")
        else:
            error_message(f"Failed to enable MCP server: {response.get('message', 'Unknown error')}")
    except Exception as e:
        error_message(f"Failed to enable MCP server: {str(e)}")


@mcp_app.async_command("disable-server")
async def disable_server(
    name: str = Argument(..., help="Server name to disable")
):
    """Disable an MCP server."""
    try:
        sdk = await get_sdk_with_auth()
        response = await sdk.mcp.disable_server(name)
        if response and response.get("success"):
            success_message(f"MCP server '{name}' disabled successfully")
        else:
            error_message(f"Failed to disable MCP server: {response.get('message', 'Unknown error')}")
    except Exception as e:
        error_message(f"Failed to disable MCP server: {str(e)}")


@mcp_app.async_command("test-server")
async def test_server(
    name: str = Argument(..., help="Server name to test")
):
    """Test connection to an MCP server."""
    try:
        sdk = await get_sdk_with_auth()
        response = await sdk.mcp.test_server(name)
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


@mcp_app.async_command("list-tools")
async def list_tools(
    server: Optional[str] = Option(None, "--server", "-s", help="Filter by server name"),
    enabled_only: bool = Option(False, "--enabled-only", help="Show only enabled tools"),
    detailed: bool = Option(False, "--detailed", "-d", help="Show detailed information"),
):
    """List all available MCP tools."""
    try:
        sdk = await get_sdk_with_auth()
        response = await sdk.mcp.list_tools(
            server=server,
            enabled_only=enabled_only,
            detailed=detailed
        )
        if not response or not response.get("success"):
            error_message("Failed to retrieve MCP tools")
            return
        tools = response.get("data", [])
        if not tools:
            info_message("No MCP tools found")
            return
        if detailed:
            for tool in tools:
                _display_tool_details(tool)
        else:
            _display_tools_table(tools)
    except Exception as e:
        error_message(f"Failed to list MCP tools: {str(e)}")


@mcp_app.async_command("enable-tool")
async def enable_tool(
    tool_name: str = Argument(..., help="Tool name to enable"),
    server: Optional[str] = Option(None, "--server", "-s", help="Server name"),
):
    """Enable an MCP tool."""
    try:
        sdk = await get_sdk_with_auth()
        response = await sdk.mcp.enable_tool(tool_name, server=server)
        if response and response.get("success"):
            success_message(f"MCP tool '{tool_name}' enabled successfully")
        else:
            error_message(f"Failed to enable MCP tool: {response.get('message', 'Unknown error')}")
    except Exception as e:
        error_message(f"Failed to enable MCP tool: {str(e)}")


@mcp_app.async_command("disable-tool")
async def disable_tool(
    tool_name: str = Argument(..., help="Tool name to disable"),
    server: Optional[str] = Option(None, "--server", "-s", help="Server name"),
):
    """Disable an MCP tool."""
    try:
        sdk = await get_sdk_with_auth()
        response = await sdk.mcp.disable_tool(tool_name, server=server)
        if response and response.get("success"):
            success_message(f"MCP tool '{tool_name}' disabled successfully")
        else:
            error_message(f"Failed to disable MCP tool: {response.get('message', 'Unknown error')}")
    except Exception as e:
        error_message(f"Failed to disable MCP tool: {str(e)}")


@mcp_app.async_command("stats")
async def stats():
    """Show MCP usage statistics."""
    try:
        sdk = await get_sdk_with_auth()
        response = await sdk.mcp.get_stats()
        if not response or not response.get("success"):
            error_message("Failed to retrieve MCP statistics")
            return
        stats_data = response.get("data", {})
        _display_stats(stats_data)
    except Exception as e:
        error_message(f"Failed to get MCP statistics: {str(e)}")


@mcp_app.async_command("refresh")
async def refresh(
    server: Optional[str] = Option(None, "--server", "-s", help="Refresh specific server"),
):
    """Refresh MCP server connections and tool discovery."""
    try:
        sdk = await get_sdk_with_auth()
        response = await sdk.mcp.refresh(server=server)
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


# Display helpers
def _display_servers_table(servers):
    from rich import box
    from rich.table import Table
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


def _display_server_details(server):
    from rich.panel import Panel
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


def _display_tools_table(tools):
    from rich import box
    from rich.table import Table
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


def _display_tool_details(tool):
    from rich.panel import Panel
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


def _display_connection_details(test_result):
    from rich.panel import Panel
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


def _display_stats(stats_data):
    from rich import box
    from rich.table import Table
    servers_stats = stats_data.get("servers", {})
    tools_stats = stats_data.get("tools", {})
    usage_stats = stats_data.get("usage", {})

    servers_table = Table(title="Server Statistics", box=box.ROUNDED)
    servers_table.add_column("Metric", style="cyan")
    servers_table.add_column("Value", style="white")
    servers_table.add_row("Total Servers", str(servers_stats.get("total", 0)))
    servers_table.add_row("Enabled", str(servers_stats.get("enabled", 0)))
    servers_table.add_row("Connected", str(servers_stats.get("connected", 0)))
    servers_table.add_row("Disconnected", str(servers_stats.get("disconnected", 0)))

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
    if usage_stats.get("top_tools"):
        top_tools_table = Table(title="Top Used Tools", box=box.ROUNDED)
        top_tools_table.add_column("Tool", style="cyan")
        top_tools_table.add_column("Server", style="blue")
        top_tools_table.add_column("Usage Count", style="green")
        for tool in usage_stats["top_tools"][:5]:
            top_tools_table.add_row(
                tool.get("name", "Unknown"),
                tool.get("server", "Unknown"),
                str(tool.get("count", 0))
            )
        console.print()
        console.print(top_tools_table)
