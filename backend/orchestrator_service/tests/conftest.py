"""
Test configuration — fixtures for API testing.

Uses the FastAPI TestClient with the application in mock mode.
All external services return mock data during tests.
"""

import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient

# Force mock mode for all external services before any imports
os.environ["AUTH_SERVICE_MOCK"] = "true"
os.environ["RAG_SERVICE_MOCK"] = "true"
os.environ["QUERY_SERVICE_MOCK"] = "true"
os.environ["OCR_SERVICE_MOCK"] = "true"
os.environ["VALIDATE_SERVICE_MOCK"] = "true"
os.environ["INTEGRATION_SERVICE_MOCK"] = "true"
os.environ["REGISTRY_SERVICE_MOCK"] = "true"

from app.main import create_application

# Use in-memory SQLite for tests
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["DEBUG"] = "false"


@pytest.fixture(scope="session")
def app():
    """Create a fresh FastAPI application instance for tests."""
    return create_application()


@pytest.fixture
def client(app) -> Generator:
    """Provide a TestClient for API endpoint testing."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_header() -> dict:
    """Provide a mock Bearer token header for authenticated requests."""
    return {"Authorization": "Bearer mock_access_token_12345"}


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def db_engine():
    """Create a fresh SQLAlchemy engine for the test session."""
    from app.db.base import engine, Base

    import asyncio

    async def _init():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_init())
    return engine


@pytest.fixture(autouse=True)
def clean_db(db_engine):
    """Clean all tables between tests."""
    from app.db.base import Base
    import asyncio

    async def _clean():
        async with db_engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                await conn.execute(table.delete())

    asyncio.run(_clean())
    yield


@pytest.fixture
async def db_session():
    """Provide a clean async DB session per test."""
    from app.db.base import AsyncSessionLocal

    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
    finally:
        await session.close()


@pytest.fixture
def app_with_real_auth():
    """Create application with auth mock disabled to test real auth flow."""
    os.environ["AUTH_SERVICE_MOCK"] = "false"
    app = create_application()
    yield app
    os.environ["AUTH_SERVICE_MOCK"] = "true"
