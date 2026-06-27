"""
Тесты proxy_request() — проксирование к сервисам.

Все внешние вызовы мокаются через mock_httpx_client.

Unit-тесты, не требуют Docker.
"""

from __future__ import annotations

import json
import os
import sys

import httpx
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import Request

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)


def _make_request(
    path: str,
    method: str = "GET",
    body: bytes = b"",
    headers: dict = None,
    query: str = "",
) -> Request:
    """Build a minimal fastapi.Request from an ASGI scope dict."""
    if headers is None:
        headers = {"host": "testserver"}

    async def _receive():
        return {"type": "http.request", "body": body, "more_body": False}

    scope_headers = [(k.lower().encode(), v.encode()) for k, v in headers.items()]

    return Request({
        "type": "http",
        "method": method,
        "scheme": "http",
        "server": ("testserver", 80),
        "path": path,
        "query_string": query.encode(),
        "headers": scope_headers,
    }, receive=_receive)


def _make_mock_client(monkeypatch):
    """Создаёт mock httpx.AsyncClient с захватом kwargs."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.content = b"ok"

    captured_kwargs = {}

    async def mock_request(method, url, **kwargs):
        captured_kwargs.update(kwargs)
        return mock_response

    mock_client.request = mock_request
    monkeypatch.setattr("gateway.client.get_client", lambda: mock_client)
    return mock_client, captured_kwargs


class TestProxySuccess:
    """Успешное проксирование."""

    @pytest.mark.asyncio
    async def test_proxy_get_200(self, mock_httpx_client, monkeypatch):
        """GET → 200, тело ответа передано."""
        from gateway.client import proxy_request, config

        mock_httpx_client(status_code=200, content=b'{"status":"ok"}')

        request = _make_request("/api/v1/auth/me")
        request.state.user_id = None

        response = await proxy_request(request, "auth", "/api/v1/auth/me")
        assert response.status_code == 200
        assert json.loads(response.body) == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_proxy_post_with_json(self, mock_httpx_client, monkeypatch):
        """POST с JSON телом → проксируется."""
        from gateway.client import proxy_request

        mock_httpx_client(status_code=201, content=b'{"id": 1}')

        body = json.dumps({"title": "test"}).encode()
        request = _make_request("/api/v1/drafts", method="POST", body=body)
        request.state.user_id = None

        response = await proxy_request(request, "orchestrator", "/api/v1/drafts")
        assert response.status_code == 201
        assert json.loads(response.body) == {"id": 1}

    @pytest.mark.asyncio
    async def test_proxy_with_target_path(self, mock_httpx_client, monkeypatch):
        """target_path — path transform для Registry."""
        from gateway.client import proxy_request

        mock_httpx_client(status_code=200, content=b'{"data":"ok"}')

        request = _make_request("/api/v1/documents/1")
        request.state.user_id = None

        response = await proxy_request(
            request, "registry", "/api/v1/registry/documents/1"
        )
        assert response.status_code == 200


class TestProxyErrors:
    """Ошибки проксирования."""

    @pytest.mark.asyncio
    async def test_service_not_configured(self, monkeypatch):
        """Сервис не настроен → 502."""
        from gateway.client import proxy_request, config

        monkeypatch.setattr(config, "service_urls", {})

        request = _make_request("/api/v1/unknown")
        request.state.user_id = None

        response = await proxy_request(request, "nonexistent", "/test")
        assert response.status_code == 502
        data = json.loads(response.body)
        assert "BAD_GATEWAY" in str(data)

    @pytest.mark.asyncio
    async def test_connect_error(self, monkeypatch):
        """ConnectError → 502."""
        from gateway.client import proxy_request

        mock_client = AsyncMock(spec=httpx.AsyncClient)

        async def mock_request(method, url, **kwargs):
            raise httpx.ConnectError("Connection refused")

        mock_client.request = mock_request
        monkeypatch.setattr("gateway.client.get_client", lambda: mock_client)

        request = _make_request("/api/v1/auth/me")
        request.state.user_id = None

        response = await proxy_request(request, "auth", "/api/v1/auth/me")
        assert response.status_code == 502
        data = json.loads(response.body)
        assert "BAD_GATEWAY" in str(data)

    @pytest.mark.asyncio
    async def test_timeout_error(self, monkeypatch):
        """TimeoutException → 504."""
        from gateway.client import proxy_request

        mock_client = AsyncMock(spec=httpx.AsyncClient)

        async def mock_request(method, url, **kwargs):
            raise httpx.TimeoutException("Timeout")

        mock_client.request = mock_request
        monkeypatch.setattr("gateway.client.get_client", lambda: mock_client)

        request = _make_request("/api/v1/auth/me")
        request.state.user_id = None

        response = await proxy_request(request, "auth", "/api/v1/auth/me")
        assert response.status_code == 504
        data = json.loads(response.body)
        assert "GATEWAY_TIMEOUT" in str(data)

    @pytest.mark.asyncio
    async def test_204_no_content(self, mock_httpx_client, monkeypatch):
        """204 No Content — тело не передаётся."""
        from gateway.client import proxy_request

        mock_httpx_client(status_code=204, content=b"")

        request = _make_request("/api/v1/drafts/1")
        request.state.user_id = None

        response = await proxy_request(request, "orchestrator", "/api/v1/drafts/1")
        assert response.status_code == 204


class TestProxyHeaders:
    """Заголовки при проксировании."""

    @pytest.mark.asyncio
    async def test_hop_by_hop_filtered(self, monkeypatch):
        """Hop-by-hop заголовки не передаются в downstream."""
        from gateway.client import proxy_request

        mock_client, captured_kwargs = _make_mock_client(monkeypatch)

        request = _make_request(
            "/api/v1/auth/me",
            headers={
                "host": "testserver",
                "connection": "keep-alive",
                "keep-alive": "timeout=5",
                "authorization": "Bearer token123",
                "x-custom": "value",
            },
        )
        request.state.user_id = None

        await proxy_request(request, "auth", "/api/v1/auth/me")

        sent_headers = captured_kwargs.get("headers", {})
        assert "connection" not in {k.lower() for k in sent_headers}
        assert "keep-alive" not in {k.lower() for k in sent_headers}
        header_keys = {k.lower(): v for k, v in sent_headers.items()}
        assert "x-custom" in header_keys

    @pytest.mark.asyncio
    async def test_x_user_id_forwarded(self, monkeypatch):
        """X-User-ID пробрасывается из request.state."""
        from gateway.client import proxy_request

        mock_client, captured_kwargs = _make_mock_client(monkeypatch)

        request = _make_request("/api/v1/auth/me")
        request.state.user_id = 42

        await proxy_request(request, "auth", "/api/v1/auth/me")

        sent = captured_kwargs.get("headers", {})
        header_keys = {k.lower(): v for k, v in sent.items()}
        assert header_keys.get("x-user-id") == "42"

    @pytest.mark.asyncio
    async def test_x_draft_id_forwarded(self, monkeypatch):
        """X-Draft-ID пробрасывается из request.state."""
        from gateway.client import proxy_request

        mock_client, captured_kwargs = _make_mock_client(monkeypatch)

        request = _make_request("/api/v1/drafts/123")
        request.state.x_draft_id = 123

        await proxy_request(request, "orchestrator", "/api/v1/drafts/123")

        sent = captured_kwargs.get("headers", {})
        header_keys = {k.lower(): v for k, v in sent.items()}
        assert header_keys.get("x-draft-id") == "123"

    @pytest.mark.asyncio
    async def test_x_document_id_forwarded(self, monkeypatch):
        """X-Document-ID пробрасывается из request.state."""
        from gateway.client import proxy_request

        mock_client, captured_kwargs = _make_mock_client(monkeypatch)

        request = _make_request("/api/v1/documents/456")
        request.state.x_document_id = 456

        await proxy_request(request, "registry", "/api/v1/registry/documents/456")

        sent = captured_kwargs.get("headers", {})
        header_keys = {k.lower(): v for k, v in sent.items()}
        assert header_keys.get("x-document-id") == "456"

    @pytest.mark.asyncio
    async def test_content_type_preserved(self, mock_httpx_client, monkeypatch):
        """Content-Type ответа сохраняется."""
        from gateway.client import proxy_request

        mock_httpx_client(
            status_code=200,
            content=b'{"data":"test"}',
            headers={"content-type": "application/pdf"},
        )

        request = _make_request("/api/v1/documents/1/file")
        request.state.user_id = None

        response = await proxy_request(request, "registry", "/api/v1/registry/documents/1/file")
        assert response.media_type == "application/pdf"

    @pytest.mark.asyncio
    async def test_query_string_passed(self, monkeypatch):
        """Query string передаётся в target_url."""
        from gateway.client import proxy_request

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        captured_url = []

        async def mock_request(method, url, **kwargs):
            captured_url.append(url)
            mock_response = AsyncMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.content = b"ok"
            return mock_response

        mock_client.request = mock_request
        monkeypatch.setattr("gateway.client.get_client", lambda: mock_client)

        request = _make_request(
            "/api/v1/documents/search",
            query="q=test&page=1",
        )
        request.state.user_id = None

        await proxy_request(request, "registry", "/api/v1/registry/search")

        assert "?q=test&page=1" in captured_url[0]


class TestProxyStatusCode:
    """Статус код проксируется."""

    @pytest.mark.parametrize("status", [200, 201, 400, 404, 500])
    @pytest.mark.asyncio
    async def test_status_code_proxied(self, status, mock_httpx_client, monkeypatch):
        """Status code проксируется как есть."""
        from gateway.client import proxy_request

        mock_httpx_client(status_code=status, content=b'{}')

        request = _make_request("/api/v1/auth/me")
        request.state.user_id = None

        response = await proxy_request(request, "auth", "/api/v1/auth/me")
        assert response.status_code == status
