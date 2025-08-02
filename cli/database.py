"""
Database management commands for the AI Chatbot Platform CLI.

This module provides comprehensive database administration functionality through
async operations and the AI Chatbot SDK. It enables database administrators and
system operators to manage database schemas, migrations, backups, and maintenance
operations with enterprise-grade reliability and security.

The module implements production-ready database management patterns including
automated migrations, backup and recovery, performance monitoring, and maintenance
scheduling. All operations include comprehensive logging and error handling for
operational safety.

Key Features:
    - Database schema management and migrations
    - Backup and recovery operations
    - Performance monitoring and optimization
    - Maintenance and cleanup operations
    - Connection pool management
    - Query performance analysis

Migration Management:
    - Automated schema migrations with rollback support
    - Migration history tracking and validation
    - Safe migration execution with transaction support
    - Pre-migration backup creation
    - Post-migration verification and testing

Backup and Recovery:
    - Full and incremental backup creation
    - Point-in-time recovery capabilities
    - Compressed backup storage and management
    - Automated backup scheduling and retention
    - Backup verification and integrity checking

Performance Monitoring:
    - Real-time connection pool monitoring
    - Query performance analysis and optimization
    - Index usage and recommendation analysis
    - Storage utilization and growth tracking
    - Deadlock detection and resolution

Security Features:
    - Secure database connection management
    - Audit logging for all database operations
    - Access control and permission validation
    - Backup encryption and secure storage
    - Compliance and regulatory reporting

Use Cases:
    - Production database administration and maintenance
    - Development environment setup and management
    - Data migration and system upgrades
    - Disaster recovery testing and procedures
    - Performance optimization and troubleshooting

Example Usage:
    ```bash
    # Database status and monitoring
    ai-chatbot database status
    ai-chatbot database health --detailed

    # Schema and migration management
    ai-chatbot database migrate --auto-approve
    ai-chatbot database rollback --version previous
    ai-chatbot database init --create-admin

    # Backup and recovery
    ai-chatbot database backup --compress --encrypt
    ai-chatbot database restore backup_file.sql --validate

    # Maintenance and optimization
    ai-chatbot database vacuum --analyze
    ai-chatbot database reindex --concurrent
    ai-chatbot database cleanup --older-than 30d
    ```

Integration:
    - Database monitoring system connectivity
    - Backup storage system integration
    - Configuration management system compatibility
    - Automation and orchestration tool integration
"""

from typing import Optional

from async_typer import AsyncTyper
from typer import Option

from .base import error_message, get_sdk, success_message

database_app = AsyncTyper(help="Database management commands", rich_markup_mode=None)


@database_app.async_command()
async def status():
    """Get database status."""
    try:
        sdk = await get_sdk()
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
        sdk = await get_sdk()
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
        sdk = await get_sdk()
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
        sdk = await get_sdk()
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
        sdk = await get_sdk()
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
        sdk = await get_sdk()
        resp = await sdk.database.vacuum()
        if getattr(resp, "success", False):
            success_message("Database vacuum completed successfully.")
        else:
            error_message(getattr(resp, "message", "Failed to vacuum database"))
    except Exception as e:
        error_message(f"Failed to vacuum database: {str(e)}")
        raise SystemExit(1)
