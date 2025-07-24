"Command-line interface for database management."

import os
import subprocess
from datetime import datetime
import typer
from rich.table import Table
from sqlalchemy import text
from ..config import settings
from ..database import AsyncSessionLocal
from .base import (
    async_command,
    console,
    error_message,
    info_message,
    success_message,
    warning_message,
)

database_app = typer.Typer(help="Database management commands")


@database_app.command()
def init(
    skip_default_data: bool = typer.Option(
        False,
        "--skip-default-data",
        help="Skip creating default prompts, profiles, and servers",
    )
):
    "Init operation."

    @async_command
    async def _init_database():
        "Init Database operation."
        try:
            from ..database import init_db

            (await init_db(with_default_data=(not skip_default_data)))
            success_message("Database initialized successfully")
            if not skip_default_data:
                info_message(
                    "Default data (prompts, profiles, servers) has been created"
                )
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    text(
                        "\n                    SELECT table_name FROM information_schema.tables \n                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'\n                    ORDER BY table_name\n                "
                    )
                )
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
    "Status operation."

    @async_command
    async def _database_status():
        "Database Status operation."
        try:
            async with AsyncSessionLocal() as db:
                (await db.execute(text("SELECT 1")))
                success_message("Database connection: OK")
                db_info = await db.execute(text("SELECT version()"))
                version = db_info.scalar()
                console.print(f"PostgreSQL Version: {version}")
                db_name = settings.database_url.split("/")[(-1)].split("?")[0]
                size_query = text(
                    "\n                    SELECT pg_size_pretty(pg_database_size(:db_name)) as size\n                "
                )
                size_result = await db.execute(size_query, {"db_name": db_name})
                db_size = size_result.scalar()
                console.print(f"Database Size: {db_size}")
                connection_info = await db.execute(
                    text(
                        "\n                    SELECT count(*) as active_connections,\n                           max(backend_start) as oldest_connection\n                    FROM pg_stat_activity \n                    WHERE state = 'active'\n                "
                    )
                )
                conn_data = connection_info.fetchone()
                if conn_data:
                    console.print(f"Active Connections: {conn_data[0]}")
                    console.print(f"Oldest Connection: {(conn_data[1] or 'N/A')}")
                vector_check = await db.execute(
                    text(
                        "\n                    SELECT EXISTS(\n                        SELECT 1 FROM pg_extension WHERE extname = 'vector'\n                    )\n                "
                    )
                )
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
    "Tables operation."

    @async_command
    async def _list_tables():
        "List Tables operation."
        try:
            async with AsyncSessionLocal() as db:
                tables_query = text(
                    "\n                    SELECT \n                        t.table_name,\n                        COALESCE(c.column_count, 0) as column_count,\n                        pg_size_pretty(pg_total_relation_size(quote_ident(t.table_name)::regclass)) as size\n                    FROM information_schema.tables t\n                    LEFT JOIN (\n                        SELECT table_name, COUNT(*) as column_count\n                        FROM information_schema.columns\n                        WHERE table_schema = 'public'\n                        GROUP BY table_name\n                    ) c ON t.table_name = c.table_name\n                    WHERE t.table_schema = 'public' \n                    AND t.table_type = 'BASE TABLE'\n                    ORDER BY t.table_name\n                "
                )
                result = await db.execute(tables_query)
                tables_info = result.fetchall()
                if not tables_info:
                    warning_message("No tables found")
                    return
                table = Table(title="Database Tables")
                table.add_column("Table Name", style="cyan", width=25)
                table.add_column("Columns", style="green", width=10)
                table.add_column("Rows", style="yellow", width=12)
                table.add_column("Size", style="blue", width=12)
                table.add_column("Description", style="dim", width=30)
                descriptions = {
                    "users": "User accounts and profiles",
                    "documents": "Uploaded documents metadata",
                    "document_chunks": "Document text chunks with embeddings",
                    "conversations": "Chat conversation sessions",
                    "messages": "Individual chat messages",
                    "alembic_version": "Database migration tracking",
                }
                total_rows = 0
                for table_name, col_count, size in tables_info:
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
                        (str(row_count) if (row_count != "Error") else row_count),
                        size,
                        description,
                    )
                console.print(table)
                console.print(
                    f"""
[bold]Total rows across all tables:[/bold] {total_rows:,}"""
                )
        except Exception as e:
            error_message(f"Failed to list tables: {e}")

    _list_tables()


