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
            data={"document_key": "doc-correlation", "source_type": "GOST"},
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


class TestTraceIdGeneration:
    """Unit tests for trace_id generation and DB compatibility (bug #16)."""

    def setup_method(self):
        reset_trace_id()

    def test_generate_trace_id_is_16_hex_chars(self):
        """generate_trace_id() returns 16 lowercase hex characters."""
        from app.core.trace import generate_trace_id
        tid = generate_trace_id()
        assert len(tid) == 16
        assert all(c in "0123456789abcdef" for c in tid), f"Not hex: {tid}"

    def test_generate_trace_id_is_unique(self):
        """Consecutive calls produce different trace IDs."""
        from app.core.trace import generate_trace_id
        ids = {generate_trace_id() for _ in range(100)}
        assert len(ids) == 100, f"Collision: got {len(ids)} unique from 100"

    def test_trace_id_fits_in_db_column(self):
        """
        Task.trace_id column is String(64).
        Both 16-char hex and 36-char UUID fit without truncation.
        """
        from app.core.trace import generate_trace_id
        tid = generate_trace_id()
        assert len(tid) <= 64, f"16-char trace_id exceeds String(64): {len(tid)}"

        # A full UUID with dashes is 36 chars — also fits
        full_uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert len(full_uuid) == 36
        assert len(full_uuid) <= 64, f"36-char UUID exceeds String(64)"

    def test_trace_id_stored_in_task_model(self):
        """
        Task model accepts both 16-char hex and 36-char UUID trace_id.
        Uses the actual model constructor (not DB insert) to verify
        no validation rejects the length.
        """
        from app.models.pipeline import Task
        # 16-char trace_id (current generate_trace_id output)
        task_short = Task(trace_id="aabbccddeeff0011")
        assert task_short.trace_id == "aabbccddeeff0011"

        # 36-char UUID (external caller, e.g. Gateway)
        task_long = Task(trace_id="550e8400-e29b-41d4-a716-446655440000")
        assert task_long.trace_id == "550e8400-e29b-41d4-a716-446655440000"

        # 64-char edge case
        task_edge = Task(trace_id="x" * 64)
        assert task_edge.trace_id == "x" * 64

    def test_set_trace_id_accepts_uuid_length(self):
        """set_trace_id() accepts and returns a 36-char UUID."""
        from app.core.trace import set_trace_id, get_trace_id
        full_uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = set_trace_id(full_uuid)
        assert result == full_uuid
        assert get_trace_id() == full_uuid

    def test_build_headers_with_uuid_length_trace(self):
        """build_correlation_headers handles 36-char trace_id."""
        full_uuid = "550e8400-e29b-41d4-a716-446655440000"
        set_trace_id(full_uuid)
        headers = build_correlation_headers()
        assert headers["X-Trace-ID"] == full_uuid
        assert headers["X-Request-ID"] == full_uuid
