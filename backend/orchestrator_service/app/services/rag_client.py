"""
RAG Service Client with mock mode support.

RS-6/RS-7 контракты (обновлено 20.06):
- RAG Builder: POST /rag/build (sections, не chunks)
- RAG Search: только query + valid_at + filters (без top_k/search_type)
"""

from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.schemas.requests import (
    RagBuildRequest,
    RagBuildResponse,
    RagGenerateRequest,
    RagSearchRequest,
)
from app.services.base_client import ServiceClient


class RAGServiceClient(ServiceClient):
    """Client for RAG Service (vector search)."""

    def __init__(self):
        super().__init__(
            service_name="rag",
            service_url=settings.services.RAG_SERVICE_URL,
            mock_mode=settings.services.RAG_SERVICE_MOCK,
        )

    async def _generate_mock(
        self, method: str, endpoint: str, default_mock: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """Generate mock RAG responses."""
        if endpoint == "/rag/build" and method == "POST":
            request_data = kwargs.get("json", {})
            sections = request_data.get("sections", [])
            return {
                "document_id": request_data.get("document_id", "doc-mock"),
                "task_id": "task-mock-001",
                "indexing_txn_id": "txn-mock-001",
                "status": "indexing",
            }

        if endpoint.startswith("/rag/build/") and method == "DELETE":
            return {
                "document_id": endpoint.split("/")[-1],
                "deleted_count": 128,
                "status": "completed",
            }

        if endpoint.startswith("/rag/build/") and endpoint.endswith("/status") and method == "GET":
            # GET /rag/build/{doc_id}/status
            parts = endpoint.split("/")
            doc_id = parts[-2] if len(parts) >= 4 else "unknown"
            return {
                "document_id": doc_id,
                "status": "indexed",
                "chunks_count": 34,
                "has_embeddings": True,
                "indexed_at": "2026-06-20T12:00:18Z",
                "warnings": [],
                "errors": [],
            }

        if endpoint.startswith("/rag/build/") and endpoint.endswith("/check") and method == "GET":
            # /rag/build/{document_id}/check
            parts = endpoint.split("/")
            doc_id = parts[-2] if len(parts) >= 4 else "unknown"
            return {
                "document_id": doc_id,
                "indexed_count": 128,
                "expected_count": 128,
                "integrity_ok": True,
                "status": "completed",
            }

        if endpoint == "/rag/search" and method == "POST":
            request_data = kwargs.get("json", {})
            query = request_data.get("query", "")

            results = []
            for i in range(3):
                results.append(
                    {
                        "source": {
                            "document_id": f"doc-norm-{i:03d}",
                            "section_id": 100 + i,
                            "clause": f"{i+1}.{i}",
                            "path": f"{i+1}/{i+1}.{i}",
                            "page": 42 + i,
                            "bbox": None,
                            "section_title": f"Section {i+1}",
                            "content": f"Mock search result for '{query}' (fragment {i + 1})",
                            "content_hash": f"sha256-mock-{i:03d}",
                        },
                        "retrieval": {
                            "chunk_id": 1000 + i,
                            "score": 0.92 - (i * 0.05),
                            "mode": "dense_rerank",
                        },
                        "context": [
                            {
                                "chunk_id": 999 + i,
                                "content": f"Context before fragment {i+1}",
                                "score": 0.45,
                                "page": 42 + i,
                            },
                            {
                                "chunk_id": 1001 + i,
                                "content": f"Context after fragment {i+1}",
                                "score": 0.44,
                                "page": 42 + i,
                            },
                        ],
                    }
                )

            return {
                "query": query,
                "results": results,
                "processing_time_ms": 120,
                "total_found": 15,
            }

        if endpoint == "/rag/generate" and method == "POST":
            request_data = kwargs.get("json", {})
            model = request_data.get("model", "llama-3-70b")
            return {
                "content": "Mock generated answer based on context.",
                "model_used": model,
                "usage": {"prompt_tokens": 150, "completion_tokens": 40},
                "finish_reason": "stop",
            }

        return default_mock

    async def index_document(
        self,
        document_id: str,
        sections: Optional[List[Dict[str, Any]]] = None,
        protected_spans: Optional[List[Dict[str, Any]]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build index for document sections (POST /rag/build).

        RS-6/RS-7: Принимает document_id + sections[].
        section_id стабилен, chunk_id — технический.
        Возвращает 202 + indexing_txn_id.
        """
        body = RagBuildRequest(
            document_id=document_id,
            sections=sections or [],
            protected_spans=protected_spans,
            options=options,
        )
        mock = RagBuildResponse(
            document_id=document_id,
            task_id="task-mock-001",
            indexing_txn_id="txn-mock-001",
            status="indexing",
        )
        return await self.call(
            "POST",
            "/rag/build",
            request_model=RagBuildRequest,
            mock_response=mock.model_dump(),
            json=body.model_dump(exclude_none=True),
        )

    async def get_build_status(
        self,
        document_id: str,
        longpoll: int = 15,
    ) -> Dict[str, Any]:
        """Get build status with longpoll (GET /rag/build/{doc_id}/status).

        Args:
            document_id: ID документа.
            longpoll: Время ожидания в секундах (по умолч. 15).
                      Сервер держит соединение до завершения или таймаута.
        """
        params = {"longpoll": str(longpoll)}
        return await self.call(
            "GET",
            f"/rag/build/{document_id}/status",
            mock_response={
                "document_id": document_id,
                "status": "indexed",
                "chunks_count": 34,
                "has_embeddings": True,
                "indexed_at": "2026-06-20T12:00:18Z",
                "warnings": [],
                "errors": [],
            },
        )

    async def delete_index(self, document_id: str) -> Dict[str, Any]:
        """Delete document from index (DELETE /rag/build/{doc_id})."""
        return await self.call(
            "DELETE",
            f"/rag/build/{document_id}",
            mock_response={"deleted_count": 0, "status": "completed"},
        )

    async def check_index(self, document_id: str) -> Dict[str, Any]:
        """
        Check index integrity for a document (P2I-2).

        Verifies that chunks are properly indexed and retrievable.
        Returns indexed_count, expected_count, and integrity_ok flag.
        """
        return await self.call(
            "GET",
            f"/rag/build/{document_id}/check",
            mock_response={
                "document_id": document_id,
                "indexed_count": 128,
                "expected_count": 128,
                "integrity_ok": True,
                "status": "completed",
            },
        )

    async def search(
        self,
        query: str,
        valid_at: Optional[str] = None,
        filters: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Search in vector index (POST /rag/search).

        RS-6: только query + valid_at + filters.
        search_type, top_k, rerank — ТОЛЬКО из app_settings.
        """
        body = RagSearchRequest(
            query=query,
            valid_at=valid_at,
            filters=filters,
        )
        return await self.call(
            "POST",
            "/rag/search",
            request_model=RagSearchRequest,
            mock_response={
                "query": query,
                "results": [],
                "processing_time_ms": 0,
                "total_found": 0,
            },
            json=body.model_dump(exclude_none=True),
        )

    async def generate(
        self,
        messages: List[Dict[str, str]],
        context_chunks: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Generate answer using LLM."""
        body = RagGenerateRequest(
            messages=messages,
            context_chunks=context_chunks,
            model=model,
            temperature=temperature,
        )

        return await self.call(
            "POST",
            "/rag/generate",
            request_model=RagGenerateRequest,
            mock_response={
                "content": "Mock generated answer based on context.",
                "model_used": model or "llama-3-70b",
                "usage": {"prompt_tokens": 150, "completion_tokens": 40},
                "finish_reason": "stop",
            },
            json=body.model_dump(exclude_none=True),
        )


# Alias for Celery tasks that import RAGBuilderClient
RAGBuilderClient = RAGServiceClient
