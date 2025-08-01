"""
Database management API endpoints.

This module provides endpoints for database administration, migration management,
backup operations, and maintenance tasks.

Key Features:
- Database initialization and schema management
- Migration execution and status monitoring
- Backup and restore operations
- Database maintenance and optimization
- Custom query execution for administration
- Performance analysis and statistics

Security:
- All operations require superuser access
- Backup/restore operations are logged and audited
- Query execution has built-in safety checks
"""

import os
import subprocess
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..dependencies import get_current_superuser
from ..models.user import User
from ..schemas.common import BaseResponse
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["database"])


@router.post("/init", response_model=BaseResponse)
@handle_api_errors("Failed to initialize database")
async def initialize_database(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Initialize the database and create all tables.

    This endpoint runs the initial database setup including:
    - Creating all tables from SQLAlchemy models
    - Setting up indexes and constraints
    - Installing required extensions (e.g., pgvector)

    Requires superuser access.
    """
    log_api_call("initialize_database", user_id=str(current_user.id))

    try:
        # Import models to ensure they're registered
        # Create all tables
        from ..database import engine
        from ..models import base

        async with engine.begin() as conn:
            # Install pgvector extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

            # Create all tables
            await conn.run_sync(base.BaseModelDB.metadata.create_all)

        return {
            "success": True,
            "message": "Database initialized successfully",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database initialization failed: {str(e)}",
        )


@router.get("/status", response_model=Dict[str, Any])
@handle_api_errors("Failed to get database status")
async def get_database_status(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Get database connection status and basic information.

    Returns information about database connectivity, version,
    installed extensions, and basic configuration.
    """
    log_api_call("get_database_status", user_id=str(current_user.id))

    try:
        # Test connection
        await db.execute(text("SELECT 1"))
        connection_status = "connected"

        # Get database version
        version_result = await db.execute(text("SELECT version()"))
        db_version = version_result.scalar()

        # Check pgvector extension
        vector_check = await db.execute(
            text(
                """
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'vector'
            )
        """
            )
        )
        pgvector_installed = vector_check.scalar()

        # Get database size
        size_result = await db.execute(
            text(
                """
            SELECT pg_size_pretty(pg_database_size(current_database()))
        """
            )
        )
        db_size = size_result.scalar()

        # Get table count
        table_count_result = await db.execute(
            text(
                """
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """
            )
        )
        table_count = table_count_result.scalar()

        return {
            "success": True,
            "data": {
                "connection_status": connection_status,
                "database_version": db_version,
                "database_size": db_size,
                "table_count": table_count,
                "pgvector_installed": pgvector_installed,
                "database_url": (
                    settings.database_url.split("@")[-1]
                    if settings.database_url
                    else "Not configured"
                ),
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    except Exception as e:
        return {
            "success": False,
            "data": {
                "connection_status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        }


@router.get("/tables", response_model=Dict[str, Any])
@handle_api_errors("Failed to list database tables")
async def list_database_tables(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    List all database tables with row counts.

    Returns information about all tables in the database including
    their row counts and basic statistics.
    """
    log_api_call("list_database_tables", user_id=str(current_user.id))

    try:
        # Get table information with row counts
        tables_result = await db.execute(
            text(
                """
            SELECT 
                schemaname,
                tablename,
                n_live_tup as row_count,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_stat_user_tables 
            ORDER BY n_live_tup DESC
        """
            )
        )

        tables = []
        for row in tables_result.fetchall():
            tables.append(
                {
                    "schema": row.schemaname,
                    "name": row.tablename,
                    "row_count": row.row_count,
                    "size": row.size,
                }
            )

        return {
            "success": True,
            "data": {
                "tables": tables,
                "total_tables": len(tables),
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tables: {str(e)}",
        )


@router.get("/migrations", response_model=Dict[str, Any])
@handle_api_errors("Failed to get migration status")
async def get_migration_status(
    current_user: User = Depends(get_current_superuser),
):
    """
    Get migration status and available migrations.

    Returns information about the current migration state and
    available migrations that can be applied.
    """
    log_api_call("get_migration_status", user_id=str(current_user.id))

    try:
        # Run alembic command to get current revision
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        )

        current_revision = (
            result.stdout.strip() if result.returncode == 0 else "Unknown"
        )

        # Get available migrations
        heads_result = subprocess.run(
            ["alembic", "heads"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        )

        available_heads = (
            heads_result.stdout.strip() if heads_result.returncode == 0 else "Unknown"
        )

        # Get migration history
        history_result = subprocess.run(
            ["alembic", "history", "--verbose"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        )

        migration_history = (
            history_result.stdout
            if history_result.returncode == 0
            else "Unable to retrieve history"
        )

        return {
            "success": True,
            "data": {
                "current_revision": current_revision,
                "available_heads": available_heads,
                "migration_history": migration_history.split("\n")[
                    :10
                ],  # Last 10 entries
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get migration status: {str(e)}",
        )


@router.post("/upgrade", response_model=BaseResponse)
@handle_api_errors("Failed to upgrade database")
async def upgrade_database(
    revision: str = Query("head", description="Target revision (default: head)"),
    current_user: User = Depends(get_current_superuser),
):
    """
    Run database migrations to upgrade schema.

    Executes Alembic migrations to bring the database schema
    up to the specified revision or latest if not specified.

    Args:
        revision: Target revision to upgrade to (default: head)
    """
    log_api_call("upgrade_database", user_id=str(current_user.id), revision=revision)

    try:
        # Run alembic upgrade
        result = subprocess.run(
            ["alembic", "upgrade", revision],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Migration failed: {result.stderr}",
            )

        return {
            "success": True,
            "message": f"Database upgraded to revision: {revision}",
            "output": result.stdout,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except subprocess.SubprocessError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration execution failed: {str(e)}",
        )


@router.post("/downgrade", response_model=BaseResponse)
@handle_api_errors("Failed to downgrade database")
async def downgrade_database(
    revision: str = Query(..., description="Target revision to downgrade to"),
    current_user: User = Depends(get_current_superuser),
):
    """
    Downgrade database to a previous migration.

    CAUTION: This operation may result in data loss.
    Always create a backup before downgrading.

    Args:
        revision: Target revision to downgrade to
    """
    log_api_call("downgrade_database", user_id=str(current_user.id), revision=revision)

    try:
        # Run alembic downgrade
        result = subprocess.run(
            ["alembic", "downgrade", revision],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Downgrade failed: {result.stderr}",
            )

        return {
            "success": True,
            "message": f"Database downgraded to revision: {revision}",
            "output": result.stdout,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except subprocess.SubprocessError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Downgrade execution failed: {str(e)}",
        )


@router.post("/backup", response_model=BaseResponse)
@handle_api_errors("Failed to create database backup")
async def create_database_backup(
    output_file: Optional[str] = Query(
        None, description="Output file path (auto-generated if not provided)"
    ),
    schema_only: bool = Query(False, description="Backup schema only (no data)"),
    current_user: User = Depends(get_current_superuser),
):
    """
    Create a database backup.

    Creates a PostgreSQL dump of the database for backup purposes.

    Args:
        output_file: Output file path (auto-generated if not provided)
        schema_only: Whether to backup schema only (no data)
    """
    log_api_call("create_database_backup", user_id=str(current_user.id))

    if not output_file:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = f"backup_{timestamp}.sql"

    try:
        # Parse database URL to get connection parameters
        import urllib.parse

        parsed = urllib.parse.urlparse(settings.database_url)

        # Build pg_dump command
        cmd = [
            "pg_dump",
            "-h",
            parsed.hostname or "localhost",
            "-p",
            str(parsed.port or 5432),
            "-U",
            parsed.username or "postgres",
            "-d",
            parsed.path.lstrip("/") if parsed.path else "ai_chatbot",
            "-f",
            output_file,
            "--verbose",
        ]

        if schema_only:
            cmd.append("--schema-only")

        # Set password via environment variable
        env = os.environ.copy()
        if parsed.password:
            env["PGPASSWORD"] = parsed.password

        # Run pg_dump
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Backup failed: {result.stderr}",
            )

        # Get file size
        file_size = os.path.getsize(output_file) if os.path.exists(output_file) else 0

        return {
            "success": True,
            "message": "Database backup created successfully",
            "output_file": output_file,
            "file_size": f"{file_size / 1024 / 1024:.2f} MB",
            "schema_only": schema_only,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup creation failed: {str(e)}",
        )


@router.post("/restore", response_model=BaseResponse)
@handle_api_errors("Failed to restore database")
async def restore_database(
    backup_file: str = Query(..., description="Backup file path to restore from"),
    current_user: User = Depends(get_current_superuser),
):
    """
    Restore database from a backup file.

    CAUTION: This operation will overwrite existing data.
    Ensure you have a current backup before proceeding.

    Args:
        backup_file: Path to the backup file to restore from
    """
    log_api_call(
        "restore_database", user_id=str(current_user.id), backup_file=backup_file
    )

    if not os.path.exists(backup_file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Backup file not found: {backup_file}",
        )

    try:
        # Parse database URL
        import urllib.parse

        parsed = urllib.parse.urlparse(settings.database_url)

        # Build psql command
        cmd = [
            "psql",
            "-h",
            parsed.hostname or "localhost",
            "-p",
            str(parsed.port or 5432),
            "-U",
            parsed.username or "postgres",
            "-d",
            parsed.path.lstrip("/") if parsed.path else "ai_chatbot",
            "-f",
            backup_file,
            "--verbose",
        ]

        # Set password via environment variable
        env = os.environ.copy()
        if parsed.password:
            env["PGPASSWORD"] = parsed.password

        # Run psql
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Restore failed: {result.stderr}",
            )

        return {
            "success": True,
            "message": f"Database restored successfully from {backup_file}",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Restore operation failed: {str(e)}",
        )


@router.post("/vacuum", response_model=BaseResponse)
@handle_api_errors("Failed to vacuum database")
async def vacuum_database(
    analyze: bool = Query(True, description="Run ANALYZE after VACUUM"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Run VACUUM to optimize database performance.

    Performs database maintenance to reclaim storage and update
    statistics for the query planner.

    Args:
        analyze: Whether to run ANALYZE after VACUUM
    """
    log_api_call("vacuum_database", user_id=str(current_user.id), analyze=analyze)

    try:
        if analyze:
            await db.execute(text("VACUUM ANALYZE"))
            message = "Database VACUUM ANALYZE completed successfully"
        else:
            await db.execute(text("VACUUM"))
            message = "Database VACUUM completed successfully"

        await db.commit()

        return {
            "success": True,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"VACUUM operation failed: {str(e)}",
        )


@router.get("/analyze", response_model=Dict[str, Any])
@handle_api_errors("Failed to analyze database")
async def analyze_database(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze database and show performance statistics.

    Returns detailed performance statistics and analysis
    of the database including table sizes, index usage,
    and query performance metrics.
    """
    log_api_call("analyze_database", user_id=str(current_user.id))

    try:
        # Get table sizes
        table_sizes = await db.execute(
            text(
                """
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_stat_user_tables 
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 10
        """
            )
        )

        largest_tables = []
        for row in table_sizes.fetchall():
            largest_tables.append(
                {
                    "schema": row.schemaname,
                    "table": row.tablename,
                    "size": row.size,
                    "size_bytes": row.size_bytes,
                }
            )

        # Get index usage statistics
        index_stats = await db.execute(
            text(
                """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes 
            ORDER BY idx_scan DESC
            LIMIT 10
        """
            )
        )

        index_usage = []
        for row in index_stats.fetchall():
            index_usage.append(
                {
                    "schema": row.schemaname,
                    "table": row.tablename,
                    "index": row.indexname,
                    "scans": row.idx_scan,
                    "tuples_read": row.idx_tup_read,
                    "tuples_fetched": row.idx_tup_fetch,
                }
            )

        # Get database statistics
        db_stats = await db.execute(
            text(
                """
            SELECT 
                numbackends,
                xact_commit,
                xact_rollback,
                blks_read,
                blks_hit,
                tup_returned,
                tup_fetched,
                tup_inserted,
                tup_updated,
                tup_deleted
            FROM pg_stat_database 
            WHERE datname = current_database()
        """
            )
        )

        stats_row = db_stats.first()
        database_stats = {
            "active_connections": stats_row.numbackends,
            "committed_transactions": stats_row.xact_commit,
            "rolled_back_transactions": stats_row.xact_rollback,
            "disk_blocks_read": stats_row.blks_read,
            "buffer_hits": stats_row.blks_hit,
            "tuples_returned": stats_row.tup_returned,
            "tuples_fetched": stats_row.tup_fetched,
            "tuples_inserted": stats_row.tup_inserted,
            "tuples_updated": stats_row.tup_updated,
            "tuples_deleted": stats_row.tup_deleted,
        }

        # Calculate cache hit ratio
        total_reads = stats_row.blks_read + stats_row.blks_hit
        cache_hit_ratio = (stats_row.blks_hit / max(total_reads, 1)) * 100

        return {
            "success": True,
            "data": {
                "largest_tables": largest_tables,
                "index_usage": index_usage,
                "database_statistics": database_stats,
                "performance_metrics": {
                    "cache_hit_ratio": round(cache_hit_ratio, 2),
                    "transaction_success_rate": round(
                        (
                            stats_row.xact_commit
                            / max(stats_row.xact_commit + stats_row.xact_rollback, 1)
                        )
                        * 100,
                        2,
                    ),
                },
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database analysis failed: {str(e)}",
        )


@router.post("/query", response_model=Dict[str, Any])
@handle_api_errors("Failed to execute query")
async def execute_custom_query(
    query: str = Query(..., description="SQL query to execute"),
    limit: int = Query(
        100, ge=1, le=1000, description="Result limit for SELECT queries"
    ),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute a custom SQL query.

    CAUTION: This endpoint allows execution of arbitrary SQL.
    Use with extreme care and only for administrative purposes.

    Args:
        query: SQL query to execute
        limit: Result limit for SELECT queries
    """
    log_api_call("execute_custom_query", user_id=str(current_user.id))

    # Safety checks
    dangerous_keywords = [
        "DROP",
        "DELETE",
        "TRUNCATE",
        "ALTER",
        "CREATE",
        "INSERT",
        "UPDATE",
    ]
    query_upper = query.upper().strip()

    # Only allow SELECT queries for safety
    if not query_upper.startswith("SELECT"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only SELECT queries are allowed for safety reasons",
        )

    # Check for dangerous keywords in comments or strings
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Query contains potentially dangerous keyword: {keyword}",
            )

    try:
        # Add LIMIT if not present
        if "LIMIT" not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {limit}"

        # Execute query
        result = await db.execute(text(query))

        # Get results
        rows = result.fetchall()
        columns = result.keys() if result.keys() else []

        # Convert to list of dictionaries
        data = []
        for row in rows:
            data.append(dict(zip(columns, row)))

        return {
            "success": True,
            "data": {
                "query": query,
                "columns": list(columns),
                "rows": data,
                "row_count": len(data),
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}",
        )
