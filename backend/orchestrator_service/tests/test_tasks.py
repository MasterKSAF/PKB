"""
Tests for Tasks API endpoints.

Covers:
  - GET /tasks/{task_id}/status — task status with step details
"""

import pytest
from fastapi.testclient import TestClient


class TestTaskStatus:
    """Tests for GET /api/v1/tasks/{task_id}/status."""

    URL = "/api/v1/tasks/{task_id}/status"

    def test_get_task_status_structure(self, client: TestClient, auth_header: dict):
        """Status response has all required fields."""
        # First create a draft to ensure a task exists in DB
        response = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            files={"file": ("test.pdf", b"%PDF-1.4 mock content", "application/pdf")},
            data={"document_key": "doc-task-test"},
        )
        assert response.status_code == 202
        task_id = response.json()["task_id"]

        # Now get task status
        response = client.get(
            self.URL.format(task_id=task_id),
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()

        assert "task_id" in data
        assert data["task_id"] == task_id
        assert "draft_id" in data
        assert "document_id" in data
        assert "status" in data
        assert data["status"] in ("active", "completed", "failed")
        assert "pipeline_stage" in data
        assert "progress_percent" in data
        assert isinstance(data["progress_percent"], int)
        assert "steps" in data
        assert isinstance(data["steps"], list)
        assert "created_at" in data

    def test_get_task_status_steps(self, client: TestClient, auth_header: dict):
        """Steps contain all expected fields."""
        # Create a draft to generate task + steps
        response = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            files={"file": ("test.pdf", b"%PDF-1.4 mock content", "application/pdf")},
            data={"document_key": "doc-steps-test"},
        )
        assert response.status_code == 202
        task_id = response.json()["task_id"]

        response = client.get(
            self.URL.format(task_id=task_id),
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()

        if data["steps"]:
            step = data["steps"][0]
            assert "step_name" in step
            assert "service_name" in step
            assert "status" in step
            assert "input_data" in step or step.get("input_data") is None
            assert "output_data" in step or step.get("output_data") is None
            assert "started_at" in step or step.get("started_at") is None
            assert "completed_at" in step or step.get("completed_at") is None

    def test_get_task_status_progress(self, client: TestClient, auth_header: dict):
        """Progress is between 0 and 100."""
        response = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            files={"file": ("test.pdf", b"%PDF-1.4 content", "application/pdf")},
            data={"document_key": "doc-progress-test"},
        )
        task_id = response.json()["task_id"]

        response = client.get(
            self.URL.format(task_id=task_id),
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert 0 <= data["progress_percent"] <= 100

    def test_get_task_status_not_found(self, client: TestClient, auth_header: dict):
        """Non-existent task returns 404."""
        response = client.get(
            self.URL.format(task_id=99999),
            headers=auth_header,
        )
        assert response.status_code == 404
        data = response.json()
        # FastAPI wraps HTTPException.detail in {"detail": ...}
        assert "error" in data.get("detail", data)


class TestTaskStatusWithoutAuth:
    """Tests for GET /tasks/{task_id}/status without auth."""

    URL = "/api/v1/tasks/{task_id}/status"

    @pytest.fixture
    def created_task_id(self, client: TestClient, auth_header: dict) -> int:
        """Create a draft and return its task_id."""
        response = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            files={"file": ("test.pdf", b"%PDF mock", "application/pdf")},
            data={"document_key": "doc-task-no-auth", "title": "Test"},
        )
        assert response.status_code == 202
        return response.json()["task_id"]

    def test_get_task_status_without_auth(self, created_task_id: int, client: TestClient):
        """Request without auth returns 200 in mock mode."""
        response = client.get(self.URL.format(task_id=created_task_id))
        assert response.status_code == 200
