"""Database management commands for the AI Chatbot Platform CLI.

This module provides comprehensive database administration functionality through
async operations and the AI Chatbot SDK for managing database schemas, migrations,
and maintenance operations.
"""

from typing import Optional

from async_typer import AsyncTyper
from rich.console import Console
from rich.table import Table
from typer import Option

from cli.base import APIError, error_message, get_sdk, success_message

console = Console()

database_app = AsyncTyper(help="Database management commands", rich_markup_mode=None)


@database_app.async_command()
async def status():
    """Get database status."""
    try:
        sdk = await get_sdk()
        data = await sdk.database.get_status()

        table = Table(title="Database Status")
        for k, v in data.items():
            table.add_row(str(k), str(v))
        console.print(table)
    except APIError as e:
        error_message(f"Failed to get database status: {e.body['message']}")
    except Exception as e:
        error_message(f"Failed to get database status: {str(e)}")


@database_app.async_command()
async def init():
    """Initialize the database."""
    try:
        sdk = await get_sdk()
        await sdk.database.init_database()
        success_message("Database initialized successfully.")
    except APIError as e:
        error_message(f"Failed to initialize database: {e.body['message']}")
    except Exception as e:
        error_message(f"Failed to initialize database: {str(e)}")


@database_app.async_command()
async def upgrade():
    """Run database migrations/upgrade."""
    try:
        sdk = await get_sdk()
        await sdk.database.upgrade()
        success_message("Database upgraded successfully.")
    except APIError as e:
        error_message(f"Failed to upgrade database: {e.body['message']}")
    except Exception as e:
        error_message(f"Failed to upgrade database: {str(e)}")


@database_app.async_command()
async def backup(
    output: Optional[str] = Option(None, "--output", help="Output file for backup"),
):
    """Create database backup."""
    try:
        sdk = await get_sdk()
        response = await sdk.database.backup(output)
        success_message(f"Database backup created successfully: {response.output_file}")
    except APIError as e:
        error_message(f"Failed to create database backup: {e.body['message']}")
    except Exception as e:
        error_message(f"Failed to create database backup: {str(e)}")


@database_app.async_command()
async def tables():
    """List database tables."""
    try:
        sdk = await get_sdk()
        data = await sdk.database.get_tables()
        tables = data.get("tables", [])
        table = Table(title="Database Tables")
        table.add_column("Table", style="cyan")
        table.add_column("Rows", style="green")
        for t in tables:
            table.add_row(str(t.get("name", "")), str(t.get("count", 0)))
        console.print(table)
    except APIError as e:
        error_message(f"Failed to list tables: {e.body['message']}")
    except Exception as e:
        error_message(f"Failed to list tables: {str(e)}")


@database_app.async_command()
async def vacuum():
    """Vacuum the database."""
    try:
        sdk = await get_sdk()
        await sdk.database.vacuum()
        success_message("Database vacuum completed successfully.")
    except APIError as e:
        error_message(f"Failed to vacuum database: {e.body['message']}")
    except Exception as e:
        error_message(f"Failed to vacuum database: {str(e)}")
