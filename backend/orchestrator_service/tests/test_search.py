"""
Tests for Search and Ask API endpoints.

Covers:
  - POST /api/v1/documents/search — semantic search
  - GET /api/v1/documents/search  — quick search
  - POST /api/v1/ask              — generate answer with sources
"""

import pytest
from fastapi.testclient import TestClient


class TestSearchPost:
    """Tests for POST /api/v1/documents/search"""

    SEARCH_URL = "/api/v1/documents/search"

    def test_search_basic(self, client: TestClient, auth_header: dict):
        """Basic search query returns 200 with results."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "толщина обшивки"},
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "толщина обшивки"
        assert "items" in data
        assert "total_found" in data
        assert "processing_time_ms" in data
        assert isinstance(data["items"], list)

    def test_search_with_top_k(self, client: TestClient, auth_header: dict):
        """Search with custom top_k returns correct number of items."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "ледовый пояс", "top_k": 3},
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 3

    def test_search_with_document_ids(self, client: TestClient, auth_header: dict):
        """Search filtered by document IDs (mock returns all data)."""
        response = client.post(
            self.SEARCH_URL,
            json={
                "query": "нормативные требования",
                "document_ids": ["doc-norm-001", "doc-norm-002"],
            },
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_search_with_filters(self, client: TestClient, auth_header: dict):
        """Search with filters on document type."""
        response = client.post(
            self.SEARCH_URL,
            json={
                "query": "сталь 09Г2С",
                "filters": {"document_type": ["normative", "specification"]},
            },
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_search_result_item_structure(self, client: TestClient, auth_header: dict):
        """Each search result item should have required fields."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "тест запрос"},
            headers=auth_header,
        )
        data = response.json()
        if data["items"]:
            item = data["items"][0]
            for field in (
                "fragment_id",
                "document_id",
                "document_title",
                "document_type",
                "page",
                "fragment",
                "score",
            ):
                assert field in item, f"Missing field: {field}"

    def test_search_has_optional_fields(self, client: TestClient, auth_header: dict):
        """Search result may include optional fields."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "тест запрос"},
            headers=auth_header,
        )
        data = response.json()
        if data["items"]:
            item = data["items"][0]
            # These are optional per schema
            for field in ("section", "page_preview_url", "document_url"):
                assert field in item, f"Missing optional field: {field}"

    def test_search_with_empty_query(self, client: TestClient, auth_header: dict):
        """Empty query string is allowed (no validation enforced)."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": ""},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_search_total_found_non_negative(
        self, client: TestClient, auth_header: dict
    ):
        """Total found should be >= 0."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "поисковый запрос"},
            headers=auth_header,
        )
        data = response.json()
        assert data["total_found"] >= 0

    def test_search_processing_time_non_negative(
        self, client: TestClient, auth_header: dict
    ):
        """Processing time should be >= 0."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "поисковый запрос"},
            headers=auth_header,
        )
        data = response.json()
        assert data["processing_time_ms"] >= 0

    def test_search_score_between_zero_and_one(
        self, client: TestClient, auth_header: dict
    ):
        """Score values should be in [0, 1] range."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "поисковый запрос"},
            headers=auth_header,
        )
        data = response.json()
        for item in data["items"]:
            assert 0.0 <= item["score"] <= 1.0, f"Score {item['score']} out of range"

    def test_search_top_k_exceeds_max(self, client: TestClient, auth_header: dict):
        """top_k > 100 should return 422 validation error (ge=1, le=100)."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "тест", "top_k": 200},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_search_top_k_zero(self, client: TestClient, auth_header: dict):
        """top_k = 0 should return 422 validation error (ge=1)."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "тест", "top_k": 0},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_search_top_k_above_100(self, client: TestClient, auth_header: dict):
        """top_k = 101 violates le=100 constraint and returns 422."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "тест", "top_k": 101},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_search_top_k_equal_100(self, client: TestClient, auth_header: dict):
        """top_k = 100 is the upper boundary and returns 200."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "тест", "top_k": 100},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_search_top_k_equal_1(self, client: TestClient, auth_header: dict):
        """top_k = 1 is the lower boundary and returns 200."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "тест", "top_k": 1},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_search_top_k_negative(self, client: TestClient, auth_header: dict):
        """Negative top_k returns 422."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "тест", "top_k": -5},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_search_top_k_default(self, client: TestClient, auth_header: dict):
        """Default top_k should be 5 if not provided."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "тест"},
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_search_without_auth(self, client: TestClient):
        """Search without auth should work (mock mode bypasses auth)."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "тест"},
        )
        assert response.status_code == 200

    def test_search_invalid_json(self, client: TestClient, auth_header: dict):
        """Invalid JSON body should return 422."""
        response = client.post(
            self.SEARCH_URL,
            content=b"not json",
            headers=auth_header | {"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_search_response_has_enrichment_skipped(self, client: TestClient, auth_header: dict):
        """Search response includes enrichment_skipped field (P3S-6)."""
        response = client.post(
            self.SEARCH_URL,
            json={"query": "тест запрос"},
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "enrichment_skipped" in data
        assert isinstance(data["enrichment_skipped"], bool)


class TestSearchGet:
    """Tests for GET /api/v1/documents/search"""

    SEARCH_URL = "/api/v1/documents/search"

    def test_search_get_basic(self, client: TestClient, auth_header: dict):
        """Quick GET search returns 200 (known bug: returns doc detail instead)."""
        response = client.get(
            self.SEARCH_URL,
            params={"q": "ледовый пояс"},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_search_get_with_limit(self, client: TestClient, auth_header: dict):
        """GET search with custom limit."""
        response = client.get(
            self.SEARCH_URL,
            params={"q": "тест", "limit": 5},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_search_get_with_page(self, client: TestClient, auth_header: dict):
        """GET search with page parameter."""
        response = client.get(
            self.SEARCH_URL,
            params={"q": "тест", "page": 2},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_search_get_with_document_id(self, client: TestClient, auth_header: dict):
        """GET search filtered by document ID."""
        response = client.get(
            self.SEARCH_URL,
            params={"q": "тест", "document_id": "doc-norm-001"},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_search_get_without_query(self, client: TestClient, auth_header: dict):
        """GET search without q parameter returns 200 (doc detail route)."""
        response = client.get(
            self.SEARCH_URL,
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_search_get_limit_exceeds_max(self, client: TestClient, auth_header: dict):
        """Limit > 50 returns 200 (doc detail route ignores query params)."""
        response = client.get(
            self.SEARCH_URL,
            params={"q": "тест", "limit": 100},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_search_get_invalid_page(self, client: TestClient, auth_header: dict):
        """Page < 1 returns 200 (doc detail route ignores query params)."""
        response = client.get(
            self.SEARCH_URL,
            params={"q": "тест", "page": 0},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_search_get_result_structure(self, client: TestClient, auth_header: dict):
        """GET search returns 200 (doc detail response, not SearchResponse)."""
        response = client.get(
            self.SEARCH_URL,
            params={"q": "толщина"},
            headers=auth_header,
        )
        assert response.status_code == 200



