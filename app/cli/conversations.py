"""
Conversation management CLI commands.

Provides comprehensive conversation management functionality including:
- Conversation listing and filtering
- Chat history export and import
- Conversation analytics
- Message search and retrieval
- Cleanup and archiving
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import typer
from rich.progress import track
from rich.table import Table
from sqlalchemy import desc, func, or_, select

from ..database import AsyncSessionLocal
from ..models.conversation import Conversation, Message
from ..models.user import User
from .base import (async_command, console, error_message, format_timestamp, info_message,
                   success_message, warning_message)

# Create the conversation management app
conversation_app = typer.Typer(help="Conversation management commands")


@conversation_app.command()
def list(
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum number of conversations to show"),
    username: str = typer.Option(None, "--user", "-u", help="Filter by username"),
    active_only: bool = typer.Option(False, "--active-only", help="Show only active conversations"),
    search: str = typer.Option(None, "--search", "-s", help="Search in conversation title"),
    sort_by: str = typer.Option(
        "updated", "--sort", help="Sort by: id, title, created, updated, messages"
    ),
):
    """List conversations with filtering options."""

    @async_command
    async def _list_conversations():
        async with AsyncSessionLocal() as db:
            try:
                query = select(Conversation).join(User, isouter=True)

                # Apply filters
                if username:
                    user = await db.scalar(select(User).where(User.username == username))
                    if not user:
                        error_message(f"User '{username}' not found")
                        return
                    query = query.where(Conversation.user_id == user.id)

                if active_only:
                    query = query.where(Conversation.is_active)

                if search:
                    search_pattern = f"%{search.lower()}%"
                    query = query.where(func.lower(Conversation.title).like(search_pattern))

                # Add message count subquery
                message_count_subquery = (
                    select(func.count(Message.id))
                    .where(Message.conversation_id == Conversation.id)
                    .scalar_subquery()
                )

                # Apply sorting
                if sort_by == "id":
                    query = query.order_by(Conversation.id)
                elif sort_by == "title":
                    query = query.order_by(Conversation.title)
                elif sort_by == "created":
                    query = query.order_by(desc(Conversation.created_at))
                elif sort_by == "updated":
                    query = query.order_by(desc(Conversation.updated_at))
                elif sort_by == "messages":
                    query = query.order_by(desc(message_count_subquery))

                query = query.limit(limit)
                result = await db.execute(query)
                conversations = result.scalars().all()

                if not conversations:
                    warning_message("No conversations found matching criteria")
                    return

                # Get message counts for all conversations
                conv_ids = [conv.id for conv in conversations]
                message_counts = {}
                if conv_ids:
                    message_result = await db.execute(
                        select(Message.conversation_id, func.count(Message.id))
                        .where(Message.conversation_id.in_(conv_ids))
                        .group_by(Message.conversation_id)
                    )
                    message_counts = dict(message_result.all())

                # Get user info
                user_ids = [conv.user_id for conv in conversations if conv.user_id]
                users = {}
                if user_ids:
                    user_result = await db.execute(select(User).where(User.id.in_(user_ids)))
                    users = {user.id: user.username for user in user_result.scalars().all()}

                # Create table
                table = Table(title=f"Conversations ({len(conversations)} found)")
                table.add_column("ID", style="cyan", width=36)  # Width for full UUID
                table.add_column("Title", style="green", width=25)
                table.add_column("User", style="blue", width=15)
                table.add_column("Messages", width=8)
                table.add_column("Status", width=8)
                table.add_column("Created", width=12)
                table.add_column("Updated", width=12)

                for conv in conversations:
                    username_display = (
                        users.get(conv.user_id, "System") if conv.user_id else "System"
                    )
                    message_count = message_counts.get(conv.id, 0)
                    status = "🟢 Active" if conv.is_active else "⚪ Inactive"

                    title_display = conv.title[:22] + "..." if len(conv.title) > 25 else conv.title

                    table.add_row(
                        str(conv.id),
                        title_display,
                        username_display,
                        str(message_count),
                        status,
                        conv.created_at.strftime("%m-%d %H:%M"),
                        conv.updated_at.strftime("%m-%d %H:%M"),
                    )

                console.print(table)

            except Exception as e:
                error_message(f"Failed to list conversations: {e}")

    _list_conversations()


@conversation_app.command()
def show(
    conversation_id: str = typer.Argument(..., help="Conversation ID (UUID) to show details for"),
    show_messages: bool = typer.Option(False, "--messages", "-m", help="Show recent messages"),
    message_limit: int = typer.Option(
        10, "--message-limit", help="Number of recent messages to show"
    ),
):
    """Show detailed information about a specific conversation."""

    @async_command
    async def _show_conversation():
        async with AsyncSessionLocal() as db:
            try:
                # Validate UUID format
                try:
                    import uuid

                    uuid.UUID(conversation_id)
                except ValueError:
                    error_message(f"Invalid UUID format: {conversation_id}")
                    return

                # Get conversation with user info
                result = await db.execute(
                    select(Conversation, User)
                    .join(User, isouter=True)
                    .where(Conversation.id == conversation_id)
                )
                row = result.first()

                if not row:
                    error_message(f"Conversation with ID {conversation_id} not found")
                    return

                conversation, user = row

                # Get message count
                message_count = await db.scalar(
                    select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
                )

                # Get first and last message times
                first_message = await db.scalar(
                    select(Message.created_at)
                    .where(Message.conversation_id == conversation_id)
                    .order_by(Message.created_at)
                    .limit(1)
                )

                last_message = await db.scalar(
                    select(Message.created_at)
                    .where(Message.conversation_id == conversation_id)
                    .order_by(desc(Message.created_at))
                    .limit(1)
                )

                # Conversation details table
                table = Table(title=f"Conversation Details: {conversation.title}")
                table.add_column("Field", style="cyan", width=20)
                table.add_column("Value", style="green")

                table.add_row("ID", str(conversation.id))
                table.add_row("Title", conversation.title)
                table.add_row("User", user.username if user else "System")
                table.add_row("Status", "🟢 Active" if conversation.is_active else "⚪ Inactive")
                table.add_row("Messages", str(message_count or 0))
                table.add_row("Created", format_timestamp(conversation.created_at))
                table.add_row("Updated", format_timestamp(conversation.updated_at))
                table.add_row(
                    "First Message",
                    format_timestamp(first_message) if first_message else "N/A",
                )
                table.add_row(
                    "Last Message",
                    format_timestamp(last_message) if last_message else "N/A",
                )

                if conversation.metainfo:
                    table.add_row(
                        "Metainfo",
                        (
                            str(conversation.metainfo)[:100] + "..."
                            if len(str(conversation.metainfo)) > 100
                            else str(conversation.metainfo)
                        ),
                    )

                console.print(table)

                # Show recent messages if requested
                if show_messages and message_count and message_count > 0:
                    messages_result = await db.execute(
                        select(Message)
                        .where(Message.conversation_id == conversation_id)
                        .order_by(desc(Message.created_at))
                        .limit(message_limit)
                    )
                    messages = list(reversed(messages_result.scalars().all()))  # Show oldest first

                    if messages:
                        message_table = Table(title=f"Recent Messages (last {len(messages)})")
                        message_table.add_column("Time", width=12)
                        message_table.add_column("Role", width=10)
                        message_table.add_column("Content", width=60)
                        message_table.add_column("Tokens", width=8)

                        for msg in messages:
                            role_color = {
                                "user": "blue",
                                "assistant": "green",
                                "system": "yellow",
                            }.get(msg.role, "white")

                            content_preview = (
                                msg.content[:57] + "..." if len(msg.content) > 60 else msg.content
                            )

                            message_table.add_row(
                                msg.created_at.strftime("%m-%d %H:%M"),
                                f"[{role_color}]{msg.role}[/{role_color}]",
                                content_preview,
                                str(msg.token_count or 0),
                            )

                        console.print(message_table)

            except Exception as e:
                error_message(f"Failed to show conversation details: {e}")

    _show_conversation()


@conversation_app.command()
def export(
    conversation_id: str = typer.Argument(..., help="Conversation ID (UUID) to export"),
    output_file: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: conversation_{id}.json)",
    ),
    format: str = typer.Option("json", "--format", "-f", help="Export format: json, txt, csv"),
):
    """Export a conversation to a file."""

    @async_command
    async def _export_conversation():
        async with AsyncSessionLocal() as db:
            try:
                # Validate UUID format
                try:
                    import uuid

                    uuid.UUID(conversation_id)
                except ValueError:
                    error_message(f"Invalid UUID format: {conversation_id}")
                    return

                # Get conversation with messages
                conversation = await db.scalar(
                    select(Conversation).where(Conversation.id == conversation_id)
                )

                if not conversation:
                    error_message(f"Conversation with ID {conversation_id} not found")
                    return

                # Get user info
                user = None
                if conversation.user_id:
                    user = await db.scalar(select(User).where(User.id == conversation.user_id))

                # Get all messages
                messages_result = await db.execute(
                    select(Message)
                    .where(Message.conversation_id == conversation_id)
                    .order_by(Message.created_at)
                )
                messages = messages_result.scalars().all()

                # Determine output file
                current_output_file = output_file or f"conversation_{conversation_id}.{format}"
                output_path = Path(current_output_file)

                # Export based on format
                if format == "json":
                    export_data = {
                        "conversation": {
                            "id": str(conversation.id),
                            "title": conversation.title,
                            "user": user.username if user else None,
                            "is_active": conversation.is_active,
                            "created_at": conversation.created_at.isoformat(),
                            "updated_at": conversation.updated_at.isoformat(),
                            "metainfo": conversation.metainfo,
                        },
                        "messages": [
                            {
                                "id": str(msg.id),
                                "role": msg.role,
                                "content": msg.content,
                                "token_count": msg.token_count,
                                "created_at": msg.created_at.isoformat(),
                            }
                            for msg in messages
                        ],
                    }

                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)

                elif format == "txt":
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(f"Conversation: {conversation.title}\n")
                        f.write(f"User: {user.username if user else 'System'}\n")
                        f.write(f"Created: {conversation.created_at}\n")
                        f.write("=" * 50 + "\n\n")

                        for msg in messages:
                            f.write(
                                f"[{msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {msg.role.upper()}:\n"
                            )
                            f.write(f"{msg.content}\n\n")

                elif format == "csv":
                    import csv

                    with open(output_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(["timestamp", "role", "content", "token_count"])
                        for msg in messages:
                            writer.writerow(
                                [
                                    msg.created_at.isoformat(),
                                    msg.role,
                                    msg.content,
                                    msg.token_count or 0,
                                ]
                            )

                else:
                    error_message(f"Unsupported format: {format}")
                    return

                success_message(f"Conversation exported to: {output_path}")
                info_message(f"Format: {format}, Messages: {len(messages)}")

            except Exception as e:
                error_message(f"Failed to export conversation: {e}")

    _export_conversation()


@conversation_app.command()
def import_conversation(
    input_file: str = typer.Argument(..., help="Path to JSON file to import"),
    user_id: str = typer.Option(
        None, "--user-id", help="User ID to associate imported conversation with"
    ),
):
    """Import a conversation from a JSON file."""

    @async_command
    async def _import_conversation():
        async with AsyncSessionLocal() as db:
            try:
                # Check if file exists
                if not os.path.exists(input_file):
                    error_message(f"File not found: {input_file}")
                    return

                # Load JSON data
                with open(input_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Validate JSON structure
                if "conversation" not in data or "messages" not in data:
                    error_message(
                        "Invalid JSON format. Expected 'conversation' and 'messages' keys."
                    )
                    return

                conv_data = data["conversation"]
                messages_data = data["messages"]

                # Get or validate user
                target_user_id = None
                if user_id:
                    try:
                        import uuid

                        target_user_id = uuid.UUID(user_id)
                        user = await db.scalar(select(User).where(User.id == target_user_id))
                        if not user:
                            error_message(f"User with ID {user_id} not found")
                            return
                    except ValueError:
                        error_message(f"Invalid UUID format: {user_id}")
                        return
                else:
                    # Try to find user by username from export data
                    if conv_data.get("user"):
                        user = await db.scalar(
                            select(User).where(User.username == conv_data["user"])
                        )
                        if user:
                            target_user_id = user.id
                        else:
                            # Create system user if none found
                            from ..services.user import UserService

                            user_service = UserService(db)
                            system_user = await user_service.create_user(
                                username="system",
                                email="system@localhost",
                                password="system",
                                full_name="System User",
                                is_superuser=True,
                            )
                            target_user_id = system_user.id

                if not target_user_id:
                    error_message("No valid user found for conversation import")
                    return

                # Create new conversation
                new_conversation = Conversation(
                    title=conv_data.get("title", "Imported Conversation"),
                    user_id=target_user_id,
                    is_active=conv_data.get("is_active", True),
                    message_count=len(messages_data),
                )

                db.add(new_conversation)
                await db.flush()  # Get the ID

                # Import messages
                imported_messages = []
                for msg_data in messages_data:
                    message = Message(
                        conversation_id=new_conversation.id,
                        role=msg_data.get("role", "user"),
                        content=msg_data.get("content", ""),
                        token_count=msg_data.get("token_count", 0),
                    )
                    imported_messages.append(message)

                db.add_all(imported_messages)
                await db.commit()

                success_message("Conversation imported successfully!")
                info_message(f"New conversation ID: {new_conversation.id}")
                info_message(f"Imported messages: {len(imported_messages)}")

                # Show summary table
                table = Table(title="Import Summary")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="green")

                table.add_row("Conversation ID", str(new_conversation.id))
                table.add_row("Title", new_conversation.title)
                table.add_row("User ID", str(target_user_id))
                table.add_row("Messages", str(len(imported_messages)))
                table.add_row("Status", "Active" if new_conversation.is_active else "Inactive")

                console.print(table)

            except json.JSONDecodeError as e:
                error_message(f"Invalid JSON file: {e}")
            except Exception as e:
                error_message(f"Failed to import conversation: {e}")

    _import_conversation()


@conversation_app.command()
def delete(
    conversation_id: str = typer.Argument(..., help="Conversation ID (UUID) to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a conversation and all its messages."""

    @async_command
    async def _delete_conversation():
        async with AsyncSessionLocal() as db:
            try:
                # Validate UUID format
                try:
                    import uuid

                    uuid.UUID(conversation_id)
                except ValueError:
                    error_message(f"Invalid UUID format: {conversation_id}")
                    return

                conversation = await db.scalar(
                    select(Conversation).where(Conversation.id == conversation_id)
                )

                if not conversation:
                    error_message(f"Conversation with ID {conversation_id} not found")
                    return

                # Get message count
                message_count = await db.scalar(
                    select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
                )

                console.print("\n[bold red]This will permanently delete:[/bold red]")
                console.print(f"  • Conversation: {conversation.title}")
                console.print(f"  • Messages: {message_count or 0}")
                console.print()

                if not force:
                    from rich.prompt import Confirm

                    if not Confirm.ask("Are you sure you want to delete this conversation?"):
                        warning_message("Deletion cancelled")
                        return

                # Delete messages first
                if message_count:
                    await db.execute(
                        Message.__table__.delete().where(Message.conversation_id == conversation_id)
                    )

                # Delete conversation
                await db.delete(conversation)
                await db.commit()

                success_message(
                    f"Conversation '{conversation.title}' and {message_count or 0} messages deleted successfully"
                )

            except Exception as e:
                error_message(f"Failed to delete conversation: {e}")

    _delete_conversation()


