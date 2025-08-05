"""Model Context Protocol (MCP) management commands for the AI Chatbot Platform CLI.

This module provides comprehensive MCP server and tool management functionality
through async operations and the AI Chatbot SDK. It enables administrators and
developers to configure, monitor, and manage MCP servers and their associated
tools for enhanced AI model capabilities.

The Model Context Protocol (MCP) is a standard for connecting AI models with
external tools and data sources. This module facilitates the management of
MCP servers, tool discovery, and integration with the AI Chatbot Platform.

Key Features:
    - MCP server registration and configuration management
    - Tool discovery and capability enumeration
    - Server health monitoring and status reporting
    - Integration testing and validation
    - Security configuration and access control
    - Performance monitoring and optimization

Server Management:
    - Server registration with validation and security checks
    - Configuration management for connection parameters
    - Health monitoring and automatic failover capabilities
    - Version management and compatibility checking
    - Authentication and authorization setup

Tool Integration:
    - Automatic tool discovery and registration
    - Tool capability testing and validation
    - Permission management and access control
    - Performance monitoring and usage analytics
    - Integration with AI model workflows

Security Features:
    - Secure server communication with encryption
    - Authentication and authorization management
    - Access control and permission validation
    - Audit logging for all MCP operations
    - Security scanning and vulnerability assessment

Performance Monitoring:
    - Real-time server health and status monitoring
    - Tool usage analytics and performance metrics
    - Error tracking and diagnostic reporting
    - Capacity planning and resource optimization
    - Integration with monitoring and alerting systems

Use Cases:
    - External tool integration for AI models
    - Third-party service connectivity and management
    - Custom tool development and deployment
    - Enterprise system integration and workflow automation
    - AI model capability extension and enhancement

Example Usage:
    ```bash
    # Server management
    ai-chatbot mcp list-servers --enabled-only
    ai-chatbot mcp register-server server_config.json
    ai-chatbot mcp test-server server_id --full-test

    # Tool management
    ai-chatbot mcp list-tools --server-id server_id
    ai-chatbot mcp test-tool tool_id --validate
    ai-chatbot mcp enable-tool tool_id

    # Monitoring and diagnostics
    ai-chatbot mcp health-check --detailed
    ai-chatbot mcp server-logs server_id --tail 100
    ai-chatbot mcp performance-report --date-range 7d
    ```
"""

from typing import Optional

from async_typer import AsyncTyper
from rich import box
from rich.console import Console
from rich.table import Table
from typer import Argument, Option

from .base import (
    error_message,
    get_sdk,
    info_message,
    success_message,
    warning_message,
)

console = Console()

mcp_app = AsyncTyper(
    help="MCP server and tool management commands",
    rich_markup_mode=None,
)


