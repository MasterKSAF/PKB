"""
Parser Service Client with mock mode support.
"""

from typing import Any, Dict, Optional

from app.core.config import settings
from app.schemas.requests import ParserPreviewRequest, ParserProcessRequest
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
        if endpoint == "/parser/preview" and method == "POST":
            return {
                "data": {
                    "task_id": "p-mock-001",
                    "status": "completed",
                    "preview_not_supported": False,
                    "pages_processed": 3,
                    "metadata": {
                        "doc_code": "ГОСТ 20868-81",
                        "title": "Стойки установочные крепежные",
                        "document_type": "normative",
                        "year": "1981",
                    },
                }
            }
        if endpoint == "/parser/process" and method == "POST":
            return {
                "data": {
                    "task_id": "p-mock-002",
                    "status": "completed",
                    "pages_processed": 10,
                    "sections": [{"type": "text", "content": "Parsed section"}],
                }
            }
        if endpoint.startswith("/parser/") and "status" in endpoint and method == "GET":
            return {
                "data": {
                    "task_id": endpoint.split("/")[2],
                    "status": "completed",
                    "progress": 100,
                }
            }
        return default_mock

    async def process_preview(self, file_key: str, max_pages: int = 3) -> Dict[str, Any]:
        """Start preview processing of a file."""
        body = ParserPreviewRequest(file_key=file_key, max_pages=max_pages)
        return await self.call(
            "POST",
            "/parser/preview",
            request_model=ParserPreviewRequest,
            mock_response={"data": {}},
            json=body.model_dump(exclude_none=True),
        )

    async def process_full(self, file_key: str) -> Dict[str, Any]:
        """Start full processing of a file."""
        body = ParserProcessRequest(file_key=file_key)
        return await self.call(
            "POST",
            "/parser/process",
            request_model=ParserProcessRequest,
            mock_response={"data": {}},
            json=body.model_dump(exclude_none=True),
        )

    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """Get parser task status."""
        return await self.call(
            "GET",
            f"/parser/{task_id}/status",
            mock_response={"data": {}},
        )
