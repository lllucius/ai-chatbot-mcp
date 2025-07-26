"""
MCP management CLI commands.

This module provides comprehensive MCP server and tool management functionality
through the command line interface.

"""

import asyncio
from typing import Optional

import typer
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..database import AsyncSessionLocal
from ..schemas.mcp import MCPServerCreateSchema, MCPListFiltersSchema, MCPServerUpdateSchema
from ..services.mcp_registry import MCPRegistryService
from .base import console, error_message, info_message, success_message, warning_message

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
            async with AsyncSessionLocal() as db:
                registry = MCPRegistryService(db)
                filters = MCPListFiltersSchema(
                    enabled_only=enabled_only, 
                    connected_only=connected_only
                )
                servers = await registry.list_servers(filters)

            if not servers:
                info_message("No MCP servers found")
                return

            if detailed:
                for server in servers:
                    status_color = "green" if server.is_connected else "red"
                    enabled_color = "green" if server.is_enabled else "yellow"

                    panel_content = f"""
[bold]URL:[/bold] {server.url}
[bold]Transport:[/bold] {server.transport}
[bold]Timeout:[/bold] {server.timeout}s
[bold]Enabled:[/bold] [{enabled_color}]{server.is_enabled}[/{enabled_color}]
[bold]Connected:[/bold] [{status_color}]{server.is_connected}[/{status_color}]
[bold]Tools:[/bold] {len(server.tools)}
[bold]Errors:[/bold] {server.connection_errors}
[bold]Last Connected:[/bold] {server.last_connected_at or 'Never'}
[bold]Description:[/bold] {server.description or 'No description'}
"""

                    console.print(
                        Panel(
                            panel_content.strip(),
                            title=f"🔌 {server.name}",
                            border_style=status_color,
                        )
                    )
                    console.print()
            else:
                table = Table(title="MCP Servers", box=box.ROUNDED)
                table.add_column("Name", style="bold")
                table.add_column("URL")
                table.add_column("Status")
                table.add_column("Enabled")
                table.add_column("Tools")
                table.add_column("Errors")

                for server in servers:
                    status = "🟢 Connected" if server.is_connected else "🔴 Disconnected"
                    enabled = "✅ Yes" if server.is_enabled else "❌ No"

                    table.add_row(
                        server.name,
                        server.url,
                        status,
                        enabled,
                        str(len(server.tools)),
                        str(server.connection_errors),
                    )

                console.print(table)

        except Exception as e:
            error_message(f"Failed to list servers: {e}")

    asyncio.run(_list_servers())


@mcp_app.command("add-server")
def add_server(
    name: str = typer.Argument(..., help="Server name/identifier"),
    url: str = typer.Argument(..., help="Server URL"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Server description"
    ),
    transport: str = typer.Option("http", "--transport", "-t", help="Transport type"),
    timeout: int = typer.Option(30, "--timeout", help="Connection timeout in seconds"),
    disabled: bool = typer.Option(False, "--disabled", help="Create server in disabled state"),
    skip_discovery: bool = typer.Option(
        False, "--skip-discovery", help="Skip automatic tool discovery"
    ),
):
    """Add a new MCP server registration."""

    async def _add_server():
        try:
            async with AsyncSessionLocal() as db:
                registry = MCPRegistryService(db)
                server_data = MCPServerCreateSchema(
                    name=name,
                    url=url,
                    description=description,
                    transport=transport,
                    timeout=timeout,
                    is_enabled=not disabled,
                )
                server = await registry.create_server(
                    server_data, auto_discover=not skip_discovery
                )

            success_message(f"Added MCP server: {server.name}")

            if not disabled and not skip_discovery:
                info_message("Automatic tool discovery will be attempted")

        except Exception as e:
            error_message(f"Failed to add server: {e}")

    asyncio.run(_add_server())


@mcp_app.command("update-server")
def update_server(
    name: str = typer.Argument(..., help="Server name"),
    url: Optional[str] = typer.Option(None, "--url", help="New URL"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="New description"),
    transport: Optional[str] = typer.Option(None, "--transport", "-t", help="New transport type"),
    timeout: Optional[int] = typer.Option(None, "--timeout", help="New timeout in seconds"),
):
    """Update an MCP server configuration."""

    async def _update_server():
        try:
            updates = {}
            if url:
                updates["url"] = url
            if description is not None:
                updates["description"] = description
            if transport:
                updates["transport"] = transport
            if timeout:
                updates["timeout"] = timeout

            if not updates:
                error_message("No updates specified")
                return

            async with AsyncSessionLocal() as db:
                registry = MCPRegistryService(db)
                update_data = MCPServerUpdateSchema(**updates)
                server = await registry.update_server(name, update_data)
            if server:
                success_message(f"Updated MCP server: {name}")
            else:
                error_message(f"Server not found: {name}")

        except Exception as e:
            error_message(f"Failed to update server: {e}")

    asyncio.run(_update_server())


