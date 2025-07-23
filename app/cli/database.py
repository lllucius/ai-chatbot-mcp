"""
Database management CLI commands.

Provides comprehensive database management functionality including:
- Database initialization and migrations
- Schema management
- Data backup and restoration
- Database maintenance and optimization
- Health checks and diagnostics
"""

import os
import subprocess
from datetime import datetime

import typer
from rich.table import Table
from sqlalchemy import text

from ..config import settings
from ..database import AsyncSessionLocal
from .base import (async_command, console, error_message, info_message, success_message, warning_message)

# Create the database management app
database_app = typer.Typer(help="Database management commands")


@database_app.command()
def init():
    """Initialize the database and create all tables."""
    
    @async_command
    async def _init_database():
        try:
            from ..database import init_db
            await init_db()
            success_message("Database initialized successfully")
            
            # Show created tables
            async with AsyncSessionLocal() as db:
                result = await db.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """))
                tables = [row[0] for row in result.fetchall()]
                
                if tables:
                    info_message(f"Created {len(tables)} tables:")
                    for table in tables:
                        console.print(f"  • {table}")
                
        except Exception as e:
            error_message(f"Database initialization failed: {e}")
    
    _init_database()


@database_app.command()
def status():
    """Show database connection status and basic information."""
    
    @async_command
    async def _database_status():
        try:
            async with AsyncSessionLocal() as db:
                # Test connection
                await db.execute(text("SELECT 1"))
                success_message("Database connection: OK")
                
                # Get database info
                db_info = await db.execute(text("SELECT version()"))
                version = db_info.scalar()
                console.print(f"PostgreSQL Version: {version}")
                
                # Database size
                db_name = settings.database_url.split('/')[-1].split('?')[0]
                size_query = text("""
                    SELECT pg_size_pretty(pg_database_size(:db_name)) as size
                """)
                size_result = await db.execute(size_query, {"db_name": db_name})
                db_size = size_result.scalar()
                console.print(f"Database Size: {db_size}")
                
                # Connection info
                connection_info = await db.execute(text("""
                    SELECT count(*) as active_connections,
                           max(backend_start) as oldest_connection
                    FROM pg_stat_activity 
                    WHERE state = 'active'
                """))
                conn_data = connection_info.fetchone()
                if conn_data:
                    console.print(f"Active Connections: {conn_data[0]}")
                    console.print(f"Oldest Connection: {conn_data[1] or 'N/A'}")
                
                # Check for pgvector extension
                vector_check = await db.execute(text("""
                    SELECT EXISTS(
                        SELECT 1 FROM pg_extension WHERE extname = 'vector'
                    )
                """))
                has_vector = vector_check.scalar()
                if has_vector:
                    success_message("pgvector extension: Available")
                else:
                    warning_message("pgvector extension: Not installed")
                
        except Exception as e:
            error_message(f"Database status check failed: {e}")
    
    _database_status()


@database_app.command()
def tables():
    """List all database tables with row counts."""
    
    @async_command
    async def _list_tables():
        try:
            async with AsyncSessionLocal() as db:
                # Get table information
                tables_query = text("""
                    SELECT 
                        t.table_name,
                        COALESCE(c.column_count, 0) as column_count,
                        pg_size_pretty(pg_total_relation_size(quote_ident(t.table_name)::regclass)) as size
                    FROM information_schema.tables t
                    LEFT JOIN (
                        SELECT table_name, COUNT(*) as column_count
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                        GROUP BY table_name
                    ) c ON t.table_name = c.table_name
                    WHERE t.table_schema = 'public' 
                    AND t.table_type = 'BASE TABLE'
                    ORDER BY t.table_name
                """)
                
                result = await db.execute(tables_query)
                tables_info = result.fetchall()
                
                if not tables_info:
                    warning_message("No tables found")
                    return
                
                # Create table with row counts
                table = Table(title="Database Tables")
                table.add_column("Table Name", style="cyan", width=25)
                table.add_column("Columns", style="green", width=10)
                table.add_column("Rows", style="yellow", width=12)
                table.add_column("Size", style="blue", width=12)
                table.add_column("Description", style="dim", width=30)
                
                # Table descriptions
                descriptions = {
                    "users": "User accounts and profiles",
                    "documents": "Uploaded documents metadata",
                    "document_chunks": "Document text chunks with embeddings",
                    "conversations": "Chat conversation sessions",
                    "messages": "Individual chat messages",
                    "alembic_version": "Database migration tracking"
                }
                
                total_rows = 0
                for table_name, col_count, size in tables_info:
                    # Get row count
                    count_query = text(f'SELECT COUNT(*) FROM "{table_name}"')
                    try:
                        row_count_result = await db.execute(count_query)
                        row_count = row_count_result.scalar()
                        total_rows += row_count or 0
                    except Exception:
                        row_count = "Error"
                    
                    description = descriptions.get(table_name, "")
                    
                    table.add_row(
                        table_name,
                        str(col_count),
                        str(row_count) if row_count != "Error" else row_count,
                        size,
                        description
                    )
                
                console.print(table)
                console.print(f"\n[bold]Total rows across all tables:[/bold] {total_rows:,}")
                
        except Exception as e:
            error_message(f"Failed to list tables: {e}")
    
    _list_tables()


@database_app.command()
def migrations():
    """Show migration status and available migrations."""
    
    @async_command
    async def _migration_status():
        try:
            # Get the project root directory dynamically
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
            # Check if alembic is available
            result = subprocess.run(
                ["alembic", "--help"], 
                capture_output=True, 
                text=True, 
                cwd=project_root
            )
            
            if result.returncode != 0:
                error_message("Alembic not available. Install with: pip install alembic")
                return
            
            # Get current revision
            current_result = subprocess.run(
                ["alembic", "current"], 
                capture_output=True, 
                text=True,
                cwd=project_root
            )
            
            if current_result.returncode == 0:
                current_revision = current_result.stdout.strip()
                if current_revision:
                    success_message(f"Current migration: {current_revision}")
                else:
                    warning_message("No migrations applied")
            
            # Get migration history
            history_result = subprocess.run(
                ["alembic", "history"], 
                capture_output=True, 
                text=True,
                cwd=project_root
            )
            
            if history_result.returncode == 0 and history_result.stdout.strip():
                console.print("\n[bold]Migration History:[/bold]")
                console.print(history_result.stdout)
            else:
                info_message("No migration history available")
            
            # Check for pending migrations
            heads_result = subprocess.run(
                ["alembic", "heads"], 
                capture_output=True, 
                text=True,
                cwd=project_root
            )
            
            if heads_result.returncode == 0:
                latest_revision = heads_result.stdout.strip()
                if latest_revision and latest_revision != current_revision.split()[0] if current_revision else "":
                    warning_message(f"Pending migration available: {latest_revision}")
                    info_message("Run 'manage database upgrade' to apply")
                
        except Exception as e:
            error_message(f"Failed to check migration status: {e}")
    
    _migration_status()


@database_app.command()
def upgrade(
    revision: str = typer.Option("head", "--revision", "-r", help="Target revision (default: head)")
):
    """Run database migrations to upgrade schema."""
    
    def _upgrade_database():
        try:
            # Get the project root directory dynamically
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
            info_message(f"Running database migrations to {revision}...")
            
            result = subprocess.run(
                ["alembic", "upgrade", revision], 
                capture_output=True, 
                text=True,
                cwd=project_root
            )
            
            if result.returncode == 0:
                success_message("Database migrations completed successfully")
                if result.stdout:
                    console.print(result.stdout)
            else:
                error_message("Database migration failed")
                if result.stderr:
                    console.print(f"[red]{result.stderr}[/red]")
                
        except Exception as e:
            error_message(f"Failed to run migrations: {e}")
    
    _upgrade_database()


@database_app.command()
def downgrade(
    revision: str = typer.Argument(..., help="Target revision to downgrade to"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Downgrade database to a previous migration."""
    
    def _downgrade_database():
        try:
            if not force:
                from rich.prompt import Confirm
                if not Confirm.ask(f"Are you sure you want to downgrade to revision {revision}? This may cause data loss."):
                    warning_message("Downgrade cancelled")
                    return
            
            info_message(f"Downgrading database to {revision}...")
            
            result = subprocess.run(
                ["alembic", "downgrade", revision], 
                capture_output=True, 
                text=True,
                cwd="/home/runner/work/ai-chatbot-mcp/ai-chatbot-mcp"
            )
            
            if result.returncode == 0:
                success_message(f"Database downgraded to {revision}")
                if result.stdout:
                    console.print(result.stdout)
            else:
                error_message("Database downgrade failed")
                if result.stderr:
                    console.print(f"[red]{result.stderr}[/red]")
                
        except Exception as e:
            error_message(f"Failed to downgrade database: {e}")
    
    _downgrade_database()


