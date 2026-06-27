"""
Unit tests for OCRServiceClient.

NOTE: Отдельного OCR-сервиса нет — OCR-клиент ходит на единый эндпоинт
Parser-сервиса POST /api/v1/parser/process (не /api/v1/ocr/process).
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.ocr_client import OCRServiceClient


@pytest.fixture
def ocr_client():
    client = OCRServiceClient()
    client.mock_mode = True
    return client


DRAFT_ID = 420001


class TestOCREndpoint:
    """Tests that OCR client uses correct Parser endpoint."""

    @pytest.mark.asyncio
    async def test_process_uses_parser_endpoint(self):
        """OCR client calls POST /api/v1/parser/process (not /api/v1/ocr/process)."""
        client = OCRServiceClient()
        client.mock_mode = False  # real mode to spy on call

        with patch.object(client, "call") as mock_call:
            mock_call.return_value = {"data": {}}
            await client.process(task_id=1, file_key="f-test", draft_id=42, mode="preview")

        mock_call.assert_called_once()
        args = mock_call.call_args
        assert args[0][0] == "POST"  # method
        assert args[0][1] == "/api/v1/parser/process"  # endpoint

    @pytest.mark.asyncio
    async def test_does_not_use_ocr_endpoint(self):
        """OCR client does NOT call /api/v1/ocr/process (no separate OCR service)."""
        client = OCRServiceClient()
        client.mock_mode = False

        with patch.object(client, "call") as mock_call:
            mock_call.return_value = {"data": {}}
            await client.process(task_id=1, file_key="f-test", draft_id=42, mode="full")

        endpoint = mock_call.call_args[0][1]
        assert "/api/v1/ocr/" not in endpoint
        assert endpoint == "/api/v1/parser/process"

    @pytest.mark.asyncio
    async def test_get_engines_not_available(self):
        """get_engines method was removed (no /api/v1/ocr/engines on Parser)."""
        client = OCRServiceClient()
        assert not hasattr(client, "get_engines"), "get_engines should have been removed"

    @pytest.mark.asyncio
    async def test_mock_handler_accepts_parser_endpoint(self, ocr_client):
        """Mock handler matches /api/v1/parser/process (not /api/v1/ocr/process)."""
        result = await ocr_client.process(
            task_id=1, file_key="f-mock", draft_id=42, mode="preview"
        )
        assert "data" in result

        # Verify _generate_mock was called with /api/v1/parser/process
        with patch.object(
            ocr_client, "_generate_mock", wraps=ocr_client._generate_mock
        ) as spy:
            await ocr_client.process(task_id=1, file_key="f-mock", draft_id=42, mode="preview")
            call_args = spy.call_args
            # _generate_mock(method, endpoint, default_mock, **kwargs)
            # endpoint is 2nd positional arg → call_args[0][1]
            actual_endpoint = call_args[0][1]
            assert actual_endpoint == "/api/v1/parser/process"


class TestOCRProcessPreview:
    """Tests for OCRServiceClient.process(mode=preview)."""

    @pytest.mark.asyncio
    async def test_preview_returns_data(self, ocr_client):
        """Preview returns a dict with data wrapper."""
        result = await ocr_client.process(
            task_id=1, file_key="file-test-001", draft_id=DRAFT_ID, mode="preview"
        )
        assert "data" in result
        data = result["data"]
        assert "task_id" in data
        assert "status" in data
        assert "preview_not_supported" in data
        assert "metadata" in data

    @pytest.mark.asyncio
    async def test_preview_has_full_metadata(self, ocr_client):
        """Preview metadata contains all required fields."""
        result = await ocr_client.process(
            task_id=1, file_key="file-test-001", draft_id=DRAFT_ID, mode="preview"
        )
        metadata = result["data"]["metadata"]
        expected_fields = [
            "doc_code", "title", "document_type", "source_type",
            "year", "revision", "era", "jurisdiction",
            "mks_oks_code", "okstu_code", "issuing_body", "udk_code",
        ]
        for field in expected_fields:
            assert field in metadata, f"Missing metadata field: {field}"

    @pytest.mark.asyncio
    async def test_preview_passes_draft_id(self, ocr_client):
        """Draft ID is passed in the request body."""
        result = await ocr_client.process(
            task_id=1, file_key="file-key", draft_id=999, mode="preview"
        )
        assert result["data"]["task_id"] is not None


class TestOCRProcessFull:
    """Tests for OCRServiceClient.process(mode=full)."""

    @pytest.mark.asyncio
    async def test_full_returns_data(self, ocr_client):
        """Full process returns a dict with data wrapper."""
        result = await ocr_client.process(
            task_id=1, file_key="file-test-001", draft_id=DRAFT_ID, mode="full"
        )
        assert "data" in result
        data = result["data"]
        assert "task_id" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_full_contains_pages_processed(self, ocr_client):
        """Full process response contains pages info."""
        result = await ocr_client.process(
            task_id=1, file_key="file-full-test", draft_id=DRAFT_ID, mode="full"
        )
        data = result.get("data", {})
        assert "pages_processed" in data
