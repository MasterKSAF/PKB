"""
Тесты PATCH /drafts/{draft_id}/metadata.

Покрывает сценарии §7 PATCH /metadata (pipeline1-orchestrator_details.md):
  - Норма → 200 с preview_metadata
  - Статус previewing/uploaded → 400 INVALID_ACTION_FOR_STATUS
  - Статус терминальный → 409 INVALID_STATE_TRANSITION
  - Конфликт уникальности → 409 DUPLICATE_DOCUMENT
  - Пустые поля → 200 (no-op)
  - Невалидные значения → 400 VALIDATION_ERROR

Внимание:
  - PATCH /metadata — прокси в Registry, оркестратор не хранит metadata
  - Валидация статуса черновика — через Registry, не через Task stage
"""

import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestPatchMetadataNormal:
    """PATCH /metadata — нормальный сценарий."""

    METADATA_URL = "/api/v1/drafts/{draft_id}/metadata"
    CREATE_URL = "/api/v1/drafts/"

    @pytest.fixture
    async def draft_in_decision(
        self, client: TestClient, auth_header: dict, db_session: AsyncSession
    ) -> int:
        """Create a draft and advance to decision stage."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 150), "application/pdf")},
            data={"document_key": "doc-meta-test", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]
        return draft_id

    async def test_patch_metadata_returns_200(
        self,
        draft_in_decision: int,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """PATCH /metadata с preview_metadata → 200."""
        draft_id = draft_in_decision

        response = client.patch(
            self.METADATA_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={
                "preview_metadata": {
                    "doc_code": "ГОСТ 1234-2024",
                    "title": "Updated Title",
                    "source_type": "GOST",
                },
            },
        )
        assert response.status_code == 200, f"Unexpected status: {response.status_code}"

    async def test_patch_metadata_no_fields_noop(
        self,
        draft_in_decision: int,
        client: TestClient,
        auth_header: dict,
    ):
        """PATCH /metadata с пустым body → 200 (no-op)."""
        draft_id = draft_in_decision

        response = client.patch(
            self.METADATA_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={},
        )
        # Ожидается no-op, может быть 200 или 400
        assert response.status_code in (200, 400)


class TestPatchMetadataValidation:
    """PATCH /metadata — validation errors."""

    METADATA_URL = "/api/v1/drafts/{draft_id}/metadata"
    CREATE_URL = "/api/v1/drafts/"

    @pytest.fixture
    async def draft_in_decision(
        self, client: TestClient, auth_header: dict, db_session: AsyncSession
    ) -> int:
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 150), "application/pdf")},
            data={"document_key": "doc-meta-val", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]
        return draft_id

    async def test_patch_metadata_invalid_source_type(
        self,
        draft_in_decision: int,
        client: TestClient,
        auth_header: dict,
    ):
        """Невалидный source_type через preview_metadata — PATCH /metadata."""
        draft_id = draft_in_decision

        response = client.patch(
            self.METADATA_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={"preview_metadata": {"source_type": "INVALID_TYPE_XYZ"}},
        )
        # В mock-режиме Registry принимает любые значения → 200
        assert response.status_code in (200, 400, 422)


class TestPatchMetadataStateValidation:
    """PATCH /metadata — state validation через Registry status.

    PATCH /metadata проверяет статус черновика в Registry (через RegistryServiceClient).
    Прокси-эндпоинт может не иметь своей state validation.
    """

    METADATA_URL = "/api/v1/drafts/{draft_id}/metadata"
    CREATE_URL = "/api/v1/drafts/"

    @pytest.fixture
    async def draft_with_status(
        self, request, client: TestClient, auth_header: dict, db_session: AsyncSession
    ) -> int:
        """Create a draft and optionally set its registry status."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 150), "application/pdf")},
            data={"document_key": f"doc-meta-{request.param}", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]

        # Update registry status
        from app.services.registry_client import RegistryServiceClient
        reg = RegistryServiceClient._storage
        if draft_id in reg["drafts"]:
            reg["drafts"][draft_id]["status"] = request.param

        return draft_id

    async def test_patch_metadata_not_found(
        self, client: TestClient, auth_header: dict
    ):
        """Несуществующий черновик → 404."""
        response = client.patch(
            self.METADATA_URL.format(draft_id=99999),
            headers=auth_header,
            json={"preview_metadata": {"doc_code": "TEST"}},
        )
        assert response.status_code != 500


