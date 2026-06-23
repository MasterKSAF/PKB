from fastapi.testclient import TestClient
from pydantic import ValidationError

from rag_search.api.app import app, get_search_service
from rag_search.models.search import SearchRequest
from rag_search.embeddings.stub import StubEmbeddingProvider
from rag_search.services.search_service import SearchService


class FakeRepository:
    def text_search(self, query_text, top_k, filters=None):
        return []

    def vector_search(self, query_embedding, top_k, filters=None):
        return []

    def expand_context(self, document_section_id):
        return []


def override_service():
    return SearchService(
        repository=FakeRepository(),
        embedding_provider=StubEmbeddingProvider(),
    )


def test_search_request_defaults() -> None:
    request = SearchRequest(query="допуск соосности")

    assert request.query == "допуск соосности"
    assert request.top_k == 10
    assert request.search_type == "hybrid"
    assert request.expand_context is False


def test_search_request_strips_query() -> None:
    request = SearchRequest(query="  допуск соосности  ")

    assert request.query == "допуск соосности"


def test_search_request_rejects_empty_query() -> None:
    try:
        SearchRequest(query="   ")
    except ValidationError as exc:
        assert "query must not be empty" in str(exc)
    else:
        raise AssertionError("ValidationError was not raised")


def test_search_endpoint_returns_empty_response() -> None:
    app.dependency_overrides[get_search_service] = override_service

    try:
        client = TestClient(app)

        response = client.post(
            "/search",
            json={
                "query": "допуск соосности",
                "top_k": 5,
                "search_type": "hybrid",
                "expand_context": True,
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["query"] == "допуск соосности"
        assert payload["search_type_used"] == "hybrid"
        assert payload["results"] == []
        assert payload["total_found"] == 0
        assert payload["context_expanded"] is True
    finally:
        app.dependency_overrides.clear()


def test_compatible_rag_search_endpoint() -> None:
    app.dependency_overrides[get_search_service] = override_service

    try:
        client = TestClient(app)

        response = client.post(
            "/rag/search",
            json={"query": "толщина обшивки", "search_type": "sparse"},
        )

        assert response.status_code == 200
        assert response.json()["search_type_used"] == "sparse"
    finally:
        app.dependency_overrides.clear()
