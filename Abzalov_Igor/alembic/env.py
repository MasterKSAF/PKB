from __future__ import annotations

from logging.config import fileConfig
import asyncio
import os

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from rag_builder.core.config import build_database_url, settings
from rag_builder.models.db import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_db_url() -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    settings_url = build_database_url(settings)
    if settings_url and settings_url.strip():
        return settings_url
    cfg_url = config.get_main_option("sqlalchemy.url")
    if cfg_url and cfg_url.strip():
        return cfg_url
    raise RuntimeError("Database URL is not configured for Alembic")


def run_migrations_offline() -> None:
    context.configure(
        url=_get_db_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _get_db_url()
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