@mcp_app.command("remove-server")
def remove_server(
    name: str = typer.Argument(..., help="Server name"),
    confirm: bool = typer.Option(False, "--confirm", "-y", help="Skip confirmation prompt"),
):
    """Remove an MCP server registration."""

    async def _remove_server():
        try:
            if not confirm:
                confirmed = typer.confirm(f"Are you sure you want to remove server '{name}'?")
                if not confirmed:
                    info_message("Operation cancelled")
                    return

            success = await MCPRegistryService.delete_server(name)
            if success:
                success_message(f"Removed MCP server: {name}")
            else:
                error_message(f"Server not found: {name}")

        except Exception as e:
            error_message(f"Failed to remove server: {e}")

    asyncio.run(_remove_server())


@mcp_app.command("enable-server")
def enable_server(
    name: str = typer.Argument(..., help="Server name"),
    skip_discovery: bool = typer.Option(
        False, "--skip-discovery", help="Skip automatic tool discovery"
    ),
):
    """Enable an MCP server."""

    async def _enable_server():
        try:
            success = await MCPRegistryService.enable_server(name, auto_discover=not skip_discovery)
            if success:
                success_message(f"Enabled MCP server: {name}")
                if not skip_discovery:
                    info_message("Automatic tool discovery will be attempted")
            else:
                error_message(f"Server not found: {name}")

        except Exception as e:
            error_message(f"Failed to enable server: {e}")

    asyncio.run(_enable_server())


@mcp_app.command("disable-server")
def disable_server(name: str = typer.Argument(..., help="Server name")):
    """Disable an MCP server."""

    async def _disable_server():
        try:
            success = await MCPRegistryService.disable_server(name)
            if success:
                success_message(f"Disabled MCP server: {name}")
            else:
                error_message(f"Server not found: {name}")

        except Exception as e:
            error_message(f"Failed to disable server: {e}")

    asyncio.run(_disable_server())


