"""
Management CLI for the AI Chatbot Platform.

This script provides command-line utilities for user management,
database operations, and system maintenance.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table
from sqlalchemy import func, select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.conversation import Conversation
from app.models.document import Document, FileStatus
from app.models.user import User
from app.services.auth import AuthService
from app.services.user import UserService

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))


console = Console()

# Create the main Typer app with minimal configuration
app = typer.Typer(help="AI Chatbot Platform Management CLI")


def create_user_cmd(
    username: str,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    superuser: bool = False,
):
    """Create a new user account."""

    async def _create_user():
        try:
            async with AsyncSessionLocal() as db:
                auth_service = AuthService(db)

                # Check if user exists
                existing_user = await auth_service.get_user_by_username(username)
                if existing_user:
                    console.print(
                        f"[red]Error: Username '{username}' already exists[/red]"
                    )
                    return

                # Create user
                from app.schemas.auth import RegisterRequest

                user_data = RegisterRequest(
                    username=username,
                    email=email,
                    password=password,
                    full_name=full_name,
                )

                user = await auth_service.register_user(user_data)

                # Make superuser if requested
                if superuser:
                    user.is_superuser = True
                    await db.commit()
                    await db.refresh(user)

                console.print("[green]User created successfully:[/green]")
                console.print(f"  Username: {user.username}")
                console.print(f"  Email: {user.email}")
                console.print(f"  Superuser: {user.is_superuser}")

        except Exception as e:
            console.print(f"[red]Error creating user: {e}[/red]")

    asyncio.run(_create_user())


def list_users_cmd(limit: int = 10, superusers_only: bool = False):
    """List user accounts."""

    async def _list_users():
        try:
            async with AsyncSessionLocal() as db:
                query = select(User)

                if superusers_only:
                    query = query.where(User.is_superuser is True)

                query = query.limit(limit)
                result = await db.execute(query)
                users = result.scalars().all()

                if not users:
                    console.print("[yellow]No users found[/yellow]")
                    return

                table = Table(title="User Accounts")
                table.add_column("ID", style="cyan")
                table.add_column("Username", style="green")
                table.add_column("Email", style="blue")
                table.add_column("Full Name")
                table.add_column("Active", style="yellow")
                table.add_column("Superuser", style="red")
                table.add_column("Created")

                for user in users:
                    table.add_row(
                        str(user.id),
                        user.username,
                        user.email,
                        user.full_name or "",
                        "✓" if user.is_active else "✗",
                        "✓" if user.is_superuser else "✗",
                        user.created_at.strftime("%Y-%m-%d"),
                    )

                console.print(table)

        except Exception as e:
            console.print(f"[red]Error listing users: {e}[/red]")

    asyncio.run(_list_users())


def delete_user_cmd(username: str, force: bool = False):
    """Delete a user account."""

    async def _delete_user():
        try:
            async with AsyncSessionLocal() as db:
                auth_service = AuthService(db)
                user_service = UserService(db)

                # Find user
                user = await auth_service.get_user_by_username(username)
                if not user:
                    console.print(f"[red]User '{username}' not found[/red]")
                    return

                # Confirm deletion
                if not force:
                    console.print("User to delete:")
                    console.print(f"  Username: {user.username}")
                    console.print(f"  Email: {user.email}")
                    console.print(f"  Superuser: {user.is_superuser}")

                    if not Confirm.ask("Are you sure you want to delete this user?"):
                        console.print("[yellow]Deletion cancelled[/yellow]")
                        return

                # Delete user
                success = await user_service.delete_user(user.id)

                if success:
                    console.print(
                        f"[green]User '{username}' deleted successfully[/green]"
                    )
                else:
                    console.print(f"[red]Failed to delete user '{username}'[/red]")

        except Exception as e:
            console.print(f"[red]Error deleting user: {e}[/red]")

    asyncio.run(_delete_user())


def reset_password_cmd(username: str, password: str):
    """Reset user password."""

    async def _reset_password():
        try:
            async with AsyncSessionLocal() as db:
                auth_service = AuthService(db)

                # Find user
                user = await auth_service.get_user_by_username(username)
                if not user:
                    console.print(f"[red]User '{username}' not found[/red]")
                    return

                # Reset password
                from app.utils.security import get_password_hash

                user.hashed_password = get_password_hash(password)
                await db.commit()

                console.print(
                    f"[green]Password reset successfully for user '{username}'[/green]"
                )

        except Exception as e:
            console.print(f"[red]Error resetting password: {e}[/red]")

    asyncio.run(_reset_password())


def show_stats():
    """Show system statistics."""

    async def _show_stats():
        try:
            async with AsyncSessionLocal() as db:
                # User statistics
                user_count = await db.scalar(select(func.count(User.id)))
                active_users = await db.scalar(
                    select(func.count(User.id)).where(User.is_active is True)
                )
                superusers = await db.scalar(
                    select(func.count(User.id)).where(User.is_superuser is True)
                )

                # Document statistics
                doc_count = await db.scalar(select(func.count(Document.id)))
                completed_docs = await db.scalar(
                    select(func.count(Document.id)).where(
                        Document.status == FileStatus.COMPLETED
                    )
                )

                # Conversation statistics
                conv_count = await db.scalar(select(func.count(Conversation.id)))
                active_convs = await db.scalar(
                    select(func.count(Conversation.id)).where(
                        Conversation.is_active is True
                    )
                )

                # Display statistics
                table = Table(title="System Statistics")
                table.add_column("Category", style="cyan")
                table.add_column("Metric", style="green")
                table.add_column("Count", style="yellow")

                stats_data = [
                    ("Users", "Total Users", str(user_count or 0)),
                    ("Users", "Active Users", str(active_users or 0)),
                    ("Users", "Superusers", str(superusers or 0)),
                    ("Documents", "Total Documents", str(doc_count or 0)),
                    ("Documents", "Completed Documents", str(completed_docs or 0)),
                    ("Conversations", "Total Conversations", str(conv_count or 0)),
                    ("Conversations", "Active Conversations", str(active_convs or 0)),
                ]

                for category, metric, count in stats_data:
                    table.add_row(category, metric, count)

                console.print(table)

        except Exception as e:
            console.print(f"[red]Error retrieving statistics: {e}[/red]")

    asyncio.run(_show_stats())


def init_database():
    """Initialize the database."""

    async def _init_db():
        try:
            from app.database import init_db

            await init_db()
            console.print("[green]Database initialized successfully[/green]")

        except Exception as e:
            console.print(f"[red]Database initialization failed: {e}[/red]")

    asyncio.run(_init_db())


def health_check():
    """Check system health."""

    async def _health_check():
        try:
            # Check database connection
            async with AsyncSessionLocal() as db:
                await db.execute(select(func.count(User.id)))
                console.print("[green]✓ Database connection OK[/green]")

            # Check OpenAI API
            try:
                from app.services.openai_client import OpenAIClient

                client = OpenAIClient()
                is_available = await client.validate_model_availability()
                if is_available:
                    console.print("[green]✓ OpenAI API connection OK[/green]")
                else:
                    console.print("[yellow]⚠ OpenAI API models not available[/yellow]")
            except Exception as e:
                console.print(f"[red]✗ OpenAI API error: {e}[/red]")

            # Check configuration
            required_settings = ["database_url", "secret_key", "openai_api_key"]
            config_ok = True
            for setting in required_settings:
                if not getattr(settings, setting, None):
                    console.print(f"[red]✗ Missing required setting: {setting}[/red]")
                    config_ok = False

            if config_ok:
                console.print("[green]✓ Configuration OK[/green]")

            console.print("\n[blue]System Status Summary:[/blue]")
            console.print(f"App Name: {settings.app_name}")
            console.print(f"Version: {settings.app_version}")
            console.print(f"Debug Mode: {settings.debug}")
            console.print(f"Log Level: {settings.log_level}")

        except Exception as e:
            console.print(f"[red]Health check failed: {e}[/red]")

    asyncio.run(_health_check())


def show_config():
    """Show current configuration."""

    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Description", style="dim")

    config_items = [
        ("APP_NAME", settings.app_name, "Application name"),
        ("APP_VERSION", settings.app_version, "Application version"),
        ("DEBUG", str(settings.debug), "Debug mode"),
        ("LOG_LEVEL", settings.log_level, "Logging level"),
        (
            "DATABASE_URL",
            settings.database_url[:50] + "..."
            if len(settings.database_url) > 50
            else settings.database_url,
            "Database connection",
        ),
        ("OPENAI_BASE_URL", settings.openai_base_url, "OpenAI API base URL"),
        ("OPENAI_CHAT_MODEL", settings.openai_chat_model, "Chat model"),
        ("OPENAI_EMBEDDING_MODEL", settings.openai_embedding_model, "Embedding model"),
        (
            "MAX_FILE_SIZE",
            f"{settings.max_file_size // 1024 // 1024}MB",
            "Maximum file size",
        ),
        (
            "ALLOWED_FILE_TYPES",
            ", ".join(settings.allowed_file_types),
            "Allowed file types",
        ),
        ("DEFAULT_CHUNK_SIZE", str(settings.default_chunk_size), "Default chunk size"),
        (
            "DEFAULT_CHUNK_OVERLAP",
            str(settings.default_chunk_overlap),
            "Default chunk overlap",
        ),
        ("UPLOAD_DIRECTORY", settings.upload_directory, "Upload directory"),
    ]

    for setting, value, description in config_items:
        table.add_row(setting, value, description)

    console.print(table)


# Register commands with simple arguments
@app.command()
def create_user(
    username: str = typer.Argument(..., help="Username"),
    email: str = typer.Argument(..., help="Email address"),
    password: str = typer.Argument(..., help="Password"),
    full_name: str = typer.Argument(None, help="Full name"),
    superuser: bool = typer.Option(False, help="Create as superuser"),
):
    """Create a new user account."""
    create_user_cmd(username, email, password, full_name, superuser)


@app.command()
def list_users(
    limit: int = typer.Option(10, help="Number of users to show"),
    superusers_only: bool = typer.Option(False, help="Show only superusers"),
):
    """List user accounts."""
    list_users_cmd(limit, superusers_only)


@app.command()
def delete_user(
    username: str = typer.Argument(..., help="Username to delete"),
    force: bool = typer.Option(False, help="Skip confirmation"),
):
    """Delete a user account."""
    delete_user_cmd(username, force)


@app.command()
def reset_password(
    username: str = typer.Argument(..., help="Username"),
    password: str = typer.Argument(..., help="New password"),
):
    """Reset user password."""
    reset_password_cmd(username, password)


@app.command()
def stats():
    """Show system statistics."""
    show_stats()


@app.command()
def init_db():
    """Initialize the database."""
    init_database()


@app.command()
def health():
    """Check system health."""
    health_check()


@app.command()
def config():
    """Show current configuration."""
    show_config()


if __name__ == "__main__":
    try:
        app()
    except Exception as e:
        console.print(f"[red]CLI Error: {e}[/red]")
        sys.exit(1)
