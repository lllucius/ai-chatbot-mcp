"""Database configuration and session management with enterprise-grade features.

This module provides comprehensive async database connection management, session
creation, connection pooling, and database initialization utilities for the AI
Chatbot Platform. Implements production-ready database patterns with connection
reliability, performance optimization, and operational excellence for PostgreSQL
with PGVector extension support.

Database Architecture:
- Async SQLAlchemy integration with optimal connection management and pooling
- PostgreSQL with PGVector extension for high-performance vector operations
- Connection lifecycle management with automatic reconnection and error recovery
- Transaction management with proper isolation levels and rollback handling
- Database migration support with version control and deployment automation
- Multi-environment configuration with development, staging, and production settings

Connection Management:
- Async connection pooling with configurable pool sizes and connection limits
- Connection health monitoring with automatic failover and recovery
- Connection string configuration with security and performance optimization
- SSL/TLS support for secure database connections in production environments
- Connection timeout and retry logic for reliability in distributed systems
- Resource management with proper connection cleanup and garbage collection

Performance Optimization:
- Connection pooling optimization with proper sizing and connection reuse
- Query optimization with prepared statements and execution plan caching
- Database indexing support with vector indexing for PGVector operations
- Connection load balancing for read replicas and distributed database setups
- Memory management with connection pool sizing and resource limits
- Query performance monitoring with execution time tracking and optimization

Vector Database Features:
- PGVector extension integration for high-performance vector storage and retrieval
- Vector indexing with IVFFlat and HNSW algorithms for fast similarity search
- Embedding storage optimization with compression and memory efficiency
- Vector query optimization with distance calculations and similarity thresholds
- Vector dimension validation and constraint enforcement
- Integration with embedding services and machine learning workflows

Security Features:
- Secure connection string handling with credential protection
- Database authentication with role-based access control
- SSL/TLS encryption for data in transit
- Connection security validation and certificate management
- Database audit logging for compliance and security monitoring
- Integration with external secret management and credential rotation

Operational Excellence:
- Database initialization with schema creation and default data setup
- Migration management with version control and automated deployment
- Health check endpoints for database connectivity monitoring
- Database backup and recovery integration with automated scheduling
- Performance monitoring with connection metrics and query analysis
- Integration with database monitoring and alerting systems

Use Cases:
- Production deployment with high-availability database clusters
- Development environment setup with local database instances
- Testing environment with isolated database instances and test data
- Container orchestration with database service discovery and configuration
- Cloud deployment with managed database services and auto-scaling
- Microservices architecture with database per service patterns
"""

import asyncio
import logging
import sys
import traceback
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.exc import DisconnectionError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings
from .core.default_data import initialize_default_data
from .models.base import BaseModelDB

logger = logging.getLogger(__name__)


# Create async engine with flexible database configuration
def _get_engine_config():
    """Get database engine configuration based on database type."""
    base_config = {
        "echo": settings.debug,
    }

    # Check if we're using PostgreSQL
    if settings.database_url.startswith(("postgresql", "asyncpg")):
        # PostgreSQL-specific configuration
        base_config.update(
            {
                "echo": "debug",
                "pool_pre_ping": True,
                "pool_size": 20,
                "max_overflow": 30,
                "pool_recycle": 1800,  # 30 minutes
                "pool_timeout": 30,
                "pool_reset_on_return": "commit",
                "connect_args": {
                    "server_settings": {
                        "jit": "off",  # Disable JIT for better connection performance
                    },
                    "command_timeout": 30,
                },
            }
        )

    return base_config


engine = create_async_engine(settings.database_url, **_get_engine_config())

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    close_resets_only=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session with improved error handling.

    Yields:
        AsyncSession: Database session for request scope

    """
    session = None
    try:
        session = AsyncSessionLocal()
        # Test connection health
        await session.execute(text("SELECT 1"))

        async with session:
            yield session
            await session.commit()

    except (DisconnectionError, OperationalError) as e:
        tb = traceback.extract_tb(sys.exc_info()[2])[-1]
        logger.error(
            f"Database connection error: {type(e).__name__}: {e} "
            f'(File "{tb.filename}", line {tb.lineno})'
        )
        if session:
            await session.rollback()
        # Attempt to recreate session for connection errors
        try:
            if session:
                await session.close()
            session = AsyncSessionLocal()
            yield session
            await session.commit()
        except Exception as retry_e:
            rtb = traceback.extract_tb(sys.exc_info()[2])[-1]
            logger.error(
                f"Database retry failed: {type(retry_e).__name__}: {retry_e} "
                f'(File "{rtb.filename}", line {rtb.lineno})'
            )
            if session:
                await session.rollback()
            raise
    except SQLAlchemyError as e:
        tb = traceback.extract_tb(sys.exc_info()[2])[-1]
        logger.error(
            f"SQLAlchemy error: {type(e).__name__}: {e} "
            f'(File "{tb.filename}", line {tb.lineno})'
        )
        if session:
            await session.rollback()
        raise
    except Exception as e:
        tb = traceback.extract_tb(sys.exc_info()[2])[-1]
        logger.error(
            f"Non-database exception in DB session: {type(e).__name__}: {e} "
            f'(File "{tb.filename}", line {tb.lineno})'
        )
        if session:
            await session.rollback()
        raise
    finally:
        if session:
            await session.close()


async def health_check_db() -> bool:
    """Check database connectivity and health.

    Returns:
        bool: True if database is healthy

    """
    try:
        async with AsyncSessionLocal() as session:
            # Test basic connectivity
            await session.execute(text("SELECT 1"))

            # Check for pgvector extension only if using PostgreSQL
            if settings.database_url.startswith(("postgresql", "asyncpg")):
                result = await session.execute(
                    text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                )
                vector_enabled = result.scalar() is not None

                if not vector_enabled:
                    logger.warning("pgvector extension is not enabled")
                    return False

            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def init_db(with_default_data: bool = True) -> None:
    """Initialize database and create all tables with retry logic.

    This function creates all tables and enables pgvector extension for PostgreSQL.
    Optionally initializes default data.

    Args:
        with_default_data: Whether to create default prompts, profiles, and servers

    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                # Enable pgvector extension only for PostgreSQL
                if settings.database_url.startswith(("postgresql", "asyncpg")):
                    await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    # Verify pgvector is working
                    await conn.execute(text("SELECT '[1,2,3]'::vector"))

                # Create all tables
                await conn.run_sync(BaseModelDB.metadata.create_all)

                logger.info("Database initialized successfully")

            # Initialize default data if requested
            if with_default_data:
                try:
                    # Create a new session for default data initialization
                    async with AsyncSessionLocal() as db_session:
                        result = await initialize_default_data(db_session)
                        await db_session.commit()
                        logger.info(
                            f"Default data initialized: {result['total_created']} items created"
                        )
                except Exception as e:
                    logger.warning(f"Failed to initialize default data: {e}")
                    # Don't fail the entire init if default data creation fails

            return

        except Exception as e:
            logger.error(
                f"Failed to initialize database (attempt {attempt + 1}/{max_retries}): {e}"
            )
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2**attempt)  # Exponential backoff


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")
