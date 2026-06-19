"""
Tests for Tasks API endpoints.

Covers:
  - GET /tasks/{task_id} — task status with step details
  - GET /tasks/ — list tasks
  - GET /tasks/stats — task statistics
"""

import pytest
from fastapi.testclient import TestClient


class TestTaskStatus:
    """Tests for GET /api/v1/tasks/{task_id}."""

    URL = "/api/v1/tasks/{task_id}"

    def _create_task(self, client: TestClient, auth_header: dict, key: str) -> int:
        """Helper: upload a draft and return task_id."""
        response = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            files={"file": ("test.pdf", b"%PDF-1.4 mock content", "application/pdf")},
            data={"document_key": key},
        )
        assert response.status_code == 202
        return response.json()["task_id"]

    def test_get_task_structure(self, client: TestClient, auth_header: dict):
        """Task response has all required fields."""
        task_id = self._create_task(client, auth_header, "doc-struct-test")

        response = client.get(self.URL.format(task_id=task_id), headers=auth_header)
        assert response.status_code == 200
        data = response.json()

        assert "task_id" in data
        assert data["task_id"] == task_id
        assert "draft_id" in data
        assert "document_id" in data
        assert "version_id" in data
        assert "status" in data
        assert data["status"] in ("active", "completed", "failed")
        assert "pipeline_stage" in data
        assert "progress_percent" in data
        assert isinstance(data["progress_percent"], int)
        assert "has_notifications" in data
        assert "critical_count" in data
        assert isinstance(data["has_notifications"], bool)
        assert isinstance(data["critical_count"], int)
        assert "steps" in data
        assert isinstance(data["steps"], list)
        assert "created_at" in data

    def test_get_task_steps(self, client: TestClient, auth_header: dict):
        """Steps contain all expected fields."""
        task_id = self._create_task(client, auth_header, "doc-steps-test")

        response = client.get(self.URL.format(task_id=task_id), headers=auth_header)
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

    def test_get_task_progress(self, client: TestClient, auth_header: dict):
        """Progress is between 0 and 100."""
        task_id = self._create_task(client, auth_header, "doc-progress-test")

        response = client.get(self.URL.format(task_id=task_id), headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert 0 <= data["progress_percent"] <= 100

    def test_get_task_not_found(self, client: TestClient, auth_header: dict):
        """Non-existent task returns 404."""
        response = client.get(self.URL.format(task_id=99999), headers=auth_header)
        assert response.status_code == 404

    def test_list_tasks(self, client: TestClient, auth_header: dict):
        """GET /tasks returns paginated list."""
        # Create a task first
        self._create_task(client, auth_header, "doc-list-test")

        response = client.get("/api/v1/tasks/", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["items"], list)

    def test_list_tasks_filters(self, client: TestClient, auth_header: dict):
        """Task list filters by status."""
        self._create_task(client, auth_header, "doc-filter-test")

        response = client.get(
            "/api/v1/tasks/?status=active", headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert all(item["status"] == "active" for item in data["items"])

    def test_task_stats(self, client: TestClient, auth_header: dict):
        """GET /tasks/stats returns statistics."""
        self._create_task(client, auth_header, "doc-stats-test")

        response = client.get("/api/v1/tasks/stats", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "active" in data
        assert "completed" in data
        assert "failed" in data
        assert "by_type" in data


class TestTaskWithoutAuth:
    """Tests for GET /tasks/{task_id} without auth."""

    URL = "/api/v1/tasks/{task_id}"

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

    def test_get_task_without_auth(self, created_task_id: int, client: TestClient):
        """Request without auth returns 200 in mock mode."""
        response = client.get(self.URL.format(task_id=created_task_id))
        assert response.status_code == 200
