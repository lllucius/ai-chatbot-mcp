"""
Conversation management commands for the API-based CLI.

This module provides conversation management functionality through API calls.
"""

import typer
from pathlib import Path
from .base import get_sdk_with_auth, console, error_message, success_message, confirm_action, format_timestamp

conversation_app = typer.Typer(help="💬 Conversation management commands")


@conversation_app.command()
def list(
    user: str = typer.Option(None, "--user", help="Filter by username"),
    active_only: bool = typer.Option(False, "--active-only", help="Show only active conversations"),
    limit: int = typer.Option(20, "--limit", help="Maximum number to show"),
):
    """List conversations with filtering options."""
    
    try:
        sdk = get_sdk_with_auth()
        
        conversations_response = sdk.conversations.list(
            page=1,
            size=limit,
            active_only=active_only if active_only else None
        )
        
        if conversations_response and "items" in conversations_response:
            from rich.table import Table
            
            conversations = conversations_response["items"]
            table = Table(title=f"Conversations ({len(conversations)} shown)")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Messages", style="green")
            table.add_column("Active", style="yellow")
            table.add_column("Created", style="dim")
            
            for conv in conversations:
                table.add_row(
                    str(conv.get("id", ""))[:8] + "...",
                    conv.get("title", ""),
                    str(conv.get("message_count", 0)),
                    "Yes" if conv.get("is_active") else "No",
                    format_timestamp(conv.get("created_at", ""))
                )
            
            console.print(table)
    
    except Exception as e:
        error_message(f"Failed to list conversations: {str(e)}")
        raise typer.Exit(1)


