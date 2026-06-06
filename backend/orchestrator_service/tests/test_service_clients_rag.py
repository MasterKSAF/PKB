"""
Unit tests for RAGServiceClient.

Tests mock generation for:
  - index_document — индексация чанков
  - delete_index — удаление из индекса
  - search — гибридный поиск
  - generate — генерация LLM
"""

import pytest

from app.services.rag_client import RAGServiceClient


@pytest.fixture
def rag_client():
    client = RAGServiceClient()
    client.mock_mode = True
    return client


class TestRAGIndex:
    """Tests for document indexing."""

    @pytest.mark.asyncio
    async def test_index_document(self, rag_client):
        chunks = [
            {"chunk_id": "chk-001", "text": "Test content", "page": 1},
            {"chunk_id": "chk-002", "text": "More content", "page": 2},
        ]
        result = await rag_client.index_document(
            document_id="doc-test-001",
            chunks=chunks,
        )
        assert result["document_id"] == "doc-test-001"
        assert result["indexed_count"] == len(chunks)
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_index_empty_chunks(self, rag_client):
        result = await rag_client.index_document(document_id="doc-empty", chunks=[])
        assert result["indexed_count"] == 0
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_delete_index(self, rag_client):
        result = await rag_client.delete_index(document_id="doc-test-001")
        assert result["document_id"] == "doc-test-001"
        assert result["status"] == "completed"
        assert "deleted_count" in result


class TestRAGSearch:
    """Tests for semantic search."""

    @pytest.mark.asyncio
    async def test_search_basic(self, rag_client):
        result = await rag_client.search(query="толщина обшивки", top_k=5)
        assert "results" in result
        assert "search_type_used" in result
        assert "processing_time_ms" in result
        assert len(result["results"]) > 0

    @pytest.mark.asyncio
    async def test_search_result_structure(self, rag_client):
        result = await rag_client.search(query="тест")
        for item in result["results"]:
            assert "chunk_id" in item
            assert "document_id" in item
            assert "text" in item
            assert "score" in item
            assert "metadata" in item
            assert 0.0 <= item["score"] <= 1.0

    @pytest.mark.asyncio
    async def test_search_with_filters(self, rag_client):
        result = await rag_client.search(
            query="сталь 09Г2С",
            filters={"document_type": ["normative"]},
        )
        assert len(result["results"]) > 0

    @pytest.mark.asyncio
    async def test_search_metadata_structure(self, rag_client):
        result = await rag_client.search(query="параметр")
        for item in result["results"]:
            meta = item["metadata"]
            assert "document_type" in meta
            assert "title" in meta

    @pytest.mark.asyncio
    async def test_search_top_k_respected(self, rag_client):
        result = await rag_client.search(query="test", top_k=2)
        assert len(result["results"]) <= 2


class TestRAGGenerate:
    """Tests for LLM generation."""

    @pytest.mark.asyncio
    async def test_generate_basic(self, rag_client):
        result = await rag_client.generate(
            messages=[{"role": "user", "content": "Вопрос?"}],
            context_chunks=[{"text": "Контекст"}],
        )
        assert "content" in result
        assert "model_used" in result
        assert "usage" in result
        assert "finish_reason" in result
        assert result["finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_generate_with_model(self, rag_client):
        result = await rag_client.generate(
            messages=[{"role": "user", "content": "Вопрос?"}],
            context_chunks=[],
            model="custom-model",
        )
        assert result["model_used"] == "custom-model"

    @pytest.mark.asyncio
    async def test_generate_with_temperature(self, rag_client):
        result = await rag_client.generate(
            messages=[{"role": "user", "content": "Вопрос?"}],
            context_chunks=[],
            temperature=0.5,
        )
        assert "content" in result

    @pytest.mark.asyncio
    async def test_generate_usage_stats(self, rag_client):
        result = await rag_client.generate(
            messages=[{"role": "user", "content": "Вопрос?"}],
            context_chunks=[{"text": "ctx1"}],
        )
        usage = result["usage"]
        assert "prompt_tokens" in usage
        assert "completion_tokens" in usage
        assert usage["prompt_tokens"] > 0
        assert usage["completion_tokens"] > 0
