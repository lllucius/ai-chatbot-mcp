"""Database management API endpoints."""

import os
import subprocess
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ExternalServiceError, NotFoundError, ValidationError
from app.database import get_db, get_session
from app.dependencies import get_current_superuser
from app.models.user import User
from app.utils.api_errors import handle_api_errors, log_api_call
from app.utils.timestamp import utcnow
from shared.schemas.base import BaseModelSchema
from shared.schemas.common import APIResponse
from shared.schemas.database import (
    DatabaseAnalysisResponse,
    DatabaseBackupResult,
    DatabaseDowngradeResult,
    DatabaseMigrationsResponse,
    DatabaseQueryResponse,
    DatabaseRestoreResult,
    DatabaseStatusResponse,
    DatabaseTablesResponse,
    DatabaseUpgradeResult,
    VacuumResult,
)

router = APIRouter(tags=["database"])


@router.post("/init", response_model=APIResponse[BaseModelSchema])
@handle_api_errors("Failed to initialize database")
async def initialize_database(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[BaseModelSchema]:
    """Initialize the database and create all tables with required extensions."""
    log_api_call("initialize_database", user_id=str(current_user.id))

    # Import models to ensure they're registered
    # Create all tables
    from app.database import engine
    from app.models import base

    async with engine.begin() as conn:
        # Install pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Create all tables
        await conn.run_sync(base.BaseModelDB.metadata.create_all)

    payload = BaseModelSchema()
    return APIResponse[BaseModelSchema](
        success=True,
        message="Database initialized successfully",
        data=payload,
    )


@router.get("/status", response_model=APIResponse[DatabaseStatusResponse])
@handle_api_errors("Failed to get database status")
async def get_database_status(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DatabaseStatusResponse]:
    """Get comprehensive database connection status and configuration information."""
    log_api_call("get_database_status", user_id=str(current_user.id))

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

    payload = DatabaseStatusResponse(
        success=True,
        connection_status=connection_status,
        version_info={
            "database_version": db_version,
            "database_size": db_size,
            "database_url": (
                settings.database_url.split("@")[-1]
                if settings.database_url
                else "Not configured"
            ),
        },
        schema_info={
            "table_count": table_count,
            "pgvector_installed": pgvector_installed,
        },
        performance_metrics={},
        timestamp=utcnow(),
    )
    return APIResponse[DatabaseStatusResponse](
        success=True,
        message="Database status retrieved successfully",
        data=payload,
    )


@router.get("/tables", response_model=APIResponse[DatabaseTablesResponse])
@handle_api_errors("Failed to list database tables")
async def list_database_tables(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DatabaseTablesResponse]:
    """List all database tables with comprehensive metadata and statistics."""
    log_api_call("list_database_tables", user_id=str(current_user.id))

    # Get table information with row counts
    tables_result = await db.execute(
        text(
            """
        SELECT
            schemaname,
            relname,
            n_live_tup as row_count,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as size
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
                "name": row.relname,
                "row_count": row.row_count,
                "size": row.size,
            }
        )

    payload = DatabaseTablesResponse(
        success=True,
        tables=tables,
        total_tables=len(tables),
        timestamp=utcnow(),
    )
    return APIResponse[DatabaseTablesResponse](
        success=True,
        message="Database tables listed successfully",
        data=payload,
    )


@router.get("/migrations", response_model=APIResponse[DatabaseMigrationsResponse])
@handle_api_errors("Failed to get migration status")
async def get_migration_status(
    current_user: User = Depends(get_current_superuser),
) -> APIResponse[DatabaseMigrationsResponse]:
    """Get comprehensive database migration status and history."""
    log_api_call("get_migration_status", user_id=str(current_user.id))

    # Run alembic command to get current revision
    result = subprocess.run(
        ["alembic", "current"],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )

    current_revision = result.stdout.strip() if result.returncode == 0 else "Unknown"

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
    subprocess.run(
        ["alembic", "history", "--verbose"],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )

    migration_status = (
        "up_to_date" if current_revision == available_heads else "pending"
    )

    payload = DatabaseMigrationsResponse(
        success=True,
        applied_migrations=[],  # Could be expanded to parse history
        pending_migrations=[],  # Could be expanded to check for pending
        migration_status=migration_status,
        last_migration=(
            {"revision": current_revision, "heads": available_heads}
            if current_revision != "Unknown"
            else None
        ),
        timestamp=utcnow(),
    )
    return APIResponse[DatabaseMigrationsResponse](
        success=True,
        message="Database migration status retrieved successfully",
        data=payload,
    )


@router.post("/upgrade", response_model=APIResponse[DatabaseUpgradeResult])
@handle_api_errors("Failed to upgrade database")
async def upgrade_database(
    revision: str = Query("head", description="Target revision (default: head)"),
    current_user: User = Depends(get_current_superuser),
) -> APIResponse[DatabaseUpgradeResult]:
    """Execute database schema migrations to upgrade to target revision."""
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
            raise ExternalServiceError(f"Migration failed: {result.stderr}")

        payload = DatabaseUpgradeResult(
            output=result.stdout,
            revision=revision,
        )
        return APIResponse[DatabaseUpgradeResult](
            success=True,
            message=f"Database upgraded to revision: {revision}",
            data=payload,
        )
    except subprocess.SubprocessError as e:
        raise ExternalServiceError(f"Migration execution failed: {str(e)}")
    except Exception:
        raise


@router.post("/downgrade", response_model=APIResponse[DatabaseDowngradeResult])
@handle_api_errors("Failed to downgrade database")
async def downgrade_database(
    revision: str = Query(..., description="Target revision to downgrade to"),
    current_user: User = Depends(get_current_superuser),
) -> APIResponse[DatabaseDowngradeResult]:
    """Downgrade database schema to a previous migration revision."""
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
            raise ExternalServiceError(f"Downgrade failed: {result.stderr}")

        payload = DatabaseDowngradeResult(
            output=result.stdout,
            revision=revision,
        )
        return APIResponse[DatabaseDowngradeResult](
            success=True,
            message=f"Database downgraded to revision: {revision}",
            data=payload,
        )
    except subprocess.SubprocessError as e:
        raise ExternalServiceError(f"Downgrade execution failed: {str(e)}")
    except Exception:
        raise


@router.post("/backup", response_model=APIResponse[DatabaseBackupResult])
@handle_api_errors("Failed to create database backup")
async def create_database_backup(
    output_file: Optional[str] = Query(
        None, description="Output file path (auto-generated if not provided)"
    ),
    schema_only: bool = Query(False, description="Backup schema only (no data)"),
    current_user: User = Depends(get_current_superuser),
) -> APIResponse[DatabaseBackupResult]:
    """Create a comprehensive database backup using PostgreSQL dump utilities."""
    log_api_call("create_database_backup", user_id=str(current_user.id))
    print("OUTPUT", output_file)
    if not output_file:
        timestamp = utcnow().strftime("%Y%m%d_%H%M%S")
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
            raise ExternalServiceError(f"Backup failed: {result.stderr}")

        # Get file size
        file_size = os.path.getsize(output_file) if os.path.exists(output_file) else 0

        payload = DatabaseBackupResult(
            output_file=output_file,
            file_size=f"{file_size / 1024 / 1024:.2f} MB",
            schema_only=schema_only,
        )
        return APIResponse[DatabaseBackupResult](
            success=True,
            message="Database backup created successfully",
            data=payload,
        )
    except Exception:
        raise


@router.post("/restore", response_model=APIResponse[DatabaseRestoreResult])
@handle_api_errors("Failed to restore database")
async def restore_database(
    backup_file: str = Query(..., description="Backup file path to restore from"),
    current_user: User = Depends(get_current_superuser),
) -> APIResponse[DatabaseRestoreResult]:
    """Restore database from a backup file with comprehensive data replacement."""
    log_api_call(
        "restore_database", user_id=str(current_user.id), backup_file=backup_file
    )

    if not os.path.exists(backup_file):
        raise NotFoundError(f"Backup file not found: {backup_file}")

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
            raise ExternalServiceError(f"Restore failed: {result.stderr}")

        payload = DatabaseRestoreResult(
            message=f"Database restored successfully from {backup_file}",
            backup_file=backup_file,
        )
        return APIResponse[DatabaseRestoreResult](
            success=True,
            message=f"Database restored successfully from {backup_file}",
            data=payload,
        )
    except Exception:
        raise


@router.post("/vacuum", response_model=APIResponse[VacuumResult])
@handle_api_errors("Failed to vacuum database")
async def vacuum_database(
    analyze: bool = Query(True, description="Run ANALYZE after VACUUM"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_session),
) -> APIResponse[VacuumResult]:
    """Execute database maintenance with VACUUM operations for optimal performance."""
    log_api_call("vacuum_database", user_id=str(current_user.id), analyze=analyze)

    print(dir(db))
    try:
        conn = db.execution_options(isolation_level="AUTOCOMMIT")

        if analyze:
            await conn.execute(text("VACUUM ANALYZE"))
            message = "Database VACUUM ANALYZE completed successfully"
        else:
            await conn.execute(text("VACUUM"))
            message = "Database VACUUM completed successfully"

        await db.commit()

        payload = VacuumResult(
            message=message,
            analyze=analyze,
        )
        return APIResponse[VacuumResult](
            success=True,
            message=message,
            data=payload,
        )
    except Exception:
        await db.rollback()
        raise


@router.get("/analyze", response_model=APIResponse[DatabaseAnalysisResponse])
@handle_api_errors("Failed to analyze database")
async def analyze_database(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DatabaseAnalysisResponse]:
    """Perform comprehensive database analysis with performance insights and recommendations."""
    log_api_call("analyze_database", user_id=str(current_user.id))

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

    payload = DatabaseAnalysisResponse(
        success=True,
        table_stats=largest_tables,
        index_analysis=index_usage,
        performance_insights={
            "cache_hit_ratio": round(cache_hit_ratio, 2),
            "transaction_success_rate": round(
                (
                    stats_row.xact_commit
                    / max(stats_row.xact_commit + stats_row.xact_rollback, 1)
                )
                * 100,
                2,
            ),
            "database_statistics": database_stats,
        },
        recommendations=[],  # Could be populated with actual recommendations
        timestamp=utcnow(),
    )
    return APIResponse[DatabaseAnalysisResponse](
        success=True,
        message="Database analysis completed successfully",
        data=payload,
    )


@router.post("/query", response_model=APIResponse[DatabaseQueryResponse])
@handle_api_errors("Failed to execute query")
async def execute_custom_query(
    query: str = Query(..., description="SQL query to execute"),
    limit: int = Query(
        100, ge=1, le=1000, description="Result limit for SELECT queries"
    ),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DatabaseQueryResponse]:
    """Execute custom SQL queries with comprehensive safety controls and monitoring."""
    log_api_call("execute_custom_query", user_id=str(current_user.id))

    import time

    start_time = time.time()

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
        raise ValidationError("Only SELECT queries are allowed for safety reasons")

    # Check for dangerous keywords in comments or strings
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            raise ValidationError(f"Query contains potentially dangerous keyword: {keyword}")

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

        execution_time_ms = (time.time() - start_time) * 1000

        payload = DatabaseQueryResponse(
            success=True,
            query=query,
            result_type="SELECT",
            rows_affected=len(data),
            execution_time_ms=execution_time_ms,
            results=data,
            timestamp=utcnow(),
        )
        return APIResponse[DatabaseQueryResponse](
            success=True,
            message="Custom query executed successfully",
            data=payload,
        )
    except Exception:
        raise
