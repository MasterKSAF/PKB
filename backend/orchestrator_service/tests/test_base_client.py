"""
Unit tests for ServiceClient base class (base_client.py).

Tests initialization, mock mode, and close behaviour.
"""

import pytest

from app.services.base_client import ServiceClient


class SimpleTestClient(ServiceClient):
    """Minimal concrete implementation for testing the base class."""

    def __init__(self, service_url=None, mock_mode=True):
        super().__init__(
            service_name="test_service",
            service_url=service_url,
            mock_mode=mock_mode,
        )

    async def _generate_mock(self, method, endpoint, default_mock, **kwargs):
        if endpoint == "/custom/mock":
            return {"custom": "data", "method": method}
        if endpoint == "/kwargs/test":
            return {"received": kwargs.get("json", {}), "params": kwargs.get("params", {})}
        return default_mock

    async def test_call(self):
        return await self.call("GET", "/test", mock_response={"mock": "response"})


class TestServiceClientInitialization:
    """Tests for ServiceClient __init__."""

    def test_initialization_with_mock_mode(self):
        client = SimpleTestClient(mock_mode=True)
        assert client.service_name == "test_service"
        assert client.service_url is None
        assert client.mock_mode is True

    def test_initialization_with_real_mode(self):
        client = SimpleTestClient(service_url="http://localhost:9999", mock_mode=False)
        assert client.service_name == "test_service"
        assert client.service_url == "http://localhost:9999"
        assert client.mock_mode is False

    def test_initialization_default_mock_mode(self):
        client = SimpleTestClient()
        assert client.mock_mode is True

    def test_service_url_strips_trailing_slash(self):
        client = SimpleTestClient(service_url="http://localhost:9999/", mock_mode=False)
        assert client.service_url == "http://localhost:9999"

    def test_service_url_none(self):
        client = SimpleTestClient(service_url=None)
        assert client.service_url is None


class TestServiceClientMockMode:
    """Tests for mock mode behavior."""

    @pytest.mark.asyncio
    async def test_mock_mode_returns_mock_data(self):
        client = SimpleTestClient(mock_mode=True)
        result = await client.test_call()
        assert result == {"mock": "response"}

    @pytest.mark.asyncio
    async def test_mock_mode_custom_endpoint(self):
        client = SimpleTestClient(mock_mode=True)
        result = await client.call("POST", "/custom/mock", mock_response={"default": "data"})
        assert result == {"custom": "data", "method": "POST"}

    @pytest.mark.asyncio
    async def test_mock_mode_no_service_url(self):
        """Should still work in mock mode even without service_url."""
        client = SimpleTestClient(service_url=None, mock_mode=True)
        result = await client.test_call()
        assert result == {"mock": "response"}

    @pytest.mark.asyncio
    async def test_mock_mode_passes_kwargs(self):
        client = SimpleTestClient(mock_mode=True)
        result = await client.call(
            "POST",
            "/kwargs/test",
            mock_response={"default": "data"},
            json={"key": "value"},
            params={"param1": "val1"},
        )
        assert result["received"] == {"key": "value"}
        assert result["params"] == {"param1": "val1"}

    @pytest.mark.asyncio
    async def test_mock_mode_default_response(self):
        """Unknown endpoint returns default_mock."""
        client = SimpleTestClient(mock_mode=True)
        result = await client.call("GET", "/unknown", mock_response={"fallback": True})
        assert result == {"fallback": True}


class TestServiceClientRealMode:
    """Tests for real (non-mock) mode behavior.

    In non-mock mode without HTTP client, call() returns mock_response as-is.
    httpx.AsyncClient creation is slow on Windows, so we use a class-level
    fixture to create the client once.
    """

    @pytest.fixture
    def real_client(self):
        """Create a real-mode client once per test."""
        return SimpleTestClient(
            service_url="http://localhost:9999", mock_mode=False
        )

    @pytest.mark.asyncio
    async def test_real_mode_returns_mock_response(self, real_client):
        """When mock_mode=False, call returns mock_response directly."""
        result = await real_client.call(
            "GET", "/api/test", mock_response={"real": "data"}
        )
        assert result == {"real": "data"}

    @pytest.mark.asyncio
    async def test_real_mode_empty_response(self, real_client):
        """When mock_mode=False and no mock_response, returns empty dict."""
        result = await real_client.call("GET", "/api/test")
        assert result == {}


class TestServiceClientDataValidation:
    """Tests for JSON guard and request_model in call()."""

    @pytest.mark.asyncio
    async def test_json_guard_rejects_non_serializable(self):
        """call() raises TypeError when json body contains non-serializable object."""
        client = SimpleTestClient(mock_mode=True)
        with pytest.raises(TypeError, match="non-serializable"):
            await client.call(
                "POST",
                "/test",
                json={"user": object()},  # object() is not JSON-serializable
            )

    @pytest.mark.asyncio
    async def test_json_guard_allows_serializable(self):
        """call() succeeds with valid JSON body."""
        client = SimpleTestClient(mock_mode=True)
        result = await client.call(
            "POST",
            "/kwargs/test",
            mock_response={"default": "data"},
            json={"name": "test", "count": 42},
        )
        assert result["received"] == {"name": "test", "count": 42}

    @pytest.mark.asyncio
    async def test_request_model_validates_types(self):
        """call() with request_model validates json body through Pydantic."""
        from pydantic import BaseModel, Field

        class TestRequest(BaseModel):
            name: str = Field(...)
            count: int = Field(...)

        client = SimpleTestClient(mock_mode=True)

        # Valid data passes
        result = await client.call(
            "POST",
            "/kwargs/test",
            mock_response={"default": "data"},
            request_model=TestRequest,
            json={"name": "hello", "count": 10},
        )
        assert result["received"] == {"name": "hello", "count": 10}

    @pytest.mark.asyncio
    async def test_request_model_rejects_wrong_types(self):
        """call() with request_model raises TypeError on type mismatch."""
        from pydantic import BaseModel, Field

        class TestRequest(BaseModel):
            name: str = Field(...)

        client = SimpleTestClient(mock_mode=True)

        with pytest.raises(TypeError, match="Pydantic validation"):
            await client.call(
                "POST",
                "/test",
                request_model=TestRequest,
                json={"name": 42},  # int where str expected
            )


class TestServiceClientCustomReadTimeout:
    """Tests for custom read_timeout parameter."""

    @pytest.mark.asyncio
    async def test_custom_read_timeout_creates_http_client(self):
        """Custom read_timeout creates httpx client (not None)."""
        client = SimpleTestClient(
            service_url="http://localhost:9999",
            mock_mode=False,
        )
        assert client._http_client is not None
        await client.close()

    @pytest.mark.asyncio
    async def test_mock_mode_no_http_client(self):
        """Mock mode does NOT create HTTP client."""
        client = SimpleTestClient(mock_mode=True)
        assert client._http_client is None
        await client.close()


class TestServiceClientClose:
    """Tests for close() method."""

    @pytest.mark.asyncio
    async def test_close_mock_mode(self):
        """close() should not raise in mock mode."""
        client = SimpleTestClient(mock_mode=True)
        await client.close()

    @pytest.mark.asyncio
    async def test_close_real_mode(self):
        """close() should not raise in real mode."""
        client = SimpleTestClient(service_url="http://localhost:9999", mock_mode=False)
        await client.close()
