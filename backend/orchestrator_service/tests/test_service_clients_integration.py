"""
Unit tests for IntegrationServiceClient.

Tests mock generation for:
  - upload_file, get_file, get_file_info, delete_file
  - export_to_meridian
  - get_external_systems_status
"""

import pytest

from app.services.integration_client import IntegrationServiceClient


@pytest.fixture
def integration_client():
    client = IntegrationServiceClient()
    client.mock_mode = True
    return client


class TestIntegrationFileOperations:
    """Tests for file storage operations."""

    @pytest.mark.asyncio
    async def test_upload_file(self, integration_client):
        result = await integration_client.upload_file(
            file_data=b"%PDF-1.4 test content",
            filename="test.pdf",
        )
        assert "file_id" in result
        assert result["file_id"] == "file-mock-xyz"
        assert result["filename"] == "uploaded_file.pdf"
        assert result["size"] > 0
        assert result["mime_type"] == "application/pdf"
        assert "url" in result
        assert "uploaded_at" in result

    @pytest.mark.asyncio
    async def test_upload_file_with_related_document(self, integration_client):
        result = await integration_client.upload_file(
            file_data=b"data",
            filename="doc.pdf",
            related_document_id="doc-001",
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_file(self, integration_client):
        result = await integration_client.get_file(file_id="file-test-001")
        assert "file_id" in result
        assert result["file_id"] == "file-test-001"

    @pytest.mark.asyncio
    async def test_get_file_info(self, integration_client):
        result = await integration_client.get_file_info(file_id="file-test-001")
        assert result["file_id"] == "file-test-001"
        assert "filename" in result
        assert "size" in result
        assert "mime_type" in result
        assert "url" in result
        assert "uploaded_at" in result

    @pytest.mark.asyncio
    async def test_get_file_info_structure(self, integration_client):
        result = await integration_client.get_file_info("file-test-001")
        for field in ("file_id", "filename", "size", "mime_type", "url", "uploaded_at"):
            assert field in result, f"Missing field: {field}"
        assert isinstance(result["size"], int)
        assert result["size"] > 0

    @pytest.mark.asyncio
    async def test_delete_file(self, integration_client):
        result = await integration_client.delete_file(file_id="file-test-001")
        assert result["file_id"] == "file-test-001"
        assert "deleted_at" in result


class TestIntegrationExport:
    """Tests for Meridian export."""

    @pytest.mark.asyncio
    async def test_export_to_meridian(self, integration_client):
        result = await integration_client.export_to_meridian(
            document_id="doc-001",
            data={"project": "Test", "parameters": {"thickness": 14}},
        )
        assert "export_id" in result
        assert "external_id" in result
        assert result["status"] == "sent"
        assert "sent_at" in result
        assert "response_message" in result

    @pytest.mark.asyncio
    async def test_export_to_meridian_status(self, integration_client):
        result = await integration_client.export_to_meridian(
            document_id="doc-001",
            data={},
        )
        assert result["status"] in ("sent", "pending", "failed")


class TestIntegrationExternalSystems:
    """Tests for external system status."""

    @pytest.mark.asyncio
    async def test_get_external_systems_status(self, integration_client):
        result = await integration_client.get_external_systems_status()
        assert "systems" in result
        assert len(result["systems"]) > 0

    @pytest.mark.asyncio
    async def test_system_status_structure(self, integration_client):
        result = await integration_client.get_external_systems_status()
        system = result["systems"][0]
        for field in ("api_name", "status", "last_checked", "latency_ms"):
            assert field in system, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_system_status_values(self, integration_client):
        result = await integration_client.get_external_systems_status()
        for system in result["systems"]:
            assert system["status"] in ("available", "unavailable", "degraded")

    @pytest.mark.asyncio
    async def test_system_latency_positive(self, integration_client):
        result = await integration_client.get_external_systems_status()
        for system in result["systems"]:
            assert system["latency_ms"] > 0

    @pytest.mark.asyncio
    async def test_system_meridian_present(self, integration_client):
        result = await integration_client.get_external_systems_status()
        api_names = [s["api_name"] for s in result["systems"]]
        assert "meridian" in api_names