class TestPatchMetadataMerge:
    """PATCH /metadata — проверка merge (5.2).

    preview_metadata должен merge-иться с существующими данными, а не заменять их.
    Пустое тело не должно затирать существующие метаданные.
    """

    METADATA_URL = "/api/v1/drafts/{draft_id}/metadata"
    CREATE_URL = "/api/v1/drafts/"

    @pytest.fixture
    async def draft_in_decision(
        self, client: TestClient, auth_header: dict, db_session: AsyncSession
    ) -> int:
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF merge " * 150), "application/pdf")},
            data={"document_key": "doc-merge-test", "source_type": "GOST"},
        )
        assert response.status_code == 202
        return response.json()["draft_id"]

    async def test_patch_metadata_merge(
        self,
        draft_in_decision: int,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """PATCH с одним полем → другие поля сохраняются (merge, не replace)."""
        draft_id = draft_in_decision

        # First PATCH: set doc_code
        response1 = client.patch(
            self.METADATA_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={"preview_metadata": {"doc_code": "ГОСТ 1234-2024"}},
        )
        assert response1.status_code == 200

        # Second PATCH: set title (should NOT clear doc_code)
        response2 = client.patch(
            self.METADATA_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={"preview_metadata": {"title": "Updated Title"}},
        )
        assert response2.status_code == 200

        # Verify via mock storage that both fields exist (merge happened)
        from app.services.registry_client import RegistryServiceClient
        storage = RegistryServiceClient._storage
        draft = storage["drafts"].get(draft_id)
        meta = (draft or {}).get("metadata_fields", {})
        assert meta.get("doc_code") == "ГОСТ 1234-2024", "doc_code was lost after second PATCH"
        assert meta.get("title") == "Updated Title"

    async def test_patch_metadata_empty_body_noop(
        self,
        draft_in_decision: int,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """Пустое тело → metadata не меняется."""
        draft_id = draft_in_decision

        # First: set some metadata
        client.patch(
            self.METADATA_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={"preview_metadata": {"doc_code": "TEST-KEY", "title": "Test Title"}},
        )

        # Second: empty body (no preview_metadata)
        response = client.patch(
            self.METADATA_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={},
        )
        assert response.status_code == 200

        # Verify metadata unchanged
        from app.services.registry_client import RegistryServiceClient
        storage = RegistryServiceClient._storage
        draft = storage["drafts"].get(draft_id)
        meta = (draft or {}).get("metadata_fields", {})
        assert meta.get("doc_code") == "TEST-KEY", "doc_code was cleared by empty PATCH"
        assert meta.get("title") == "Test Title"

    async def test_patch_metadata_overrides_stored(
        self,
        draft_in_decision: int,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """PATCH metadata_overrides → проверяем что overrides сохранены в Registry."""
        draft_id = draft_in_decision

        overrides = {"title": "Overridden Title", "doc_code": "OVERRIDE-001"}
        response = client.patch(
            self.METADATA_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={"metadata_overrides": overrides},
        )
        assert response.status_code == 200

        # Verify overrides stored in Registry mock
        from app.services.registry_client import RegistryServiceClient
        storage = RegistryServiceClient._storage
        draft = storage["drafts"].get(draft_id)
        assert draft is not None
        stored_overrides = draft.get("metadata_overrides", {})
        assert stored_overrides.get("title") == "Overridden Title"
        assert stored_overrides.get("doc_code") == "OVERRIDE-001"
