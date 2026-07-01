"""
OCR Service Client with mock mode support.

NOTE: Отдельный OCR-сервис не реализован — его роль выполняет Parser-сервис.
Оба клиента (ocr_client + parser_client) ходят на один Parser-сервис
по единому эндпоинту POST /api/v1/parser/process.
Различие только в семантике: OCR-клиент используется как fallback.
"""

from typing import Any, Dict, Optional

from app.core.config import settings
from app.schemas.requests import OcrProcessRequest
from app.services.base_client import ServiceClient


class OCRServiceClient(ServiceClient):
    """Client for OCR capabilities (served by Parser service)."""

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
        # Реальный API Parser/OCR: все ответы без обёртки data
        if endpoint == "/api/v1/parser/process" and method == "POST":
            request_data = kwargs.get("json", {})
            file_key = request_data.get("file_key", "file-mock")
            mode = request_data.get("mode", "full")

            if mode == "preview":
                return {
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

            return {
                "task_id": f"ocr-mock-{file_key}",
                "status": "completed",
                "pages_processed": 10,
                "total_pages": 10,
                "successful_pages": 10,
                "low_confidence_pages": 0,
                "failed_pages": 0,
            }

        return default_mock

    async def process(
        self, task_id: int, file_key: str, draft_id: int, mode: str = "full", max_pages: Optional[int] = None
    ) -> Dict[str, Any]:
        """Process a file with OCR (mode=preview|full).

        NOTE: ходит на единый эндпоинт Parser-сервиса /api/v1/parser/process.
        Отдельного OCR-сервиса нет — Parser обслуживает оба режима.
        """
        body = OcrProcessRequest(
            task_id=task_id,
            file_key=file_key,
            draft_id=draft_id,
            mode=mode,
            max_pages=max_pages,
        )
        return await self.call(
            "POST",
            "/api/v1/parser/process",
            request_model=OcrProcessRequest,
            mock_response={"data": {}},
            json=body.model_dump(exclude_none=True),
        )
