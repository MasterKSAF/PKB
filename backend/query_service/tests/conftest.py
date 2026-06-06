import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_query.db"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def app():
    import os
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["DEV_AUTH_MODE"] = "true"
    os.environ["MOCK_RAG_ENABLED"] = "true"

    # patch lru_cache
    from app.config import get_settings
    get_settings.cache_clear()

    from app.db import Base, engine as orig_engine
    import app.db as db_module

    test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    TestSession = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

    db_module.engine = test_engine
    db_module.AsyncSessionLocal = TestSession

    from app import models  # noqa
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from app.main import app as fastapi_app
    yield fastapi_app

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
