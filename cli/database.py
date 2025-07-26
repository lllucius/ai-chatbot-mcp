"""
Database management commands for the API-based CLI.

All commands use async/await and the async SDK client.
"""

from typing import Optional

from async_typer import AsyncTyper
from typer import Option

from .base import console, error_message, get_sdk_with_auth, success_message

database_app = AsyncTyper(help="🗄️ Database management commands")


@database_app.async_command()
async def status():
    """Get database status."""
    try:
        sdk = await get_sdk_with_auth()
        data = await sdk.database.get_status()
        if data:
            from rich.table import Table
            table = Table(title="Database Status")
            for k, v in data.items():
                table.add_row(str(k), str(v))
            console.print(table)
    except Exception as e:
        error_message(f"Failed to get database status: {str(e)}")
        raise SystemExit(1)


@database_app.async_command()
async def init():
    """Initialize the database."""
    try:
        sdk = await get_sdk_with_auth()
        resp = await sdk.database.init_database()
        if getattr(resp, "success", False):
            success_message("Database initialized successfully.")
        else:
            error_message(getattr(resp, "message", "Failed to initialize database"))
    except Exception as e:
        error_message(f"Failed to initialize database: {str(e)}")
        raise SystemExit(1)


@database_app.async_command()
async def upgrade():
    """Run database migrations/upgrade."""
    try:
        sdk = await get_sdk_with_auth()
        resp = await sdk.database.upgrade()
        if getattr(resp, "success", False):
            success_message("Database upgraded successfully.")
        else:
            error_message(getattr(resp, "message", "Failed to upgrade database"))
    except Exception as e:
        error_message(f"Failed to upgrade database: {str(e)}")
        raise SystemExit(1)


@database_app.async_command()
async def backup(
    output: Optional[str] = Option(None, "--output", help="Output file for backup"),
):
    """Create database backup."""
    try:
        sdk = await get_sdk_with_auth()
        resp = await sdk.database.backup(output)
        if getattr(resp, "success", False):
            success_message("Database backup created successfully.")
        else:
            error_message(getattr(resp, "message", "Failed to create backup"))
    except Exception as e:
        error_message(f"Failed to create database backup: {str(e)}")
        raise SystemExit(1)


@database_app.async_command()
async def tables():
    """List database tables."""
    try:
        sdk = await get_sdk_with_auth()
        data = await sdk.database.get_tables()
        if data:
            from rich.table import Table
            tables = data.get("tables", [])
            table = Table(title="Database Tables")
            table.add_column("Table", style="cyan")
            table.add_column("Rows", style="green")
            for t in tables:
                table.add_row(str(t.get("name", "")), str(t.get("count", 0)))
            console.print(table)
    except Exception as e:
        error_message(f"Failed to list tables: {str(e)}")
        raise SystemExit(1)


@database_app.async_command()
async def vacuum():
    """Vacuum the database."""
    try:
        sdk = await get_sdk_with_auth()
        resp = await sdk.database.vacuum()
        if getattr(resp, "success", False):
            success_message("Database vacuum completed successfully.")
        else:
            error_message(getattr(resp, "message", "Failed to vacuum database"))
    except Exception as e:
        error_message(f"Failed to vacuum database: {str(e)}")
        raise SystemExit(1)
