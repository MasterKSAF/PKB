"""
DB session helpers for non-FastAPI contexts (Celery tasks, background jobs).

Usage inside a Celery task:
    async with get_db_context() as db:
        repo = DocumentRepository(db)
        ...
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AsyncSessionLocal


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async DB session outside of FastAPI request lifecycle.

    Handles commit/rollback automatically.
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_db_context_direct() -> AsyncSession:
    """Create a raw session for manual lifecycle management.

    Caller MUST handle commit/rollback/close.
    """
    return AsyncSessionLocal()
