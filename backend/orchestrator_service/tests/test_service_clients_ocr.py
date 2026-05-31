"""
Unit tests for OCRServiceClient.

Tests mock generation for:
  - process_document — обработка OCR
  - get_engines — список движков
"""

import pytest

from app.services.ocr_client import OCRServiceClient


@pytest.fixture
def ocr_client():
    client = OCRServiceClient()
    client.mock_mode = True
    return client


class TestOCRProcess:
    """Tests for OCR document processing."""

    @pytest.mark.asyncio
    async def test_process_document_basic(self, ocr_client):
        result = await ocr_client.process_document(file_id="file-test-001")
        assert "document_id" in result
        assert "pages" in result
        assert "total_pages" in result
        assert "successful_pages" in result
        assert "low_confidence_pages" in result
        assert "failed_pages" in result

    @pytest.mark.asyncio
    async def test_process_document_page_structure(self, ocr_client):
        result = await ocr_client.process_document(file_id="file-test-001")
        assert len(result["pages"]) > 0
        page = result["pages"][0]
        for field in ("page", "text", "confidence", "engine_used",
                      "page_type_detected", "blocks", "status", "errors"):
            assert field in page, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_process_document_confidence_range(self, ocr_client):
        result = await ocr_client.process_document(file_id="file-test-001")
        for page in result["pages"]:
            assert 0.0 <= page["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_process_with_custom_pages(self, ocr_client):
        result = await ocr_client.process_document(
            file_id="file-test-001",
            pages="1-3",
        )
        assert result["total_pages"] > 0

    @pytest.mark.asyncio
    async def test_process_with_options(self, ocr_client):
        result = await ocr_client.process_document(
            file_id="file-test-001",
            options={"engine": "tesseract", "language": "ru"},
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_process_document_successful_pages_count(self, ocr_client):
        result = await ocr_client.process_document(file_id="file-test-001")
        assert result["successful_pages"] >= 0
        assert result["successful_pages"] + result["failed_pages"] == result["total_pages"]


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
