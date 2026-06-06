"""
Unit tests for ServiceClient base class (base_client.py).

Tests the dual-mode (mock/real), HTTP client management, and error handling.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.base_client import ServiceClient, ServiceError


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
        assert client._http_client is None

    def test_initialization_with_real_mode(self):
        client = SimpleTestClient(service_url="http://localhost:9999", mock_mode=False)
        assert client.service_name == "test_service"
        assert client.service_url == "http://localhost:9999"
        assert client.mock_mode is False
        assert client._http_client is None

    def test_initialization_default_mock_mode(self):
        client = SimpleTestClient()
        assert client.mock_mode is True


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


class TestServiceClientRealMode:
    """Tests for real (HTTP) mode behavior."""

    @pytest.mark.asyncio
    async def test_real_mode_makes_http_request(self):
        """When mock_mode=False and service_url is set, should make HTTP call."""
        client = SimpleTestClient(service_url="http://localhost:9999", mock_mode=False)

        # Patch the internal _make_request
        with patch.object(client, "_make_request", new=AsyncMock()) as mock_request:
            mock_request.return_value = {"real": "response"}

            result = await client.call("GET", "/api/test", mock_response={"mock": "data"})
            assert result == {"real": "response"}
            mock_request.assert_awaited_once_with("GET", "/api/test")

    @pytest.mark.asyncio
    async def test_real_mode_passes_kwargs(self):
        """call() should forward kwargs to _make_request."""
        client = SimpleTestClient(service_url="http://localhost:9999", mock_mode=False)

        with patch.object(client, "_make_request", new=AsyncMock()) as mock_request:
            mock_request.return_value = {"ok": True}

            await client.call(
                "POST",
                "/api/echo",
                mock_response={},
                json={"hello": "world"},
                params={"x": "1"},
            )

            # Verify _make_request received the kwargs
            call_kwargs = mock_request.call_args.kwargs
            assert call_kwargs.get("json") == {"hello": "world"}
            assert call_kwargs.get("params") == {"x": "1"}


class TestServiceClientHttpClient:
    """Tests for HTTP client (_get_client / close)."""

    @pytest.mark.asyncio
    async def test_get_client_creates_new_client(self):
        client = SimpleTestClient(service_url="http://localhost:9999", mock_mode=False)
        http_client = await client._get_client()
        assert http_client is not None
        assert client._http_client is not None
        assert http_client is client._http_client

    @pytest.mark.asyncio
    async def test_get_client_reuses_existing(self):
        client = SimpleTestClient(service_url="http://localhost:9999", mock_mode=False)
        first = await client._get_client()
        second = await client._get_client()
        assert first is second

    @pytest.mark.asyncio
    async def test_close_clears_http_client(self):
        client = SimpleTestClient(service_url="http://localhost:9999", mock_mode=False)
        http_client = await client._get_client()
        mock_close = AsyncMock()
        http_client.aclose = mock_close

        await client.close()
        assert client._http_client is None
        mock_close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_close_when_no_client(self):
        client = SimpleTestClient(mock_mode=True)
        # Should not raise
        await client.close()


class TestServiceError:
    """Tests for ServiceError exception."""

    def test_service_error_default_code(self):
        error = ServiceError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.status_code == 500
        assert error.details is None
        assert str(error) == "Something went wrong"

    def test_service_error_with_all_params(self):
        error = ServiceError("Not found", status_code=404, details="missing doc")
        assert error.status_code == 404
        assert error.details == "missing doc"

    def test_to_dict_format(self):
        error = ServiceError("Document not found", status_code=404)
        result = error.to_dict()
        assert "error" in result
        assert result["error"]["code"] == "NOT_FOUND"
        assert result["error"]["message"] == "Document not found"
        assert result["error"]["details"] == {}

    def test_to_dict_with_details(self):
        error = ServiceError("Error", status_code=400, details="invalid param")
        result = error.to_dict()
        assert result["error"]["code"] == "BAD_REQUEST"
        assert result["error"]["details"] == {"service_error": "invalid param"}

    def test_to_dict_code_mapping(self):
        mapping = [
            (400, "BAD_REQUEST"),
            (401, "UNAUTHORIZED"),
            (403, "FORBIDDEN"),
            (404, "NOT_FOUND"),
            (409, "CONFLICT"),
            (422, "VALIDATION_FAILED"),
            (500, "INTERNAL_ERROR"),
            (503, "SERVICE_UNAVAILABLE"),
            (999, "INTERNAL_ERROR"),  # unknown
        ]
        for status_code, expected_code in mapping:
            error = ServiceError("Test", status_code=status_code)
            assert error._get_code_name() == expected_code, f"Failed for {status_code}"


class TestBaseClientAbstract:
    """Tests that ServiceClient properly enforces abstract interface."""

    def test_cannot_instantiate_abstract(self):
        """ServiceClient is abstract due to _generate_mock, but Python allows
        instantiation if all abstract methods are defined. This test verifies
        that a class without the method raises TypeError."""
        with pytest.raises(TypeError):
            # noinspection PyUnusedLocal,PyAbstractClass
            class IncompleteClient(ServiceClient):
                def __init__(self):
                    super().__init__("test", mock_mode=True)

            IncompleteClient()