@database_app.command()
def backup(
    output_file: str = typer.Option(None, "--output", "-o", help="Backup file path"),
    schema_only: bool = typer.Option(False, "--schema-only", help="Backup schema only (no data)"),
    data_only: bool = typer.Option(False, "--data-only", help="Backup data only (no schema)"),
):
    """Create a database backup."""
    
    def _backup_database():
        try:
            # Generate backup filename if not provided
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_type = "schema" if schema_only else "data" if data_only else "full"
                filename = f"backup_{backup_type}_{timestamp}.sql"
            else:
                filename = output_file
            
            # Parse database URL to get connection parameters
            db_url = settings.database_url
            if "postgresql" in db_url:
                # Extract connection details
                # Format: postgresql+asyncpg://user:pass@host:port/dbname
                import urllib.parse
                parsed = urllib.parse.urlparse(db_url.replace("+asyncpg", ""))
                
                cmd = ["pg_dump"]
                
                if parsed.hostname:
                    cmd.extend(["-h", parsed.hostname])
                if parsed.port:
                    cmd.extend(["-p", str(parsed.port)])
                if parsed.username:
                    cmd.extend(["-U", parsed.username])
                
                if schema_only:
                    cmd.append("--schema-only")
                elif data_only:
                    cmd.append("--data-only")
                
                cmd.extend(["-f", filename])
                cmd.append(parsed.path[1:])  # Remove leading slash
                
                # Set password environment variable if available
                env = os.environ.copy()
                if parsed.password:
                    env["PGPASSWORD"] = parsed.password
                
                info_message(f"Creating database backup: {filename}")
                
                result = subprocess.run(cmd, capture_output=True, text=True, env=env)
                
                if result.returncode == 0:
                    success_message(f"Backup created successfully: {filename}")
                    
                    # Show file size
                    if os.path.exists(filename):
                        size = os.path.getsize(filename)
                        from .base import format_size
                        info_message(f"Backup size: {format_size(size)}")
                else:
                    error_message("Backup failed")
                    if result.stderr:
                        console.print(f"[red]{result.stderr}[/red]")
            else:
                error_message("Backup only supported for PostgreSQL databases")
                
        except Exception as e:
            error_message(f"Failed to create backup: {e}")
    
    _backup_database()


