"""
Converter-Validator Service Client with mock mode support.
"""

from typing import Any, Dict, Optional

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
        self, method: str, endpoint: str, default_mock: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        if endpoint == "/api/v1/converter/preview" and method == "POST":
            return {
                "data": {
                    "task_id": "c-mock-001",
                    "status": "completed",
                    "validated": True,
                    "metadata": {
                        "doc_code": "ГОСТ 20868-81",
                        "title": "Стойки установочные крепежные",
                        "document_type": "normative",
                    },
                }
            }
        if endpoint == "/api/v1/converter/convert" and method == "POST":
            return {
                "data": {
                    "task_id": "c-mock-002",
                    "status": "completed",
                    "validated": True,
                    "parameters": {"thickness": "12mm"},
                }
            }
        if endpoint.startswith("/api/v1/converter/") and "status" in endpoint and method == "GET":
            return {
                "data": {
                    "task_id": endpoint.split("/")[4],
                    "status": "completed",
                    "progress": 100,
                }
            }
        return default_mock

    async def convert_preview(self, data: Dict[str, Any], max_pages: int = 3) -> Dict[str, Any]:
        """Start preview conversion."""
        return await self.call(
            "POST",
            "/api/v1/converter/preview",
            mock_response={"data": {}},
            json={**data, "max_pages": max_pages},
        )

    async def convert_full(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Start full conversion."""
        return await self.call(
            "POST",
            "/api/v1/converter/convert",
            mock_response={"data": {}},
            json=data,
        )

    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """Get converter task status."""
        return await self.call(
            "GET",
            f"/api/v1/converter/{task_id}/status",
            mock_response={"data": {}},
        )
