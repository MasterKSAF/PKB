"""
Query Service Client with mock mode support.
"""
from typing import Any, Dict, List, Optional
from app.services.base_client import ServiceClient
from app.core.config import settings


class QueryServiceClient(ServiceClient):
    """Client for Query Service."""
    
    def __init__(self):
        super().__init__(
            service_name="query",
            service_url=settings.services.QUERY_SERVICE_URL,
            mock_mode=settings.services.QUERY_SERVICE_MOCK
        )
    
    async def _generate_mock(
        self,
        method: str,
        endpoint: str,
        default_mock: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate mock query responses."""
        if endpoint == "/text/search" and method == "POST":
            request_data = kwargs.get("json", {})
            text = request_data.get("text", "")
            top_k = request_data.get("top_k", 5)
            
            return {
                "original_text": text,
                "analysis": {
                    "normalized_query": "нормализованный запрос",
                    "entities": [
                        {"type": "parameter", "value": "толщина обшивки"}
                    ],
                    "subqueries": ["подзапрос 1", "подзапрос 2"]
                },
                "results": [
                    {
                        "fragment_id": f"frg-mock-{i:03d}",
                        "document_id": f"doc-norm-{i:03d}",
                        "document_title": "Правила РС, часть I",
                        "page_number": 42 + i,
                        "text": f"Результат поиска для запроса (фрагмент {i+1})",
                        "coordinates": {"x": 120, "y": 350 + i*100, "width": 400, "height": 60},
                        "score": 0.94 - (i * 0.05),
                        "document_type": "normative",
                        "matched_subquery": "подзапрос 1"
                    }
                    for i in range(min(top_k, 3))
                ],
                "total_found": 3,
                "processing_time_ms": 1850
            }
        
        if endpoint == "/text/ask" and method == "POST":
            request_data = kwargs.get("json", {})
            text = request_data.get("text", "")
            
            return {
                "original_text": text,
                "normalized_question": "Сформулированный вопрос",
                "answer": "Ответ на основе найденных источников. Согласно нормативным документам...",
                "sources": [
                    {
                        "document_id": "doc-norm-001",
                        "document_title": "Правила РС, часть I",
                        "page_number": 42,
                        "fragment_id": "frg-001",
                        "text": "Релевантный текст из документа",
                        "score": 0.92
                    }
                ],
                "processing_time_ms": 3200,
                "model_used": "llama-3-70b"
            }
        
        return default_mock
    
    async def text_search(
        self,
        text: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        filters: Optional[Dict] = None,
        options: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Search by arbitrary text."""
        return await self.call(
            "POST",
            "/text/search",
            mock_response={},
            json={
                "text": text,
                "document_ids": document_ids,
                "top_k": top_k,
                "filters": filters or {},
                "options": options or {}
            }
        )
    
    async def text_ask(
        self,
        text: str,
        document_ids: Optional[List[str]] = None,
        options: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Ask question based on arbitrary text."""
        return await self.call(
            "POST",
            "/text/ask",
            mock_response={},
            json={
                "text": text,
                "document_ids": document_ids,
                "options": options or {}
            }
        )
