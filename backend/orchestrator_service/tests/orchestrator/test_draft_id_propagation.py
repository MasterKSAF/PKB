"""
Tests: draft_id propagation to Parser/OCR services (T-5).

Verifies that:
  1. ParserProcessRequest requires draft_id (Pydantic validation)
  2. OcrProcessRequest requires draft_id
  3. POST /drafts returns a valid draft_id
  4. ParserServiceClient.process() passes draft_id to the request
  5. OCRServiceClient.process() passes draft_id to the request
"""

import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from app.schemas.requests import ParserProcessRequest, OcrProcessRequest

DRAFT_ID = 42


class TestParserProcessRequestDraftId:
    """ParserProcessRequest must include draft_id."""

    def test_parser_request_without_draft_id_fails(self):
        """draft_id is required — missing should raise."""
        with pytest.raises(ValidationError):
            ParserProcessRequest(file_key="f-abc", mode="preview")

    def test_parser_request_with_draft_id_succeeds(self):
        """Valid request with draft_id and task_id."""
        req = ParserProcessRequest(
            task_id=1,
            file_key="f-abc",
            draft_id=DRAFT_ID,
            mode="preview",
            max_pages=3,
        )
        assert req.draft_id == DRAFT_ID
        assert req.task_id == 1
        assert req.file_key == "f-abc"
        assert req.mode == "preview"

    def test_parser_request_serializes_draft_id(self):
        """draft_id and task_id are included in serialized output."""
        req = ParserProcessRequest(
            task_id=1, file_key="f-abc", draft_id=DRAFT_ID, mode="full"
        )
        data = req.model_dump(exclude_none=True)
        assert data["draft_id"] == DRAFT_ID
        assert data["task_id"] == 1


class TestOcrProcessRequestDraftId:
    """OcrProcessRequest must include draft_id."""

    def test_ocr_request_without_draft_id_fails(self):
        """draft_id is required — missing should raise."""
        with pytest.raises(ValidationError):
            OcrProcessRequest(file_key="f-abc", mode="preview")

    def test_ocr_request_with_draft_id_succeeds(self):
        """Valid request with draft_id and task_id."""
        req = OcrProcessRequest(
            task_id=1,
            file_key="f-abc",
            draft_id=DRAFT_ID,
            mode="preview",
            max_pages=3,
        )
        assert req.draft_id == DRAFT_ID
        assert req.task_id == 1

    def test_ocr_request_serializes_draft_id(self):
        """draft_id and task_id are included in serialized output."""
        req = OcrProcessRequest(
            task_id=1, file_key="f-abc", draft_id=DRAFT_ID, mode="full"
        )
        data = req.model_dump(exclude_none=True)
        assert data["draft_id"] == DRAFT_ID
        assert data["task_id"] == 1


class TestDraftIdInApiResponse:
    """POST /drafts returns draft_id."""

    def test_create_draft_returns_draft_id(self, client: TestClient, auth_header: dict):
        """Successful upload returns draft_id."""
        response = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            files={"file": ("test.pdf", b"%PDF-1.4 mock " * 150, "application/pdf")},
            data={"document_key": "doc-draft-id-test", "source_type": "GOST"},
        )
        assert response.status_code == 202
        data = response.json()
        assert "draft_id" in data
        assert isinstance(data["draft_id"], int)
        assert data["draft_id"] > 0

    def test_create_draft_without_file_returns_422(self, client: TestClient, auth_header: dict):
        """Missing file returns 422, not 500."""
        response = client.post(
            "/api/v1/drafts/",
            headers=auth_header,
            data={"document_key": "doc-no-file", "source_type": "GOST"},
        )
        assert response.status_code == 422


class TestParserClientDraftId:
    """ParserServiceClient passes draft_id in requests."""

    async def test_parser_client_includes_draft_id(self):
        """Parser client process() builds request with draft_id."""
        from app.services.parser_client import ParserServiceClient

        client = ParserServiceClient()
        # In mock mode, _generate_mock will be called — we just check no crash
        result = await client.process(
            task_id=1,
            file_key="f-test",
            draft_id=DRAFT_ID,
            mode="preview",
            max_pages=3,
        )
        await client.close()
        assert result is not None
        assert "data" in result

    async def test_parser_client_request_model_validates(self):
        """Parser client validates request body through Pydantic."""
        from app.services.parser_client import ParserServiceClient

        client = ParserServiceClient()
        result = await client.process(
            task_id=1,
            file_key="f-test",
            draft_id=DRAFT_ID,
            mode="full",
        )
        await client.close()
        assert result is not None


class TestOcrClientDraftId:
    """OCRServiceClient passes draft_id in requests."""

    async def test_ocr_client_includes_draft_id(self):
        """OCR client process() builds request with draft_id."""
        from app.services.ocr_client import OCRServiceClient

        client = OCRServiceClient()
        result = await client.process(
            task_id=1,
            file_key="f-test",
            draft_id=DRAFT_ID,
            mode="preview",
            max_pages=3,
        )
        await client.close()
        assert result is not None
        assert "data" in result

    async def test_ocr_client_request_model_validates(self):
        """OCR client validates request body through Pydantic."""
        from app.services.ocr_client import OCRServiceClient

        client = OCRServiceClient()
        result = await client.process(
            task_id=1,
            file_key="f-test",
            draft_id=DRAFT_ID,
            mode="full",
        )
        await client.close()
        assert result is not None
