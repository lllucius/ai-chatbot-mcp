"Alembic migration environment configuration."

import asyncio
import sys
from pathlib import Path
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

sys.path.append(str(Path(__file__).parent.parent))
from app.config import settings
from app.models import (
    BaseModelDB,
    TimestampMixin,
    UUIDMixin,
    User,
    Document,
    DocumentChunk,
    Conversation,
    Message,
    MCPServer,
    MCPTool,
    Prompt,
    LLMProfile,
)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
target_metadata = None
try:
    from app.database import Base

    target_metadata = Base.metadata
except ImportError:
    target_metadata = None


def get_url():
    "Get url data."
    return settings.database_url


def run_migrations_offline() -> None:
    "Run Migrations Offline operation."
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    "Do Run Migrations operation."
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    "Run Async Migrations operation."
    connectable = create_async_engine(get_url(), poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        (await connection.run_sync(do_run_migrations))
    (await connectable.dispose())


def run_migrations_online() -> None:
    "Run Migrations Online operation."
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
