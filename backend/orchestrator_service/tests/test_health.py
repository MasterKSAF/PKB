"""
Tests for health and system endpoints.

These endpoints are public (no authentication required).
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Tests for GET /"""

    def test_root_returns_service_info(self, client: TestClient):
        """Root endpoint should return service name and version."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "orchestrator-service"
        assert "version" in data
        assert "docs" in data
        assert data["docs"] == "/docs"

    def test_root_has_valid_version(self, client: TestClient):
        """Version should be a non-empty string."""
        response = client.get("/")
        data = response.json()
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0


class TestHealthEndpoint:
    """Tests for GET /api/v1/system/health"""

    def test_health_check_returns_ok(self, client: TestClient):
        """Health check should return 200 with overall status."""
        response = client.get("/api/v1/system/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], int)

    def test_health_check_services_status(self, client: TestClient):
        """All external services should report 'ok' in mock mode."""
        response = client.get("/api/v1/system/health")
        data = response.json()
        services = data["services"]
        expected_services = {"auth", "rag", "ocr", "validation", "integration"}
        assert set(services.keys()) == expected_services
        for service_name, status in services.items():
            assert status == "ok", f"Service {service_name} should be 'ok'"

    def test_health_check_subsystem_status(self, client: TestClient):
        """Subsystems like database, search_index, etc. should be 'ok'."""
        response = client.get("/api/v1/system/health")
        data = response.json()
        for key in ("database", "search_index", "ocr_queue", "storage"):
            assert data[key] == "ok", f"Subsystem {key} should be 'ok'"

    def test_health_check_uptime_is_positive(self, client: TestClient):
        """Uptime should be a non-negative integer."""
        response = client.get("/api/v1/system/health")
        data = response.json()
        assert data["uptime_seconds"] >= 0

    def test_health_check_public_no_auth(self, client: TestClient):
        """Health endpoint should be accessible without auth token."""
        response = client.get("/api/v1/system/health", headers={})
        assert response.status_code == 200

    def test_health_check_cors_headers(self, client: TestClient):
        """Health response should include CORS headers."""
        response = client.get(
            "/api/v1/system/health",
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 200
        # FastAPI CORS middleware adds the header
        cors_origin = response.headers.get("access-control-allow-origin")
        assert cors_origin is not None


class TestOpenAPIEndpoints:
    """Tests for OpenAPI documentation endpoints (public)."""

    def test_docs_swagger_ui(self, client: TestClient):
        """Swagger UI should be available at /docs."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_redoc_ui(self, client: TestClient):
        """ReDoc should be available at /redoc."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_openapi_json(self, client: TestClient):
        """OpenAPI schema should be available at /openapi.json."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["openapi"].startswith("3.")
        assert data["info"]["title"] == "Orchestrator Service API"

    def test_openapi_has_all_paths(self, client: TestClient):
        """OpenAPI should include all documented API paths."""
        response = client.get("/openapi.json")
        data = response.json()
        paths = data.get("paths", {})
        assert "/api/v1/system/health" in paths
        assert "/api/v1/documents/" in paths
        assert "/api/v1/documents/search" in paths
        assert "/api/v1/ask" in paths
        assert "/api/v1/validate/compare" in paths
