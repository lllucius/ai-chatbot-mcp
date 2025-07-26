"""
Conversation management commands for the API-based CLI.

All commands use async/await and the async SDK client.
"""

from async_typer import AsyncTyper
from typer import Option, Argument
from typing import Optional
from uuid import UUID
from .base import get_sdk_with_auth, console, error_message, success_message, format_timestamp

conversation_app = AsyncTyper(help="💬 Conversation management commands")


@conversation_app.async_command()
async def list(
    page: int = Option(1, "--page", "-p", help="Page number"),
    size: int = Option(20, "--size", "-s", help="Items per page"),
    active_only: bool = Option(False, "--active-only", help="Show only active conversations"),
):
    """List conversations."""
    try:
        sdk = await get_sdk_with_auth()
        resp = await sdk.conversations.list(page=page, size=size, active_only=active_only)
        if resp and resp.items:
            from rich.table import Table
            table = Table(title=f"Conversations (Page {resp.pagination.page})")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Active", style="green")
            table.add_column("Messages", style="yellow")
            table.add_column("Created", style="blue")
            for conv in resp.items:
                table.add_row(
                    str(conv.id)[:8] + "...",
                    conv.title,
                    "✓" if conv.is_active else "✗",
                    str(conv.message_count),
                    format_timestamp(str(conv.created_at))
                )
            console.print(table)
        else:
            console.print("[yellow]No conversations found.[/yellow]")
    except Exception as e:
        error_message(f"Failed to list conversations: {str(e)}")
        raise SystemExit(1)


@conversation_app.async_command()
async def show(
    conversation_id: str = Argument(..., help="Conversation ID"),
):
    """Show conversation details."""
    try:
        sdk = await get_sdk_with_auth()
        conv = await sdk.conversations.get(UUID(conversation_id))
        if conv:
            from rich.panel import Panel
            details = (
                f"ID: [cyan]{conv.id}[/cyan]\n"
                f"Title: [white]{conv.title}[/white]\n"
                f"Active: [green]{'Yes' if conv.is_active else 'No'}[/green]\n"
                f"Messages: [yellow]{conv.message_count}[/yellow]\n"
                f"Created: [blue]{format_timestamp(str(conv.created_at))}[/blue]"
            )
            panel = Panel(details, title="Conversation Details", border_style="magenta")
            console.print(panel)
    except Exception as e:
        error_message(f"Failed to get conversation details: {str(e)}")
        raise SystemExit(1)


@conversation_app.async_command()
async def export(
    conversation_id: str = Argument(..., help="Conversation ID"),
    output: Optional[str] = Option(None, "--output", help="Output file"),
):
    """Export a conversation to a file."""
    try:
        sdk = await get_sdk_with_auth()
        from uuid import UUID
        data = await sdk.admin.export_conversation(UUID(conversation_id))
        import json
        filename = output or f"conversation_{conversation_id}.json"
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        success_message(f"Conversation exported to {filename}")
    except Exception as e:
        error_message(f"Failed to export conversation: {str(e)}")
        raise SystemExit(1)
