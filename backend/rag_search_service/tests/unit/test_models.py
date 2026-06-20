"""Unit-тесты для Pydantic моделей запросов и ответов."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from app.models.request import SearchFilters, SearchRequest
from app.models.response import (
    ContextChunk,
    ErrorResponse,
    HealthResponse,
    RetrievalMeta,
    SearchResponse,
    SearchResult,
    SourceLocator,
)


class TestSearchRequest:
    """Тесты валидации SearchRequest."""

    def test_valid_request(self):
        req = SearchRequest(query="тест", valid_at=date(2026, 6, 18))
        assert req.query == "тест"
        assert req.valid_at == date(2026, 6, 18)
        assert req.filters is None

    def test_empty_query_accepted_by_pydantic(self):
        """Пустой query проходит Pydantic-валидацию (обрабатывается endpoint'ом как 400)."""
        req = SearchRequest(query="", valid_at=date(2026, 6, 18))
        assert req.query == ""

    def test_whitespace_only_query_accepted_by_pydantic(self):
        req = SearchRequest(query="   ", valid_at=date(2026, 6, 18))
        assert req.query == "   "

    def test_query_max_length_2000(self):
        req = SearchRequest(query="a" * 2000, valid_at=date(2026, 6, 18))
        assert len(req.query) == 2000

    def test_query_exceeds_max_length(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="a" * 2001, valid_at=date(2026, 6, 18))

    def test_valid_at_required(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="тест")

    def test_default_values(self):
        req = SearchRequest(query="тест", valid_at=date(2026, 6, 18))
        assert req.filters is None


class TestSearchFilters:
    """Тесты валидации SearchFilters."""

    def test_valid_filters(self):
        f = SearchFilters(document_type=["normative"], category_ids=[1, 2], document_ids=[10])
        assert f.document_type == ["normative"]
        assert f.category_ids == [1, 2]
        assert f.document_ids == [10]

    def test_empty_filters(self):
        f = SearchFilters()
        assert f.document_type is None
        assert f.category_ids is None
        assert f.document_ids is None


class TestSearchRequestWithFilters:
    """Тесты SearchRequest с фильтрами."""

    def test_request_with_filters(self):
        req = SearchRequest(
            query="тест",
            valid_at=date(2026, 6, 18),
            filters=SearchFilters(document_type=["normative"], category_ids=[5]),
        )
        assert req.filters is not None
        assert req.filters.document_type == ["normative"]
        assert req.filters.category_ids == [5]

    def test_request_with_null_filters(self):
        req = SearchRequest(query="тест", valid_at=date(2026, 6, 18), filters=None)
        assert req.filters is None


class TestSourceLocator:
    """Тесты модели SourceLocator."""

    def test_minimal_source(self):
        s = SourceLocator(document_id=1, content="text")
        assert s.document_id == 1
        assert s.content == "text"
        assert s.section_id is None
        assert s.clause is None
        assert s.path is None
        assert s.page is None
        assert s.bbox is None

    def test_full_source(self):
        s = SourceLocator(
            document_id=42,
            section_id=8,
            clause="6.1",
            path="6/6.1",
            page=2,
            bbox=[0.1, 0.2, 0.3, 0.4],
            section_title="Допуск соосности",
            content="Для ледового класса Arc4...",
        )
        assert s.document_id == 42
        assert s.section_id == 8
        assert s.path == "6/6.1"
        assert s.bbox == [0.1, 0.2, 0.3, 0.4]


class TestRetrievalMeta:
    """Тесты модели RetrievalMeta."""

    def test_retrieval(self):
        r = RetrievalMeta(chunk_id=119, score=0.87, mode="dense_rerank")
        assert r.chunk_id == 119
        assert r.score == 0.87
        assert r.mode == "dense_rerank"


class TestContextChunk:
    """Тесты модели ContextChunk."""

    def test_context_chunk(self):
        c = ContextChunk(chunk_id=1, content="text", page=2)
        assert c.chunk_id == 1
        assert c.content == "text"
        assert c.page == 2

    def test_context_chunk_minimal(self):
        c = ContextChunk(chunk_id=1, content="text")
        assert c.page is None


class TestSearchResult:
    """Тесты модели SearchResult."""

    def test_result_structure(self):
        r = SearchResult(
            source=SourceLocator(document_id=1, content="text"),
            retrieval=RetrievalMeta(chunk_id=1, score=0.9, mode="dense_rerank"),
            context=[ContextChunk(chunk_id=2, content="ctx")],
        )
        assert r.source.document_id == 1
        assert r.retrieval.score == 0.9
        assert len(r.context) == 1

    def test_empty_context(self):
        r = SearchResult(
            source=SourceLocator(document_id=1, content="text"),
            retrieval=RetrievalMeta(chunk_id=1, score=0.9, mode="dense_rerank"),
        )
        assert r.context == []


class TestSearchResponse:
    """Тесты модели SearchResponse."""

    def test_search_response_structure(self):
        resp = SearchResponse(
            query="test",
            results=[],
            processing_time_ms=100,
            total_found=0,
        )
        assert resp.query == "test"
        assert resp.results == []
        assert resp.total_found == 0


class TestHealthResponse:
    """Тесты модели HealthResponse."""

    def test_health_response(self):
        resp = HealthResponse(
            status="ok",
            service="rag-search",
            version="0.1.0",
            uptime_seconds=3600,
        )
        assert resp.status == "ok"
        assert resp.details == {}

    def test_health_response_with_details(self):
        resp = HealthResponse(
            status="degraded",
            service="rag-search",
            version="0.1.0",
            uptime_seconds=60,
            details={"database": {"status": "error"}},
        )
        assert resp.status == "degraded"
        assert resp.details["database"]["status"] == "error"


class TestErrorResponse:
    """Тесты модели ErrorResponse."""

    def test_error_response_structure(self):
        err = ErrorResponse(
            error={
                "code": "SEARCH_FAILED",
                "message": "Search failed",
                "details": {},
            }
        )
        assert err.error.code == "SEARCH_FAILED"

    def test_error_response_minimal(self):
        err = ErrorResponse(
            error={
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
            }
        )
        assert err.error.code == "INTERNAL_ERROR"
        assert err.error.details == {}
