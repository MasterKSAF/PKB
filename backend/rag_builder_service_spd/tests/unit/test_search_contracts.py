# rag_builder_service_spd/tests/unit/test_search_contracts.py

import pytest
from pydantic import ValidationError

from rag_builder.models.search import (
    SearchChunkResult,
    SearchRequest,
    SearchResponse,
)

from rag_builder.models.search import (
    SearchChunkResult,
    SearchContextItem,
    SearchRequest,
    SearchResponse,
)

def test_search_request_strips_query():
    request = SearchRequest(
        query="  допуск соосности  ",
        top_k=5,
    )

    assert request.query == "допуск соосности"
    assert request.top_k == 5
    assert request.search_type == "dense"
    assert request.expand_context is False


def test_search_request_rejects_empty_query():
    with pytest.raises(ValidationError):
        SearchRequest(query="   ")


def test_search_request_rejects_invalid_top_k():
    with pytest.raises(ValidationError):
        SearchRequest(query="допуск", top_k=0)

    with pytest.raises(ValidationError):
        SearchRequest(query="допуск", top_k=101)


def test_search_response_contains_citation_fields():
    chunk = SearchChunkResult(
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
        content="Допуск соосности должен соответствовать приведенной в таблице.",
        score=0.95,
        distance=0.05,
    )

    response = SearchResponse(
        query="допуск соосности",
        search_type_used="dense",
        results=[chunk],
        total_found=1,
        processing_time_ms=12,
    )

    assert response.results[0].document_id == 420000
    assert response.results[0].document_version_id == 420001
    assert response.results[0].document_section_id == 10
    assert response.results[0].section_id == 8
    assert response.results[0].clause == "6.1"
    assert response.results[0].page == 2
    assert response.results[0].content
    assert response.context_expanded is False

def test_search_chunk_result_supports_context_items():
    context_item = SearchContextItem(
        relation="parent",
        document_section_id=7,
        section_id=7,
        parent_id=None,
        clause="6",
        title="Допуски формы и расположения поверхностей",
        path="6",
        page=1,
        section_type="text",
        content={
            "text": "Допуски формы и расположения поверхностей установлены..."
        },
    )

    chunk = SearchChunkResult(
        chunk_id=139,
        document_id=420000,
        document_version_id=420001,
        document_section_id=8,
        section_id=8,
        clause="6.1",
        path="6/6.1",
        page=2,
        bbox=None,
        chunk_index=0,
        chunk_type="text",
        content="Допуск соосности оси отверстия...",
        score=1.0,
        distance=None,
        context=[context_item],
    )

    assert chunk.context[0].relation == "parent"
    assert chunk.context[0].clause == "6"
    assert chunk.context[0].path == "6"