"""
Database management commands for the API-based CLI.

This module provides database administration functionality through API calls.
"""

import asyncio
import typer
from .base import get_client_with_auth, handle_api_response, console, error_message, success_message, confirm_action

database_app = typer.Typer(help="🗄️ Database management commands")


@database_app.command()
def init():
    """Initialize the database and create all tables."""
    
    async def _init_database():
        client = get_client_with_auth()
        
        try:
            response = await client.post("/api/v1/database/init")
            handle_api_response(response, "database initialization")
        
        except Exception as e:
            error_message(f"Failed to initialize database: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_init_database())


@database_app.command()
def status():
    """Show database connection status and basic information."""
    
    async def _show_status():
        client = get_client_with_auth()
        
        try:
            response = await client.get("/api/v1/database/status")
            data = handle_api_response(response, "getting database status")
            
            if data:
                from rich.table import Table
                
                table = Table(title="Database Status")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="white")
                
                table.add_row("Connection Status", data.get("connection_status", "Unknown"))
                table.add_row("Database Version", data.get("database_version", "Unknown"))
                table.add_row("Database Size", data.get("database_size", "Unknown"))
                table.add_row("Table Count", str(data.get("table_count", 0)))
                table.add_row("PGVector Installed", "Yes" if data.get("pgvector_installed") else "No")
                
                console.print(table)
        
        except Exception as e:
            error_message(f"Failed to get database status: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_show_status())


@database_app.command()
def tables():
    """List all database tables with row counts."""
    
    async def _list_tables():
        client = get_client_with_auth()
        
        try:
            response = await client.get("/api/v1/database/tables")
            data = handle_api_response(response, "listing database tables")
            
            if data:
                from rich.table import Table
                
                tables = data.get("tables", [])
                
                table = Table(title=f"Database Tables ({len(tables)} total)")
                table.add_column("Schema", style="cyan")
                table.add_column("Table Name", style="white")
                table.add_column("Row Count", style="green")
                table.add_column("Size", style="yellow")
                
                for tbl in tables:
                    table.add_row(
                        tbl.get("schema", ""),
                        tbl.get("name", ""),
                        str(tbl.get("row_count", 0)),
                        tbl.get("size", "")
                    )
                
                console.print(table)
        
        except Exception as e:
            error_message(f"Failed to list tables: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_list_tables())


@database_app.command()
def migrations():
    """Show migration status and available migrations."""
    
    async def _show_migrations():
        client = get_client_with_auth()
        
        try:
            response = await client.get("/api/v1/database/migrations")
            data = handle_api_response(response, "getting migration status")
            
            if data:
                from rich.table import Table
                from rich.panel import Panel
                
                # Show current status
                status_panel = Panel(
                    f"Current Revision: [green]{data.get('current_revision', 'Unknown')}[/green]\n"
                    f"Available Heads: [blue]{data.get('available_heads', 'Unknown')}[/blue]",
                    title="Migration Status",
                    border_style="blue"
                )
                console.print(status_panel)
                
                # Show history
                history = data.get("migration_history", [])
                if history:
                    console.print("\n[bold]Recent Migration History:[/bold]")
                    for i, entry in enumerate(history[:5]):
                        console.print(f"{i+1}. {entry}")
        
        except Exception as e:
            error_message(f"Failed to get migration status: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_show_migrations())


@database_app.command()
def upgrade(
    revision: str = typer.Option("head", "--revision", help="Target revision"),
):
    """Run database migrations to upgrade schema."""
    
    async def _upgrade_database():
        client = get_client_with_auth()
        
        try:
            params = {"revision": revision}
            response = await client.post("/api/v1/database/upgrade", params=params)
            data = handle_api_response(response, "database upgrade")
            
            if data and "output" in data:
                console.print("\n[bold]Migration Output:[/bold]")
                console.print(data["output"])
        
        except Exception as e:
            error_message(f"Failed to upgrade database: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_upgrade_database())


@database_app.command()
def downgrade(
    revision: str = typer.Argument(..., help="Target revision to downgrade to"),
):
    """Downgrade database to a previous migration."""
    
    async def _downgrade_database():
        if not confirm_action(f"Are you sure you want to downgrade to revision '{revision}'? This may cause data loss."):
            return
        
        client = get_client_with_auth()
        
        try:
            params = {"revision": revision}
            response = await client.post("/api/v1/database/downgrade", params=params)
            data = handle_api_response(response, "database downgrade")
            
            if data and "output" in data:
                console.print("\n[bold]Downgrade Output:[/bold]")
                console.print(data["output"])
        
        except Exception as e:
            error_message(f"Failed to downgrade database: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_downgrade_database())


@database_app.command()
def backup(
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
    schema_only: bool = typer.Option(False, "--schema-only", help="Backup schema only"),
):
    """Create a database backup."""
    
    async def _backup_database():
        client = get_client_with_auth()
        
        try:
            params = {"schema_only": schema_only}
            if output:
                params["output_file"] = output
            
            response = await client.post("/api/v1/database/backup", params=params)
            data = handle_api_response(response, "database backup")
            
            if data:
                from rich.panel import Panel
                
                backup_panel = Panel(
                    f"Output File: [green]{data.get('output_file', '')}[/green]\n"
                    f"File Size: [blue]{data.get('file_size', '')}[/blue]\n"
                    f"Schema Only: [yellow]{'Yes' if data.get('schema_only') else 'No'}[/yellow]",
                    title="Backup Created",
                    border_style="green"
                )
                console.print(backup_panel)
        
        except Exception as e:
            error_message(f"Failed to create backup: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_backup_database())


@database_app.command()
def restore(
    backup_file: str = typer.Argument(..., help="Backup file to restore from"),
):
    """Restore database from a backup file."""
    
    async def _restore_database():
        if not confirm_action(f"Are you sure you want to restore from '{backup_file}'? This will overwrite existing data."):
            return
        
        client = get_client_with_auth()
        
        try:
            params = {"backup_file": backup_file}
            response = await client.post("/api/v1/database/restore", params=params)
            handle_api_response(response, "database restore")
        
        except Exception as e:
            error_message(f"Failed to restore database: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_restore_database())


@database_app.command()
def vacuum(
    analyze: bool = typer.Option(True, "--analyze/--no-analyze", help="Run ANALYZE after VACUUM"),
):
    """Run VACUUM to optimize database performance."""
    
    async def _vacuum_database():
        client = get_client_with_auth()
        
        try:
            params = {"analyze": analyze}
            response = await client.post("/api/v1/database/vacuum", params=params)
            handle_api_response(response, "database vacuum")
        
        except Exception as e:
            error_message(f"Failed to vacuum database: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_vacuum_database())


@database_app.command()
def analyze():
    """Analyze database and show performance statistics."""
    
    async def _analyze_database():
        client = get_client_with_auth()
        
        try:
            response = await client.get("/api/v1/database/analyze")
            data = handle_api_response(response, "database analysis")
            
            if data:
                from rich.table import Table
                from rich.panel import Panel
                from rich.columns import Columns
                
                # Performance metrics
                perf_metrics = data.get("performance_metrics", {})
                perf_panel = Panel(
                    f"Cache Hit Ratio: [green]{perf_metrics.get('cache_hit_ratio', 0):.1f}%[/green]\n"
                    f"Transaction Success: [blue]{perf_metrics.get('transaction_success_rate', 0):.1f}%[/blue]",
                    title="Performance",
                    border_style="green"
                )
                
                # Database stats
                db_stats = data.get("database_statistics", {})
                stats_panel = Panel(
                    f"Active Connections: [yellow]{db_stats.get('active_connections', 0)}[/yellow]\n"
                    f"Committed Transactions: [green]{db_stats.get('committed_transactions', 0)}[/green]\n"
                    f"Rolled Back: [red]{db_stats.get('rolled_back_transactions', 0)}[/red]",
                    title="Statistics",
                    border_style="blue"
                )
                
                console.print(Columns([perf_panel, stats_panel]))
                
                # Largest tables
                largest_tables = data.get("largest_tables", [])
                if largest_tables:
                    table = Table(title="Largest Tables")
                    table.add_column("Schema", style="cyan")
                    table.add_column("Table", style="white")
                    table.add_column("Size", style="green")
                    
                    for tbl in largest_tables[:5]:
                        table.add_row(
                            tbl.get("schema", ""),
                            tbl.get("table", ""),
                            tbl.get("size", "")
                        )
                    
                    console.print(table)
        
        except Exception as e:
            error_message(f"Failed to analyze database: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_analyze_database())


@database_app.command()
def query(
    sql: str = typer.Argument(..., help="SQL query to execute"),
    limit: int = typer.Option(100, "--limit", help="Result limit"),
):
    """Execute a custom SQL query."""
    
    async def _execute_query():
        client = get_client_with_auth()
        
        try:
            params = {"query": sql, "limit": limit}
            response = await client.post("/api/v1/database/query", params=params)
            data = handle_api_response(response, "query execution")
            
            if data:
                from rich.table import Table
                
                rows = data.get("rows", [])
                columns = data.get("columns", [])
                
                if rows and columns:
                    table = Table(title=f"Query Results ({data.get('row_count', 0)} rows)")
                    
                    for col in columns:
                        table.add_column(col, style="cyan")
                    
                    for row in rows:
                        table.add_row(*[str(row.get(col, "")) for col in columns])
                    
                    console.print(table)
                else:
                    success_message("Query executed successfully (no results)")
        
        except Exception as e:
            error_message(f"Failed to execute query: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_execute_query())