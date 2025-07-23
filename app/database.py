"""
Database configuration and session management.

This module provides async database connection management, session creation,
and database initialization utilities.
"""

import asyncio
import logging
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.exc import (DisconnectionError, OperationalError,
                            SQLAlchemyError)
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from .config import settings
from .models.base import BaseModelDB

logger = logging.getLogger(__name__)

# Create async engine with PostgreSQL-specific configuration
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=20,  # Increased from 10 for better performance
    max_overflow=30,  # Increased from 20
    pool_recycle=1800,  # Recycle connections every 30 minutes (reduced from 1 hour)
    pool_timeout=30,  # Connection timeout
    pool_reset_on_return="commit",  # Reset connections on return
    connect_args={
        "server_settings": {
            "jit": "off",  # Disable JIT for better connection performance
        },
        "command_timeout": 30,  # Command timeout in seconds
    },
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session with improved error handling.

    Yields:
        AsyncSession: Database session for request scope
    """
    session = None
    try:
        session = AsyncSessionLocal()
        # Test connection health
        await session.execute(text("SELECT 1"))

        yield session
        await session.commit()
    except (DisconnectionError, OperationalError) as e:
        logger.error(f"Database connection error: {e}")
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
            logger.error(f"Database retry failed: {retry_e}")
            if session:
                await session.rollback()
            raise
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        if session:
            await session.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected database error: {e}")
        if session:
            await session.rollback()
        raise
    finally:
        if session:
            await session.close()


async def health_check_db() -> bool:
    """
    Check database connectivity and health.

    Returns:
        bool: True if database is healthy
    """
    try:
        async with AsyncSessionLocal() as session:
            # Test basic connectivity
            await session.execute(text("SELECT 1"))

            # Test pgvector extension for PostgreSQL
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
    """
    Initialize database and create all tables with retry logic.

    This function creates all tables and enables pgvector extension for PostgreSQL.
    Optionally initializes default data.

    Args:
        with_default_data: Whether to create default prompts, profiles, and servers
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                # Enable pgvector extension
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

                # Verify pgvector is working
                await conn.execute(text("SELECT '[1,2,3]'::vector"))

                # Create all tables
                await conn.run_sync(BaseModelDB.metadata.create_all)

                logger.info("Database initialized successfully")

                # Initialize default data if requested
                if with_default_data:
                    try:
                        from ..core.default_data import initialize_default_data

                        result = await initialize_default_data()
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