@mcp_app.command("list-tools")
def list_tools(
    server: Optional[str] = typer.Option(None, "--server", "-s", help="Filter by server name"),
    enabled_only: bool = typer.Option(False, "--enabled-only", help="Show only enabled tools"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information"),
):
    """List all registered MCP tools."""

    async def _list_tools():
        try:
            tools = await MCPRegistryService.list_tools(
                server_name=server, enabled_only=enabled_only
            )

            if not tools:
                info_message("No MCP tools found")
                return

            if detailed:
                for tool in tools:
                    enabled_color = "green" if tool.is_enabled else "yellow"
                    success_rate = (
                        f"{tool.success_rate:.1f}%" if tool.usage_count > 0 else "No usage"
                    )

                    panel_content = f"""
[bold]Server:[/bold] {tool.server.name}
[bold]Original Name:[/bold] {tool.original_name}
[bold]Enabled:[/bold] [{enabled_color}]{tool.is_enabled}[/{enabled_color}]
[bold]Usage Count:[/bold] {tool.usage_count}
[bold]Success Rate:[/bold] {success_rate}
[bold]Avg Duration:[/bold] {tool.average_duration_ms or 'N/A'}ms
[bold]Last Used:[/bold] {tool.last_used_at or 'Never'}
[bold]Description:[/bold] {tool.description or 'No description'}
"""

                    console.print(
                        Panel(
                            panel_content.strip(),
                            title=f"🛠️ {tool.name}",
                            border_style=enabled_color,
                        )
                    )
                    console.print()
            else:
                table = Table(title="MCP Tools", box=box.ROUNDED)
                table.add_column("Name", style="bold")
                table.add_column("Server")
                table.add_column("Enabled")
                table.add_column("Usage")
                table.add_column("Success Rate")
                table.add_column("Last Used")

                for tool in tools:
                    enabled = "✅ Yes" if tool.is_enabled else "❌ No"
                    success_rate = (
                        f"{tool.success_rate:.1f}%" if tool.usage_count > 0 else "No usage"
                    )
                    last_used = (
                        tool.last_used_at.strftime("%Y-%m-%d %H:%M")
                        if tool.last_used_at
                        else "Never"
                    )

                    table.add_row(
                        tool.name,
                        tool.server.name,
                        enabled,
                        str(tool.usage_count),
                        success_rate,
                        last_used,
                    )

                console.print(table)

        except Exception as e:
            error_message(f"Failed to list tools: {e}")

    asyncio.run(_list_tools())


@mcp_app.command("enable-tool")
def enable_tool(tool_name: str = typer.Argument(..., help="Tool name")):
    """Enable an MCP tool."""

    async def _enable_tool():
        try:
            success = await MCPRegistryService.enable_tool(tool_name)
            if success:
                success_message(f"Enabled tool: {tool_name}")
            else:
                error_message(f"Tool not found: {tool_name}")

        except Exception as e:
            error_message(f"Failed to enable tool: {e}")

    asyncio.run(_enable_tool())


@mcp_app.command("disable-tool")
def disable_tool(tool_name: str = typer.Argument(..., help="Tool name")):
    """Disable an MCP tool."""

    async def _disable_tool():
        try:
            success = await MCPRegistryService.disable_tool(tool_name)
            if success:
                success_message(f"Disabled tool: {tool_name}")
            else:
                error_message(f"Tool not found: {tool_name}")

        except Exception as e:
            error_message(f"Failed to disable tool: {e}")

    asyncio.run(_disable_tool())


@mcp_app.command("stats")
def show_stats(
    server: Optional[str] = typer.Option(None, "--server", "-s", help="Filter by server name"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of tools to show"),
):
    """Show MCP tool usage statistics."""

    async def _show_stats():
        try:
            stats = await MCPRegistryService.get_tool_stats(server_name=server, limit=limit)

            if not stats:
                info_message("No tool statistics available")
                return

            table = Table(title="MCP Tool Statistics", box=box.ROUNDED)
            table.add_column("Tool", style="bold")
            table.add_column("Server")
            table.add_column("Usage")
            table.add_column("Success")
            table.add_column("Errors")
            table.add_column("Success Rate")
            table.add_column("Avg Duration")
            table.add_column("Status")

            for stat in stats:
                status = "✅ Enabled" if stat["is_enabled"] else "❌ Disabled"
                success_rate = f"{stat['success_rate']:.1f}%"
                avg_duration = (
                    f"{stat['average_duration_ms']}ms" if stat["average_duration_ms"] else "N/A"
                )

                table.add_row(
                    stat["name"],
                    stat["server"],
                    str(stat["usage_count"]),
                    str(stat["success_count"]),
                    str(stat["error_count"]),
                    success_rate,
                    avg_duration,
                    status,
                )

            console.print(table)

        except Exception as e:
            error_message(f"Failed to get statistics: {e}")

    asyncio.run(_show_stats())


@mcp_app.command("discover")
def discover_tools(
    server: Optional[str] = typer.Option(
        None, "--server", "-s", help="Discover tools from a specific server only"
    ),
    all_servers: bool = typer.Option(
        False, "--all", help="Discover tools from all enabled servers"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force discovery even if server is disabled"
    ),
):
    """Discover tools from MCP servers and update the registry."""

    async def _discover_tools():
        try:
            if server and all_servers:
                error_message("Cannot specify both --server and --all options")
                return

            if not server and not all_servers:
                error_message("Must specify either --server <name> or --all")
                return

            if all_servers:
                info_message("Discovering tools from all enabled servers...")
                results = await MCPRegistryService.discover_tools_all_servers()

                if not results:
                    warning_message("No enabled servers found for tool discovery")
                    return

                # Summary table
                table = Table(title="Tool Discovery Results", box=box.ROUNDED)
                table.add_column("Server", style="bold")
                table.add_column("Status")
                table.add_column("New Tools")
                table.add_column("Updated Tools")
                table.add_column("Total Found")
                table.add_column("Errors")

                total_new = 0
                total_updated = 0
                total_found = 0
                success_count = 0

                for result in results:
                    status = "✅ Success" if result["success"] else "❌ Failed"
                    new_tools = result.get("new_tools", 0)
                    updated_tools = result.get("updated_tools", 0)
                    total_discovered = result.get("total_discovered", 0)
                    errors = len(result.get("errors", []))

                    if result["success"]:
                        success_count += 1
                        total_new += new_tools
                        total_updated += updated_tools
                        total_found += total_discovered

                    table.add_row(
                        result["server"],
                        status,
                        str(new_tools),
                        str(updated_tools),
                        str(total_discovered),
                        str(errors) if errors > 0 else "None",
                    )

                console.print(table)
                success_message(
                    f"Discovery completed: {success_count}/{len(results)} servers succeeded"
                )
                info_message(
                    f"Total: {total_new} new tools, {total_updated} updated tools, {total_found} discovered"
                )

            else:
                # Single server discovery
                info_message(f"Discovering tools from server: {server}")
                result = await MCPRegistryService.discover_tools_from_server(server)

                if result["success"]:
                    success_message(f"Tool discovery completed for {server}")
                    info_message(
                        f"Results: {result['new_tools']} new tools, {result['updated_tools']} updated tools"
                    )

                    if result.get("errors"):
                        warning_message(
                            f"Encountered {len(result['errors'])} errors during discovery"
                        )
                        for error in result["errors"]:
                            console.print(f"  • {error}")
                else:
                    error_message(
                        f"Tool discovery failed for {server}: {result.get('error', 'Unknown error')}"
                    )

        except Exception as e:
            error_message(f"Failed to discover tools: {e}")

    asyncio.run(_discover_tools())
