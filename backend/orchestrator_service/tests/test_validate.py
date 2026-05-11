"""
Tests for Validation API endpoints.

Covers:
  - POST /api/v1/validate/compare              — start comparison
  - GET  /api/v1/validate/compare/{id}          — get comparison result
  - POST /api/v1/validate/compare/batch         — batch comparison
  - POST /api/v1/validate/checks                — start check run
  - GET  /api/v1/validate/checks/{check_run_id} — check run status
  - GET  /api/v1/validate/checks/{check_run_id}/export — export results
"""

import pytest
from fastapi.testclient import TestClient


class TestStartComparison:
    """Tests for POST /api/v1/validate/compare"""

    COMPARE_URL = "/api/v1/validate/compare"

    def test_start_comparison_basic(self, client: TestClient, auth_header: dict):
        """Start a basic comparison returns 202 with comparison_id."""
        response = client.post(
            self.COMPARE_URL,
            json={
                "normative_query": "Толщина обшивки должна быть не менее 12 мм",
                "project_document_id": "doc-proj-001",
            },
            headers=auth_header,
        )
        assert response.status_code == 202
        data = response.json()
        assert "comparison_id" in data
        assert data["status"] == "processing"
        assert "created_at" in data

    def test_start_comparison_with_fragments(
        self, client: TestClient, auth_header: dict
    ):
        """Start comparison with specific fragment IDs."""
        response = client.post(
            self.COMPARE_URL,
            json={
                "normative_fragment_id": "frg-norm-001",
                "project_fragment_id": "frg-proj-001",
            },
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_start_comparison_returns_valid_uuid(
        self, client: TestClient, auth_header: dict
    ):
        """Comparison ID should follow the cmp-xxxxxxx pattern."""
        response = client.post(
            self.COMPARE_URL,
            json={"normative_query": "тест"},
            headers=auth_header,
        )
        data = response.json()
        assert data["comparison_id"].startswith("cmp-")
        assert len(data["comparison_id"]) == 11  # "cmp-" + 7 hex chars

    def test_start_comparison_created_at_valid(
        self, client: TestClient, auth_header: dict
    ):
        """created_at should be a valid ISO datetime string."""
        response = client.post(
            self.COMPARE_URL,
            json={"normative_query": "тест"},
            headers=auth_header,
        )
        data = response.json()
        from datetime import datetime

        # Should parse without error
        dt = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        assert dt is not None

    def test_start_comparison_empty_body(self, client: TestClient, auth_header: dict):
        """Empty body should still be accepted (all fields are optional)."""
        response = client.post(
            self.COMPARE_URL,
            json={},
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_start_comparison_without_auth(self, client: TestClient):
        """Start comparison without auth should succeed in mock mode."""
        response = client.post(
            self.COMPARE_URL,
            json={"normative_query": "тест"},
        )
        assert response.status_code == 202
        data = response.json()
        assert "comparison_id" in data


class TestGetComparisonResult:
    """Tests for GET /api/v1/validate/compare/{comparison_id}"""

    def test_get_comparison_result(self, client: TestClient, auth_header: dict):
        """Get comparison result by ID."""
        response = client.get(
            "/api/v1/validate/compare/cmp-mock-001",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["comparison_id"] == "cmp-mock-001"
        assert "match_status" in data
        assert "normative_block" in data
        assert "project_block" in data

    def test_comparison_result_full_structure(
        self, client: TestClient, auth_header: dict
    ):
        """Comparison result should contain all expected fields."""
        response = client.get(
            "/api/v1/validate/compare/cmp-mock-001",
            headers=auth_header,
        )
        data = response.json()
        for field in (
            "comparison_id",
            "status",
            "normative_block",
            "project_block",
            "match_status",
            "details",
            "sources",
            "disclaimer",
            "processing_time_ms",
        ):
            assert field in data, f"Missing field: {field}"

    def test_normative_block_structure(self, client: TestClient, auth_header: dict):
        """Normative block should contain document details."""
        response = client.get(
            "/api/v1/validate/compare/cmp-mock-001",
            headers=auth_header,
        )
        data = response.json()["normative_block"]
        for field in (
            "document_id",
            "document_title",
            "page_number",
            "requirement_text",
        ):
            assert field in data, f"Missing field: {field}"

    def test_project_block_structure(self, client: TestClient, auth_header: dict):
        """Project block should contain document details."""
        response = client.get(
            "/api/v1/validate/compare/cmp-mock-001",
            headers=auth_header,
        )
        data = response.json()["project_block"]
        for field in ("document_id", "document_title", "page_number", "parameter_text"):
            assert field in data, f"Missing field: {field}"

    @pytest.mark.parametrize(
        "status", ["match", "possible_discrepancy", "not_found_in_project"]
    )
    def test_comparison_match_status_values(
        self, client: TestClient, auth_header: dict, status: str
    ):
        """Comparison should accept various match statuses."""
        response = client.get(
            f"/api/v1/validate/compare/cmp-{status}",
            headers=auth_header,
        )
        assert response.status_code == 200
        assert response.json()["match_status"] in [
            "match",
            "possible_discrepancy",
            "not_found_in_project",
            "not_found_in_norm",
            "insufficient_data",
        ]

    def test_comparison_sources_list(self, client: TestClient, auth_header: dict):
        """Sources should be a list of source references."""
        response = client.get(
            "/api/v1/validate/compare/cmp-mock-001",
            headers=auth_header,
        )
        data = response.json()
        assert isinstance(data["sources"], list)
        if data["sources"]:
            source = data["sources"][0]
            assert "document_id" in source
            assert "page" in source

    def test_comparison_disclaimer_present(self, client: TestClient, auth_header: dict):
        """Disclaimer should be a non-empty string."""
        response = client.get(
            "/api/v1/validate/compare/cmp-mock-001",
            headers=auth_header,
        )
        disclaimer = response.json()["disclaimer"]
        assert isinstance(disclaimer, str)
        assert len(disclaimer) > 0

    def test_comparison_processing_time(self, client: TestClient, auth_header: dict):
        """Processing time should be >= 0."""
        response = client.get(
            "/api/v1/validate/compare/cmp-mock-001",
            headers=auth_header,
        )
        assert response.json()["processing_time_ms"] >= 0

    def test_get_nonexistent_comparison(self, client: TestClient, auth_header: dict):
        """Non-existent comparison returns mock data in mock mode."""
        response = client.get(
            "/api/v1/validate/compare/cmp-nonexistent",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["comparison_id"] == "cmp-nonexistent"

    def test_get_comparison_without_auth(self, client: TestClient):
        """Get comparison without auth should succeed in mock mode."""
        response = client.get("/api/v1/validate/compare/cmp-mock-001")
        assert response.status_code == 200
        data = response.json()
        assert "comparison_id" in data


class TestBatchCompare:
    """Tests for POST /api/v1/validate/compare/batch"""

    BATCH_URL = "/api/v1/validate/compare/batch"

    def test_batch_compare_basic(self, client: TestClient, auth_header: dict):
        """Batch compare with a list of pairs."""
        pairs = [
            {
                "normative_text": "Толщина обшивки ≥ 12 мм",
                "project_text": "Обшивка t=14 мм",
                "document_type": "specification",
            },
            {
                "normative_text": "Высота потолков ≥ 2.7 м",
                "project_text": "Высота 2.5 м",
                "document_type": "specification",
            },
        ]
        response = client.post(
            self.BATCH_URL,
            json=pairs,
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "batch_id" in data
        assert "comparisons" in data
        assert "total_pairs" in data
        assert data["total_pairs"] == len(pairs)

    def test_batch_compare_single_pair(self, client: TestClient, auth_header: dict):
        """Batch compare with a single pair."""
        response = client.post(
            self.BATCH_URL,
            json=[
                {
                    "normative_text": "тест",
                    "project_text": "тест",
                    "document_type": "normative",
                }
            ],
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_pairs"] == 1
        assert data["matched"] >= 0

    def test_batch_compare_summary_counts(self, client: TestClient, auth_header: dict):
        """Batch response should include discrepancy counts."""
        response = client.post(
            self.BATCH_URL,
            json=[
                {
                    "normative_text": "требование 1",
                    "project_text": "проект 1",
                    "document_type": "normative",
                },
            ],
            headers=auth_header,
        )
        data = response.json()
        for field in ("matched", "discrepancies_found", "insufficient_data"):
            assert field in data
            assert isinstance(data[field], int)
            assert data[field] >= 0

    def test_batch_compare_comparison_items(
        self, client: TestClient, auth_header: dict
    ):
        """Each comparison in batch should have required fields."""
        response = client.post(
            self.BATCH_URL,
            json=[
                {
                    "normative_text": "тест 1",
                    "project_text": "проект 1",
                    "document_type": "normative",
                },
                {
                    "normative_text": "тест 2",
                    "project_text": "проект 2",
                    "document_type": "specification",
                },
            ],
            headers=auth_header,
        )
        data = response.json()
        for comp in data["comparisons"]:
            for field in ("comparison_id", "match_status", "summary"):
                assert field in comp, f"Missing field: {field}"

    def test_batch_compare_empty_list(self, client: TestClient, auth_header: dict):
        """Empty pair list should be accepted (edge case)."""
        response = client.post(
            self.BATCH_URL,
            json=[],
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_batch_compare_without_auth(self, client: TestClient):
        """Batch compare without auth should succeed in mock mode."""
        response = client.post(
            self.BATCH_URL,
            json=[
                {
                    "normative_text": "тест",
                    "project_text": "тест",
                    "document_type": "normative",
                }
            ],
        )
        assert response.status_code == 200
        data = response.json()
        assert "batch_id" in data

    def test_batch_compare_invalid_input(self, client: TestClient, auth_header: dict):
        """Invalid input type should fail."""
        response = client.post(
            self.BATCH_URL,
            json={"not_a_list": True},
            headers=auth_header,
        )
        assert response.status_code == 422


class TestCheckRun:
    """Tests for POST /api/v1/validate/checks"""

    CHECKS_URL = "/api/v1/validate/checks"

    def test_start_check_run(self, client: TestClient, auth_header: dict):
        """Start a check run returns 201 with check results."""
        response = client.post(
            self.CHECKS_URL,
            headers=auth_header,
        )
        assert response.status_code == 201
        data = response.json()
        assert "check_run_id" in data
        assert data["status"] == "completed"
        assert "summary" in data
        assert "items" in data

    def test_check_run_summary_structure(self, client: TestClient, auth_header: dict):
        """Check run summary should have ok/warning/error counts."""
        response = client.post(
            self.CHECKS_URL,
            headers=auth_header,
        )
        summary = response.json()["summary"]
        for field in ("ok", "warning", "error"):
            assert field in summary
            assert isinstance(summary[field], int)
            assert summary[field] >= 0

    def test_check_run_items_structure(self, client: TestClient, auth_header: dict):
        """Each check item should have required fields."""
        response = client.post(
            self.CHECKS_URL,
            headers=auth_header,
        )
        data = response.json()
        if data["items"]:
            item = data["items"][0]
            for field in (
                "check_item_id",
                "project",
                "section",
                "parameter",
                "project_value",
                "nsi_requirement",
                "nsi_document",
                "status",
            ):
                assert field in item, f"Missing field: {field}"

    def test_check_run_item_status_values(self, client: TestClient, auth_header: dict):
        """Check item status should be one of ok/warning/error."""
        response = client.post(
            self.CHECKS_URL,
            headers=auth_header,
        )
        data = response.json()
        valid_statuses = {"ok", "warning", "error"}
        for item in data["items"]:
            assert item["status"] in valid_statuses, f"Invalid status: {item['status']}"

    def test_check_run_sources_structure(self, client: TestClient, auth_header: dict):
        """Check sources should have document_id and page."""
        response = client.post(
            self.CHECKS_URL,
            headers=auth_header,
        )
        data = response.json()
        for item in data["items"]:
            for source_field in ("project_source", "nsi_source"):
                source = item.get(source_field)
                if source:
                    assert "document_id" in source
                    assert "page" in source

    def test_check_run_id_format(self, client: TestClient, auth_header: dict):
        """Check run ID should start with chk-."""
        response = client.post(
            self.CHECKS_URL,
            headers=auth_header,
        )
        check_run_id = response.json()["check_run_id"]
        assert check_run_id.startswith("chk-")

    def test_check_run_without_auth(self, client: TestClient):
        """Start check run without auth should succeed in mock mode."""
        response = client.post(self.CHECKS_URL)
        assert response.status_code == 201
        data = response.json()
        assert "check_run_id" in data


class TestCheckRunStatus:
    """Tests for GET /api/v1/validate/checks/{check_run_id}"""

    def test_get_check_run_status(self, client: TestClient, auth_header: dict):
        """Get check run status returns 200 with progress."""
        response = client.get(
            "/api/v1/validate/checks/chk-mock-001",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["check_run_id"] == "chk-mock-001"
        assert "status" in data
        assert "progress_percent" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_check_run_progress_percent(self, client: TestClient, auth_header: dict):
        """Progress percent should be between 0 and 100."""
        response = client.get(
            "/api/v1/validate/checks/chk-mock-001",
            headers=auth_header,
        )
        progress = response.json()["progress_percent"]
        assert 0.0 <= progress <= 100.0

    def test_check_run_timestamps(self, client: TestClient, auth_header: dict):
        """Timestamps should be valid ISO datetime strings."""
        response = client.get(
            "/api/v1/validate/checks/chk-mock-001",
            headers=auth_header,
        )
        data = response.json()
        from datetime import datetime

        for field in ("created_at", "updated_at"):
            dt = datetime.fromisoformat(data[field].replace("Z", "+00:00"))
            assert dt is not None

    def test_get_nonexistent_check_run(self, client: TestClient, auth_header: dict):
        """Non-existent check run returns mock data in mock mode."""
        response = client.get(
            "/api/v1/validate/checks/chk-nonexistent",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["check_run_id"] == "chk-nonexistent"

    def test_get_check_run_without_auth(self, client: TestClient):
        """Get check run status without auth should succeed in mock mode."""
        response = client.get("/api/v1/validate/checks/chk-mock-001")
        assert response.status_code == 200
        data = response.json()
        assert "check_run_id" in data


class TestCheckRunExport:
    """Tests for GET /api/v1/validate/checks/{check_run_id}/export"""

    def test_export_check_run(self, client: TestClient, auth_header: dict):
        """Export check run results."""
        response = client.get(
            "/api/v1/validate/checks/chk-mock-001/export",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["check_run_id"] == "chk-mock-001"
        assert "export_url" in data
        assert "format" in data
        assert "created_at" in data

    def test_export_url_format(self, client: TestClient, auth_header: dict):
        """Export URL should end with '/report.xlsx'."""
        response = client.get(
            "/api/v1/validate/checks/chk-mock-001/export",
            headers=auth_header,
        )
        data = response.json()
        assert data["export_url"].endswith("/report.xlsx")
        assert data["format"] in ("xlsx", "csv", "pdf")

    def test_export_without_auth(self, client: TestClient):
        """Export without auth should succeed in mock mode."""
        response = client.get("/api/v1/validate/checks/chk-mock-001/export")
        assert response.status_code == 200
        data = response.json()
        assert "export_url" in data
