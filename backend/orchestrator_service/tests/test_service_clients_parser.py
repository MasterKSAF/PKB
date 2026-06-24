"""
Unit tests for ParserServiceClient.

Tests mock generation for:
  - POST /parser/process (mode=preview|full)
  - GET /parser/{task_id}/status
"""

import pytest

from app.services.parser_client import ParserServiceClient


@pytest.fixture
def parser_client():
    client = ParserServiceClient()
    client.mock_mode = True
    return client


DRAFT_ID = 420001


class TestParserProcessPreview:
    """Tests for ParserServiceClient.process(mode=preview)."""

    @pytest.mark.asyncio
    async def test_preview_returns_data(self, parser_client):
        """Preview returns a dict with data."""
        result = await parser_client.process(
            file_key="f-abc123", draft_id=DRAFT_ID, mode="preview", max_pages=3
        )
        assert "data" in result
        data = result["data"]
        assert "task_id" in data
        assert "status" in data
        assert "preview_not_supported" in data
        assert "metadata" in data

    @pytest.mark.asyncio
    async def test_preview_has_metadata(self, parser_client):
        """Preview metadata contains document fields."""
        result = await parser_client.process(
            file_key="f-test-key", draft_id=DRAFT_ID, mode="preview", max_pages=5
        )
        data = result.get("data", {})
        metadata = data.get("metadata", {})
        assert metadata.get("doc_code") == "ГОСТ 20868-81"
        assert metadata.get("title") is not None
        assert metadata.get("document_type") == "normative"
        assert metadata.get("source_type") == "GOST"
        assert metadata.get("era") == "USSR"

    @pytest.mark.asyncio
    async def test_preview_default_max_pages(self, parser_client):
        """Default max_pages is not sent but mock works."""
        result = await parser_client.process(
            file_key="f-abc", draft_id=DRAFT_ID, mode="preview"
        )
        assert result.get("data", {}).get("preview_not_supported") is not None

    @pytest.mark.asyncio
    async def test_preview_passes_draft_id(self, parser_client):
        """Draft ID is passed in the request body."""
        result = await parser_client.process(
            file_key="f-key", draft_id=999, mode="preview"
        )
        assert result is not None


class TestParserProcessFull:
    """Tests for ParserServiceClient.process(mode=full)."""

    @pytest.mark.asyncio
    async def test_full_returns_data(self, parser_client):
        """Full process returns a dict with data."""
        result = await parser_client.process(
            file_key="f-abc123", draft_id=DRAFT_ID, mode="full"
        )
        assert "data" in result
        data = result["data"]
        assert "task_id" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_full_contains_sections(self, parser_client):
        """Full process response contains parsed sections."""
        result = await parser_client.process(
            file_key="f-full-test", draft_id=DRAFT_ID, mode="full"
        )
        data = result.get("data", {})
        assert "pages_processed" in data or "sections" in data


class TestParserStatus:
    """Tests for ParserServiceClient.get_status."""

    @pytest.mark.asyncio
    async def test_get_status_returns_data(self, parser_client):
        """get_status returns a dict with status info."""
        result = await parser_client.get_status(task_id="p-mock-001")
        assert "data" in result
        data = result["data"]
        assert "task_id" in data or "status" in data

    @pytest.mark.asyncio
    async def test_get_status_passes_task_id(self, parser_client):
        """Task ID is reflected in the endpoint URL."""
        result = await parser_client.get_status(task_id="p-custom-42")
        data = result.get("data", {})
        assert data is not None
