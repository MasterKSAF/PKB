"""
PKB Neuroassistant — Query Service API Definitions.

Основано на: docs/api/query_service_api.md
Обновления (19.06.2026):
- QS-3: POST /chat/sessions — document_ids, project_id
- QS-7: valid_at filter в POST /text/search, category_ids[]
- QS-8: enrichment_skipped в ответ
- QS-10: rating: int + rating_status
- QS-12: POST /chat/sessions/{session_id}/messages/search
"""

from __future__ import annotations

from .base import (
    EndpointDef,
    ServiceDef,
    API_PREFIX,
)

SERVICE_KEY = "query"
PORT = 8083
DISPLAY_NAME = "Query Service"


def get_service_def() -> ServiceDef:
    """Вернуть полное описание Query Service."""

    prepare_endpoints = [
        # QS-3: document_ids, project_id
        EndpointDef("POST", f"{API_PREFIX}/chat/sessions", "chat",
            "Создать сессию (prepare)",
            body={"title": "Тестовая сессия API Coverage",
                  "document_ids": [], "project_id": "{project_id}"},
            extract_keys=["session_id"],
            response_schema={"session_id": int, "title": str},
            is_preparation=True,
            expected_status=201),
        EndpointDef("POST", f"{API_PREFIX}/chat/sessions/{{session_id}}/messages", "chat",
            "Отправить сообщение (prepare)",
            body={"text": "Тестовое сообщение для prepare", "content": "Тестовое сообщение"},
            extract_keys=["message_id"],
            response_schema={"message_id": str},
            is_preparation=True,
            expected_status=202),
    ]

    endpoints = [
        # Health
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check",
            response_schema={"status": str}),
        EndpointDef("GET", f"{API_PREFIX}/system/health", "health", "System health",
            response_schema={"status": str}),
        # Chat sessions
        EndpointDef("POST", f"{API_PREFIX}/chat/sessions", "chat", "Создать сессию",
            body={"title": "Тестовая сессия API", "document_ids": [], "project_id": "{project_id}"},
            extract_keys=["session_id"],
            response_schema={"session_id": int, "title": str}),
        EndpointDef("GET", f"{API_PREFIX}/chat/sessions", "chat", "Список сессий",
            response_schema={"sessions": list}),
        EndpointDef("GET", f"{API_PREFIX}/chat/sessions/{{session_id}}", "chat",
            "Детали сессии",
            response_schema={"session_id": int, "messages": list}),
        EndpointDef("PUT", f"{API_PREFIX}/chat/sessions/{{session_id}}", "chat",
            "Обновить сессию",
            body={"title": "Обновлённая сессия"},
            response_schema={"session_id": int}),
        EndpointDef("POST", f"{API_PREFIX}/chat/sessions/{{session_id}}/messages", "chat",
            "Отправить сообщение",
            body={"text": "Тестовое сообщение", "content": "Тестовое сообщение"},
            extract_keys=["message_id"],
            response_schema={"message_id": str}),
        EndpointDef("GET", f"{API_PREFIX}/chat/sessions/{{session_id}}/messages/last",
            "chat", "Последние сообщения",
            response_schema={"messages": list}),
        EndpointDef("GET", f"{API_PREFIX}/chat/sessions/{{session_id}}/messages",
            "chat", "История сообщений",
            response_schema={"messages": list}),
        EndpointDef("GET",
            f"{API_PREFIX}/chat/sessions/{{session_id}}/messages/{{message_id}}",
            "chat", "Детали сообщения",
            response_schema={"message": dict}),
        # QS-12: Поиск по сессии
        EndpointDef("POST",
            f"{API_PREFIX}/chat/sessions/{{session_id}}/messages/search",
            "chat", "Поиск по истории сессии",
            body={"query": "тест"},
            response_schema={"results": list}),
        EndpointDef("POST", f"{API_PREFIX}/chat/sessions/{{session_id}}/context",
            "chat", "Управление контекстом",
            body={"action": "add_documents", "params": {"document_ids": []}},
            response_schema={"status": str}),
        EndpointDef("POST", f"{API_PREFIX}/chat/sessions/{{session_id}}/export",
            "chat", "Экспорт сессии",
            body={"format": "json"},
            response_schema={"status": str}),
        # QS-10: rating: int + rating_status
        EndpointDef("POST", f"{API_PREFIX}/chat/feedback", "chat", "Отправить отзыв",
            body={"session_id": "{session_id}", "message_id": "{message_id}",
                  "rating": 5, "rating_status": "positive"},
            response_schema={"saved": bool, "feedback_id": int}),
        EndpointDef("DELETE", f"{API_PREFIX}/chat/sessions/{{session_id}}", "chat",
            "Удалить сессию",
            response_schema={"session_id": int}),
        # History
        EndpointDef("GET", f"{API_PREFIX}/chat/history", "chat", "История чатов",
            response_schema={"items": list, "meta": dict}),
        EndpointDef("GET", f"{API_PREFIX}/chat/history/export", "chat", "Экспорт истории"),
        # Text search / ask — QS-7: valid_at + category_ids
        EndpointDef("POST", f"{API_PREFIX}/text/search", "text", "Поиск по тексту",
            body={"text": "толщина обшивки ледового пояса", "top_k": 5,
                  "valid_at": "2026-06-19", "filters": {"category_ids": []}},
            response_schema={"results": list, "enrichment_skipped": bool}),  # QS-8
        EndpointDef("POST", f"{API_PREFIX}/text/ask", "text", "Задать вопрос",
            body={"text": "Какая толщина обшивки?", "document_ids": []},
            response_schema={"answer": str, "sources": list}),
    ]

    _warnings = [
        "⚠️ POST /chat/feedback: rating:int + rating_status:string (QS-10). "
        "Ранее был rating:string без rating_status.",
    ]

    return ServiceDef(
        service_key=SERVICE_KEY,
        display_name=DISPLAY_NAME,
        port=PORT,
        needs_auth=True,
        endpoints=endpoints,
        prepare_endpoints=prepare_endpoints,
        depends_on=["registry"],
        base_data={},
        warnings=_warnings,
    )
