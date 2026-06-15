from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from rag_builder.core.config import build_database_url, settings


def _alembic_ini_path() -> Path:
    return Path(__file__).resolve().parents[3] / "alembic.ini"


def get_alembic_config(db_url: str | None = None) -> Config:
    cfg = Config(str(_alembic_ini_path()))
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parents[3] / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url or build_database_url(settings))
    return cfg


def get_head_revision() -> str:
    script = ScriptDirectory.from_config(get_alembic_config())
    head = script.get_current_head()
    if head is None:
        raise RuntimeError("Alembic head revision is not defined")
    return head


def upgrade_to_head(db_url: str | None = None) -> None:
    logger.info("Alembic upgrade start")
    if db_url is None:
        command.upgrade(get_alembic_config(db_url), "head")
    else:
        _run_alembic_subprocess(["upgrade", "head"], db_url)
    logger.info("Alembic upgrade done")


def downgrade_to_base(db_url: str | None = None) -> None:
    logger.info("Alembic downgrade start")
    if db_url is None:
        command.downgrade(get_alembic_config(db_url), "base")
    else:
        _run_alembic_subprocess(["downgrade", "base"], db_url)
    logger.info("Alembic downgrade done")


def _run_alembic_subprocess(args: list[str], db_url: str) -> None:
    project_root = Path(__file__).resolve().parents[3]
    env = dict(**os.environ)
    env["DATABASE_URL"] = db_url
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=str(project_root),
        env=env,
        check=True,
    )


async def validate_startup_migrations(engine: AsyncEngine) -> None:
    expected = get_head_revision()
    async with engine.connect() as conn:
        table_exists = await conn.scalar(text("SELECT to_regclass('public.alembic_version')::text"))
        if table_exists is None:
            raise RuntimeError("alembic_version table not found; run migrations")
        current = await conn.scalar(text("SELECT version_num FROM alembic_version LIMIT 1"))
        if current != expected:
            raise RuntimeError(f"alembic revision mismatch current={current} expected={expected}")
        vector_ext = await conn.scalar(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector' LIMIT 1")
        )
        if vector_ext is None:
            raise RuntimeError("pgvector extension 'vector' is missing")
    logger.info("Migration validation passed revision={} pgvector={}", expected, vector_ext)
