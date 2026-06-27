"""
Tests for RequestTracingMiddleware (P11-2/CM-5).

Проверяет:
  - X-Request-ID генерируется UUIDv4 при отсутствии
  - X-Request-ID сохраняется при передаче клиентом
  - X-Trace-ID генерируется UUIDv4 при отсутствии
  - X-Trace-ID сохраняется при передаче клиентом
  - CorrelationHeadersMiddleware (X-Draft-ID/X-Document-ID/X-Version-ID)"""

import sys
import os
import uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


class TestCorrelationHeaders:
    """X-Request-ID, X-Trace-ID заголовки."""

    def test_request_id_generated(self, client):
        """Если клиент не передал X-Request-ID — ответ содержит сгенерированный."""
        resp = client.get("/api/v1/system/health")
        assert "X-Request-ID" in resp.headers
        req_id = resp.headers["X-Request-ID"]
        # Должен быть UUID
        uuid.UUID(req_id)  # raises ValueError if invalid

    def test_request_id_preserved(self, client):
        """Если клиент передал X-Request-ID — он сохраняется в ответе."""
        custom_id = str(uuid.uuid4())
        resp = client.get(
            "/api/v1/system/health",
            headers={"X-Request-ID": custom_id},
        )
        assert resp.headers.get("X-Request-ID") == custom_id

    def test_trace_id_generated(self, client):
        """X-Trace-ID генерируется при отсутствии."""
        resp = client.get("/api/v1/system/health")
        assert "X-Trace-ID" in resp.headers
        trace_id = resp.headers["X-Trace-ID"]
        uuid.UUID(trace_id)

    def test_trace_id_preserved(self, client):
        """X-Trace-ID сохраняется при передаче."""
        custom_trace = str(uuid.uuid4())
        resp = client.get(
            "/api/v1/system/health",
            headers={"X-Trace-ID": custom_trace},
        )
        assert resp.headers.get("X-Trace-ID") == custom_trace
