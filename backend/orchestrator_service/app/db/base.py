"""
Async SQLAlchemy engine and session factory.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Build async engine
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
_is_memory_sqlite = _is_sqlite and (
    ":memory:" in settings.DATABASE_URL
    or settings.DATABASE_URL == "sqlite+aiosqlite://"
)
_connect_args = {}
if _is_sqlite:
    # Allow multiple connections to share the same database
    _connect_args["check_same_thread"] = False

if _is_memory_sqlite:
    # In-memory SQLite: each connection must be the only one,
    # otherwise each pooled connection gets a separate DB.
    # Support URI mode for shared cache (file::memory:?cache=shared)
    if "uri=true" in settings.DATABASE_URL or "?" in settings.DATABASE_URL:
        _connect_args["uri"] = True
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args=_connect_args,
        poolclass=NullPool,
    )
elif _is_sqlite:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args=_connect_args,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=False,
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )

# Session factory for FastAPI dependencies
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""

    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency — provides an async DB session.

    Yields a session that is automatically closed when the request ends.
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
