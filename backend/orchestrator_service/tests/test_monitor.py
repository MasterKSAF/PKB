"""
Tests for Monitor and Auth API endpoints.

Covers:
  - GET /api/v1/monitor/metrics — system monitoring metrics
  - Auth dependency behaviour (public vs protected paths)
"""

import pytest
from fastapi.testclient import TestClient


class TestMonitorMetrics:
    """Tests for GET /api/v1/monitor/metrics"""

    METRICS_URL = "/api/v1/monitor/metrics"

    def test_get_metrics(self, client: TestClient, auth_header: dict):
        """Get system monitoring metrics returns 200 with data."""
        response = client.get(self.METRICS_URL, headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "control_metrics" in data
        assert "answer_metrics" in data
        assert "logs" in data

    def test_control_metrics_structure(self, client: TestClient, auth_header: dict):
        """Control metrics should contain quality indicators."""
        response = client.get(self.METRICS_URL, headers=auth_header)
        cm = response.json()["control_metrics"]
        for field in (
            "ocr_quality",
            "retrieval_quality",
            "answers_with_sources",
            "avg_latency_ms",
        ):
            assert field in cm, f"Missing field: {field}"

    def test_control_metrics_range(self, client: TestClient, auth_header: dict):
        """Quality metrics should be between 0 and 1."""
        response = client.get(self.METRICS_URL, headers=auth_header)
        cm = response.json()["control_metrics"]
        for field in ("ocr_quality", "retrieval_quality", "answers_with_sources"):
            assert 0.0 <= cm[field] <= 1.0, f"{field} out of range: {cm[field]}"

    def test_control_metrics_latency(self, client: TestClient, auth_header: dict):
        """Average latency should be a positive integer."""
        response = client.get(self.METRICS_URL, headers=auth_header)
        cm = response.json()["control_metrics"]
        assert isinstance(cm["avg_latency_ms"], int)
        assert cm["avg_latency_ms"] > 0

    def test_answer_metrics_structure(self, client: TestClient, auth_header: dict):
        """Answer metrics should contain usage statistics."""
        response = client.get(self.METRICS_URL, headers=auth_header)
        am = response.json()["answer_metrics"]
        for field in (
            "useful_rate",
            "rated_answers",
            "flagged_for_review",
            "open_questions",
        ):
            assert field in am, f"Missing field: {field}"

    def test_answer_metrics_useful_rate(self, client: TestClient, auth_header: dict):
        """Useful rate should be between 0 and 1."""
        response = client.get(self.METRICS_URL, headers=auth_header)
        am = response.json()["answer_metrics"]
        assert 0.0 <= am["useful_rate"] <= 1.0

    def test_answer_metrics_counts(self, client: TestClient, auth_header: dict):
        """Count metrics should be non-negative integers."""
        response = client.get(self.METRICS_URL, headers=auth_header)
        am = response.json()["answer_metrics"]
        for field in ("rated_answers", "flagged_for_review", "open_questions"):
            assert isinstance(am[field], int)
            assert am[field] >= 0

    def test_logs_structure(self, client: TestClient, auth_header: dict):
        """Log entries should have required fields."""
        response = client.get(self.METRICS_URL, headers=auth_header)
        logs = response.json()["logs"]
        assert isinstance(logs, list)
        if logs:
            entry = logs[0]
            for field in ("time", "type", "text", "level"):
                assert field in entry, f"Missing field: {field}"

    def test_log_entry_types(self, client: TestClient, auth_header: dict):
        """Log entry types should be recognized categories."""
        response = client.get(self.METRICS_URL, headers=auth_header)
        logs = response.json()["logs"]
        valid_types = {"system", "search", "validation", "auth", "ocr", "error"}
        for entry in logs:
            assert entry["type"] in valid_types, f"Unknown type: {entry['type']}"

    def test_log_levels(self, client: TestClient, auth_header: dict):
        """Log levels should be standard severity levels."""
        response = client.get(self.METRICS_URL, headers=auth_header)
        logs = response.json()["logs"]
        valid_levels = {"info", "warning", "error", "debug"}
        for entry in logs:
            assert entry["level"] in valid_levels, f"Unknown level: {entry['level']}"

    def test_metrics_without_auth_in_mock_mode(self, client: TestClient):
        """In mock mode, metrics endpoint works even without auth token."""
        response = client.get(self.METRICS_URL)
        assert response.status_code == 200
        data = response.json()
        assert "control_metrics" in data

    def test_metrics_with_invalid_token(self, client: TestClient):
        """In mock mode, any token is accepted."""
        response = client.get(
            self.METRICS_URL,
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 200


class TestAuthBehaviourInMockMode:
    """Tests for auth dependency behaviour in mock mode.

    In mock mode (AUTH_SERVICE_MOCK=true), the auth dependency returns
    a MOCK_USER for any request to protected endpoints, so all endpoints
    work without a real token.
    """

    def test_public_health_endpoint(self, client: TestClient):
        """Health endpoint should be accessible without auth."""
        response = client.get("/api/v1/system/health")
        assert response.status_code == 200

    def test_public_docs_endpoints(self, client: TestClient):
        """Documentation endpoints should be accessible without auth."""
        for path in ("/docs", "/redoc", "/openapi.json"):
            response = client.get(path)
            assert response.status_code in (200, 307), f"Failed for {path}"

    def test_protected_endpoints_work_in_mock_mode(self, client: TestClient):
        """In mock mode, protected endpoints return data without auth token."""
        protected_paths = [
            ("GET", "/api/v1/documents/"),
            ("GET", "/api/v1/documents/doc-mock-001"),
            ("GET", "/api/v1/documents/search"),
            ("POST", "/api/v1/ask"),
            ("POST", "/api/v1/validate/compare"),
            ("POST", "/api/v1/validate/checks"),
        ]
        for method, path in protected_paths:
            if method == "GET":
                response = client.get(path)
            else:
                response = client.post(
                    path,
                    json={"question": "тест"} if "ask" in path else {},
                )
            assert response.status_code in (200, 201, 202), (
                f"Expected 2xx for {method} {path} in mock mode, "
                f"got {response.status_code}"
            )

    def test_mock_auth_accepts_any_token(self, client: TestClient):
        """In mock mode, any Bearer token should be accepted."""
        response = client.get(
            "/api/v1/monitor/metrics",
            headers={"Authorization": "Bearer some_random_token"},
        )
        assert response.status_code == 200

    def test_protected_post_endpoint_works_without_auth(self, client: TestClient):
        """Protected POST endpoints work in mock mode even without auth."""
        response = client.post(
            "/api/v1/validate/compare",
            json={"normative_query": "тест"},
        )
        assert response.status_code == 202