@database_app.command()
def restore(
    backup_file: str = typer.Argument(..., help="Path to backup file"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Restore database from a backup file."""
    
    def _restore_database():
        try:
            if not os.path.exists(backup_file):
                error_message(f"Backup file not found: {backup_file}")
                return
            
            if not force:
                from rich.prompt import Confirm
                if not Confirm.ask(f"Are you sure you want to restore from {backup_file}? This will overwrite existing data."):
                    warning_message("Restore cancelled")
                    return
            
            # Parse database URL
            db_url = settings.database_url
            if "postgresql" in db_url:
                import urllib.parse
                parsed = urllib.parse.urlparse(db_url.replace("+asyncpg", ""))
                
                cmd = ["psql"]
                
                if parsed.hostname:
                    cmd.extend(["-h", parsed.hostname])
                if parsed.port:
                    cmd.extend(["-p", str(parsed.port)])
                if parsed.username:
                    cmd.extend(["-U", parsed.username])
                
                cmd.extend(["-f", backup_file])
                cmd.append(parsed.path[1:])  # Remove leading slash
                
                # Set password environment variable if available
                env = os.environ.copy()
                if parsed.password:
                    env["PGPASSWORD"] = parsed.password
                
                info_message(f"Restoring database from: {backup_file}")
                
                result = subprocess.run(cmd, capture_output=True, text=True, env=env)
                
                if result.returncode == 0:
                    success_message("Database restored successfully")
                    if result.stdout:
                        console.print(result.stdout)
                else:
                    error_message("Restore failed")
                    if result.stderr:
                        console.print(f"[red]{result.stderr}[/red]")
            else:
                error_message("Restore only supported for PostgreSQL databases")
                
        except Exception as e:
            error_message(f"Failed to restore database: {e}")
    
    _restore_database()


@database_app.command()
def vacuum():
    """Run VACUUM to optimize database performance."""
    
    @async_command
    async def _vacuum_database():
        try:
            info_message("Running database VACUUM...")
            
            # VACUUM cannot run inside a transaction, so we need a direct connection
            from ..database import engine
            
            # Run VACUUM on main tables
            tables_to_vacuum = [
                "users", "documents", "document_chunks", 
                "conversations", "messages"
            ]
            
            async with engine.connect() as conn:
                # Check which tables exist first
                for table_name in tables_to_vacuum:
                    try:
                        # Check if table exists
                        exists_result = await conn.execute(text("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_name = :table_name
                            )
                        """), {"table_name": table_name})
                        
                        if exists_result.scalar():
                            # Execute VACUUM outside of transaction
                            await conn.execute(text("COMMIT"))  # End any existing transaction
                            await conn.execute(text(f'VACUUM ANALYZE "{table_name}"'))
                            info_message(f"Vacuumed table: {table_name}")
                        else:
                            warning_message(f"Table not found: {table_name}")
                            
                    except Exception as e:
                        warning_message(f"Failed to vacuum {table_name}: {e}")
            
            success_message("Database VACUUM completed")
                
        except Exception as e:
            error_message(f"Database VACUUM failed: {e}")
    
    _vacuum_database()


