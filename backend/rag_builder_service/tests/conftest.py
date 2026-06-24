"""Root conftest — shared fixtures. DB fixtures only activate when requested."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.ext.asyncio.session import AsyncSession

from rag_builder.api.app import create_app
from rag_builder.db.session import get_session
from rag_builder.db.migrations import upgrade_to_head

# pkb-postgres exposed on host port 15432 (see `docker ps`)
TEST_DB_URL = "postgresql+asyncpg://pkb:pkb@localhost:15432/pkb_neuro"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "db: marks tests that need PostgreSQL with pgvector")


@pytest.fixture(scope="session")
def migrate_test_db() -> None:
    """Apply Alembic migrations. Only runs when a test requests DB fixtures."""
    upgrade_to_head(TEST_DB_URL)


@pytest_asyncio.fixture()
async def engine(migrate_test_db: None) -> AsyncGenerator[AsyncEngine, None]:
    eng = create_async_engine(TEST_DB_URL, future=True)
    async with eng.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE rag.document_chunks RESTART IDENTITY"))
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture()
async def session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s


@pytest_asyncio.fixture()
async def app(engine: AsyncEngine) -> FastAPI:
    app = create_app()
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with maker() as s:
            yield s

    app.dependency_overrides[get_session] = override_get_session
    return app
