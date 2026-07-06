"""
Database connection retry logic for orchestrator startup.

Wraps the initial database connection + schema creation in a tenacity
retry loop so that a temporarily unavailable PostgreSQL (e.g. still in
crash recovery after a restart) does not kill the service on first attempt.
"""

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from app.core.config import settings
from app.db.base import Base, engine

logger = logging.getLogger("orchestrator.db.retry")

# ── Retryable exceptions ──────────────────────────────────────────────
# asyncpg raises CannotConnectNowError when PG is still in crash recovery;
# SQLAlchemy wraps it in OperationalError. Catch both explicitly to avoid
# masking real code bugs.
RETRYABLE_DB_EXCEPTIONS = (
    OperationalError,
    ConnectionError,
    TimeoutError,
)


@retry(
    stop=stop_after_attempt(10),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type(RETRYABLE_DB_EXCEPTIONS),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def init_database() -> None:
    """Connect to the database and ensure the schema + tables exist.

    Retries on transient connection errors (PG still in recovery, network
    flap, etc.) with exponential backoff (2s → 4s → … → 30s max).
    Raises the last exception if all attempts are exhausted.
    """
    async with engine.begin() as conn:
        # Ensure pipeline schema exists
        if settings.DATABASE_URL.startswith("sqlite"):
            try:
                await conn.execute(text("ATTACH DATABASE ':memory:' AS pipeline"))
            except Exception:
                pass  # already attached
        else:
            try:
                await conn.execute(text("CREATE SCHEMA IF NOT EXISTS pipeline"))
            except Exception:
                pass  # non-fatal

        # Create all tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database schema initialised successfully")
