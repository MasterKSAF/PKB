"""
PKB Neuroassistant — RAG Search Service API Definitions.

Основано на: docs/api/rag_search_service_api.md
"""

from __future__ import annotations

from services.base import (
    EndpointDef,
    ServiceDef,
    API_PREFIX,
)

SERVICE_KEY = "rag_search"
PORT = 8091
DISPLAY_NAME = "RAG Search Service"


def get_service_def() -> ServiceDef:
    """Вернуть полное описание RAG Search Service."""

    endpoints = [
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса",
            response_schema={"status": str}),
        EndpointDef("POST", f"{API_PREFIX}/rag/search", "rag",
            "Гибридный поиск чанков",
            body={"query": "ледовый класс Arc4", "top_k": 5},
            # docs: { query, results[], search_type_used, processing_time_ms, total_found }
            response_schema={"results": list, "search_type_used": str,
                             "processing_time_ms": (int, float), "total_found": int}),
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
