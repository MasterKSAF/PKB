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


@pytest.fixture
def app_with_real_auth():
    """Create application with auth mock disabled to test real auth flow."""
    os.environ["AUTH_SERVICE_MOCK"] = "false"
    app = create_application()
    yield app
    os.environ["AUTH_SERVICE_MOCK"] = "true"
