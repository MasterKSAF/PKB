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
os.environ["REGISTRY_SERVICE_MOCK"] = "true"
os.environ["RAG_SERVICE_MOCK"] = "true"
os.environ["OCR_SERVICE_MOCK"] = "true"
os.environ["PARSER_SERVICE_MOCK"] = "true"
os.environ["CONVERTER_SERVICE_MOCK"] = "true"

# Local SQLite for tests — file with PRAGMA optimizations (near-RAM speed)
# PRAGMA journal_mode=MEMORY + synchronous=OFF eliminates disk I/O bottleneck
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_pipeline.db"
os.environ["DEBUG"] = "false"

# Celery: use in-memory transport + eager mode (no Redis needed)
os.environ["CELERY_BROKER_URL"] = "memory://"
os.environ["CELERY_RESULT_BACKEND"] = "cache+memory://"

from app.main import create_application
from sqlalchemy import event as sa_event

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
from unittest.mock import AsyncMock, patch

from app.celery_app import celery_app
celery_app.conf.update(
    task_always_eager=False,  # Don't auto-execute; we mock .delay() instead
    task_eager_propagates=False,
)

# Patch .delay() globally to be a no-op (prevents hanging on Redis)
_delay_patcher = patch("celery.app.task.Task.delay", autospec=True, return_value=None)
_delay_patcher.start()

# Patch MinIO upload globally (no MinIO in tests; would hang otherwise)
# Note: drafts.py does `from app.storage import upload_file` at module level,
# creating a local reference. documents.py imports inside function body.
# We patch the source (app.storage.upload_file) to cover both cases.
_upload_patcher = patch("app.api.v1.endpoints.drafts.upload_file", new=AsyncMock())
_upload_patcher.start()
_storage_patcher = patch("app.storage.upload_file", new=AsyncMock())
_storage_patcher.start()

# --- Block all real HTTP requests (prevent network timeouts in tests) ---
# When mock_mode=False, tests like test_real_mode_* try to connect to
# non-existent servers and wait seconds for connect timeout.
# This patch makes httpx.AsyncClient.request instantly raise ConnectError.
import httpx

# Replace AsyncClient with a fast fake — on Windows, creating a real
# httpx.AsyncClient takes ~0.4s due to connection pool setup, which adds up
# across all real-mode tests.
class _FakeHttpxClient:
    """Duck-typed fake that avoids slow httpx.AsyncClient.__init__."""
    def __init__(self, *args, **kwargs):
        pass
    async def aclose(self):
        pass
    async def request(self, method, url, **kwargs):
        raise httpx.ConnectError(f"Blocked by test: {method} {url}")

httpx.AsyncClient = _FakeHttpxClient  # type: ignore[misc]


@pytest.fixture(scope="session")
def app(db_engine):
    """Create a fresh FastAPI application instance for tests.

    Зависимость от db_engine гарантирует, что все таблицы созданы
    и ATTACH DATABASE listener зарегистрирован до старта BackgroundTaskPoller.
    """
    return create_application()


@pytest.fixture(scope="session")
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
    """Create a fresh SQLAlchemy engine for the test session.

    Uses tempfile + PRAGMA optimizations for near-RAM speed.
    """
    from app.db.base import engine, Base

    # Ensure all models are imported/registered with Base.metadata
    import app.models.pipeline  # noqa: F401
    import app.models.external_task  # noqa: F401

    import asyncio

    # For SQLite, attach pipeline schema as file-based DB (not :memory:)
    # because ATTACH DATABASE is connection-specific and each connection
    # from NullPool would get a separate in-memory database.
    _pipeline_db_path = os.path.join(os.path.dirname(__file__), "test_pipeline_meta.db")

    @sa_event.listens_for(engine.sync_engine, "connect")
    def _attach_pipeline(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute(f"ATTACH DATABASE '{_pipeline_db_path}' AS pipeline")
        cursor.execute("PRAGMA journal_mode=MEMORY")
        cursor.execute("PRAGMA synchronous=OFF")
        cursor.execute("PRAGMA cache_size=-64000")
        cursor.close()

    async def _init():
        # Remove stale pipeline db
        if os.path.exists(_pipeline_db_path):
            os.remove(_pipeline_db_path)
        async with engine.begin() as conn:
            from sqlalchemy import text
            # Performance pragmas
            await conn.execute(text("PRAGMA journal_mode=MEMORY"))
            await conn.execute(text("PRAGMA synchronous=OFF"))
            await conn.execute(text("PRAGMA cache_size=-64000"))
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_init())
    return engine


@pytest.fixture(autouse=True)
async def clean_db(request, db_engine):
    """Clean all tables between tests.

    Fast path: checks if any rows exist before iterating all tables.
    Also resets RegistryServiceClient in-memory storage to keep
    tests isolated (class-level _storage persists across tests).
    """
    if request.node.get_closest_marker("no_db"):
        yield
        return
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

    # Reset Idempotency cache
    from app.api.v1.endpoints.drafts import _IDEMPOTENCY_CACHE
    _IDEMPOTENCY_CACHE.clear()

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
