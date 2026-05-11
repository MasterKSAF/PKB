"""
RAG Service Client with mock mode support.
"""
from typing import Any, Dict, List, Optional
from app.services.base_client import ServiceClient
from app.core.config import settings


class RAGServiceClient(ServiceClient):
    """Client for RAG Service (vector search)."""
    
    def __init__(self):
        super().__init__(
            service_name="rag",
            service_url=settings.services.RAG_SERVICE_URL,
            mock_mode=settings.services.RAG_SERVICE_MOCK
        )
    
    async def _generate_mock(
        self,
        method: str,
        endpoint: str,
        default_mock: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate mock RAG responses."""
        if endpoint == "/index" and method == "POST":
            request_data = kwargs.get("json", {})
            chunks = request_data.get("chunks", [])
            return {
                "document_id": request_data.get("document_id", "doc-mock"),
                "indexed_count": len(chunks),
                "status": "completed"
            }
        
        if endpoint.startswith("/index/") and method == "DELETE":
            return {
                "document_id": endpoint.split("/")[-1],
                "deleted_count": 128,
                "status": "completed"
            }
        
        if endpoint == "/search" and method == "POST":
            request_data = kwargs.get("json", {})
            query = request_data.get("query", "")
            top_k = request_data.get("top_k", 5)
            
            results = []
            for i in range(min(top_k, 3)):
                results.append({
                    "chunk_id": f"chk-mock-{i:03d}",
                    "document_id": f"doc-norm-{i:03d}",
                    "page_number": 42 + i,
                    "text": f"Результат поиска для '{query}' (фрагмент {i+1})",
                    "coordinates": {"x": 120, "y": 350 + i*100, "width": 400, "height": 60},
                    "score": 0.92 - (i * 0.05),
                    "metadata": {"document_type": "normative", "title": "Правила РС"}
                })
            
            return {
                "results": results,
                "search_type_used": request_data.get("search_type", "hybrid"),
                "processing_time_ms": 120
            }
        
        return default_mock
    
    async def index_document(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Index document chunks."""
        return await self.call(
            "POST",
            "/index",
            mock_response={"indexed_count": len(chunks), "status": "completed"},
            json={"document_id": document_id, "chunks": chunks}
        )
    
    async def delete_index(self, document_id: str) -> Dict[str, Any]:
        """Delete document from index."""
        return await self.call(
            "DELETE",
            f"/index/{document_id}",
            mock_response={"deleted_count": 0, "status": "completed"}
        )
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None,
        search_type: str = "hybrid"
    ) -> Dict[str, Any]:
        """Search in vector index."""
        return await self.call(
            "POST",
            "/search",
            mock_response={"results": [], "search_type_used": search_type, "processing_time_ms": 0},
            json={
                "query": query,
                "top_k": top_k,
                "filters": filters or {},
                "search_type": search_type
            }
        )
