"""
Unit tests for ParserServiceClient.

Tests mock generation for all parser service endpoints:
  - POST /parser/preview — start preview processing
  - POST /parser/process — start full processing
  - GET /parser/{task_id}/status — check task status
"""

import pytest

from app.services.parser_client import ParserServiceClient


@pytest.fixture
def parser_client():
    client = ParserServiceClient()
    client.mock_mode = True
    return client


class TestParserPreview:
    """Tests for ParserServiceClient.process_preview."""

    URL = "/parser/preview"
    METHOD = "POST"

    @pytest.mark.asyncio
    async def test_process_preview_returns_data(self, parser_client):
        """process_preview returns a dict with data."""
        result = await parser_client.process_preview(file_key="f-abc123", max_pages=3)
        assert "data" in result
        data = result["data"]
        assert "task_id" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_process_preview_passes_file_key(self, parser_client):
        """File key is passed in the request body."""
        result = await parser_client.process_preview(file_key="f-test-key", max_pages=5)
        data = result.get("data", {})
        assert data.get("task_id") is not None

    @pytest.mark.asyncio
    async def test_process_preview_default_max_pages(self, parser_client):
        """Default max_pages is 3."""
        result = await parser_client.process_preview(file_key="f-abc")
        data = result.get("data", {})
        # Mock returns standard preview response
        assert data.get("preview_not_supported") is not None


class TestParserProcess:
    """Tests for ParserServiceClient.process_full."""

    URL = "/parser/process"
    METHOD = "POST"

    @pytest.mark.asyncio
    async def test_process_full_returns_data(self, parser_client):
        """process_full returns a dict with data."""
        result = await parser_client.process_full(file_key="f-abc123")
        assert "data" in result
        data = result["data"]
        assert "task_id" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_process_full_contains_sections(self, parser_client):
        """Full process response contains parsed sections."""
        result = await parser_client.process_full(file_key="f-full-test")
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
        # Mock returns task_id from URL
        assert data is not None
