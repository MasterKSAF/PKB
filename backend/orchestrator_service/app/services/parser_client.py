"""
Parser Service Client with mock mode support.
Unified endpoint: POST /parser/process?mode=preview|full
"""

from typing import Any, Dict, Optional

from app.core.config import settings
from app.schemas.requests import ParserProcessRequest
from app.services.base_client import ServiceClient


class ParserServiceClient(ServiceClient):
    """Client for Parser Service."""

    def __init__(self):
        super().__init__(
            service_name="parser",
            service_url=settings.services.PARSER_SERVICE_URL,
            mock_mode=settings.services.PARSER_SERVICE_MOCK,
        )

    async def _generate_mock(
        self, method: str, endpoint: str, default_mock: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        # Реальный API: все ответы без обёртки data
        if endpoint == "/api/v1/parser/process" and method == "POST":
            request_data = kwargs.get("json", {})
            mode = request_data.get("mode", "full")
            if mode == "preview":
                return {
                    "task_id": "p-mock-001",
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
                        "score": 0.92,
                        "notifications": [
                            {
                                "code": "low_confidence_pages",
                                "message": "1 page with low OCR confidence (<85%)",
                                "severity": "warning",
                            }
                        ],
                    },
                }
            return {
                "task_id": "p-mock-002",
                "status": "completed",
                "pages_processed": 10,
                "sections": [{"type": "text", "content": "Parsed section"}],
            }
        if endpoint.startswith("/api/v1/parser/") and "status" in endpoint and method == "GET":
            return {
                "task_id": endpoint.split("/")[4],
                "status": "completed",
                "progress": 100,
            }
        return default_mock

    async def process(
        self, task_id: int, file_key: str, draft_id: int, mode: str = "full", max_pages: Optional[int] = None
    ) -> Dict[str, Any]:
        """Process a file with Parser (mode=preview|full)."""
        body = ParserProcessRequest(
            task_id=task_id,
            file_key=file_key,
            draft_id=draft_id,
            mode=mode,
            max_pages=max_pages,
        )
        return await self.call(
            "POST",
            "/api/v1/parser/process",
            request_model=ParserProcessRequest,
            mock_response={"data": {}},
            json=body.model_dump(exclude_none=True),
        )

    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """Get parser task status (polls /parser/process/{task_id}/status)."""
        return await self.call(
            "GET",
            f"/api/v1/parser/process/{task_id}/status",
            mock_response={"data": {}},
        )

    async def get_result(self, task_id: str) -> Dict[str, Any]:
        """Get parser task result (/parser/process/{task_id}/result)."""
        return await self.call(
            "GET",
            f"/api/v1/parser/process/{task_id}/result",
            mock_response={"data": {}},
        )
