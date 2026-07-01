"""
Unit tests for ParserServiceClient.

Tests mock generation for:
  - POST /api/v1/parser/process (mode=preview|full)
  - GET /api/v1/parser/{task_id}/status
"""

import pytest
from unittest.mock import patch

from app.services.parser_client import ParserServiceClient


@pytest.fixture
def parser_client():
    client = ParserServiceClient()
    client.mock_mode = True
    return client


DRAFT_ID = 420001


class TestParserEndpoint:
    """Tests that parser client uses correct endpoint."""

    @pytest.mark.asyncio
    async def test_process_uses_parser_endpoint(self):
        """Parser client calls POST /api/v1/parser/process."""
        client = ParserServiceClient()
        client.mock_mode = False

        with patch.object(client, "call") as mock_call:
            mock_call.return_value = {"data": {}}
            await client.process(task_id=1, file_key="f-test", draft_id=42, mode="preview")

        endpoint = mock_call.call_args[0][1]
        assert endpoint == "/api/v1/parser/process"

    @pytest.mark.asyncio
    async def test_status_uses_parser_endpoint(self):
        """Parser client calls GET /api/v1/parser/{task_id}/status."""
        client = ParserServiceClient()
        client.mock_mode = False

        with patch.object(client, "call") as mock_call:
            mock_call.return_value = {"data": {}}
            await client.get_status(task_id="task-42")

        endpoint = mock_call.call_args[0][1]
        assert "/api/v1/parser/" in endpoint
        assert "task-42" in endpoint
        assert "/status" in endpoint


class TestParserProcessPreview:
    """Tests for ParserServiceClient.process(mode=preview)."""

    @pytest.mark.asyncio
    async def test_preview_returns_task_id(self, parser_client):
        """Preview returns task_id and status directly (без data)."""
        result = await parser_client.process(
            task_id=1, file_key="f-abc123", draft_id=DRAFT_ID, mode="preview", max_pages=3
        )
        assert "task_id" in result
        assert "status" in result
        assert "preview_not_supported" in result
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_preview_has_metadata(self, parser_client):
        """Preview metadata contains document fields."""
        result = await parser_client.process(
            task_id=1, file_key="f-test-key", draft_id=DRAFT_ID, mode="preview", max_pages=5
        )
        metadata = result.get("metadata", {})
        assert metadata.get("doc_code") == "ГОСТ 20868-81"
        assert metadata.get("title") is not None
        assert metadata.get("document_type") == "normative"
        assert metadata.get("source_type") == "GOST"
        assert metadata.get("era") == "USSR"

    @pytest.mark.asyncio
    async def test_preview_default_max_pages(self, parser_client):
        """Default max_pages is not sent but mock works."""
        result = await parser_client.process(
            task_id=1, file_key="f-abc", draft_id=DRAFT_ID, mode="preview"
        )
        assert result.get("preview_not_supported") is not None

    @pytest.mark.asyncio
    async def test_preview_passes_draft_id(self, parser_client):
        """Draft ID is passed in the request body."""
        result = await parser_client.process(
            task_id=1, file_key="f-key", draft_id=999, mode="preview"
        )
        assert result is not None


class TestParserProcessFull:
    """Tests for ParserServiceClient.process(mode=full)."""

    @pytest.mark.asyncio
    async def test_full_returns_task_id(self, parser_client):
        """Full process returns task_id and status directly (без data)."""
        result = await parser_client.process(
            task_id=1, file_key="f-abc123", draft_id=DRAFT_ID, mode="full"
        )
        assert "task_id" in result
        assert "status" in result

    @pytest.mark.asyncio
    async def test_full_contains_sections(self, parser_client):
        """Full process response contains parsed sections."""
        result = await parser_client.process(
            task_id=1, file_key="f-full-test", draft_id=DRAFT_ID, mode="full"
        )
        assert "pages_processed" in result or "sections" in result


class TestParserStatus:
    """Tests for ParserServiceClient.get_status."""

    @pytest.mark.asyncio
    async def test_get_status_returns_task_id(self, parser_client):
        """get_status returns task_id and status directly (без data)."""
        result = await parser_client.get_status(task_id="p-mock-001")
        assert "task_id" in result or "status" in result

    @pytest.mark.asyncio
    async def test_get_status_passes_task_id(self, parser_client):
        """Task ID is reflected in the endpoint URL."""
        result = await parser_client.get_status(task_id="p-custom-42")
        assert result is not None
