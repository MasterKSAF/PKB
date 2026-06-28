"""
Converter-Validator Service client.

The service is synchronous and exposes four contract endpoints:
- POST /api/v1/converter/preview
- POST /api/v1/converter/convert
- POST /api/v1/validate/metadata
- POST /api/v1/validate/document
"""

import hashlib
from typing import Any, Dict

from app.core.config import settings
from app.services.base_client import ServiceClient


class ConverterValidatorClient(ServiceClient):
    """Client for Converter-Validator Service."""

    def __init__(self):
        super().__init__(
            service_name="converter",
            service_url=settings.services.CONVERTER_SERVICE_URL,
            mock_mode=settings.services.CONVERTER_SERVICE_MOCK,
        )

    async def _generate_mock(
        self,
        method: str,
        endpoint: str,
        default_mock: Dict[str, Any],
        **kwargs,
    ) -> Dict[str, Any]:
        payload = kwargs.get("json") or {}

        if endpoint == "/api/v1/converter/preview" and method == "POST":
            raw_json = payload.get("raw_json") or {}
            metadata = raw_json.get("metadata") or {}
            document = raw_json.get("document") or {}
            source = document.get("source") or {}

            return {
                "doc_code": metadata.get("doc_code") or raw_json.get("doc_code") or "20868-81",
                "title": metadata.get("title") or source.get("title") or "?????? ???????????? ?????????",
                "mks_oks_code": metadata.get("mks_oks_code") or "47.020",
                "okstu_code": metadata.get("okstu_code"),
                "udk_code": metadata.get("udk_code"),
                "pkb_codes": metadata.get("pkb_codes") or [],
                "document_type": metadata.get("document_type") or "normative",
                "year": metadata.get("year") or 1981,
                "era": metadata.get("era") or "USSR",
                "validity_status": metadata.get("validity_status") or "active",
                "issuing_body": metadata.get("issuing_body"),
                "jurisdiction": metadata.get("jurisdiction") or "RU",
                "source_type": metadata.get("source_type") or "GOST",
                "language": metadata.get("language") or "ru",
            }

        if endpoint == "/api/v1/converter/convert" and method == "POST":
            task_id = payload.get("task_id", 420000)
            version_id = payload.get("version_id", 420001)
            document_id = payload.get("document_id")

            return {
                "task_id": task_id,
                "version_id": version_id,
                "document_id": document_id,
                "metadata": {
                    "schema": "validated_v3",
                    "task_id": task_id,
                    "created_at": "2026-01-01T00:00:00Z",
                    "parser": {},
                },
                "document": {
                    "metadata": {
                        "doc_code": "20868-81",
                        "title": "?????? ???????????? ?????????",
                    },
                    "source": {
                        "file_name": "mock.pdf",
                        "file_hash_sha256": "mock-file-hash",
                    },
                    "content": [
                        {
                            "section_id": 1,
                            "type": "text",
                            "content": {"text": "Mock converted content"},
                        }
                    ],
                },
                "validation": {
                    "validation_id": "val-mock",
                    "structure_valid": True,
                    "classification": {"overall_status": "CONFIRMED"},
                    "fingerprint": {
                        "file_hash_sha256": "mock-file-hash",
                        "title_hash_sha256": "mock-title-hash",
                        "title_key": "USSR|gost|47.020||20868-81|?????? ???????????? ?????????",
                    },
                    "matching": {
                        "predecessor_doc_id": None,
                        "successor_doc_id": None,
                    },
                    "cross_references": [],
                    "decision": "auto",
                    "status": "completed",
                },
                "llm_usage": None,
            }

        if endpoint == "/api/v1/validate/metadata" and method == "POST":
            era = str(payload.get("era", "USSR")).upper()
            source_type = str(payload.get("source_type", "GOST")).lower()
            mks_oks_code = payload.get("mks_oks_code") or ""
            okstu_code = payload.get("okstu_code") or ""
            doc_code = str(payload.get("doc_code", "20868-81"))
            normalized_title = " ".join(
                str(payload.get("title", "?????? ???????????? ?????????"))
                .strip()
                .lower()
                .replace("?", "?")
                .split()
            )
            title_key = "|".join(
                [era, source_type, mks_oks_code, okstu_code, doc_code, normalized_title]
            )
            return {
                "title_hash_sha256": hashlib.sha256(title_key.encode("utf-8")).hexdigest(),
                "title_key": title_key,
                "normalized_title": normalized_title,
                "source_type_normalized": source_type,
                "era_normalized": era.lower(),
            }

        if endpoint == "/api/v1/validate/document" and method == "POST":
            return {
                "validation_id": "val-mock",
                "document_id": payload.get("document_id"),
                "structure_valid": True,
                "classification": {"overall_status": "CONFIRMED"},
                "fingerprint": {
                    "file_hash_sha256": "mock-file-hash",
                    "title_hash_sha256": "mock-title-hash",
                    "title_key": "USSR|gost|47.020||20868-81|?????? ???????????? ?????????",
                },
                "matching": {
                    "predecessor_doc_id": None,
                    "successor_doc_id": None,
                },
                "cross_references": [],
                "decision": "auto",
                "status": "completed",
            }

        return default_mock

    async def convert_preview(self, data: Dict[str, Any], max_pages: int = 3) -> Dict[str, Any]:
        """Extract preview metadata from raw Parser/OCR JSON."""
        return await self.call(
            "POST",
            "/api/v1/converter/preview",
            mock_response={},
            json={**data, "max_pages": max_pages},
        )

    async def convert_full(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run full conversion to validated_v3."""
        return await self.call(
            "POST",
            "/api/v1/converter/convert",
            mock_response={},
            json=data,
        )

    async def validate_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize metadata and compute title_hash_sha256/title_key."""
        return await self.call(
            "POST",
            "/api/v1/validate/metadata",
            mock_response={},
            json=data,
        )

    async def validate_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an already converted or raw document."""
        return await self.call(
            "POST",
            "/api/v1/validate/document",
            mock_response={},
            json=data,
        )