@database_app.command()
def migrations():
    "Migrations operation."

    @async_command
    async def _migration_status():
        "Migration Status operation."
        try:
            import os

            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            result = subprocess.run(
                ["alembic", "--help"], capture_output=True, text=True, cwd=project_root
            )
            if result.returncode != 0:
                error_message(
                    "Alembic not available. Install with: pip install alembic"
                )
                return
            current_revision = ""
            current_result = subprocess.run(
                ["alembic", "current"], capture_output=True, text=True, cwd=project_root
            )
            if current_result.returncode == 0:
                current_revision = current_result.stdout.strip()
                if current_revision:
                    success_message(f"Current migration: {current_revision}")
                else:
                    warning_message("No migrations applied")
            else:
                warning_message("Could not get current migration status")
            history_result = subprocess.run(
                ["alembic", "history"], capture_output=True, text=True, cwd=project_root
            )
            if (history_result.returncode == 0) and history_result.stdout.strip():
                console.print("\n[bold]Migration History:[/bold]")
                console.print(history_result.stdout)
            else:
                info_message("No migration history available")
            heads_result = subprocess.run(
                ["alembic", "heads"], capture_output=True, text=True, cwd=project_root
            )
            if heads_result.returncode == 0:
                latest_revision = heads_result.stdout.strip()
                if (
                    (
                        latest_revision
                        and (latest_revision != current_revision.split()[0])
                    )
                    if current_revision
                    else ""
                ):
                    warning_message(f"Pending migration available: {latest_revision}")
                    info_message("Run 'manage database upgrade' to apply")
        except Exception as e:
            error_message(f"Failed to check migration status: {e}")

    _migration_status()


