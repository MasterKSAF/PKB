"""
Unit tests for OCRServiceClient.

Tests mock generation for:
  - POST /ocr/process (mode=preview|full)
  - GET /ocr/engines
"""

import pytest

from app.services.ocr_client import OCRServiceClient


@pytest.fixture
def ocr_client():
    client = OCRServiceClient()
    client.mock_mode = True
    return client


DRAFT_ID = 420001


class TestOCRProcessPreview:
    """Tests for OCRServiceClient.process(mode=preview)."""

    @pytest.mark.asyncio
    async def test_preview_returns_data(self, ocr_client):
        """Preview returns a dict with data wrapper."""
        result = await ocr_client.process(
            file_key="file-test-001", draft_id=DRAFT_ID, mode="preview"
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
            file_key="file-test-001", draft_id=DRAFT_ID, mode="preview"
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
            file_key="file-key", draft_id=999, mode="preview"
        )
        assert result["data"]["task_id"] is not None


class TestOCRProcessFull:
    """Tests for OCRServiceClient.process(mode=full)."""

    @pytest.mark.asyncio
    async def test_full_returns_data(self, ocr_client):
        """Full process returns a dict with data wrapper."""
        result = await ocr_client.process(
            file_key="file-test-001", draft_id=DRAFT_ID, mode="full"
        )
        assert "data" in result
        data = result["data"]
        assert "task_id" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_full_contains_pages_processed(self, ocr_client):
        """Full process response contains pages info."""
        result = await ocr_client.process(
            file_key="file-full-test", draft_id=DRAFT_ID, mode="full"
        )
        data = result.get("data", {})
        assert "pages_processed" in data


class TestOCREngines:
    """Tests for OCR engine listing."""

    @pytest.mark.asyncio
    async def test_get_engines(self, ocr_client):
        result = await ocr_client.get_engines()
        assert "engines" in result
        assert len(result["engines"]) > 0

    @pytest.mark.asyncio
    async def test_engine_structure(self, ocr_client):
        result = await ocr_client.get_engines()
        engine = result["engines"][0]
        for field in ("engine_id", "name", "status", "supported_languages",
                      "average_processing_time_ms", "default_for_types"):
            assert field in engine, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_engine_status_values(self, ocr_client):
        result = await ocr_client.get_engines()
        for engine in result["engines"]:
            assert engine["status"] in ("available", "unavailable", "error")

    @pytest.mark.asyncio
    async def test_engine_supported_languages(self, ocr_client):
        result = await ocr_client.get_engines()
        for engine in result["engines"]:
            assert len(engine["supported_languages"]) > 0
            assert "ru" in engine["supported_languages"]

    @pytest.mark.asyncio
    async def test_engine_processing_time_positive(self, ocr_client):
        result = await ocr_client.get_engines()
        for engine in result["engines"]:
            assert engine["average_processing_time_ms"] > 0
