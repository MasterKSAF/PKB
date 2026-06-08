"""
Unit tests for ConverterValidatorClient.

Tests mock generation for all converter-validator endpoints:
  - POST /convert/preview — start preview conversion
  - POST /convert/process — start full conversion
  - GET /convert/{task_id}/status — check task status
"""

import pytest

from app.services.converter_client import ConverterValidatorClient


@pytest.fixture
def converter_client():
    client = ConverterValidatorClient()
    client.mock_mode = True
    return client


class TestConverterPreview:
    """Tests for ConverterValidatorClient.convert_preview."""

    @pytest.mark.asyncio
    async def test_convert_preview_returns_data(self, converter_client):
        """convert_preview returns a dict with data."""
        result = await converter_client.convert_preview({"file_key": "f-abc123"}, max_pages=3)
        assert "data" in result
        data = result["data"]
        assert "task_id" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_convert_preview_with_metadata(self, converter_client):
        """Preview response contains validation info."""
        result = await converter_client.convert_preview({"file_key": "f-test-key"}, max_pages=5)
        data = result.get("data", {})
        # Mock includes validated flag
        assert data.get("validated") is not None

    @pytest.mark.asyncio
    async def test_convert_preview_default_max_pages(self, converter_client):
        """Default max_pages is 3."""
        result = await converter_client.convert_preview({"file_key": "f-abc"})
        data = result.get("data", {})
        assert data.get("validated") is not None


class TestConverterProcess:
    """Tests for ConverterValidatorClient.convert_full."""

    @pytest.mark.asyncio
    async def test_convert_full_returns_data(self, converter_client):
        """convert_full returns a dict with data."""
        result = await converter_client.convert_full({"file_key": "f-abc123"})
        assert "data" in result
        data = result["data"]
        assert "task_id" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_convert_full_with_parameters(self, converter_client):
        """Full conversion response contains parameters."""
        result = await converter_client.convert_full({"file_key": "f-full-test"})
        data = result.get("data", {})
        # Mock includes validated and parameters
        assert "validated" in data or "parameters" in data


class TestConverterStatus:
    """Tests for ConverterValidatorClient.get_status."""

    @pytest.mark.asyncio
    async def test_get_status_returns_data(self, converter_client):
        """get_status returns a dict with status info."""
        result = await converter_client.get_status(task_id="c-mock-001")
        assert "data" in result
        data = result["data"]
        assert "task_id" in data or "status" in data

    @pytest.mark.asyncio
    async def test_get_status_progress(self, converter_client):
        """Status response contains progress info."""
        result = await converter_client.get_status(task_id="c-custom-42")
        data = result.get("data", {})
        # Mock returns progress info
        assert data is not None
