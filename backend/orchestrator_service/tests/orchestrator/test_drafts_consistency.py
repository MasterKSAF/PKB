"""
Data consistency, mock-real gap, boundary conditions для Drafts API.

Покрывает:
  1. Consistency: после approve document_id ≠ None + is_new_document=False в Registry
  2. Mock-real gap: draft_id=0 в storage, ключи id=0/draft_id
  3. Boundary: file_size=MAX, metadata=null, title=""
  4. Idempotency: двойной POST /drafts, двойной POST /drafts/{id}/preview
"""

import io
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


# ============================================================================
#  1. Data consistency — после approve
# ============================================================================


class TestApproveConsistency:
    """Согласованность данных после approve: document_id в Registry."""

    CREATE_URL = "/api/v1/drafts/"
    DECIDE_URL = "/api/v1/drafts/{draft_id}/decide"
    GET_DRAFT_URL = "/api/v1/drafts/{draft_id}"

    @pytest.fixture
    async def created_draft(self, client: TestClient, auth_header: dict, db_session: AsyncSession) -> int:
        resp = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-consistency"), "application/pdf")},
            data={"document_key": "doc-consistency", "title": "Consistency", "source_type": "GOST"},
        )
        assert resp.status_code == 202
        return resp.json()["draft_id"]

    async def test_approve_sets_document_id_in_registry(
        self,
        created_draft: int,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """После approve:
        1. GET /drafts/{id} должен показывать document_id (не None)
        2. is_new_document должен быть False
        3. Registry draft.document_id должен быть установлен
        """
        # Advance task to decision stage
        from sqlalchemy import select
        from app.models.pipeline import Task

        result = await db_session.execute(
            select(Task).where(Task.draft_id == created_draft)
        )
        task = result.scalar_one_or_none()
        assert task is not None
        task.pipeline_stage = "decision"
        task.status = "active"
        await db_session.flush()
        await db_session.commit()

        # Approve
        decide_resp = client.patch(
            self.DECIDE_URL.format(draft_id=created_draft),
            headers=auth_header,
            json={"action": "approve"},
        )
        assert decide_resp.status_code == 200, f"Approve failed: {decide_resp.text}"
        decide_data = decide_resp.json()
        assert decide_data["document_id"] is not None, "document_id must not be None after approve"
        doc_id = decide_data["document_id"]

        # GET /drafts/{id} — прокси в Registry
        get_resp = client.get(
            self.GET_DRAFT_URL.format(draft_id=created_draft),
            headers=auth_header,
        )
        assert get_resp.status_code == 200, f"GET draft failed: {get_resp.text}"
        get_data = get_resp.json()

        # Registry должен знать о document_id
        reg_doc_id = get_data.get("document_id")
        is_new = get_data.get("is_new_document")

        assert reg_doc_id == doc_id, (
            f"Registry draft.document_id ({reg_doc_id}) != created document_id ({doc_id})"
        )
        assert is_new is False, "is_new_document should be False after approve"

    async def test_approve_document_id_in_decision_response(
        self,
        created_draft: int,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """document_id и version_id в ответе decide после approve."""
        from sqlalchemy import select
        from app.models.pipeline import Task

        result = await db_session.execute(
            select(Task).where(Task.draft_id == created_draft)
        )
        task = result.scalar_one_or_none()
        assert task is not None
        task.pipeline_stage = "decision"
        task.status = "active"
        await db_session.flush()
        await db_session.commit()

        response = client.patch(
            self.DECIDE_URL.format(draft_id=created_draft),
            headers=auth_header,
            json={"action": "approve"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] is not None, "document_id must be present after approve"
        assert data["version_id"] is not None, "version_id must be present after approve"
        assert data["is_new_document"] is True, "First approve should be is_new_document=True"
        assert data["status"] == "proceeding"
        assert data["action"] == "approve"


# ============================================================================
#  2. Mock-real gap: draft_id=0 и ключи id=0/draft_id
# ============================================================================


class TestMockRealGap:
    """Проверки на расхождение mock-логики с реальностью."""

    def test_draft_id_zero_returns_not_found(
        self, client: TestClient, auth_header: dict
    ):
        """draft_id=0: _SEED_DRAFTS.get(0) → None → 404.

        Проверяет, что draft_id=0 корректно обрабатывается.
        """
        response = client.get(
            "/api/v1/drafts/0",
            headers=auth_header,
        )
        assert response.status_code == 404

    def test_draft_id_zero_after_create(
        self, client: TestClient, auth_header: dict
    ):
        """Созданный черновик, id принудительно установлен в 0.

        Проверяет, что data.get("id")=0 корректно возвращается,
        а не фолбечится на data.get("draft_id") из-за falsy 0.
        """

        # Create draft
        create_resp = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock-id-zero"), "application/pdf")},
            data={"document_key": "doc-id-zero", "source_type": "GOST"},
        )
        assert create_resp.status_code == 202
        draft_id = create_resp.json()["draft_id"]

        # Directly set id=0 in Registry storage
        from app.services.registry_client import RegistryServiceClient
        storage = RegistryServiceClient._storage
        if draft_id in storage["drafts"]:
            storage["drafts"][draft_id]["id"] = 0

        # GET draft — прокси в Registry
        response = client.get(
            f"/api/v1/drafts/{draft_id}",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()

        # Если id=0, то data.get("id") → 0 (falsy),
        # используется data.get("draft_id") — его может не быть
        draft_id_in_response = data.get("draft_id")
        assert draft_id_in_response is not None, (
            "BUG: draft_id is None because data.get('id') returned 0 (falsy), "
            "and data.get('draft_id') also returned None. "
            "Endpoint should use: data.get('id') if data.get('id') is not None else data.get('draft_id')"
        )

    def test_get_draft_with_id_zero_in_storage(
        self, client: TestClient, auth_header: dict
    ):
        """Registry storage с id=0 — проверка _mock_get_draft."""
        from app.services.registry_client import RegistryServiceClient
        storage = RegistryServiceClient._storage

        # Create a draft at mock level with id=0
        draft = {
            "id": 0,
            "draft_id": 999,
            "file_key": "test-key",
            "status": "uploaded",
            "created_by": "test",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        storage["drafts"][999] = draft

        response = client.get(
            "/api/v1/drafts/999",
            headers=auth_header,
        )

        # Endpoint now uses: data.get("id") if data.get("id") is not None else data.get("draft_id")
        # data.get("id") = 0 → not None → returns 0 (correct, был баг: 0 falsy → 999)
        assert response.status_code == 200
        data = response.json()
        # After fix: id=0 is returned properly, not as 999 fallback
        assert data["draft_id"] == 0, (
            f"Expected draft_id=0 (correct id after fix), got {data.get('draft_id')}. "
            f"Id in response: {data.get('id')}"
        )

    def test_draft_id_zero_without_draft_id_in_storage(
        self, client: TestClient, auth_header: dict
    ):
        """Registry storage с id=0 и без draft_id — фикс 0 is falsy.

        После фикса: data.get("id")=0 возвращается корректно (0),
        а не None из-за falsy 0.
        """
        from app.services.registry_client import RegistryServiceClient
        storage = RegistryServiceClient._storage

        # draft with id=0, NO draft_id key at all
        draft = {
            "id": 0,
            "file_key": "test-key-no-draft-id",
            "status": "uploaded",
            "created_by": "test",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        storage["drafts"][998] = draft

        response = client.get(
            "/api/v1/drafts/998",
            headers=auth_header,
        )

        assert response.status_code == 200
        data = response.json()
        # After fix: id=0 is NOT falsy → draft_id=0 (not None)
        assert data["draft_id"] == 0, (
            f"Expected draft_id=0 (fix: id=0 should not be falsy), "
            f"got {data.get('draft_id')}. Full response: {data}"
        )


# ============================================================================
#  3. Boundary conditions
# ============================================================================


class TestBoundaryConditions:
    """Граничные значения для POST /drafts."""

    URL = "/api/v1/drafts/"

    def test_file_size_exactly_max(
        self, client: TestClient, auth_header: dict
    ):
        """file_size = MAX_FILE_SIZE_BYTES — ровно на границе (< vs <=).

        Используем патч константы, чтобы не генерировать 100 MB данных."""
        import app.api.v1.endpoints.drafts as drafts_module
        original = drafts_module.MAX_FILE_SIZE_BYTES
        boundary = 1024 * 10  # 10 KB для теста
        drafts_module.MAX_FILE_SIZE_BYTES = boundary

        try:
            content = b"X" * boundary  # ровно MAX
            response = client.post(
                self.URL,
                headers=auth_header,
                files={"file": ("large.pdf", io.BytesIO(content), "application/pdf")},
                data={"document_key": "doc-max-size", "source_type": "GOST"},
            )
            # Если условие file_size > MAX → 202 (ровно MAX проходит)
            # Если условие file_size >= MAX → 413 (баг)
            assert response.status_code == 202, (
                f"BUG if 413: file_size ({boundary}) == MAX should be allowed. "
                f"Got {response.status_code}, body={response.text[:200]}"
            )
        finally:
            drafts_module.MAX_FILE_SIZE_BYTES = original

    def test_file_size_one_byte_over_max(
        self, client: TestClient, auth_header: dict
    ):
        """file_size = MAX + 1 → 413."""
        import app.api.v1.endpoints.drafts as drafts_module
        original = drafts_module.MAX_FILE_SIZE_BYTES
        boundary = 1024 * 10
        drafts_module.MAX_FILE_SIZE_BYTES = boundary

        try:
            content = b"X" * (boundary + 1)
            response = client.post(
                self.URL,
                headers=auth_header,
                files={"file": ("large.pdf", io.BytesIO(content), "application/pdf")},
                data={"document_key": "doc-over-size", "source_type": "GOST"},
            )
            assert response.status_code == 413, (
                f"file_size={boundary + 1}: expected 413, "
                f"got {response.status_code}"
            )
        finally:
            drafts_module.MAX_FILE_SIZE_BYTES = original

    def test_metadata_json_null(
        self, client: TestClient, auth_header: dict
    ):
        """metadata='null' → json.loads('null') → None → не dict → 422."""
        response = client.post(
            self.URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF meta-null"), "application/pdf")},
            data={
                "document_key": "doc-meta-null",
                "source_type": "GOST",
                "metadata": "null",
            },
        )
        assert response.status_code == 422, (
            f"metadata='null': expected 422, got {response.status_code}, body={response.text}"
        )

    def test_metadata_json_array(
        self, client: TestClient, auth_header: dict
    ):
        """metadata='[]' → valid JSON но не dict → 422."""
        response = client.post(
            self.URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF meta-arr"), "application/pdf")},
            data={
                "document_key": "doc-meta-arr",
                "source_type": "GOST",
                "metadata": "[]",
            },
        )
        assert response.status_code == 422, (
            f"metadata='[]': expected 422, got {response.status_code}"
        )

    def test_title_empty_string(
        self, client: TestClient, auth_header: dict
    ):
        """title='' — пустая строка не вызывает ошибок.

        Проверяет, что title='' не ломает title_hash (if title → False).
        DraftCreateResponse не содержит поля 'title', но title не должен
        вызывать 500 или 422.
        """
        response = client.post(
            self.URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF empty-title"), "application/pdf")},
            data={"document_key": "doc-empty-title", "title": "", "source_type": "GOST"},
        )
        assert response.status_code == 202, (
            f"title='': expected 202, got {response.status_code}, body={response.text}"
        )
        data = response.json()
        # Title не возвращается в DraftCreateResponse, но ошибки быть не должно
        assert data["status"] == "uploaded"
        assert data["draft_id"] > 0

    def test_page_size_zero(
        self, client: TestClient, auth_header: dict
    ):
        """page_size=0 — если есть query-параметр с ge=1, то 422."""
        # GET /drafts не существует в оркестраторе,
        # но если endpoint принимает page_size, проверяем валидацию
        # В текущем API нет GET /drafts с page_size.
        # Проверяем через unknown query — должно игнорироваться.
        response = client.get(
            "/api/v1/drafts/1",
            headers=auth_header,
            params={"page_size": 0},
        )
        # page_size не валидируется на GET /drafts/{id}, т.к. это прокси
        # Просто проверяем, что не 500
        assert response.status_code in (200, 422), (
            f"page_size=0: unexpected {response.status_code}"
        )


# ============================================================================
#  4. Idempotency — двойные запросы
# ============================================================================


class TestIdempotency:
    """Проверка идемпотентности (или её отсутствия)."""

    CREATE_URL = "/api/v1/drafts/"
    PREVIEW_URL = "/api/v1/drafts/{draft_id}/preview"

    def test_double_post_drafts_idempotent(
        self, client: TestClient, auth_header: dict
    ):
        """Два POST /drafts с одинаковым Idempotency-Key → 200 + тот же draft_id.

        Первый запрос: 202 (создание).
        Второй запрос: 200 (idempotent hit) с тем же draft_id.
        """
        headers = {**auth_header, "Idempotency-Key": "idem-same-key-123"}

        resp1 = client.post(
            self.CREATE_URL,
            headers=headers,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF idem1"), "application/pdf")},
            data={"document_key": "doc-idem", "source_type": "GOST"},
        )
        assert resp1.status_code == 202, f"First POST: {resp1.status_code}, {resp1.text}"
        data1 = resp1.json()
        draft_id_1 = data1["draft_id"]
        task_id_1 = data1["task_id"]

        # Second POST with same key — idempotent hit
        resp2 = client.post(
            self.CREATE_URL,
            headers=headers,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF idem2"), "application/pdf")},
            data={"document_key": "doc-idem", "source_type": "GOST"},
        )
        assert resp2.status_code == 200, (
            f"Idempotent POST: expected 200, got {resp2.status_code}, body={resp2.text}"
        )
        data2 = resp2.json()
        assert data2["draft_id"] == draft_id_1, (
            f"Idempotent: expected draft_id={draft_id_1}, got {data2['draft_id']}"
        )
        assert data2["task_id"] == task_id_1, (
            f"Idempotent: expected task_id={task_id_1}, got {data2['task_id']}"
        )

    def test_double_post_drafts_different_keys(
        self, client: TestClient, auth_header: dict
    ):
        """Два POST /drafts с разными Idempotency-Key → два разных draft_id."""
        resp1 = client.post(
            self.CREATE_URL,
            headers={**auth_header, "Idempotency-Key": "key-1"},
            files={"file": ("test.pdf", io.BytesIO(b"%PDF diff1"), "application/pdf")},
            data={"document_key": "doc-diff-key", "source_type": "GOST"},
        )
        assert resp1.status_code == 202
        draft_id_1 = resp1.json()["draft_id"]

        resp2 = client.post(
            self.CREATE_URL,
            headers={**auth_header, "Idempotency-Key": "key-2"},
            files={"file": ("test.pdf", io.BytesIO(b"%PDF diff2"), "application/pdf")},
            data={"document_key": "doc-diff-key", "source_type": "GOST"},
        )
        assert resp2.status_code == 202
        draft_id_2 = resp2.json()["draft_id"]

        assert draft_id_1 != draft_id_2, "Different keys must create different drafts"

    async def test_preview_idempotency_409(
        self,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """Повторный POST /drafts/{id}/preview → 409 PREVIEW_ALREADY_RUNNING.

        ВАЖНО: старт preview НЕ обновляет статус черновика в Registry
        (см. orchestrator.start_pipeline — нет вызова update_draft_status).
        Поэтому второй запрос НЕ отсекается по статусу 'uploaded'.

        Вместо этого, код проверяет TaskSteps в статусе 'running'/'completed'.
        Тест создаёт steps со статусом 'running' для проверки этой ветки.
        """
        # Create draft
        create_resp = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF idem-preview"), "application/pdf")},
            data={"document_key": "doc-idem-preview", "source_type": "GOST"},
        )
        assert create_resp.status_code == 202
        draft_id = create_resp.json()["draft_id"]

        # Keep draft status as 'uploaded' in Registry (
        # оркестратор не меняет статус черновика при старте preview)
        from app.services.registry_client import RegistryServiceClient
        registry = RegistryServiceClient()
        await registry.update_draft_status(draft_id, status="uploaded")
        await registry.close()

        # First preview start
        resp1 = client.post(
            self.PREVIEW_URL.format(draft_id=draft_id),
            headers=auth_header,
        )
        assert resp1.status_code == 202, f"First preview: {resp1.text}"

        # Update TaskSteps to 'running' status so idempotency check triggers
        from sqlalchemy import select, update
        from app.models.pipeline import Task, TaskStep

        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        task = result.scalar_one_or_none()
        assert task is not None, "Task must exist after preview start"

        # Mark PREVIEW steps as running (they're created by start_pipeline)
        stmt = (
            update(TaskStep)
            .where(
                TaskStep.task_id == task.id,
                TaskStep.step_name.in_(["preview_ocr", "preview_converter"]),
            )
            .values(status="running")
        )
        await db_session.execute(stmt)
        await db_session.commit()

        # Second preview start → should be 409
        resp2 = client.post(
            self.PREVIEW_URL.format(draft_id=draft_id),
            headers=auth_header,
        )
        assert resp2.status_code == 409, (
            f"Second preview: expected 409, got {resp2.status_code}, body={resp2.text}"
        )
        data = resp2.json()
        detail = data.get("detail", data)
        assert "error" in detail
        assert detail["error"]["code"] == "PREVIEW_ALREADY_RUNNING", (
            f"Expected PREVIEW_ALREADY_RUNNING, got {detail['error']['code']}"
        )