@database_app.command()
def upgrade(
    revision: str = typer.Option(
        "head", "--revision", "-r", help="Target revision (default: head)"
    )
):
    "Upgrade operation."

    def _upgrade_database():
        "Upgrade Database operation."
        try:
            import os

            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            info_message(f"Running database migrations to {revision}...")
            result = subprocess.run(
                ["alembic", "upgrade", revision],
                capture_output=True,
                text=True,
                cwd=project_root,
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
    "Downgrade operation."

    def _downgrade_database():
        "Downgrade Database operation."
        try:
            if not force:
                from rich.prompt import Confirm

                if not Confirm.ask(
                    f"Are you sure you want to downgrade to revision {revision}? This may cause data loss."
                ):
                    warning_message("Downgrade cancelled")
                    return
            import os

            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            info_message(f"Downgrading database to {revision}...")
            result = subprocess.run(
                ["alembic", "downgrade", revision],
                capture_output=True,
                text=True,
                cwd=project_root,
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
    schema_only: bool = typer.Option(
        False, "--schema-only", help="Backup schema only (no data)"
    ),
    data_only: bool = typer.Option(
        False, "--data-only", help="Backup data only (no schema)"
    ),
):
    "Backup operation."

    def _backup_database():
        "Backup Database operation."
        try:
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_type = (
                    "schema" if schema_only else ("data" if data_only else "full")
                )
                filename = f"backup_{backup_type}_{timestamp}.sql"
            else:
                filename = output_file
            db_url = settings.database_url
            if "postgresql" in db_url:
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
                cmd.append(parsed.path[1:])
                env = os.environ.copy()
                if parsed.password:
                    env["PGPASSWORD"] = parsed.password
                info_message(f"Creating database backup: {filename}")
                result = subprocess.run(cmd, capture_output=True, text=True, env=env)
                if result.returncode == 0:
                    success_message(f"Backup created successfully: {filename}")
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
    "Restore operation."

    def _restore_database():
        "Restore Database operation."
        try:
            if not os.path.exists(backup_file):
                error_message(f"Backup file not found: {backup_file}")
                return
            if not force:
                from rich.prompt import Confirm

                if not Confirm.ask(
                    f"Are you sure you want to restore from {backup_file}? This will overwrite existing data."
                ):
                    warning_message("Restore cancelled")
                    return
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
                cmd.append(parsed.path[1:])
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
    "Vacuum operation."

    @async_command
    async def _vacuum_database():
        "Vacuum Database operation."
        try:
            info_message("Running database VACUUM...")
            from ..database import engine

            async with engine.connect() as conn:
                tables_result = await conn.execute(
                    text(
                        "\n                    SELECT table_name \n                    FROM information_schema.tables \n                    WHERE table_schema = 'public' \n                    AND table_type = 'BASE TABLE'\n                    AND table_name != 'alembic_version'\n                    ORDER BY table_name\n                "
                    )
                )
                all_tables = [row[0] for row in tables_result.fetchall()]
                if not all_tables:
                    warning_message("No user tables found to vacuum")
                    return
                info_message(
                    f"Found {len(all_tables)} tables to vacuum: {', '.join(all_tables)}"
                )
                vacuumed_count = 0
                for table_name in all_tables:
                    try:
                        (await conn.execute(text("COMMIT")))
                        (await conn.execute(text(f'VACUUM ANALYZE "{table_name}"')))
                        info_message(f"Vacuumed table: {table_name}")
                        vacuumed_count += 1
                    except Exception as e:
                        warning_message(f"Failed to vacuum {table_name}: {e}")
            success_message(
                f"Database VACUUM completed - {vacuumed_count}/{len(all_tables)} tables processed"
            )
        except Exception as e:
            error_message(f"Database VACUUM failed: {e}")

    _vacuum_database()


@database_app.command()
def analyze():
    "Analyze operation."

    @async_command
    async def _analyze_database():
        "Analyze Database operation."
        try:
            async with AsyncSessionLocal() as db:
                db_name = settings.database_url.split("/")[(-1)].split("?")[0]
                size_query = text(
                    "\n                    SELECT \n                        pg_size_pretty(pg_database_size(:db_name)) as total_size,\n                        pg_database_size(:db_name) as size_bytes\n                "
                )
                size_result = await db.execute(size_query, {"db_name": db_name})
                size_data = size_result.fetchone()
                table_sizes = await db.execute(
                    text(
                        "\n                    SELECT \n                        schemaname,\n                        tablename,\n                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,\n                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes\n                    FROM pg_tables \n                    WHERE schemaname = 'public'\n                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC\n                "
                    )
                )
                index_stats = await db.execute(
                    text(
                        "\n                    SELECT \n                        schemaname,\n                        relname as tablename,\n                        indexrelname as indexname,\n                        idx_scan as scans,\n                        pg_size_pretty(pg_relation_size(indexrelid)) as size\n                    FROM pg_stat_user_indexes \n                    ORDER BY idx_scan DESC\n                    LIMIT 10\n                "
                    )
                )
                db_name = settings.database_url.split("/")[(-1)].split("?")[0]
                console.print(f"[bold]Database Analysis for: {db_name}[/bold]")
                console.print(
                    f"Total Size: {(size_data[0] if size_data else 'Unknown')}"
                )
                table_table = Table(title="Table Sizes")
                table_table.add_column("Table", style="cyan", width=20)
                table_table.add_column("Size", style="green", width=12)
                table_table.add_column("% of Total", style="yellow", width=10)
                total_db_size = size_data[1] if size_data else 1
                for row in table_sizes.fetchall():
                    (schema, table_name, size_pretty, size_bytes) = row
                    percentage = (
                        ((size_bytes / total_db_size) * 100)
                        if (total_db_size > 0)
                        else 0
                    )
                    table_table.add_row(table_name, size_pretty, f"{percentage:.1f}%")
                console.print(table_table)
                index_table = Table(title="Top Index Usage")
                index_table.add_column("Table", style="cyan", width=20)
                index_table.add_column("Index", style="green", width=25)
                index_table.add_column("Scans", style="yellow", width=10)
                index_table.add_column("Size", style="blue", width=10)
                for row in index_stats.fetchall():
                    (schema, table_name, index_name, scans, size) = row
                    index_table.add_row(table_name, index_name, str(scans), size)
                console.print(index_table)
                conn_stats = await db.execute(
                    text(
                        "\n                    SELECT \n                        state,\n                        count(*) as count\n                    FROM pg_stat_activity \n                    WHERE datname = current_database()\n                    GROUP BY state\n                "
                    )
                )
                console.print("\n[bold]Connection Statistics:[/bold]")
                for state, count in conn_stats.fetchall():
                    console.print(f"  {(state or 'unknown')}: {count}")
        except Exception as e:
            error_message(f"Database analysis failed: {e}")

    _analyze_database()


@database_app.command()
def query(
    sql: str = typer.Argument(..., help="SQL query to execute"),
    limit: int = typer.Option(
        100, "--limit", "-l", help="Limit results (for SELECT queries)"
    ),
):
    "Query operation."

    @async_command
    async def _execute_query():
        "Execute Query operation."
        try:
            async with AsyncSessionLocal() as db:
                query_lower = sql.strip().lower()
                if not query_lower.startswith("select"):
                    error_message("Only SELECT queries are allowed for safety")
                    return
                if ("limit" not in query_lower) and limit:
                    sql_with_limit = f"{sql} LIMIT {limit}"
                else:
                    sql_with_limit = sql
                info_message(f"Executing query: {sql_with_limit}")
                result = await db.execute(text(sql_with_limit))
                rows = result.fetchall()
                if not rows:
                    warning_message("No results returned")
                    return
                columns = list(result.keys()) if hasattr(result, "keys") else []
                if columns:
                    results_table = Table(title=f"Query Results ({len(rows)} rows)")
                    for col in columns[:10]:
                        results_table.add_column(str(col), style="cyan")
                    for row in rows[:50]:
                        row_values = [
                            (
                                (str(value)[:50] + "...")
                                if (len(str(value)) > 50)
                                else str(value)
                            )
                            for value in row[:10]
                        ]
                        results_table.add_row(*row_values)
                    console.print(results_table)
                    if len(rows) > 50:
                        info_message(f"Showing first 50 of {len(rows)} rows")
                else:
                    for i, row in enumerate(rows[:20], 1):
                        console.print(f"Row {i}: {row}")
        except Exception as e:
            error_message(f"Query execution failed: {e}")

    _execute_query()
