"""
Unit tests for ConverterValidatorClient.

Contract endpoints:
- POST /converter/preview
- POST /converter/convert
- POST /validate/metadata
- POST /validate/document
"""

import pytest


pytestmark = pytest.mark.no_db

from app.services.converter_client import ConverterValidatorClient


@pytest.fixture
def converter_client():
    client = ConverterValidatorClient()
    client.mock_mode = True
    return client


class TestConverterPreview:
    @pytest.mark.asyncio
    async def test_convert_preview_returns_flat_metadata(self, converter_client):
        result = await converter_client.convert_preview(
            {
                "task_id": 420000,
                "version_id": 420001,
                "raw_json": {
                    "metadata": {
                        "doc_code": "20868-81",
                        "title": "?????? ???????????? ?????????",
                    }
                },
            },
            max_pages=3,
        )

        assert "data" not in result
        assert result["doc_code"] == "20868-81"
        assert result["title"]


class TestConverterFull:
    @pytest.mark.asyncio
    async def test_convert_full_returns_validated_v3_contract(self, converter_client):
        result = await converter_client.convert_full(
            {
                "task_id": 420000,
                "version_id": 420001,
                "raw_json": {"metadata": {"doc_code": "20868-81"}},
            }
        )

        assert "data" not in result
        assert result["task_id"] == 420000
        assert result["version_id"] == 420001
        assert result["metadata"]["schema"] == "validated_v3"
        assert result["document"]["content"]
        assert result["validation"]["status"] == "completed"


class TestValidateMetadata:
    @pytest.mark.asyncio
    async def test_validate_metadata_returns_business_key(self, converter_client):
        result = await converter_client.validate_metadata(
            {
                "era": "USSR",
                "source_type": "GOST",
                "mks_oks_code": "47.020",
                "okstu_code": None,
                "doc_code": "20868-81",
                "title": "?????? ???????????? ?????????",
            }
        )

        assert result["title_hash_sha256"]
        assert result["title_key"]
        assert result["normalized_title"] == "?????? ???????????? ?????????"


class TestValidateDocument:
    @pytest.mark.asyncio
    async def test_validate_document_returns_validation_contract(self, converter_client):
        result = await converter_client.validate_document(
            {
                "task_id": 420000,
                "version_id": 420001,
                "raw_json": {"document": {"content": []}},
            }
        )

        assert "data" not in result
        assert result["validation_id"]
        assert result["status"] == "completed"
