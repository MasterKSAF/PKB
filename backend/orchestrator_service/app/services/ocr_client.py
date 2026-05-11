"""
OCR Service Client with mock mode support.
"""

from typing import Any, Dict, List, Optional

from app.core.config import settings
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
        if endpoint == "/ocr/process" and method == "POST":
            request_data = kwargs.get("json", {})
            file_id = request_data.get("file_id", "file-mock")
            pages_str = request_data.get("pages", "1-5")

            pages = []
            total_pages = 5
            for i in range(1, total_pages + 1):
                pages.append(
                    {
                        "page": i,
                        "text": f"Текст распознанной страницы {i} для файла {file_id}",
                        "confidence": 0.95 - (i * 0.02),
                        "engine_used": "paddleocr",
                        "page_type_detected": "text" if i % 2 == 1 else "table",
                        "blocks": [],
                        "status": "success",
                        "errors": [],
                    }
                )

            return {
                "document_id": f"temp-doc-{file_id}",
                "pages": pages,
                "total_pages": total_pages,
                "successful_pages": total_pages,
                "low_confidence_pages": 0,
                "failed_pages": 0,
            }

        if endpoint == "/ocr/engines" and method == "GET":
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

    async def process_document(
        self, file_id: str, pages: Optional[str] = None, options: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Process document with OCR."""
        return await self.call(
            "POST",
            "/ocr/process",
            mock_response={"pages": [], "total_pages": 0, "successful_pages": 0},
            json={"file_id": file_id, "pages": pages, "options": options or {}},
        )

    async def get_engines(self) -> Dict[str, Any]:
        """Get available OCR engines."""
        return await self.call("GET", "/ocr/engines", mock_response={"engines": []})
