from collections.abc import AsyncGenerator

import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.ext.asyncio.session import AsyncSession

from rag_builder.api.app import create_app
from rag_builder.db.session import get_session
from rag_builder.models.db import Base

TEST_DB_URL = "postgresql+asyncpg://pkb_user:pkb_pass@localhost:5433/pkb_db"


@pytest_asyncio.fixture()
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    eng = create_async_engine(TEST_DB_URL, future=True)
    async with eng.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS rag"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
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
