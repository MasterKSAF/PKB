"""
OCR Service Client with mock mode support.
Unified endpoint: POST /ocr/process?mode=preview|full
"""

from typing import Any, Dict, Optional

from app.core.config import settings
from app.schemas.requests import OcrProcessRequest
from app.services.base_client import ServiceClient


class OCRServiceClient(ServiceClient):
    """Client for OCR Service."""

    def __init__(self):
        super().__init__(
            service_name="ocr",
            service_url=settings.services.OCR_SERVICE_URL,
            mock_mode=settings.services.OCR_SERVICE_MOCK,
        )

    async def _generate_mock(
        self, method: str, endpoint: str, default_mock: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """Generate mock OCR responses."""
        if endpoint == "/api/v1/ocr/process" and method == "POST":
            request_data = kwargs.get("json", {})
            file_key = request_data.get("file_key", "file-mock")
            mode = request_data.get("mode", "full")

            if mode == "preview":
                return {
                    "data": {
                        "task_id": "ocr-mock-preview",
                        "status": "completed",
                        "preview_not_supported": False,
                        "pages_processed": 3,
                        "metadata": {
                            "doc_code": "ГОСТ 20868-81",
                            "title": "Стойки установочные крепежные",
                            "document_type": "normative",
                            "source_type": "GOST",
                            "year": "1981",
                            "revision": "1",
                            "era": "USSR",
                            "jurisdiction": "RU",
                            "mks_oks_code": "21.060",
                            "okstu_code": "",
                            "issuing_body": "Госстандарт",
                            "udk_code": "621.882",
                        },
                        "quality": {
                            "score": 0.94,
                            "notifications": [],
                        },
                    }
                }

            return {
                "data": {
                    "task_id": f"ocr-mock-{file_key}",
                    "status": "completed",
                    "pages_processed": 10,
                    "total_pages": 10,
                    "successful_pages": 10,
                    "low_confidence_pages": 0,
                    "failed_pages": 0,
                }
            }

        if endpoint == "/api/v1/ocr/engines" and method == "GET":
            return {
                "engines": [
                    {
                        "engine_id": "paddleocr",
                        "name": "PaddleOCR",
                        "status": "available",
                        "supported_languages": ["ru", "en"],
                        "average_processing_time_ms": 1500,
                        "default_for_types": ["normative", "specification"],
                    },
                    {
                        "engine_id": "tesseract",
                        "name": "Tesseract 5",
                        "status": "available",
                        "supported_languages": ["ru", "en"],
                        "average_processing_time_ms": 2500,
                        "default_for_types": ["archival_scan"],
                    },
                ]
            }

        return default_mock

    async def process(
        self, task_id: int, file_key: str, draft_id: int, mode: str = "full", max_pages: Optional[int] = None
    ) -> Dict[str, Any]:
        """Process a file with OCR (mode=preview|full)."""
        body = OcrProcessRequest(
            task_id=task_id,
            file_key=file_key,
            draft_id=draft_id,
            mode=mode,
            max_pages=max_pages,
        )
        return await self.call(
            "POST",
            "/api/v1/ocr/process",
            request_model=OcrProcessRequest,
            mock_response={"data": {}},
            json=body.model_dump(exclude_none=True),
        )

    async def get_engines(self) -> Dict[str, Any]:
        """Get available OCR engines."""
        return await self.call("GET", "/api/v1/ocr/engines", mock_response={"engines": []})
