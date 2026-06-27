"""
Тесты граничных сценариев POST /drafts.

Покрывает сценарии §0 Точка входа (pipeline1-orchestrator_details.md):
  - Неподдерживаемый MIME → 422 UNSUPPORTED_FILE_TYPE
  - Дубликат file_hash_sha256 → проверка is_duplicate_file

Внимание:
  - FILE_TOO_SMALL (< 1 КБ) → 400 FILE_TOO_SMALL
  - FILE_TOO_LARGE (> 100 МБ) покрыт в test_drafts_consistency.py
  - MinIO недоступен — замокан в conftest
"""

import io

import pytest
from fastapi.testclient import TestClient


class TestUnsupportedMimeType:
    """POST /drafts с неподдерживаемым MIME → 422 UNSUPPORTED_FILE_TYPE."""

    CREATE_URL = "/api/v1/drafts/"

    def test_unsupported_mime_returns_422(self, client: TestClient, auth_header: dict):
        """'application/octet-stream' → 422 UNSUPPORTED_FILE_TYPE."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.bin", io.BytesIO(b"not a pdf"), "application/octet-stream")},
            data={"document_key": "doc-bad-mime", "source_type": "GOST"},
        )
        assert response.status_code == 422
        data = response.json()
        detail = data.get("detail", data)
        assert "error" in detail
        assert "UNSUPPORTED_FILE_TYPE" in detail["error"]["code"]
        assert "allowed_types" in detail["error"]["details"]

    def test_unsupported_mime_text_returns_422(
        self, client: TestClient, auth_header: dict
    ):
        """'text/plain' → 422 UNSUPPORTED_FILE_TYPE."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.txt", io.BytesIO(b"plain text"), "text/plain")},
            data={"document_key": "doc-txt", "source_type": "GOST"},
        )
        assert response.status_code == 422

    def test_supported_mime_pdf_returns_202(
        self, client: TestClient, auth_header: dict
    ):
        """'application/pdf' → 202 Accepted."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 150), "application/pdf")},
            data={"document_key": "doc-pdf-ok", "source_type": "GOST"},
        )
        assert response.status_code == 202

    def test_supported_mime_png_returns_202(
        self, client: TestClient, auth_header: dict
    ):
        """'image/png' → 202 Accepted."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.png", io.BytesIO(b"\x89PNG mock " * 150), "image/png")},
            data={"document_key": "doc-png-ok", "source_type": "GOST"},
        )
        assert response.status_code == 202


class TestEmptyFileEdgeCases:
    """POST /drafts с пустым файлом и файлом минимального размера."""

    CREATE_URL = "/api/v1/drafts/"

    def test_empty_file_returns_422(self, client: TestClient, auth_header: dict):
        """Пустой файл (0 байт) → 422 EMPTY_FILE."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
            data={"document_key": "doc-empty", "source_type": "GOST"},
        )
        assert response.status_code == 422
        data = response.json()
        detail = data.get("detail", data)
        assert "error" in detail
        assert detail["error"]["code"] == "EMPTY_FILE"

    def test_very_small_file_returns_400(self, client: TestClient, auth_header: dict):
        """Очень маленький файл (10 байт, >0) → 400 FILE_TOO_SMALL."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("tiny.pdf", io.BytesIO(b"%PDF-1.4\n"), "application/pdf")},
            data={"document_key": "doc-tiny", "source_type": "GOST"},
        )
        assert response.status_code == 400
        data = response.json()
        detail = data.get("detail", data)
        assert "error" in detail
        assert detail["error"]["code"] == "FILE_TOO_SMALL"


class TestDuplicateDetection:
    """POST /drafts — проверка is_duplicate_file/is_duplicate_document в ответе.

    В mock-режиме RegistryServiceClient.check_uniqueness возвращает
    предсказуемые значения. Тест проверяет наличие полей в ответе.
    """

    CREATE_URL = "/api/v1/drafts/"

    def test_response_contains_duplicate_flags(
        self, client: TestClient, auth_header: dict
    ):
        """Ответ содержит is_duplicate_file и is_duplicate_document."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 150), "application/pdf")},
            data={"document_key": "doc-dup-check", "source_type": "GOST"},
        )
        assert response.status_code == 202
        data = response.json()
        assert "is_duplicate_file" in data
        assert "is_duplicate_document" in data
        assert isinstance(data["is_duplicate_file"], bool)
        assert isinstance(data["is_duplicate_document"], bool)
        assert "file_hash_sha256" in data
        assert isinstance(data["file_hash_sha256"], str)
        assert len(data["file_hash_sha256"]) == 64  # SHA-256 hex

    def test_response_contains_title_hash_when_title_provided(
        self, client: TestClient, auth_header: dict
    ):
        """При наличии title в ответе есть title_hash_sha256 и title_key."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 150), "application/pdf")},
            data={
                "document_key": "doc-title-hash",
                "source_type": "GOST",
                "title": "Тестовый документ",
                "era": "CURRENT",
                "doc_code": "ГОСТ 1234-2024",
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert data["title_hash_sha256"] is not None
        assert isinstance(data["title_hash_sha256"], str)
        assert len(data["title_hash_sha256"]) == 64
        assert data["title_key"] is not None
        # title_key should contain concatenated fields
        assert "CURRENT" in data["title_key"]
        assert "GOST" in data["title_key"]
        assert "ГОСТ 1234-2024" in data["title_key"]

    def test_response_title_hash_null_when_no_title(
        self, client: TestClient, auth_header: dict
    ):
        """Без title — title_hash_sha256 отсутствует (null).

        title_key может содержать source_type и др. поля, даже без title.
        """
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 150), "application/pdf")},
            data={"document_key": "doc-no-title", "source_type": "GOST"},
        )
        assert response.status_code == 202
        data = response.json()
        # title_hash_sha256 вычисляется ТОЛЬКО из title
        # Если title не передан, hash не вычисляется
        assert data["title_hash_sha256"] is None
        # title_key может быть None или содержать source_type
        # (зависит от реализации)
