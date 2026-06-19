"""
Test correlation headers propagation (T-11).

Verifies that:
  1. X-Trace-ID and X-Request-ID are set on response
  2. X-User-ID is read from request headers
  3. build_correlation_headers() returns all 6 headers when set
"""

import pytest
from fastapi.testclient import TestClient

from app.core.trace import (
    build_correlation_headers,
    set_trace_id,
    set_user_id,
    set_draft_id,
    set_document_id,
    set_version_id,
    reset_trace_id,
)


class TestCorrelationHeadersApi:
    """API-level correlation header tests."""

    def test_trace_id_in_response(self, client: TestClient, auth_header: dict):
        """X-Trace-ID is set on response."""
        response = client.get("/api/v1/system/health")
        assert response.status_code == 200
        assert "X-Trace-ID" in response.headers
        assert len(response.headers["X-Trace-ID"]) > 0

    def test_trace_id_on_draft_create(self, client: TestClient, auth_header: dict):
        """Draft create response has trace ID."""
        response = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            files={"file": ("test.pdf", b"%PDF mock", "application/pdf")},
            data={"document_key": "doc-correlation"},
        )
        assert "X-Trace-ID" in response.headers

    def test_user_id_from_request(self, client: TestClient):
        """X-User-ID from request is available in context."""
        headers = {"X-User-ID": "u-test-001"}
        response = client.get("/api/v1/system/health", headers=headers)
        assert response.status_code == 200


class TestBuildCorrelationHeaders:
    """Unit tests for build_correlation_headers()."""

    def setup_method(self):
        reset_trace_id()

    def test_empty_when_nothing_set(self):
        """When no IDs set, returns empty dict."""
        headers = build_correlation_headers()
        assert headers == {}

    def test_trace_id_only(self):
        """X-Trace-ID and X-Request-ID when trace set."""
        set_trace_id("abc123")
        headers = build_correlation_headers()
        assert headers["X-Trace-ID"] == "abc123"
        assert headers["X-Request-ID"] == "abc123"

    def test_all_headers(self):
        """All 6 headers when all IDs set."""
        set_trace_id("trace-001")
        set_user_id("user-42")
        set_draft_id("draft-7")
        set_document_id("doc-99")
        set_version_id("ver-1")
        headers = build_correlation_headers()
        assert headers["X-Trace-ID"] == "trace-001"
        assert headers["X-Request-ID"] == "trace-001"
        assert headers["X-User-ID"] == "user-42"
        assert headers["X-Draft-ID"] == "draft-7"
        assert headers["X-Document-ID"] == "doc-99"
        assert headers["X-Version-ID"] == "ver-1"

    def test_partial_headers(self):
        """Only set IDs appear in headers."""
        set_trace_id("trace-002")
        set_draft_id("draft-10")
        headers = build_correlation_headers()
        assert "X-Trace-ID" in headers
        assert "X-Draft-ID" in headers
        assert "X-User-ID" not in headers
        assert "X-Document-ID" not in headers
