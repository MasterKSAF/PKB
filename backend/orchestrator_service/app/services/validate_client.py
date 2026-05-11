"""
Validation Service Client with mock mode support.
"""

from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.base_client import ServiceClient


class ValidationServiceClient(ServiceClient):
    """Client for Validation Service."""

    def __init__(self):
        super().__init__(
            service_name="validation",
            service_url=settings.services.VALIDATE_SERVICE_URL,
            mock_mode=settings.services.VALIDATE_SERVICE_MOCK,
        )

    async def _generate_mock(
        self, method: str, endpoint: str, default_mock: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """Generate mock validation responses."""
        if endpoint == "/validate/extract/parameters" and method == "POST":
            request_data = kwargs.get("json", {})
            doc_id = request_data.get("document_id", "doc-mock")
            doc_type = request_data.get("document_type", "specification")

            return {
                "document_id": doc_id,
                "document_type": doc_type,
                "parameters": {
                    "designation": "21900M2.362135.0903",
                    "title": "Секция 0903",
                    "materials": ["сталь 09Г2С", "алюминий АМг5"],
                    "dimensions": ["1200x800x6", "L=2500"],
                    "references": ["21900M2.362135.0901СБ", "21900M2.362135.0902СБ"],
                    "specification_items": [
                        {
                            "position": "1",
                            "name": "Кница",
                            "quantity": "2",
                            "dimensions": "10x200x300",
                            "weight": "0.5",
                            "material": "сталь 09Г2С",
                            "note": "",
                        }
                    ],
                },
                "extraction_confidence": 0.89,
                "unconfirmed_fields": [],
                "updated_at": "2026-05-05T10:00:00Z",
                "processing_time_ms": 1500,
            }

        if endpoint == "/validate/compare" and method == "POST":
            request_data = kwargs.get("json", {})
            return {
                "comparison_id": "cmp-mock-001",
                "match_status": "match",
                "normative_text": request_data.get("normative_text", ""),
                "project_text": request_data.get("project_text", ""),
                "details": "Требование выполнено",
                "sources": [],
                "disclaimer": "Результат носит информационный характер и подлежит обязательной инженерной проверке.",
                "processing_time_ms": 8700,
            }

        if endpoint.startswith("/validate/compare/") and method == "GET":
            comp_id = endpoint.split("/")[-1]
            return {
                "comparison_id": comp_id,
                "status": "completed",
                "normative_block": {
                    "document_id": "doc-norm-001",
                    "document_title": "Правила РС часть I",
                    "page_number": 42,
                    "requirement_text": "Толщина обшивки в районе ледового пояса для класса Arc4 ≥ 12 мм",
                },
                "project_block": {
                    "document_id": "doc-draw-001",
                    "document_title": "21900M2.362135.0903СБ",
                    "page_number": 1,
                    "parameter_text": "Обшивка ледового пояса t=14 мм",
                },
                "match_status": "match",
                "details": "Требование выполнено: проектная толщина 14 мм превышает минимальные 12 мм.",
                "sources": [
                    {"document_id": "doc-norm-001", "page": 42},
                    {"document_id": "doc-draw-001", "page": 1},
                ],
                "disclaimer": "Результат носит информационный характер и подлежит обязательной инженерной проверке.",
                "processing_time_ms": 8700,
            }

        if endpoint == "/validate/compare/batch" and method == "POST":
            request_data = kwargs.get("json", {})
            pairs = request_data.get("pairs", [])

            comparisons = []
            for i, pair in enumerate(pairs):
                comparisons.append(
                    {
                        "comparison_id": f"cmp-batch-{i:03d}",
                        "match_status": "match",
                        "summary": f"Сопоставление {i + 1} выполнено успешно",
                    }
                )

            return {
                "batch_id": "batch-mock-001",
                "comparisons": comparisons,
                "total_pairs": len(pairs),
                "matched": len(pairs),
                "discrepancies_found": 0,
                "insufficient_data": 0,
            }

        if endpoint == "/validate/check" and method == "POST":
            return {"passed": True, "checks": [], "processing_time_ms": 50}

        if endpoint == "/validate/calculate" and method == "POST":
            request_data = kwargs.get("json", {})
            expr = request_data.get("expression", "")
            return {
                "expression": expr,
                "result": 610,
                "unit": "мм",
                "steps": ["Вычисление выполнено"],
            }

        if endpoint == "/validate/recommend" and method == "POST":
            request_data = kwargs.get("json", {})
            failures = request_data.get("failures", [])
            doc_type = request_data.get("document_type", "")
            return {
                "recommendations": [
                    {
                        "failure_ref": failures[0]["failure_ref"]
                        if failures
                        else "min_thickness_12mm",
                        "recommendation_text": "Увеличить толщину обшивки до 12 мм согласно Правилам РС, часть I, стр.42.",
                        "severity": "critical",
                        "reference_document": "doc-norm-001",
                    }
                ]
            }

        return default_mock

    async def extract_parameters(
        self, document_id: str, document_type: str, page_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract structured parameters from document."""
        return await self.call(
            "POST",
            "/validate/extract/parameters",
            mock_response={},
            json={
                "document_id": document_id,
                "document_type": document_type,
                "page_id": page_id,
            },
        )

    async def compare(
        self, normative_text: str, project_text: str, document_type: str
    ) -> Dict[str, Any]:
        """Compare normative and project texts."""
        return await self.call(
            "POST",
            "/validate/compare",
            mock_response={},
            json={
                "normative_text": normative_text,
                "project_text": project_text,
                "document_type": document_type,
            },
        )

    async def get_comparison(self, comparison_id: str) -> Dict[str, Any]:
        """Get comparison result by ID."""
        return await self.call(
            "GET", f"/validate/compare/{comparison_id}", mock_response={}
        )

    async def compare_batch(self, pairs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Batch compare multiple pairs."""
        return await self.call(
            "POST", "/validate/compare/batch", mock_response={}, json={"pairs": pairs}
        )

    async def check(self, document_id: str, document_type: str) -> Dict[str, Any]:
        """Run validation checks on a document."""
        return await self.call(
            "POST",
            "/validate/check",
            mock_response={},
            json={"document_id": document_id, "document_type": document_type},
        )

    async def calculate(
        self, expression: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Calculate a value from an expression."""
        return await self.call(
            "POST",
            "/validate/calculate",
            mock_response={},
            json={"expression": expression, "context": context or {}},
        )

    async def recommend(
        self, failures: List[Dict[str, Any]], document_type: str
    ) -> Dict[str, Any]:
        """Get recommendations for fixing validation failures."""
        return await self.call(
            "POST",
            "/validate/recommend",
            mock_response={},
            json={"failures": failures, "document_type": document_type},
        )
