# rag_builder_service_spd/tests/unit/test_search_api.py

import pytest

pytest.skip(
    "Search API belongs to rag_search_service, not rag_builder_service_spd",
    allow_module_level=True,
)

pytestmark = pytest.mark.skip(
    reason="Search API belongs to rag_search_service, not rag_builder_service_spd"
)

from fastapi.testclient import TestClient

from rag_builder.api import search_routes
from rag_builder.api.app import app
from rag_builder.models.search import (
    SearchChunkResult,
    SearchRequest,
    SearchResponse,
)



class FakeSearchService:
    def search(self, request: SearchRequest) -> SearchResponse:
        return SearchResponse(
            query=request.query,
            search_type_used="dense",
            results=[
                SearchChunkResult(
                    chunk_id=1001,
                    document_id=420000,
                    document_version_id=420001,
                    document_section_id=10,
                    section_id=8,
                    clause="6.1",
                    path="6/6.1",
                    page=2,
                    bbox=None,
                    chunk_index=0,
                    chunk_type="text",
                    content="Допуск соосности должен соответствовать таблице.",
                    score=0.95,
                    distance=0.05,
                )
            ],
            total_found=1,
            processing_time_ms=10,
            embedding_tokens=7,
            embedding_cost_usd=0.000001,
            context_expanded=False,
        )


class FailingSearchService:
    def search(self, request: SearchRequest) -> SearchResponse:
        raise ValueError("Only dense search is supported in RAG Search MVP")


def test_search_endpoint_returns_chunks(monkeypatch):
    monkeypatch.setattr(
        search_routes,
        "SearchService",
        lambda: FakeSearchService(),
    )

    client = TestClient(app)

    response = client.post(
        "/search",
        json={
            "query": "допуск соосности",
            "top_k": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == "допуск соосности"
    assert data["search_type_used"] == "dense"
    assert data["total_found"] == 1

    result = data["results"][0]

    assert result["document_id"] == 420000
    assert result["document_version_id"] == 420001
    assert result["document_section_id"] == 10
    assert result["section_id"] == 8
    assert result["clause"] == "6.1"
    assert result["page"] == 2
    assert result["content"]

def test_rag_search_alias_returns_chunks(monkeypatch):
    monkeypatch.setattr(
        search_routes,
        "SearchService",
        lambda: FakeSearchService(),
    )

    client = TestClient(app)

    response = client.post(
        "/rag/search",
        json={
            "query": "допуск соосности",
            "top_k": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == "допуск соосности"
    assert data["search_type_used"] == "dense"
    assert data["total_found"] == 1
    assert "results" in data
    assert "processing_time_ms" in data
    assert "embedding_tokens" in data
    assert "embedding_cost_usd" in data
    assert "context_expanded" in data

    result = data["results"][0]

    assert result["document_id"] == 420000
    assert result["document_version_id"] == 420001
    assert result["document_section_id"] == 10
    assert result["section_id"] == 8
    assert result["clause"] == "6.1"
    assert result["page"] == 2
    assert result["content"]


def test_search_endpoint_maps_service_error_to_422(monkeypatch):
    monkeypatch.setattr(
        search_routes,
        "SearchService",
        lambda: FailingSearchService(),
    )

    client = TestClient(app)

    response = client.post(
        "/search",
        json={
            "query": "допуск",
            "search_type": "sparse",
        },
    )

    assert response.status_code == 422
    assert "Only dense search" in response.json()["detail"]
