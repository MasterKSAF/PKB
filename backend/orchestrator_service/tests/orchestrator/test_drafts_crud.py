"""
CRUD-тесты черновиков через Orchestrator API.

Покрывает сценарии, не вошедшие в tests/test_drafts.py:
  - POST /drafts с пустым файлом → 422
  - GET /drafts/{id} — существующий → 200
  - GET /drafts/{id} — несуществующий → 404
  - GET /drafts/abc — нечисловой → 422

Внимание:
  - GET /drafts (список), фильтрация и пагинация — функциональность Registry,
    не доступна через Orchestrator (см. guide.md).
"""

import io
import json

import pytest
from fastapi.testclient import TestClient


class TestCreateDraftEdgeCases:
    """Дополнительные кейсы POST /api/v1/drafts."""

    URL = "/api/v1/drafts/"

    def test_create_draft_with_empty_file_returns_422(
        self, client: TestClient, auth_header: dict
    ):
        """Пустой файл (0 байт) → 422."""
        response = client.post(
            self.URL,
            headers=auth_header,
            files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
            data={"document_key": "doc-empty", "source_type": "GOST"},
        )
        assert response.status_code == 422

    def test_create_draft_with_invalid_metadata_json(
        self, client: TestClient, auth_header: dict
    ):
        """Некорректный JSON в поле metadata → 422."""
        response = client.post(
            self.URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 " * 200), "application/pdf")},
            data={
                "document_key": "doc-bad-json",
                "source_type": "GOST",
                "metadata": "not-json-at-all",
            },
        )
        assert response.status_code == 422
        data = response.json()
        detail = data.get("detail", data)
        assert "VALIDATION_ERROR" in str(detail) or "validation" in str(detail).lower()


class TestGetDraft:
    """Tests for GET /api/v1/drafts/{draft_id} (proxy to Registry)."""

    GET_URL = "/api/v1/drafts/{draft_id}"

    def test_get_draft_existing(self, client: TestClient, auth_header: dict):
        """Существующий черновик (seed draft_id=1) → 200, все поля."""
        response = client.get(self.GET_URL.format(draft_id=1), headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "draft_id" in data
        assert data["draft_id"] == 1
        assert "document_key" in data
        assert "status" in data
        assert "file_key" in data
        assert "created_at" in data
        assert "preview_metadata" in data

    def test_get_draft_created_via_api(
        self, client: TestClient, auth_header: dict
    ):
        """Черновик, созданный через API → 200."""
        create_resp = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 150), "application/pdf")},
            data={"document_key": "doc-get-test", "source_type": "GOST"},
        )
        assert create_resp.status_code == 202
        draft_id = create_resp.json()["draft_id"]

        response = client.get(
            self.GET_URL.format(draft_id=draft_id), headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert data["draft_id"] == draft_id
        assert data["document_key"] == "doc-get-test"
        assert data["status"] == "uploaded"

    def test_get_draft_not_found(self, client: TestClient, auth_header: dict):
        """Несуществующий черновик → 404."""
        response = client.get(
            self.GET_URL.format(draft_id=99999), headers=auth_header
        )
        assert response.status_code == 404
        data = response.json()
        detail = data.get("detail", data)
        assert "error" in detail
        assert detail["error"]["code"] == "NOT_FOUND"

    def test_get_draft_non_numeric_id(
        self, client: TestClient, auth_header: dict
    ):
        """Нечисловой draft_id → 422 (path validation)."""
        response = client.get(
            self.GET_URL.format(draft_id="abc"), headers=auth_header
        )
        # FastAPI path validation returns 422 for type mismatch
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