@conversation_app.command()
def show(
    conversation_id: str = typer.Argument(..., help="Conversation ID to show"),
    messages: bool = typer.Option(False, "--messages", help="Include messages"),
    message_limit: int = typer.Option(10, "--message-limit", help="Max messages to show"),
):
    """Show detailed information about a specific conversation."""
    
    async def _show_conversation():
        client = get_client_with_auth()
        
        try:
            response = await client.get(f"/api/v1/conversations/{conversation_id}")
            data = handle_api_response(response, "getting conversation details")
            
            if data:
                from rich.table import Table
                from rich.panel import Panel
                from .base import format_timestamp
                
                # Conversation details
                table = Table(title="Conversation Details")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="white")
                
                table.add_row("ID", str(data.get("id", "")))
                table.add_row("Title", data.get("title", ""))
                table.add_row("Active", "Yes" if data.get("is_active") else "No")
                table.add_row("Created", format_timestamp(data.get("created_at", "")))
                table.add_row("Updated", format_timestamp(data.get("updated_at", "")))
                
                console.print(table)
                
                # Show messages if requested
                if messages:
                    msg_response = await client.get(
                        f"/api/v1/conversations/{conversation_id}/messages",
                        params={"limit": message_limit}
                    )
                    msg_data = handle_api_response(msg_response, "getting messages")
                    
                    if msg_data and "items" in msg_data:
                        msg_table = Table(title=f"Recent Messages ({len(msg_data['items'])} shown)")
                        msg_table.add_column("Role", style="cyan")
                        msg_table.add_column("Content", style="white")
                        msg_table.add_column("Created", style="dim")
                        
                        for msg in msg_data["items"][-message_limit:]:
                            content = msg.get("content", "")
                            if len(content) > 100:
                                content = content[:97] + "..."
                            
                            msg_table.add_row(
                                msg.get("role", ""),
                                content,
                                format_timestamp(msg.get("created_at", ""))
                            )
                        
                        console.print(msg_table)
        
        except Exception as e:
            error_message(f"Failed to show conversation: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_show_conversation())


@conversation_app.command()
def export(
    conversation_id: str = typer.Argument(..., help="Conversation ID to export"),
    format: str = typer.Option("json", "--format", help="Export format: json, txt, csv"),
    output: str = typer.Option(None, "--output", "-o", help="Output file"),
    include_metadata: bool = typer.Option(True, "--metadata/--no-metadata", help="Include metadata"),
):
    """Export a conversation to a file."""
    
    async def _export_conversation():
        client = get_client_with_auth()
        
        try:
            params = {
                "format": format,
                "include_metadata": include_metadata
            }
            
            response = await client.get(f"/api/v1/admin/conversations/{conversation_id}/export", params=params)
            data = handle_api_response(response, "exporting conversation")
            
            if data:
                # Determine output file
                if not output:
                    output = f"conversation_{conversation_id[:8]}.{format}"
                
                # Write content based on format
                content = data.get("content", "")
                if format == "json":
                    content = json.dumps(data, indent=2, default=str)
                
                with open(output, "w", encoding="utf-8") as f:
                    f.write(content)
                
                from .base import success_message
                export_info = data.get("export_info", {})
                success_message(f"Conversation exported to {output}")
                console.print(f"Format: {export_info.get('format', format)}")
                console.print(f"Messages: {export_info.get('message_count', 0)}")
        
        except Exception as e:
            error_message(f"Failed to export conversation: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_export_conversation())


@conversation_app.command("import-conversation")
def import_conversation(
    file_path: str = typer.Argument(..., help="JSON file to import"),
    title: str = typer.Option(None, "--title", help="Override conversation title"),
):
    """Import a conversation from a JSON file."""
    
    async def _import_conversation():
        if not Path(file_path).exists():
            error_message(f"File not found: {file_path}")
            return
        
        client = get_client_with_auth()
        
        try:
            with open(file_path, "rb") as f:
                files = {"file": (Path(file_path).name, f, "application/json")}
                data = {}
                if title:
                    data["title"] = title
                
                response = await client.post("/api/v1/admin/conversations/import", data=data, files=files)
                result = handle_api_response(response, "conversation import")
                
                if result:
                    from rich.panel import Panel
                    
                    import_panel = Panel(
                        f"Conversation ID: [green]{result.get('conversation_id', '')}[/green]\n"
                        f"Title: [blue]{result.get('conversation_title', '')}[/blue]\n"
                        f"Messages Imported: [yellow]{result.get('imported_messages', 0)}[/yellow]\n"
                        f"Total Messages: [white]{result.get('total_messages', 0)}[/white]",
                        title="Import Complete",
                        border_style="green"
                    )
                    console.print(import_panel)
                    
                    errors = result.get("errors", [])
                    if errors:
                        console.print("\n[bold]Import Errors:[/bold]")
                        for error in errors:
                            console.print(f"• {error}")
        
        except Exception as e:
            error_message(f"Failed to import conversation: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_import_conversation())


@conversation_app.command()
def delete(
    conversation_id: str = typer.Argument(..., help="Conversation ID to delete"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
):
    """Delete a conversation and all its messages."""
    
    async def _delete_conversation():
        from .base import confirm_action
        
        if not force:
            if not confirm_action("Are you sure you want to delete this conversation?"):
                return
        
        client = get_client_with_auth()
        
        try:
            response = await client.delete(f"/api/v1/conversations/{conversation_id}")
            handle_api_response(response, "conversation deletion")
        
        except Exception as e:
            error_message(f"Failed to delete conversation: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_delete_conversation())


@conversation_app.command()
def archive(
    older_than: int = typer.Option(90, "--older-than", help="Archive conversations older than X days"),
    inactive_only: bool = typer.Option(True, "--inactive-only/--all", help="Archive only inactive conversations"),
    dry_run: bool = typer.Option(True, "--dry-run/--execute", help="Dry run mode"),
):
    """Archive old conversations by marking them as inactive."""
    
    async def _archive_conversations():
        client = get_client_with_auth()
        
        try:
            params = {
                "older_than_days": older_than,
                "inactive_only": inactive_only,
                "dry_run": dry_run
            }
            
            response = await client.post("/api/v1/admin/conversations/archive", params=params)
            data = handle_api_response(response, "conversation archival")
            
            if data:
                from rich.panel import Panel
                
                if dry_run:
                    archive_panel = Panel(
                        f"Would archive: [yellow]{data.get('total_count', 0)}[/yellow] conversations\n"
                        f"Criteria: [dim]older than {older_than} days, inactive only: {inactive_only}[/dim]",
                        title="📦 Archive Preview",
                        border_style="yellow"
                    )
                    console.print(archive_panel)
                    
                    preview = data.get("preview", [])
                    if preview:
                        from rich.table import Table
                        from .base import format_timestamp
                        
                        table = Table(title="Preview (first 10)")
                        table.add_column("Title", style="cyan")
                        table.add_column("Messages", style="green")
                        table.add_column("Created", style="dim")
                        
                        for conv in preview:
                            table.add_row(
                                conv.get("title", ""),
                                str(conv.get("message_count", 0)),
                                format_timestamp(conv.get("created_at", ""))
                            )
                        
                        console.print(table)
                else:
                    archive_panel = Panel(
                        f"Archived: [green]{data.get('archived_count', 0)}[/green] conversations",
                        title="📦 Archive Complete",
                        border_style="green"
                    )
                    console.print(archive_panel)
        
        except Exception as e:
            error_message(f"Failed to archive conversations: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_archive_conversations())


@conversation_app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    search_messages: bool = typer.Option(True, "--messages/--titles-only", help="Search in message content"),
    user_filter: str = typer.Option(None, "--user", help="Filter by username"),
    active_only: bool = typer.Option(True, "--active-only/--all", help="Search only active conversations"),
    limit: int = typer.Option(10, "--limit", help="Maximum results"),
):
    """Search conversations and messages."""
    
    async def _search_conversations():
        client = get_client_with_auth()
        
        try:
            params = {
                "query": query,
                "search_messages": search_messages,
                "active_only": active_only,
                "limit": limit
            }
            
            if user_filter:
                params["user_filter"] = user_filter
            
            response = await client.get("/api/v1/admin/conversations/search", params=params)
            data = handle_api_response(response, "conversation search")
            
            if data:
                from rich.table import Table
                from .base import format_timestamp
                
                results = data.get("results", [])
                table = Table(title=f"Search Results ({len(results)} found)")
                table.add_column("Title", style="cyan")
                table.add_column("Messages", style="green")
                table.add_column("User", style="blue")
                table.add_column("Created", style="dim")
                
                for conv in results:
                    user_info = conv.get("user", {})
                    table.add_row(
                        conv.get("title", ""),
                        str(conv.get("message_count", 0)),
                        user_info.get("username", ""),
                        format_timestamp(conv.get("created_at", ""))
                    )
                
                console.print(table)
                
                # Show matching messages if available
                for conv in results:
                    matching_messages = conv.get("matching_messages", [])
                    if matching_messages:
                        console.print(f"\n[bold]Matches in '{conv.get('title', '')}':[/bold]")
                        for msg in matching_messages[:2]:  # Show first 2 matches
                            console.print(f"  [{msg.get('role', '')}]: {msg.get('excerpt', '')}")
        
        except Exception as e:
            error_message(f"Failed to search conversations: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_search_conversations())


@conversation_app.command()
def stats():
    """Display conversation statistics and summary."""
    
    async def _show_stats():
        client = get_client_with_auth()
        
        try:
            response = await client.get("/api/v1/admin/conversations/stats")
            data = handle_api_response(response, "getting conversation statistics")
            
            if data:
                from rich.panel import Panel
                from rich.columns import Columns
                
                conversations = data.get("conversations", {})
                messages = data.get("messages", {})
                engagement = data.get("user_engagement", {})
                recent = data.get("recent_activity", {})
                
                # Basic stats
                conv_panel = Panel(
                    f"Total: [white]{conversations.get('total', 0)}[/white]\n"
                    f"Active: [green]{conversations.get('active', 0)}[/green]\n"
                    f"Inactive: [yellow]{conversations.get('inactive', 0)}[/yellow]",
                    title="💬 Conversations",
                    border_style="cyan"
                )
                
                # Message stats
                msg_panel = Panel(
                    f"Total: [white]{messages.get('total', 0)}[/white]\n"
                    f"Avg/Conv: [blue]{messages.get('avg_per_conversation', 0):.1f}[/blue]",
                    title="📨 Messages",
                    border_style="green"
                )
                
                # Engagement
                engage_panel = Panel(
                    f"Users with Convs: [green]{engagement.get('users_with_conversations', 0)}[/green]\n"
                    f"Recent (7d): [yellow]{recent.get('conversations_last_7_days', 0)}[/yellow]",
                    title="👥 Engagement",
                    border_style="blue"
                )
                
                console.print(Columns([conv_panel, msg_panel, engage_panel]))
                
                # Role distribution
                role_dist = messages.get("role_distribution", {})
                if role_dist:
                    from rich.table import Table
                    
                    table = Table(title="Message Role Distribution")
                    table.add_column("Role", style="cyan")
                    table.add_column("Count", style="green")
                    
                    for role, count in role_dist.items():
                        table.add_row(role, str(count))
                    
                    console.print(table)
                
                # Top users
                top_users = engagement.get("top_users", [])
                if top_users:
                    user_table = Table(title="Most Active Users")
                    user_table.add_column("Username", style="cyan")
                    user_table.add_column("Conversations", style="green")
                    user_table.add_column("Total Messages", style="blue")
                    
                    for user in top_users:
                        user_table.add_row(
                            user.get("username", ""),
                            str(user.get("conversation_count", 0)),
                            str(user.get("total_messages", 0))
                        )
                    
                    console.print(user_table)
        
        except Exception as e:
            error_message(f"Failed to get conversation statistics: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_show_stats())