@database_app.command()
def analyze():
    """Analyze database and show performance statistics."""
    
    @async_command
    async def _analyze_database():
        try:
            async with AsyncSessionLocal() as db:
                # Database size analysis (PostgreSQL specific)
                db_name = settings.database_url.split('/')[-1].split('?')[0]
                size_query = text("""
                    SELECT 
                        pg_size_pretty(pg_database_size(:db_name)) as total_size,
                        pg_database_size(:db_name) as size_bytes
                """)
                size_result = await db.execute(size_query, {"db_name": db_name})
                size_data = size_result.fetchone()
                
                # Table sizes (PostgreSQL specific)
                # PostgreSQL specific
                table_sizes = await db.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """))
                
                # Index usage statistics (PostgreSQL specific)  
                index_stats = await db.execute(text("""
                    SELECT 
                        schemaname,
                        relname as tablename,
                        indexrelname as indexname,
                        idx_scan as scans,
                        pg_size_pretty(pg_relation_size(indexrelid)) as size
                    FROM pg_stat_user_indexes 
                    ORDER BY idx_scan DESC
                    LIMIT 10
                """))
                
                # Display results
                db_name = settings.database_url.split('/')[-1].split('?')[0]
                console.print(f"[bold]Database Analysis for: {db_name}[/bold]")
                console.print(f"Total Size: {size_data[0] if size_data else 'Unknown'}")
                
                # Table sizes table
                table_table = Table(title="Table Sizes")
                table_table.add_column("Table", style="cyan", width=20)
                table_table.add_column("Size", style="green", width=12)
                table_table.add_column("% of Total", style="yellow", width=10)
                
                total_db_size = size_data[1] if size_data else 1
                for row in table_sizes.fetchall():
                    schema, table_name, size_pretty, size_bytes = row
                    percentage = (size_bytes / total_db_size) * 100 if total_db_size > 0 else 0
                    table_table.add_row(table_name, size_pretty, f"{percentage:.1f}%")
                
                console.print(table_table)
                
                # Index usage table
                index_table = Table(title="Top Index Usage")
                index_table.add_column("Table", style="cyan", width=20)
                index_table.add_column("Index", style="green", width=25)
                index_table.add_column("Scans", style="yellow", width=10)
                index_table.add_column("Size", style="blue", width=10)
                
                for row in index_stats.fetchall():
                    schema, table_name, index_name, scans, size = row
                    index_table.add_row(table_name, index_name, str(scans), size)
                
                console.print(index_table)
                
                # Connection statistics
                conn_stats = await db.execute(text("""
                    SELECT 
                        state,
                        count(*) as count
                    FROM pg_stat_activity 
                    WHERE datname = current_database()
                    GROUP BY state
                """))
                
                console.print("\n[bold]Connection Statistics:[/bold]")
                for state, count in conn_stats.fetchall():
                    console.print(f"  {state or 'unknown'}: {count}")
                
        except Exception as e:
            error_message(f"Database analysis failed: {e}")
    
    _analyze_database()


@database_app.command()
def query(
    sql: str = typer.Argument(..., help="SQL query to execute"),
    limit: int = typer.Option(100, "--limit", "-l", help="Limit results (for SELECT queries)"),
):
    """Execute a custom SQL query."""
    
    @async_command
    async def _execute_query():
        try:
            async with AsyncSessionLocal() as db:
                # Safety check - only allow SELECT queries
                query_lower = sql.strip().lower()
                if not query_lower.startswith('select'):
                    error_message("Only SELECT queries are allowed for safety")
                    return
                
                # Add LIMIT if not present
                if 'limit' not in query_lower and limit:
                    sql_with_limit = f"{sql} LIMIT {limit}"
                else:
                    sql_with_limit = sql
                
                info_message(f"Executing query: {sql_with_limit}")
                
                result = await db.execute(text(sql_with_limit))
                rows = result.fetchall()
                
                if not rows:
                    warning_message("No results returned")
                    return
                
                # Get column names
                columns = list(result.keys()) if hasattr(result, 'keys') else []
                
                if columns:
                    # Create results table
                    results_table = Table(title=f"Query Results ({len(rows)} rows)")
                    
                    # Add columns
                    for col in columns[:10]:  # Limit to 10 columns for display
                        results_table.add_column(str(col), style="cyan")
                    
                    # Add rows
                    for row in rows[:50]:  # Limit to 50 rows for display
                        row_values = [str(value)[:50] + "..." if len(str(value)) > 50 else str(value) 
                                    for value in row[:10]]
                        results_table.add_row(*row_values)
                    
                    console.print(results_table)
                    
                    if len(rows) > 50:
                        info_message(f"Showing first 50 of {len(rows)} rows")
                else:
                    # Simple text output
                    for i, row in enumerate(rows[:20], 1):
                        console.print(f"Row {i}: {row}")
                
        except Exception as e:
            error_message(f"Query execution failed: {e}")
    
    _execute_query()