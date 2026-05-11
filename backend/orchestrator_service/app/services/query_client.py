"""
Query Service Client with mock mode support.
"""

from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.base_client import ServiceClient


class QueryServiceClient(ServiceClient):
    """Client for Query Service."""

    def __init__(self):
        super().__init__(
            service_name="query",
            service_url=settings.services.QUERY_SERVICE_URL,
            mock_mode=settings.services.QUERY_SERVICE_MOCK,
        )

    async def _generate_mock(
        self, method: str, endpoint: str, default_mock: Dict[str, Any], **kwargs
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
                    "entities": [{"type": "parameter", "value": "толщина обшивки"}],
                    "subqueries": ["подзапрос 1", "подзапрос 2"],
                },
                "results": [
                    {
                        "fragment_id": f"frg-mock-{i:03d}",
                        "document_id": f"doc-norm-{i:03d}",
                        "document_title": "Правила РС, часть I",
                        "page_number": 42 + i,
                        "text": f"Результат поиска для запроса (фрагмент {i + 1})",
                        "coordinates": {
                            "x": 120,
                            "y": 350 + i * 100,
                            "width": 400,
                            "height": 60,
                        },
                        "score": 0.94 - (i * 0.05),
                        "document_type": "normative",
                        "matched_subquery": "подзапрос 1",
                    }
                    for i in range(min(top_k, 3))
                ],
                "total_found": 3,
                "processing_time_ms": 1850,
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
                        "score": 0.92,
                    }
                ],
                "processing_time_ms": 3200,
                "model_used": "llama-3-70b",
            }

        # --- Chat endpoints ---

        if endpoint == "/chat/sessions" and method == "POST":
            title = kwargs.get("json", {}).get("title", "Новый чат")
            return {
                "session_id": "sess-mock-001",
                "title": title,
                "user_id": "u-mock-001",
                "document_ids": [],
                "options": {},
                "message_count": 0,
                "created_at": "2026-05-05T10:00:00Z",
                "updated_at": "2026-05-05T10:00:00Z",
            }

        if endpoint == "/chat/sessions" and method == "GET":
            page = int(kwargs.get("params", {}).get("page", 1))
            page_size = int(kwargs.get("params", {}).get("page_size", 50))
            return {
                "sessions": [],
                "meta": {"total": 0, "page": page, "page_size": page_size},
            }

        if (
            endpoint.startswith("/chat/sessions/")
            and method == "GET"
            and not endpoint.endswith(("/messages", "/context", "/export"))
        ):
            # Handle /chat/sessions/{session_id}
            session_id = endpoint.split("/")[-1]
            return {
                "session_id": session_id,
                "title": "Чат",
                "document_ids": [],
                "messages": [],
                "has_more": False,
            }

        if (
            endpoint.startswith("/chat/sessions/")
            and method == "PUT"
            and not endpoint.endswith(("/context", "/export"))
        ):
            # Handle PUT /chat/sessions/{session_id}
            return {}

        if (
            endpoint.startswith("/chat/sessions/")
            and method == "DELETE"
            and not endpoint.endswith(("/messages", "/context", "/export"))
        ):
            # Handle DELETE /chat/sessions/{session_id}
            session_id = endpoint.split("/")[-1]
            return {"session_id": session_id, "deleted_at": "2026-05-05T10:30:00Z"}

        if endpoint.endswith("/messages") and method == "POST":
            # Handle POST /chat/sessions/{session_id}/messages
            return {
                "message_id": "msg-mock-001",
                "session_id": endpoint.split("/")[2],
                "role": "assistant",
                "status": "completed",
                "content": "Mock assistant response.",
                "sources": [],
                "model_used": "llama-3-70b",
                "processing_time_ms": 3200,
                "timestamp": "2026-05-05T10:00:00Z",
            }

        if endpoint.endswith("/context") and method == "POST":
            # Handle POST /chat/sessions/{session_id}/context
            session_id = endpoint.split("/")[2]
            action = kwargs.get("json", {}).get("action", "add")
            return {
                "session_id": session_id,
                "action": action,
                "status": "success",
                "message": "Контекст обновлён",
                "timestamp": "2026-05-05T10:00:00Z",
            }

        if endpoint.endswith("/export") and method == "POST":
            # Handle POST /chat/sessions/{session_id}/export
            session_id = endpoint.split("/")[2]
            fmt = kwargs.get("json", {}).get("format", "pdf")
            return {
                "export_id": "exp-mock-001",
                "session_id": session_id,
                "format": fmt,
                "status": "completed",
                "url": f"/exports/chat/{session_id}",
                "expires_at": "2026-06-05T10:00:00Z",
                "created_at": "2026-05-05T10:00:00Z",
            }

        if endpoint == "/chat/feedback" and method == "POST":
            body = kwargs.get("json", {})
            return {
                "feedback_id": "fb-mock-001",
                "saved": True,
                "metrics_changed": {
                    "rated_answers": body.get("message_id", "msg-mock-001")
                    == "msg-mock-001"
                    and 1
                    or 0,
                    "useful_rate": 0.88,
                    "flagged_for_review": 0,
                },
            }

        if endpoint == "/chat/history" and method == "GET":
            page = int(kwargs.get("params", {}).get("page", 1))
            page_size = int(kwargs.get("params", {}).get("page_size", 50))
            return {
                "items": [],
                "meta": {"total": 0, "page": page, "page_size": page_size},
            }

        if endpoint == "/chat/history/export" and method == "POST":
            fmt = kwargs.get("json", {}).get("format", "pdf")
            return {
                "export_id": "exp-hist-mock-001",
                "format": fmt,
                "url": "/exports/chat/history",
                "created_at": "2026-05-05T10:00:00Z",
            }

        if endpoint == "/chat" and method == "POST":
            body = kwargs.get("json", {})
            _question = body.get("question", "")
            return {
                "answer_id": "ans-mock-001",
                "session_id": body.get("session_id", "sess-mock-001"),
                "status": "completed",
                "message": "Ответ на основе нормативных документов...",
                "answer_items": [],
                "latency_ms": 3200,
            }

        return default_mock

    async def text_search(
        self,
        text: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        filters: Optional[Dict] = None,
        options: Optional[Dict] = None,
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
                "options": options or {},
            },
        )

    async def text_ask(
        self,
        text: str,
        document_ids: Optional[List[str]] = None,
        options: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Ask question based on arbitrary text."""
        return await self.call(
            "POST",
            "/text/ask",
            mock_response={},
            json={"text": text, "document_ids": document_ids, "options": options or {}},
        )

    async def create_session(
        self,
        title: str,
        document_ids: Optional[List[str]] = None,
        options: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Create a new chat session."""
        return await self.call(
            "POST",
            "/chat/sessions",
            mock_response={
                "session_id": "sess-mock-001",
                "title": title or "Новый чат",
                "user_id": "u-mock-001",
                "document_ids": document_ids or [],
                "options": options or {},
                "message_count": 0,
                "created_at": "2026-05-05T10:00:00Z",
                "updated_at": "2026-05-05T10:00:00Z",
            },
            json={
                "title": title,
                "document_ids": document_ids,
                "options": options or {},
            },
        )

    async def list_sessions(self, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """List chat sessions."""
        return await self.call(
            "GET",
            "/chat/sessions",
            mock_response={
                "sessions": [],
                "meta": {"total": 0, "page": page, "page_size": page_size},
            },
            params={"page": page, "page_size": page_size},
        )

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get chat session with messages."""
        return await self.call(
            "GET",
            f"/chat/sessions/{session_id}",
            mock_response={
                "session_id": session_id,
                "title": "Чат",
                "document_ids": [],
                "messages": [],
                "has_more": False,
            },
        )

    async def update_session(
        self,
        session_id: str,
        title: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Update chat session."""
        body = {}
        if title is not None:
            body["title"] = title
        if document_ids is not None:
            body["document_ids"] = document_ids
        return await self.call(
            "PUT", f"/chat/sessions/{session_id}", mock_response={}, json=body
        )

    async def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Delete chat session."""
        return await self.call(
            "DELETE",
            f"/chat/sessions/{session_id}",
            mock_response={
                "session_id": session_id,
                "deleted_at": "2026-05-05T10:30:00Z",
            },
        )

    async def send_message(
        self,
        session_id: str,
        content: str,
        attachments: Optional[List[Dict]] = None,
        options: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Send a message in a chat session."""
        body: Dict[str, Any] = {"content": content}
        if attachments:
            body["attachments"] = attachments
        if options:
            body["options"] = options
        return await self.call(
            "POST",
            f"/chat/sessions/{session_id}/messages",
            mock_response={
                "message_id": "msg-mock-001",
                "session_id": session_id,
                "role": "assistant",
                "status": "completed",
                "content": "Mock assistant response.",
                "sources": [],
                "model_used": "llama-3-70b",
                "processing_time_ms": 3200,
                "timestamp": "2026-05-05T10:00:00Z",
            },
            json=body,
        )

    async def update_context(
        self, session_id: str, action: str, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Update session context (add/remove documents)."""
        body: Dict[str, Any] = {"action": action}
        if params:
            body["params"] = params
        return await self.call(
            "POST",
            f"/chat/sessions/{session_id}/context",
            mock_response={
                "session_id": session_id,
                "action": action,
                "status": "success",
                "message": "Контекст обновлён",
                "timestamp": "2026-05-05T10:00:00Z",
            },
            json=body,
        )

    async def export_session(
        self, session_id: str, format: str = "pdf", options: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Export chat session."""
        body: Dict[str, Any] = {"format": format}
        if options:
            body["options"] = options
        return await self.call(
            "POST",
            f"/chat/sessions/{session_id}/export",
            mock_response={
                "export_id": "exp-mock-001",
                "session_id": session_id,
                "format": format,
                "status": "completed",
                "url": f"/exports/chat/{session_id}",
                "expires_at": "2026-06-05T10:00:00Z",
                "created_at": "2026-05-05T10:00:00Z",
            },
            json=body,
        )

    async def submit_feedback(
        self,
        session_id: str,
        message_id: str,
        rating: int,
        comment: Optional[str] = None,
        aspects: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Submit feedback for a message."""
        body = {"session_id": session_id, "message_id": message_id, "rating": rating}
        if comment:
            body["comment"] = comment
        if aspects:
            body["aspects"] = aspects
        return await self.call(
            "POST",
            "/chat/feedback",
            mock_response={
                "feedback_id": "fb-mock-001",
                "saved": True,
                "metrics_changed": {
                    "rated_answers": 1,
                    "useful_rate": 0.88,
                    "flagged_for_review": 0,
                },
            },
            json=body,
        )

    async def get_history(self, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Get chat history."""
        return await self.call(
            "GET",
            "/chat/history",
            mock_response={
                "items": [],
                "meta": {"total": 0, "page": page, "page_size": page_size},
            },
            params={"page": page, "page_size": page_size},
        )

    async def export_history(self, format: str = "pdf") -> Dict[str, Any]:
        """Export chat history."""
        return await self.call(
            "POST",
            "/chat/history/export",
            mock_response={
                "export_id": "exp-hist-mock-001",
                "format": format,
                "url": "/exports/chat/history",
                "created_at": "2026-05-05T10:00:00Z",
            },
            json={"format": format},
        )

    async def quick_chat(
        self,
        question: str,
        session_id: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Quick chat without session management."""
        body: Dict[str, Any] = {"question": question}
        if session_id:
            body["session_id"] = session_id
        if context:
            body["context"] = context
        return await self.call(
            "POST",
            "/chat",
            mock_response={
                "answer_id": "ans-mock-001",
                "session_id": session_id or "sess-mock-001",
                "status": "completed",
                "message": "Ответ на основе нормативных документов...",
                "answer_items": [],
                "latency_ms": 3200,
            },
            json=body,
        )