@mcp_app.async_command("list-servers")
async def list_servers(
    enabled_only: bool = Option(
        False, "--enabled-only", help="Show only enabled servers"
    ),
    connected_only: bool = Option(
        False, "--connected-only", help="Show only connected servers"
    ),
    detailed: bool = Option(
        False, "--detailed", "-d", help="Show detailed information"
    ),
):
    """List all registered MCP servers."""
    try:
        sdk = await get_sdk()
        response = await sdk.mcp.list_servers(
            enabled_only=enabled_only, connected_only=connected_only, detailed=detailed
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


@mcp_app.async_command("show-server")
async def show_server(
    name: str = Argument(..., help="Server name"),
):
    """Show detailed information about a specific MCP server."""
    try:
        sdk = await get_sdk()
        response = await sdk.mcp.get_server(name)
        if response and response.get("success") and response.get("data"):
            _display_server_details(response["data"])
        else:
            error_message(
                f"Failed to get MCP server: {response.get('message', 'Unknown error')}"
            )
    except Exception as e:
        error_message(f"Failed to show server: {str(e)}")
        raise SystemExit(1)


@mcp_app.async_command("add-server")
async def add_server(
    name: str = Argument(..., help="Server name"),
    url: str = Argument(..., help="Server URL"),
    description: str = Option("", "--description", "-d", help="Server description"),
    enabled: bool = Option(
        True, "--enabled/--disabled", help="Enable server after creation"
    ),
    transport: str = Option(
        "http", "--transport", help="Transport type (http, websocket)"
    ),
):
    """Add a new MCP server."""
    try:
        sdk = await get_sdk()
        response = await sdk.mcp.add_server(
            name=name,
            url=url,
            description=description,
            enabled=enabled,
            transport=transport,
        )
        if response and response.get("success"):
            success_message(f"MCP server '{name}' added successfully")
            if response.get("data"):
                _display_server_details(response["data"])
        else:
            error_message(
                f"Failed to add MCP server: {response.get('message', 'Unknown error')}"
            )
    except Exception as e:
        error_message(f"Failed to add MCP server: {str(e)}")


@mcp_app.async_command("remove-server")
async def remove_server(
    name: str = Argument(..., help="Server name to remove"),
    force: bool = Option(
        False, "--force", "-f", help="Force removal without confirmation"
    ),
):
    """Remove an MCP server."""
    try:
        if not force:
            from .base import confirm_action

            confirmed = confirm_action(
                f"Are you sure you want to remove MCP server '{name}'?"
            )
            if not confirmed:
                info_message("Operation cancelled")
                return
        sdk = await get_sdk()
        response = await sdk.mcp.remove_server(name)
        if getattr(response, "success", False):
            success_message(f"MCP server '{name}' removed successfully")
        else:
            error_message(
                f"Failed to remove MCP server: {getattr(response, 'message', 'Unknown error')}"
            )
    except Exception as e:
        error_message(f"Failed to remove MCP server: {str(e)}")


@mcp_app.async_command("enable-server")
async def enable_server(name: str = Argument(..., help="Server name to enable")):
    """Enable an MCP server."""
    try:
        sdk = await get_sdk()
        response = await sdk.mcp.enable_server(name)
        if response and response.get("success"):
            success_message(f"MCP server '{name}' enabled successfully")
        else:
            error_message(
                f"Failed to enable MCP server: {response.get('message', 'Unknown error')}"
            )
    except Exception as e:
        error_message(f"Failed to enable MCP server: {str(e)}")


@mcp_app.async_command("disable-server")
async def disable_server(name: str = Argument(..., help="Server name to disable")):
    """Disable an MCP server."""
    try:
        sdk = await get_sdk()
        response = await sdk.mcp.disable_server(name)
        if response and response.get("success"):
            success_message(f"MCP server '{name}' disabled successfully")
        else:
            error_message(
                f"Failed to disable MCP server: {response.get('message', 'Unknown error')}"
            )
    except Exception as e:
        error_message(f"Failed to disable MCP server: {str(e)}")


@mcp_app.async_command("test-server")
async def test_server(name: str = Argument(..., help="Server name to test")):
    """Test connection to an MCP server."""
    try:
        sdk = await get_sdk()
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
            error_message(
                f"Failed to test MCP server: {response.get('message', 'Unknown error')}"
            )
    except Exception as e:
        error_message(f"Failed to test MCP server: {str(e)}")


@mcp_app.async_command("list-tools")
async def list_tools(
    server: Optional[str] = Option(
        None, "--server", "-s", help="Filter by server name"
    ),
    enabled_only: bool = Option(
        False, "--enabled-only", help="Show only enabled tools"
    ),
    detailed: bool = Option(
        False, "--detailed", "-d", help="Show detailed information"
    ),
):
    """List all available MCP tools."""
    try:
        sdk = await get_sdk()
        response = await sdk.mcp.list_tools(
            server=server, enabled_only=enabled_only, detailed=detailed
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


@mcp_app.async_command("show-tool")
async def show_tool(
    tool_name: str = Argument(..., help="Server name"),
    server: Optional[str] = Option(None, "--server", "-s", help="Server name"),
):
    """Show detailed information about a specific MCP tool."""
    try:
        sdk = await get_sdk()
        response = await sdk.mcp.get_tool(tool_name, server=server)
        if response and response.get("success") and response.get("data"):
            _display_tool_details(response["data"])
        else:
            error_message(
                f"Failed to get MCP tool: {response.get('message', 'Unknown error')}"
            )
    except Exception as e:
        error_message(f"Failed to show tool: {str(e)}")


@mcp_app.async_command("enable-tool")
async def enable_tool(
    tool_name: str = Argument(..., help="Tool name to enable"),
    server: Optional[str] = Option(None, "--server", "-s", help="Server name"),
):
    """Enable an MCP tool."""
    try:
        sdk = await get_sdk()
        response = await sdk.mcp.enable_tool(tool_name, server=server)
        if response and response.get("success"):
            success_message(f"MCP tool '{tool_name}' enabled successfully")
        else:
            error_message(
                f"Failed to enable MCP tool: {response.get('message', 'Unknown error')}"
            )
    except Exception as e:
        error_message(f"Failed to enable MCP tool: {str(e)}")


@mcp_app.async_command("disable-tool")
async def disable_tool(
    tool_name: str = Argument(..., help="Tool name to disable"),
    server: Optional[str] = Option(None, "--server", "-s", help="Server name"),
):
    """Disable an MCP tool."""
    try:
        sdk = await get_sdk()
        response = await sdk.mcp.disable_tool(tool_name, server=server)
        if response and response.get("success"):
            success_message(f"MCP tool '{tool_name}' disabled successfully")
        else:
            error_message(
                f"Failed to disable MCP tool: {response.get('message', 'Unknown error')}"
            )
    except Exception as e:
        error_message(f"Failed to disable MCP tool: {str(e)}")


@mcp_app.async_command("test-tool")
async def test_tool(
    tool_name: str = Argument(..., help="Tool name to test"),
    server: Optional[str] = Option(None, "--server", "-s", help="Server name"),
    params: Optional[str] = Option(
        None, "--params", "-p", help="Test parameters as JSON"
    ),
):
    """Test execution of an MCP tool."""
    try:
        sdk = await get_sdk()
        test_params = {}
        if params:
            import json

            try:
                test_params = json.loads(params)
            except json.JSONDecodeError:
                error_message("Invalid JSON format for test parameters")
                return

        response = await sdk.mcp.test_tool(tool_name, test_params)
        if response and response.get("success"):
            success_message(f"MCP tool '{tool_name}' test completed successfully")
            if response.get("result"):
                print(f"Test result: {response['result']}")
        else:
            error_message(
                f"Failed to test MCP tool: {response.get('message', 'Unknown error')}"
            )
    except Exception as e:
        error_message(f"Failed to test MCP tool: {str(e)}")


@mcp_app.async_command("server-status")
async def server_status():
    """Show comprehensive status for all MCP servers."""
    try:
        sdk = await get_sdk()
        response = await sdk.mcp.get_servers_status()
        if response and response.get("success"):
            _display_server_status(response.get("data", {}))
        else:
            error_message(
                f"Failed to get server status: {response.get('message', 'Unknown error')}"
            )
    except Exception as e:
        error_message(f"Failed to get server status: {str(e)}")


@mcp_app.async_command("stats")
async def stats():
    """Show MCP usage statistics."""
    try:
        sdk = await get_sdk()
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
    server: Optional[str] = Option(
        None, "--server", "-s", help="Refresh specific server"
    ),
):
    """Refresh MCP server connections and tool discovery."""
    try:
        sdk = await get_sdk()
        response = await sdk.mcp.refresh(server=server)
        if response and response.get("success"):
            success_message("MCP refresh completed successfully")
            refresh_data = response.get("data", {})
            if refresh_data.get("servers_refreshed"):
                info_message(f"Refreshed {refresh_data['servers_refreshed']} servers")
            if refresh_data.get("tools_discovered"):
                info_message(f"Discovered {refresh_data['tools_discovered']} tools")
        else:
            error_message(
                f"Failed to refresh MCP: {response.get('message', 'Unknown error')}"
            )
    except Exception as e:
        error_message(f"Failed to refresh MCP: {str(e)}")


# Display helpers
def _display_servers_table(servers):
    """Display MCP servers in a formatted table.

    Args:
        servers: List of server dictionaries with server information.

    Note:
        Shows server name, URL, status (enabled/disabled, connected/disconnected),
        transport type, and tool count in a Rich table format.

    """
    from rich import box
    from rich.table import Table

    table = Table(title="MCP Servers", box=box.ROUNDED)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("URL", style="blue")
    table.add_column("Status", style="green")
    table.add_column("Transport", style="yellow")
    table.add_column("Tools", style="magenta")
    for server in servers:
        print("SERVER", server)
        status = "🟢 Enabled" if server.get("is_enabled") else "🔴 Disabled"
        if server.get("is_connected"):
            status += " (Connected)"
        elif server.get("is_enabled"):
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
    """Display detailed information for a single MCP server.

    Args:
        server: Dictionary containing server details.

    Note:
        Shows comprehensive server information including connection status,
        description, and last connection time in a formatted panel.

    """
    from rich.panel import Panel

    name = server.get("name", "Unknown")
    status = "🟢 Enabled" if server.get("is_enabled") else "🔴 Disabled"
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
    """Display MCP tools in a formatted table.

    Args:
        tools: List of tool dictionaries with tool information.

    Note:
        Shows tool name, server, description (truncated), and status
        in a Rich table format. Descriptions longer than 50 characters are truncated.

    """
    from rich import box
    from rich.table import Table

    table = Table(title="MCP Tools", box=box.ROUNDED)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Server", style="blue")
    table.add_column("Description", style="white")
    table.add_column("Status", style="green")
    for tool in tools:
        status = "🟢 Enabled" if tool.get("is_enabled") else "🔴 Disabled"
        table.add_row(
            tool.get("name", "Unknown"),
            tool.get("server_name", ""),
            (
                tool.get("description", "")[:50] + "..."
                if len(tool.get("description", "")) > 50
                else tool.get("description", "")
            ),
            status,
        )
    console.print(table)


def _display_tool_details(tool):
    """Display detailed information for a single MCP tool.

    Args:
        tool: Dictionary containing tool details.

    Note:
        Shows comprehensive tool information including parameters count,
        usage statistics, and full description in a formatted panel.

    """
    from rich.panel import Panel

    name = tool.get("name", "Unknown")
    status = "🟢 Enabled" if tool.get("is_enabled") else "🔴 Disabled"
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
    """Display MCP server connection test results.

    Args:
        test_result: Dictionary containing connection test results.

    Note:
        Shows connection status, response time, error details if any,
        and discovered capabilities in a formatted panel.

    """
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
    """Display comprehensive MCP statistics in formatted tables.

    Args:
        stats_data: Dictionary containing server, tool, and usage statistics.

    Note:
        Shows three separate tables for server stats, tool stats, and usage stats
        with metrics like totals, enabled/disabled counts, and usage patterns.

    """
    from rich import box
    from rich.table import Table

    servers_stats = stats_data.get("servers", {})
    tools_stats = stats_data.get("tools", {})
    usage_stats = stats_data.get("usage", {})

    servers_table = Table(title="Server Statistics", box=box.ROUNDED)
    servers_table.add_column("Metric", style="cyan")
    servers_table.add_column("Value", style="white")
    servers_table.add_row("Total Servers", str(servers_stats.get("total", 0)))
    servers_table.add_row("Enabled", str(servers_stats.get("is_enabled", 0)))
    servers_table.add_row("Connected", str(servers_stats.get("connected", 0)))
    servers_table.add_row("Disconnected", str(servers_stats.get("disconnected", 0)))

    tools_table = Table(title="Tool Statistics", box=box.ROUNDED)
    tools_table.add_column("Metric", style="cyan")
    tools_table.add_column("Value", style="white")
    tools_table.add_row("Total Tools", str(tools_stats.get("total", 0)))
    tools_table.add_row("Enabled", str(tools_stats.get("is_enabled", 0)))
    tools_table.add_row("Used Today", str(usage_stats.get("today", 0)))
    tools_table.add_row("Used This Week", str(usage_stats.get("week", 0)))
    tools_table.add_row("Used This Month", str(usage_stats.get("month", 0)))

    console.print(servers_table)
    print()
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
                str(tool.get("count", 0)),
            )
        print()
        console.print(top_tools_table)


