"""
Unit tests for RAG Builder and Search clients.

Tests mock generation for:
  - RAGBuilderClient: index_document, delete_index, check_index
  - RAGSearchClient: search, generate
"""

import pytest

from app.services.rag_client import RAGBuilderClient, RAGSearchClient


@pytest.fixture
def rag_builder_client():
    client = RAGBuilderClient()
    client.mock_mode = True
    return client


@pytest.fixture
def rag_search_client():
    client = RAGSearchClient()
    client.mock_mode = True
    return client


class TestRAGBuild:
    """Tests for document indexing via POST /rag/build."""

    @pytest.mark.asyncio
    async def test_index_document(self, rag_builder_client):
        sections = [
            {"section_id": 1, "type": "text", "content": {"text": "Test content"}, "page": 1},
            {"section_id": 2, "type": "text", "content": {"text": "More content"}, "page": 2},
        ]
        result = await rag_builder_client.index_document(
            document_id=1001,
            sections=sections,
        )
        assert result["document_id"] == 1001
        assert result["indexing_txn_id"] == "txn-mock-001"
        assert result["status"] == "indexing"

    @pytest.mark.asyncio
    async def test_index_empty_sections(self, rag_builder_client):
        """Should handle empty sections gracefully."""
        result = await rag_builder_client.index_document(document_id=9999, sections=[])
        assert result["document_id"] == 9999
        assert result["status"] == "indexing"

    @pytest.mark.asyncio
    async def test_index_no_sections_defaults_to_empty(self, rag_builder_client):
        """sections defaults to [] when not provided."""
        result = await rag_builder_client.index_document(document_id=1002)
        assert result["status"] == "indexing"

    @pytest.mark.asyncio
    async def test_delete_index(self, rag_builder_client):
        result = await rag_builder_client.delete_index(document_id="doc-test-001")
        assert result["document_id"] == "doc-test-001"
        assert result["status"] == "completed"
        assert "deleted_count" in result


class TestRAGCheckIndex:
    """Tests for index integrity check (P2I-2)."""

    @pytest.mark.asyncio
    async def test_check_index_ok(self, rag_builder_client):
        """check_index returns integrity_ok for properly indexed doc."""
        result = await rag_builder_client.check_index(document_id="doc-valid-001")
        assert result["document_id"] == "doc-valid-001"
        assert result["integrity_ok"] is True
        assert result["indexed_count"] == 128
        assert result["expected_count"] == 128
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_check_index_has_all_fields(self, rag_builder_client):
        """check_index returns all required fields."""
        result = await rag_builder_client.check_index(document_id="doc-test")
        required = ["document_id", "indexed_count", "expected_count",
                    "integrity_ok", "status"]
        for field in required:
            assert field in result, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_check_index_different_doc_ids(self, rag_builder_client):
        """check_index echoes the document_id parameter."""
        for doc_id in ["doc-001", "doc-999", "doc-empty"]:
            result = await rag_builder_client.check_index(document_id=doc_id)
            assert result["document_id"] == doc_id


class TestRAGSearch:
    """Tests for semantic search (RS-6 contract)."""

    @pytest.mark.asyncio
    async def test_search_basic(self, rag_search_client):
        """Basic search with only query."""
        result = await rag_search_client.search(query="толщина обшивки")
        assert "results" in result
        assert "query" in result
        assert "processing_time_ms" in result
        assert "total_found" in result

    @pytest.mark.asyncio
    async def test_search_result_structure(self, rag_search_client):
        """Each result has source + retrieval + context structure."""
        result = await rag_search_client.search(query="тест")
        for item in result["results"]:
            # source block with stable locators
            assert "source" in item
            assert "document_id" in item["source"]
            assert "section_id" in item["source"]
            assert "content" in item["source"]
            # retrieval block with technical metadata
            assert "retrieval" in item
            assert "chunk_id" in item["retrieval"]
            assert "score" in item["retrieval"]
            assert "mode" in item["retrieval"]
            assert 0.0 <= item["retrieval"]["score"] <= 1.0
            # context expansion
            assert "context" in item

    @pytest.mark.asyncio
    async def test_search_with_valid_at(self, rag_search_client):
        """Search with valid_at date filter."""
        result = await rag_search_client.search(
            query="сталь 09Г2С",
            valid_at="2026-06-20",
        )
        assert len(result["results"]) > 0

    @pytest.mark.asyncio
    async def test_search_with_filters(self, rag_search_client):
        """Search with document filters."""
        result = await rag_search_client.search(
            query="допуск соосности",
            filters={"document_type": ["gost"], "category_ids": [1, 2]},
        )
        assert len(result["results"]) > 0

    @pytest.mark.asyncio
    async def test_search_no_search_type_param(self, rag_search_client):
        """search_type must NOT be in the method signature (RS-6)."""
        import inspect
        sig = inspect.signature(rag_search_client.search)
        params = list(sig.parameters.keys())
        assert "search_type" not in params, "search_type must be from app_settings only"
        assert "top_k" not in params, "top_k must be from app_settings only"
        assert "filters" in params
        assert "valid_at" in params

    @pytest.mark.asyncio
    async def test_search_source_retrieval_separation(self, rag_search_client):
        """source and retrieval must be separate blocks."""
        result = await rag_search_client.search(query="параметр")
        for item in result["results"]:
            # source should NOT contain retrieval metadata
            src = item["source"]
            assert "score" not in src
            assert "mode" not in src
            assert "chunk_id" not in src
            # retrieval should NOT contain source locators
            ret = item["retrieval"]
            assert "document_id" not in ret
            assert "section_id" not in ret


class TestRAGGenerate:
    """Tests for LLM generation."""

    @pytest.mark.asyncio
    async def test_generate_basic(self, rag_search_client):
        result = await rag_search_client.generate(
            messages=[{"role": "user", "content": "Вопрос?"}],
            context_chunks=[{"text": "Контекст"}],
        )
        assert "content" in result
        assert "model_used" in result
        assert "usage" in result
        assert "finish_reason" in result
        assert result["finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_generate_with_model(self, rag_search_client):
        result = await rag_search_client.generate(
            messages=[{"role": "user", "content": "Вопрос?"}],
            context_chunks=[],
            model="custom-model",
        )
        assert result["model_used"] == "custom-model"

    @pytest.mark.asyncio
    async def test_generate_with_temperature(self, rag_search_client):
        result = await rag_search_client.generate(
            messages=[{"role": "user", "content": "Вопрос?"}],
            context_chunks=[],
            temperature=0.5,
        )
        assert "content" in result

    @pytest.mark.asyncio
    async def test_generate_usage_stats(self, rag_search_client):
        result = await rag_search_client.generate(
            messages=[{"role": "user", "content": "Вопрос?"}],
            context_chunks=[{"text": "ctx1"}],
        )
        usage = result["usage"]
        assert "prompt_tokens" in usage
        assert "completion_tokens" in usage
        assert usage["prompt_tokens"] > 0
        assert usage["completion_tokens"] > 0