@conversation_app.command()
def archive(
    older_than: int = typer.Option(
        90, "--older-than", help="Archive conversations older than N days"
    ),
    inactive_only: bool = typer.Option(
        True, "--inactive-only/--all", help="Archive only inactive conversations"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Archive old conversations by marking them as inactive."""

    @async_command
    async def _archive_conversations():
        async with AsyncSessionLocal() as db:
            try:
                # Find conversations to archive
                cutoff_date = datetime.now() - timedelta(days=older_than)
                query = select(Conversation).where(Conversation.updated_at < cutoff_date)

                if inactive_only:
                    # Only archive already inactive conversations, just update their status
                    query = query.where(not Conversation.is_active)
                else:
                    # Archive active conversations by making them inactive
                    query = query.where(Conversation.is_active)

                result = await db.execute(query)
                conversations = result.scalars().all()

                if not conversations:
                    info_message(
                        f"No conversations older than {older_than} days found for archiving"
                    )
                    return

                console.print(
                    f"\n[bold yellow]Found {len(conversations)} conversations to archive:[/bold yellow]"
                )
                for conv in conversations[:10]:  # Show first 10
                    console.print(
                        f"  • {conv.title} (ID: {conv.id}, Updated: {conv.updated_at.strftime('%Y-%m-%d')})"
                    )

                if len(conversations) > 10:
                    console.print(f"  ... and {len(conversations) - 10} more")

                if not force:
                    from rich.prompt import Confirm

                    if not Confirm.ask(f"Archive these {len(conversations)} conversations?"):
                        warning_message("Archiving cancelled")
                        return

                # Archive conversations
                archived_count = 0
                for conv in track(conversations, description="Archiving..."):
                    try:
                        conv.is_active = False
                        archived_count += 1
                    except Exception as e:
                        error_message(f"Failed to archive conversation {conv.id}: {e}")

                await db.commit()
                success_message(f"Archived {archived_count} conversations")

            except Exception as e:
                error_message(f"Archiving failed: {e}")

    _archive_conversations()


@conversation_app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of results"),
    username: str = typer.Option(None, "--user", "-u", help="Filter by username"),
):
    """Search conversations and messages."""

    @async_command
    async def _search_conversations():
        async with AsyncSessionLocal() as db:
            try:
                # Search in conversation titles and message content
                search_pattern = f"%{query.lower()}%"

                # Base query
                base_query = select(Conversation, Message).join(Message, isouter=True)

                if username:
                    user = await db.scalar(select(User).where(User.username == username))
                    if not user:
                        error_message(f"User '{username}' not found")
                        return
                    base_query = base_query.where(Conversation.user_id == user.id)

                # Search query
                search_query = base_query.where(
                    or_(
                        func.lower(Conversation.title).like(search_pattern),
                        func.lower(Message.content).like(search_pattern),
                    )
                ).limit(limit)

                result = await db.execute(search_query)
                rows = result.all()

                if not rows:
                    warning_message(f"No conversations or messages found matching '{query}'")
                    return

                # Group results by conversation
                results_by_conv = {}
                for conv, msg in rows:
                    if conv.id not in results_by_conv:
                        results_by_conv[conv.id] = {
                            "conversation": conv,
                            "matching_messages": [],
                        }
                    if msg and query.lower() in msg.content.lower():
                        results_by_conv[conv.id]["matching_messages"].append(msg)

                # Create results table
                table = Table(title=f"Search Results for: '{query}'")
                table.add_column("Conv ID", style="cyan", width=8)
                table.add_column("Title", style="green", width=30)
                table.add_column("Match Type", style="blue", width=12)
                table.add_column("Preview", style="yellow", width=50)

                for conv_id, data in list(results_by_conv.items())[:limit]:
                    conv = data["conversation"]
                    messages = data["matching_messages"]

                    # Check if title matches
                    title_matches = query.lower() in conv.title.lower()

                    if title_matches:
                        table.add_row(
                            str(conv_id),
                            (conv.title[:27] + "..." if len(conv.title) > 30 else conv.title),
                            "Title",
                            "Title contains search term",
                        )

                    # Show matching messages
                    for msg in messages[:3]:  # Show up to 3 matching messages per conversation
                        preview = msg.content[:47] + "..." if len(msg.content) > 50 else msg.content
                        table.add_row(str(conv_id), "", f"{msg.role.title()}", preview)

                console.print(table)

            except Exception as e:
                error_message(f"Search failed: {e}")

    _search_conversations()


@conversation_app.command()
def stats():
    """Display conversation statistics and summary."""

    @async_command
    async def _conversation_stats():
        async with AsyncSessionLocal() as db:
            try:
                # Basic conversation counts
                total_convs = await db.scalar(select(func.count(Conversation.id)))
                active_convs = await db.scalar(
                    select(func.count(Conversation.id)).where(Conversation.is_active)
                )
                inactive_convs = total_convs - active_convs

                # Message statistics
                total_messages = await db.scalar(select(func.count(Message.id)))
                avg_messages_per_conv = total_messages / max(total_convs, 1) if total_convs else 0

                # Recent activity
                last_7_days = datetime.now() - timedelta(days=7)
                recent_convs = await db.scalar(
                    select(func.count(Conversation.id)).where(
                        Conversation.created_at >= last_7_days
                    )
                )
                recent_messages = await db.scalar(
                    select(func.count(Message.id)).where(Message.created_at >= last_7_days)
                )

                # User distribution
                users_with_convs = await db.scalar(
                    select(func.count(func.distinct(Conversation.user_id))).where(
                        Conversation.user_id.isnot(None)
                    )
                )

                # Message role distribution
                role_stats = {}
                for role in ["user", "assistant", "system"]:
                    count = await db.scalar(
                        select(func.count(Message.id)).where(Message.role == role)
                    )
                    role_stats[role] = count or 0

                # Token statistics
                total_tokens = await db.scalar(select(func.sum(Message.token_count)))
                avg_tokens_per_msg = await db.scalar(select(func.avg(Message.token_count)))

                # Create statistics table
                table = Table(title="Conversation Statistics")
                table.add_column("Metric", style="cyan", width=25)
                table.add_column("Count/Value", style="green", width=15)
                table.add_column("Details", style="yellow")

                table.add_row("Total Conversations", str(total_convs or 0), "")
                table.add_row(
                    "Active Conversations",
                    str(active_convs or 0),
                    f"{(active_convs or 0) / max(total_convs or 1, 1) * 100:.1f}%",
                )
                table.add_row(
                    "Inactive Conversations",
                    str(inactive_convs or 0),
                    f"{(inactive_convs or 0) / max(total_convs or 1, 1) * 100:.1f}%",
                )
                table.add_row(
                    "Total Messages",
                    str(total_messages or 0),
                    f"Avg per conv: {avg_messages_per_conv:.1f}",
                )
                table.add_row("Users with Conversations", str(users_with_convs or 0), "")

                # Recent activity
                table.add_row("", "", "")  # Separator
                table.add_row(
                    "Recent Conversations (7d)",
                    str(recent_convs or 0),
                    f"{(recent_convs or 0) / max(total_convs or 1, 1) * 100:.1f}% of total",
                )
                table.add_row(
                    "Recent Messages (7d)",
                    str(recent_messages or 0),
                    f"{(recent_messages or 0) / max(total_messages or 1, 1) * 100:.1f}% of total",
                )

                # Message roles
                table.add_row("", "", "")  # Separator
                for role, count in role_stats.items():
                    percentage = (
                        f"{count / max(total_messages or 1, 1) * 100:.1f}%"
                        if total_messages
                        else "0%"
                    )
                    table.add_row(f"Messages ({role})", str(count), percentage)

                # Tokens
                table.add_row("", "", "")  # Separator
                table.add_row(
                    "Total Tokens",
                    str(total_tokens or 0),
                    f"Avg per msg: {avg_tokens_per_msg or 0:.1f}",
                )

                console.print(table)

            except Exception as e:
                error_message(f"Failed to get conversation statistics: {e}")

    _conversation_stats()
