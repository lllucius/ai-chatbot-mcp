"""
MCP management CLI commands.

This module provides comprehensive MCP server and tool management functionality
through the command line interface.

Current Date and Time (UTC): 2025-07-23 03:35:00
Current User: lllucius / assistant
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

import typer
from rich.table import Table
from rich.panel import Panel
from rich import box

from .base import console, success_message, error_message, info_message
from ..services.mcp_registry import MCPRegistryService

# Create the MCP management app
mcp_app = typer.Typer(
    help="🔌 MCP server and tool management commands",
    rich_markup_mode="rich"
)


@mcp_app.command("list-servers")
def list_servers(
    enabled_only: bool = typer.Option(False, "--enabled-only", help="Show only enabled servers"),
    connected_only: bool = typer.Option(False, "--connected-only", help="Show only connected servers"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information")
):
    """List all registered MCP servers."""
    
    async def _list_servers():
        try:
            servers = await MCPRegistryService.list_servers(
                enabled_only=enabled_only,
                connected_only=connected_only
            )
            
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
                    
                    console.print(Panel(
                        panel_content.strip(),
                        title=f"🔌 {server.name}",
                        border_style=status_color
                    ))
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
                        str(server.connection_errors)
                    )
                
                console.print(table)
                
        except Exception as e:
            error_message(f"Failed to list servers: {e}")
    
    asyncio.run(_list_servers())


@mcp_app.command("add-server")
def add_server(
    name: str = typer.Argument(..., help="Server name/identifier"),
    url: str = typer.Argument(..., help="Server URL"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Server description"),
    transport: str = typer.Option("http", "--transport", "-t", help="Transport type"),
    timeout: int = typer.Option(30, "--timeout", help="Connection timeout in seconds"),
    disabled: bool = typer.Option(False, "--disabled", help="Create server in disabled state")
):
    """Add a new MCP server registration."""
    
    async def _add_server():
        try:
            server = await MCPRegistryService.create_server(
                name=name,
                url=url,
                description=description,
                transport=transport,
                timeout=timeout,
                is_enabled=not disabled
            )
            
            success_message(f"Added MCP server: {server.name}")
            
        except Exception as e:
            error_message(f"Failed to add server: {e}")
    
    asyncio.run(_add_server())


@mcp_app.command("update-server")
def update_server(
    name: str = typer.Argument(..., help="Server name"),
    url: Optional[str] = typer.Option(None, "--url", help="New URL"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="New description"),
    transport: Optional[str] = typer.Option(None, "--transport", "-t", help="New transport type"),
    timeout: Optional[int] = typer.Option(None, "--timeout", help="New timeout in seconds")
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
                
            server = await MCPRegistryService.update_server(name, **updates)
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
    confirm: bool = typer.Option(False, "--confirm", "-y", help="Skip confirmation prompt")
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
def enable_server(name: str = typer.Argument(..., help="Server name")):
    """Enable an MCP server."""
    
    async def _enable_server():
        try:
            success = await MCPRegistryService.enable_server(name)
            if success:
                success_message(f"Enabled MCP server: {name}")
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
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information")
):
    """List all registered MCP tools."""
    
    async def _list_tools():
        try:
            tools = await MCPRegistryService.list_tools(
                server_name=server,
                enabled_only=enabled_only
            )
            
            if not tools:
                info_message("No MCP tools found")
                return
            
            if detailed:
                for tool in tools:
                    enabled_color = "green" if tool.is_enabled else "yellow"
                    success_rate = f"{tool.success_rate:.1f}%" if tool.usage_count > 0 else "No usage"
                    
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
                    
                    console.print(Panel(
                        panel_content.strip(),
                        title=f"🛠️ {tool.name}",
                        border_style=enabled_color
                    ))
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
                    success_rate = f"{tool.success_rate:.1f}%" if tool.usage_count > 0 else "No usage"
                    last_used = tool.last_used_at.strftime("%Y-%m-%d %H:%M") if tool.last_used_at else "Never"
                    
                    table.add_row(
                        tool.name,
                        tool.server.name,
                        enabled,
                        str(tool.usage_count),
                        success_rate,
                        last_used
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
    limit: int = typer.Option(10, "--limit", "-l", help="Number of tools to show")
):
    """Show MCP tool usage statistics."""
    
    async def _show_stats():
        try:
            stats = await MCPRegistryService.get_tool_stats(
                server_name=server,
                limit=limit
            )
            
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
                avg_duration = f"{stat['average_duration_ms']}ms" if stat["average_duration_ms"] else "N/A"
                
                table.add_row(
                    stat["name"],
                    stat["server"],
                    str(stat["usage_count"]),
                    str(stat["success_count"]),
                    str(stat["error_count"]),
                    success_rate,
                    avg_duration,
                    status
                )
            
            console.print(table)
            
        except Exception as e:
            error_message(f"Failed to get statistics: {e}")
    
    asyncio.run(_show_stats())