def _display_server_status(status_data):
    """Display server status information in a formatted table."""
    if not status_data:
        warning_message("No server status data available")
        return

    servers = status_data.get("servers", [])
    if not servers:
        warning_message("No servers found")
        return

    status_table = Table(title="MCP Server Status", box=box.ROUNDED)
    status_table.add_column("Server", style="cyan")
    status_table.add_column("Status", style="bold")
    status_table.add_column("Connected", style="green")
    status_table.add_column("Tools", style="blue")
    status_table.add_column("Last Check", style="dim")

    for server in servers:
        status_style = "green" if server.get("is_connected") else "red"
        connected_text = "✓" if server.get("is_connected") else "✗"

        status_table.add_row(
            server.get("name", "Unknown"),
            f"[{status_style}]{server.get('status', 'Unknown')}[/{status_style}]",
            f"[{status_style}]{connected_text}[/{status_style}]",
            str(server.get("tool_count", 0)),
            server.get("last_check", "Never"),
        )

    console.print(status_table)

    # Display summary
    total_servers = len(servers)
    connected_servers = sum(1 for s in servers if s.get("is_connected"))
    total_tools = sum(s.get("tool_count", 0) for s in servers)

    summary_table = Table(title="Summary", box=box.SIMPLE)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="bold")

    summary_table.add_row("Total Servers", str(total_servers))
    summary_table.add_row("Connected Servers", f"{connected_servers}/{total_servers}")
    summary_table.add_row("Total Tools", str(total_tools))

    print()
    console.print(summary_table)
