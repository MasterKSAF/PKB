from fastapi.testclient import TestClient

from rag_search.api.app import app
from rag_search.models.search import SearchRequest


def test_search_request_defaults() -> None:
    request = SearchRequest(query="допуск соосности")

    assert request.top_k == 10
    assert request.search_type == "hybrid"
    assert request.expand_context is False


def test_search_endpoint_returns_empty_scaffold_response() -> None:
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


def test_compatible_rag_search_endpoint() -> None:
    client = TestClient(app)

    response = client.post(
        "/rag/search",
        json={"query": "толщина обшивки", "search_type": "sparse"},
    )

    assert response.status_code == 200
    assert response.json()["search_type_used"] == "sparse"
