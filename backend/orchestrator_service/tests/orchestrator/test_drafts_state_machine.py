"""
State Machine Violations — табличный тест [действие × stage].

Проверяет все 30 комбинаций 5 действий × 6 этапов:
  - approve, reject, proceed, stop_duplicate, force_new_version
  - upload, preview, decision, full, registry, indexation

Каждая комбинация проверяет HTTP-статус и код ошибки (если 409).
"""

import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

# Actions and their allowed stages (source: decide_draft in drafts.py)
# approve/reject/proceed/force_new_version → allowed: decision, upload, preview
# stop_duplicate → allowed: preview, decision
ALLOWED_STAGES = {
    "approve": {"decision", "upload", "preview"},
    "reject": {"decision", "upload", "preview"},
    "proceed": {"decision", "upload", "preview"},
    "force_new_version": {"decision", "upload", "preview"},
    "stop_duplicate": {"preview", "decision"},
}

STAGES = ["upload", "preview", "decision", "full", "registry", "indexation"]
ACTIONS = ["approve", "reject", "proceed", "stop_duplicate", "force_new_version"]


def _expected_status(action: str, stage: str) -> tuple[int, str | None]:
    """Return (http_status, expected_error_code) for action+stage."""
    if stage in ALLOWED_STAGES[action]:
        return 200, None
    return 409, "INVALID_STAGE"


# Build parametrized list: (action, stage, expected_status, expected_error)
PARAMETRIZED_CASES = [
    (action, stage, *_expected_status(action, stage))
    for action in ACTIONS
    for stage in STAGES
]


class TestDecideActionStageMatrix:
    """Матричный тест: все комбинации действие × этап."""

    URL = "/api/v1/drafts/{draft_id}/decide"

    @pytest.fixture
    async def created_draft(self, client: TestClient, auth_header: dict, db_session: AsyncSession) -> int:
        """Create a draft and set it to a known base state."""
        response = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-matrix"), "application/pdf")},
            data={"document_key": "doc-matrix", "title": "Matrix Test", "source_type": "GOST"},
        )
        assert response.status_code == 202
        return response.json()["draft_id"]

    @pytest.mark.parametrize("action,stage,expected_status,expected_error", PARAMETRIZED_CASES)
    async def test_decide_action_stage_combination(
        self,
        action: str,
        stage: str,
        expected_status: int,
        expected_error: str | None,
        created_draft: int,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """Проверка одной комбинации действие × этап."""
        # Set task to the target stage
        from sqlalchemy import select
        from app.models.pipeline import Task

        result = await db_session.execute(
            select(Task).where(Task.draft_id == created_draft)
        )
        task = result.scalar_one_or_none()
        assert task is not None, "Task must exist after draft creation"

        task.pipeline_stage = stage
        task.status = "active"
        await db_session.flush()
        await db_session.commit()

        # Call decide
        response = client.patch(
            self.URL.format(draft_id=created_draft),
            headers=auth_header,
            json={"action": action},
        )

        assert response.status_code == expected_status, (
            f"action={action}, stage={stage}: "
            f"expected {expected_status}, got {response.status_code}, body={response.text}"
        )

        if expected_error:
            data = response.json()
            detail = data.get("detail", data)
            assert "error" in detail, f"Expected error detail, got: {data}"
            assert detail["error"]["code"] == expected_error, (
                f"action={action}, stage={stage}: "
                f"expected error code {expected_error}, got {detail['error']['code']}"
            )


class TestDecideTerminalTaskAllActions:
    """Все действия на терминальной задаче (completed/failed) → 409."""

    URL = "/api/v1/drafts/{draft_id}/decide"
    TERMINAL_STATUSES = ["completed", "failed"]

    @pytest.fixture
    async def created_draft(self, client: TestClient, auth_header: dict, db_session: AsyncSession) -> int:
        response = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-term"), "application/pdf")},
            data={"document_key": "doc-terminal", "title": "Terminal Test", "source_type": "GOST"},
        )
        assert response.status_code == 202
        return response.json()["draft_id"]

    @pytest.mark.parametrize("action", ACTIONS)
    @pytest.mark.parametrize("terminal_status", TERMINAL_STATUSES)
    async def test_terminal_task_returns_409(
        self,
        action: str,
        terminal_status: str,
        created_draft: int,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """Любое действие на completed/failed задаче → 409 TASK_ALREADY_TERMINAL."""
        from sqlalchemy import select
        from app.models.pipeline import Task

        result = await db_session.execute(
            select(Task).where(Task.draft_id == created_draft)
        )
        task = result.scalar_one_or_none()
        assert task is not None
        task.status = terminal_status
        task.pipeline_stage = "decision"
        await db_session.flush()
        await db_session.commit()

        response = client.patch(
            self.URL.format(draft_id=created_draft),
            headers=auth_header,
            json={"action": action},
        )

        assert response.status_code == 409, (
            f"action={action}, terminal={terminal_status}: expected 409, "
            f"got {response.status_code}, body={response.text}"
        )
        data = response.json()
        detail = data.get("detail", data)
        assert detail["error"]["code"] == "TASK_ALREADY_TERMINAL"
