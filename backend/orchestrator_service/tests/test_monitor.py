"""
Tests for Auth dependency behaviour in mock mode.

Covers:
  - Auth dependency behaviour (public vs protected paths)
"""

import pytest
from fastapi.testclient import TestClient


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
            ("GET", "/api/v1/drafts/1/tasks"),
            ("GET", "/api/v1/tasks"),
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

    def test_protected_post_endpoint_works_without_auth(self, client: TestClient):
        """Protected POST endpoints work in mock mode even without auth."""
        response = client.post(
            "/api/v1/drafts",
            data={"document_key": "test-key"},
        )
        assert response.status_code in (200, 201, 202, 422)
