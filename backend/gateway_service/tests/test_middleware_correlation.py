"""
Тесты CorrelationHeadersMiddleware — X-Request-ID, X-Trace-ID.

Unit-тесты, не требуют Docker.
"""

from __future__ import annotations

import os
import sys

import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)


class TestCorrelationHeaders:
    """Корреляционные заголовки."""

    def test_response_has_x_request_id(self, client):
        """Ответ содержит X-Request-ID."""
        resp = client.get("/api/v1/health")
        assert "X-Request-ID" in resp.headers or "x-request-id" in resp.headers

    def test_x_request_id_is_uuid(self, client):
        """X-Request-ID — валидный UUID."""
        resp = client.get("/api/v1/health")
        rid = resp.headers.get("X-Request-ID", resp.headers.get("x-request-id", ""))
        import uuid
        try:
            uuid.UUID(rid)
        except ValueError:
            pytest.fail(f"X-Request-ID не является UUID: {rid}")

    def test_x_trace_id_present(self, client):
        """Ответ содержит X-Trace-ID."""
        resp = client.get("/api/v1/health")
        assert "X-Trace-ID" in resp.headers or "x-trace-id" in resp.headers
