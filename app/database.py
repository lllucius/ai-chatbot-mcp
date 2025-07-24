"Database connection and session management."

import asyncio
import logging
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.exc import DisconnectionError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from .config import settings
from .models.base import BaseModelDB

logger = logging.getLogger(__name__)
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=30,
    pool_recycle=1800,
    pool_timeout=30,
    pool_reset_on_return="commit",
    connect_args={"server_settings": {"jit": "off"}, "command_timeout": 30},
)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[(AsyncSession, None)]:
    "Get db data."
    session = None
    try:
        session = AsyncSessionLocal()
        (await session.execute(text("SELECT 1")))
        (yield session)
        (await session.commit())
    except (DisconnectionError, OperationalError) as e:
        logger.error(f"Database connection error: {e}")
        if session:
            (await session.rollback())
        try:
            if session:
                (await session.close())
            session = AsyncSessionLocal()
            (yield session)
            (await session.commit())
        except Exception as retry_e:
            logger.error(f"Database retry failed: {retry_e}")
            if session:
                (await session.rollback())
            raise
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        if session:
            (await session.rollback())
        raise
    except Exception as e:
        logger.error(f"Unexpected database error: {e}")
        if session:
            (await session.rollback())
        raise
    finally:
        if session:
            (await session.close())


async def health_check_db() -> bool:
    "Health Check Db operation."
    try:
        async with AsyncSessionLocal() as session:
            (await session.execute(text("SELECT 1")))
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
    "Init Db operation."
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                (await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector")))
                (await conn.execute(text("SELECT '[1,2,3]'::vector")))
                (await conn.run_sync(BaseModelDB.metadata.create_all))
                logger.info("Database initialized successfully")
                if with_default_data:
                    try:
                        from ..core.default_data import initialize_default_data

                        result = await initialize_default_data()
                        logger.info(
                            f"Default data initialized: {result['total_created']} items created"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to initialize default data: {e}")
                return
        except Exception as e:
            logger.error(
                f"Failed to initialize database (attempt {(attempt + 1)}/{max_retries}): {e}"
            )
            if attempt == (max_retries - 1):
                raise
            (await asyncio.sleep((2**attempt)))


async def close_db() -> None:
    "Close Db operation."
    (await engine.dispose())
    logger.info("Database connections closed")
