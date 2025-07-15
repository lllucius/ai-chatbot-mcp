"""
Database configuration and session management.

This module provides async database connection management, session creation,
and database initialization utilities.
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

from .config import settings
from .models.base import BaseModelDB

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600  # Recycle connections every hour
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Yields:
        AsyncSession: Database session for request scope
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database and create all tables.
    
    This function creates all tables and enables pgvector extension.
    """
    #try:
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        

        import sqlalchemy    
        print("TABLES", BaseModelDB.metadata.tables.keys())
        
        # Create all tables
        await conn.run_sync(BaseModelDB.metadata.create_all)
        logger.info("Database initialized successfully")
        
#    except Exception as e:
#        logger.error(f"Failed to initialize database: {e}")
#        raise


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")
