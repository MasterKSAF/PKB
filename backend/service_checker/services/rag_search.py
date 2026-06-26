"""
PKB Neuroassistant — RAG Search Service API Definitions.

Основано на: docs/api/rag_search_service_api.md
Обновления (19.06.2026):
- RS-6: search_type убран, стратегия в app_settings.
        Поля: query, valid_at, filters.document_type[]/category_ids[]/document_ids[]
- RS-12: Коды ошибок EMPTY_QUERY (400), INVALID_PARAMETER (422)
"""

from __future__ import annotations

from .base import (
    EndpointDef,
    ServiceDef,
    API_PREFIX,
)

SERVICE_KEY = "rag_search"
PORT = 18091
DISPLAY_NAME = "RAG Search Service"


def get_service_def() -> ServiceDef:
    """Вернуть полное описание RAG Search Service."""

    endpoints = [
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса",
            response_schema={"status": str}),
        # RS-6: без search_type, top_k, rerank; с valid_at и filters
        EndpointDef("POST", f"{API_PREFIX}/rag/search", "rag",
            "Поиск по RAG",
            body={"query": "ледовый класс Arc4", "valid_at": "2026-06-19",
                  "filters": {"document_type": [], "category_ids": [], "document_ids": []}},
            response_schema={"results": list, "processing_time_ms": (int, float),
                             "total_found": int}),
    ]

    return ServiceDef(
        service_key=SERVICE_KEY,
        display_name=DISPLAY_NAME,
        port=PORT,
        needs_auth=False,
        endpoints=endpoints,
        prepare_endpoints=[],
        depends_on=["registry"],
        base_data={},
    )
