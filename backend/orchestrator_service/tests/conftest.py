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
os.environ["RAG_SERVICE_MOCK"] = "true"
os.environ["OCR_SERVICE_MOCK"] = "true"
os.environ["REGISTRY_SERVICE_MOCK"] = "true"

# Use local SQLite for tests — creates test_pipeline.db in project dir
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_pipeline.db"
os.environ["DEBUG"] = "false"

# Celery: use in-memory transport + eager mode (no Redis needed)
os.environ["CELERY_BROKER_URL"] = "memory://"
os.environ["CELERY_RESULT_BACKEND"] = "cache+memory://"

from app.main import create_application

# --- Celery configuration for tests ---
#
# 1. Use memory:// transport (no Redis needed).
# 2. Globally mock .delay() on all Celery tasks so that
#    API-level tests (test_drafts, etc.) don't actually execute tasks.
#    Tests that need real task execution (test_celery_tasks) call
#    task_function.run() directly, bypassing .delay().
#    Tests that test the orchestrator (test_pipeline_formation)
#    mock .delay() themselves with specific assertions.
#
from unittest.mock import patch

from app.celery_app import celery_app
celery_app.conf.update(
    task_always_eager=False,  # Don't auto-execute; we mock .delay() instead
    task_eager_propagates=False,
)

# Patch .delay() globally to be a no-op (prevents hanging on Redis)
_delay_patcher = patch("celery.app.task.Task.delay", autospec=True, return_value=None)
_delay_patcher.start()


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

    # Ensure all models are imported/registered with Base.metadata
    import app.models.pipeline  # noqa: F401

    import asyncio

    async def _init():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_init())
    return engine


@pytest.fixture(autouse=True)
async def clean_db(db_engine):
    """Clean all tables between tests.

    Fast path: checks if any rows exist before iterating all tables.
    Also resets RegistryServiceClient in-memory storage to keep
    tests isolated (class-level _storage persists across tests).
    """
    from app.db.base import Base
    from app.services.registry_client import RegistryServiceClient

    async with db_engine.begin() as conn:
        # Quick check — skip if DB is already empty
        has_data = False
        for table in Base.metadata.sorted_tables:
            result = await conn.execute(table.select().limit(1))
            if result.first() is not None:
                has_data = True
                break
        if has_data:
            for table in reversed(Base.metadata.sorted_tables):
                await conn.execute(table.delete())

    # Reset RegistryServiceClient in-memory storage
    reg_storage = RegistryServiceClient._storage
    reg_storage["drafts"].clear()
    reg_storage["documents"].clear()
    reg_storage["draft_seq"] = 1
    reg_storage["doc_seq"] = 1

    yield


@pytest.fixture
async def db_session():
    """Provide a clean async DB session per test.

    Database is cleaned by the autouse clean_db fixture.
    """
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
