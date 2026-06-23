"""
Tests for Tasks API endpoints.

Covers:
  - GET /tasks/{task_id} — task status with step details
  - GET /tasks/ — list tasks with filters and pagination
  - GET /tasks/stats — task statistics
  - GET /tasks/{task_id}/steps — task step list
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
            data={"document_key": key, "source_type": "GOST"},
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
        assert "meta" in data
        assert "total" in data["meta"]
        assert "page" in data["meta"]
        assert "page_size" in data["meta"]
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

    def test_draft_tasks(self, client: TestClient, auth_header: dict):
        """GET /drafts/{draft_id}/tasks returns task list for a draft."""
        task_id = self._create_task(client, auth_header, "doc-draft-tasks-test")

        # Get draft_id from task
        task_resp = client.get(f"/api/v1/tasks/{task_id}", headers=auth_header)
        assert task_resp.status_code == 200
        draft_id = task_resp.json()["draft_id"]

        response = client.get(
            f"/api/v1/drafts/{draft_id}/tasks", headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert "draft_id" in data
        assert data["draft_id"] == draft_id
        assert "tasks" in data
        assert isinstance(data["tasks"], list)
        assert len(data["tasks"]) >= 1

        task_item = data["tasks"][0]
        assert "task_id" in task_item
        assert task_item["task_id"] == task_id
        assert "status" in task_item
        assert "pipeline_stage" in task_item
        assert "initiated_by" in task_item
        assert "created_at" in task_item

    def test_draft_tasks_not_found(self, client: TestClient, auth_header: dict):
        """Non-existent draft returns empty task list (not 404)."""
        response = client.get(
            "/api/v1/drafts/99999/tasks", headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert data["draft_id"] == 99999
        assert data["tasks"] == []

    def test_task_stats(self, client: TestClient, auth_header: dict):
        """GET /tasks/stats returns statistics."""
        self._create_task(client, auth_header, "doc-stats-test")

        response = client.get("/api/v1/tasks/stats", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_status" in data
        assert "by_stage" in data

    def test_list_tasks_empty_db(self, client: TestClient, auth_header: dict):
        """Empty task list returns empty items."""
        response = client.get("/api/v1/tasks/", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["meta"]["total"] == 0

    def test_list_tasks_filter_by_draft_id(self, client: TestClient, auth_header: dict):
        """Filter tasks by draft_id."""
        from app.repositories.pipeline import TaskRepository
        from app.db.base import AsyncSessionLocal

        task_id = self._create_task(client, auth_header, "doc-filter-draft")
        # Get the draft_id from the task
        task_resp = client.get(f"/api/v1/tasks/{task_id}", headers=auth_header)
        draft_id = task_resp.json()["draft_id"]

        # Filter by exact draft_id
        response = client.get(
            f"/api/v1/tasks/?draft_id={draft_id}",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert all(item["draft_id"] == draft_id for item in data["items"])

    def test_list_tasks_filter_by_pipeline_type(self, client: TestClient, auth_header: dict):
        """Filter tasks by pipeline_type."""
        self._create_task(client, auth_header, "doc-formation-filter")

        response = client.get(
            "/api/v1/tasks/?pipeline_type=formation",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert all(item["pipeline_type"] == "formation" for item in data["items"])

    def test_list_tasks_pagination(self, client: TestClient, auth_header: dict):
        """Task list respects page_size."""
        self._create_task(client, auth_header, "doc-page-1")

        response = client.get(
            "/api/v1/tasks/?page_size=1",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["page_size"] == 1
        assert len(data["items"]) <= 1

    def test_task_stats_structure(self, client: TestClient, auth_header: dict):
        """Task stats contains by_status and by_stage breakdowns."""
        self._create_task(client, auth_header, "doc-stats-struct")

        response = client.get("/api/v1/tasks/stats", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["by_status"], dict)
        assert isinstance(data["by_stage"], dict)
        assert data["total"] >= 1


class TestTaskSteps:
    """Tests for GET /api/v1/tasks/{task_id}/steps."""

    URL = "/api/v1/tasks/{task_id}/steps"

    def _create_task(self, client: TestClient, auth_header: dict, key: str) -> int:
        """Helper: upload a draft and return task_id."""
        response = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            files={"file": ("test.pdf", b"%PDF-1.4 mock content", "application/pdf")},
            data={"document_key": key, "source_type": "GOST"},
        )
        assert response.status_code == 202
        return response.json()["task_id"]

    def test_get_steps_structure(self, client: TestClient, auth_header: dict):
        """Task steps endpoint returns valid structure."""
        task_id = self._create_task(client, auth_header, "doc-steps-struct")

        response = client.get(self.URL.format(task_id=task_id), headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert "steps" in data
        assert "total" in data
        assert isinstance(data["steps"], list)
        assert isinstance(data["total"], int)
        if data["steps"]:
            step = data["steps"][0]
            assert "step_name" in step
            assert "service_name" in step
            assert "status" in step

    def test_get_steps_not_found(self, client: TestClient, auth_header: dict):
        """Non-existent task returns 404."""
        response = client.get(self.URL.format(task_id=99999), headers=auth_header)
        assert response.status_code == 404


class TestTaskDetailsWithDbData:
    """Task details with directly created DB records."""

    URL = "/api/v1/tasks/{task_id}"
    STEPS_URL = "/api/v1/tasks/{task_id}/steps"

    async def _create_task_with_steps(
        self, db_session, draft_id: int = 900,
        pipeline_stage: str = "upload", status: str = "active",
    ) -> int:
        """Create task + steps directly in DB. Returns task_id."""
        from app.repositories.pipeline import TaskRepository
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=draft_id, pipeline_type="formation", total_steps=2,
        )
        task.pipeline_stage = pipeline_stage
        task.status = status
        await db_session.flush()

        # Create steps
        step1 = await repo.create_task_step(
            task_id=task.id, step_name="upload", step_index=0,
            service_name="Orchestrator",
            input_data={"file_key": "f-test.pdf"},
        )
        await repo.start_task_step(step1.id)
        await repo.complete_task_step(step1.id, output_data={"status": "ok"})

        step2 = await repo.create_task_step(
            task_id=task.id, step_name="preview_ocr", step_index=1,
            service_name="OCR Service",
        )
        await repo.start_task_step(step2.id)
        await db_session.commit()

        return task.id

    async def test_get_task_with_notifications(
        self, client: TestClient, auth_header: dict, db_session,
    ):
        """Task with notifications returns has_notifications=True."""
        from app.models.pipeline import DraftNotification

        task_id = await self._create_task_with_steps(db_session)

        # Add notifications
        notif = DraftNotification(
            task_id=task_id, draft_id=900,
            service="ocr", code="low_quality",
            message="Low quality", severity="warning",
        )
        db_session.add(notif)
        notif2 = DraftNotification(
            task_id=task_id, draft_id=900,
            service="ocr", code="missing_pages",
            message="Missing pages", severity="critical",
        )
        db_session.add(notif2)
        await db_session.commit()

        response = client.get(
            self.URL.format(task_id=task_id), headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_notifications"] is True
        assert data["critical_count"] >= 1
        assert len(data["steps"]) >= 2

    async def test_get_task_steps_with_data(
        self, client: TestClient, auth_header: dict, db_session,
    ):
        """Steps list contains step details."""
        task_id = await self._create_task_with_steps(db_session)

        response = client.get(
            self.STEPS_URL.format(task_id=task_id), headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["total"] >= 2
        assert len(data["steps"]) >= 2

        # Verify step structure
        step = data["steps"][0]
        assert "step_name" in step
        assert "service_name" in step
        assert "status" in step
        assert "input_data" in step
        assert "output_data" in step
        assert "started_at" in step
        assert "completed_at" in step

    async def test_task_stats_aggregation(
        self, client: TestClient, auth_header: dict, db_session,
    ):
        """Stats aggregates multiple tasks correctly."""
        # Create tasks with different states
        from app.repositories.pipeline import TaskRepository
        repo = TaskRepository(db_session)

        # Active + upload stage = "uploaded"
        t1 = await repo.create_task(draft_id=910, pipeline_type="formation", total_steps=1)
        t1.status = "active"
        t1.pipeline_stage = "upload"

        # Active + preview stage = "previewing"
        t2 = await repo.create_task(draft_id=911, pipeline_type="formation", total_steps=1)
        t2.status = "active"
        t2.pipeline_stage = "preview"

        # Completed + formation = "created"
        t3 = await repo.create_task(draft_id=912, pipeline_type="formation", total_steps=1)
        t3.status = "completed"

        # Failed
        t4 = await repo.create_task(draft_id=913, pipeline_type="formation", total_steps=1)
        t4.status = "failed"

        await db_session.commit()

        response = client.get("/api/v1/tasks/stats", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 4
        assert data["by_status"].get("uploaded", 0) >= 1
        assert data["by_status"].get("failed", 0) >= 1


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
            data={"document_key": "doc-task-no-auth", "title": "Test", "source_type": "GOST"},
        )
        assert response.status_code == 202
        return response.json()["task_id"]

    def test_get_task_without_auth(self, created_task_id: int, client: TestClient):
        """Request without auth returns 200 in mock mode."""
        response = client.get(self.URL.format(task_id=created_task_id))
        assert response.status_code == 200
