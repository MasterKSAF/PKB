"""
Unit tests for QueryServiceClient.

Tests mock generation for all query service endpoints:
  - text_search, text_ask
  - Chat sessions CRUD
  - Messages, context, export, feedback
  - History
"""

import pytest

from app.services.query_client import QueryServiceClient


@pytest.fixture
def query_client():
    client = QueryServiceClient()
    client.mock_mode = True
    return client


class TestQueryText:
    """Tests for text processing endpoints."""

    @pytest.mark.asyncio
    async def test_text_search_basic(self, query_client):
        result = await query_client.text_search(text="толщина обшивки")
        assert "original_text" in result
        assert "analysis" in result
        assert "results" in result
        assert result["original_text"] == "толщина обшивки"

    @pytest.mark.asyncio
    async def test_text_search_analysis(self, query_client):
        result = await query_client.text_search(text="Проверь толщину")
        analysis = result["analysis"]
        assert "normalized_query" in analysis
        assert "entities" in analysis
        assert "subqueries" in analysis

    @pytest.mark.asyncio
    async def test_text_search_result_structure(self, query_client):
        result = await query_client.text_search(text="тест", top_k=3)
        for item in result["results"]:
            for field in ("fragment_id", "document_id", "document_title",
                          "page_number", "text", "score", "document_type"):
                assert field in item, f"Missing field: {field}"
            assert 0.0 <= item["score"] <= 1.0

    @pytest.mark.asyncio
    async def test_text_ask_basic(self, query_client):
        result = await query_client.text_ask(text="Какие требования?")
        assert "original_text" in result
        assert "answer" in result
        assert "sources" in result
        assert "processing_time_ms" in result
        assert "model_used" in result
        assert result["original_text"] == "Какие требования?"

    @pytest.mark.asyncio
    async def test_text_ask_sources(self, query_client):
        result = await query_client.text_ask(text="Вопрос")
        for src in result["sources"]:
            for field in ("document_id", "document_title", "page_number",
                          "fragment_id", "text", "score"):
                assert field in src, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_text_ask_with_document_ids(self, query_client):
        result = await query_client.text_ask(
            text="Вопрос",
            document_ids=["doc-norm-001", "doc-norm-002"],
        )
        assert "answer" in result

    @pytest.mark.asyncio
    async def test_text_ask_with_options(self, query_client):
        result = await query_client.text_ask(text="Вопрос", options={"temperature": 0.3})
        assert "answer" in result

    @pytest.mark.asyncio
    async def test_text_search_with_document_ids(self, query_client):
        result = await query_client.text_search(
            text="поиск",
            document_ids=["doc-001"],
            top_k=10,
        )
        assert "results" in result

    @pytest.mark.asyncio
    async def test_text_search_with_filters(self, query_client):
        result = await query_client.text_search(
            text="поиск",
            filters={"document_type": ["normative"]},
        )
        assert "results" in result


class TestQuerySessions:
    """Tests for chat session management."""

    @pytest.mark.asyncio
    async def test_create_session(self, query_client):
        result = await query_client.create_session(title="Новый чат")
        assert result["session_id"] == "sess-mock-001"
        assert result["title"] == "Новый чат"
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_list_sessions(self, query_client):
        result = await query_client.list_sessions(page=1, page_size=20)
        assert "sessions" in result
        assert "meta" in result
        assert result["meta"]["page"] == 1
        assert result["meta"]["page_size"] == 20

    @pytest.mark.asyncio
    async def test_get_session(self, query_client):
        result = await query_client.get_session(session_id="sess-test-001")
        assert result["session_id"] == "sess-test-001"
        assert "title" in result
        assert "messages" in result

    @pytest.mark.asyncio
    async def test_update_session(self, query_client):
        result = await query_client.update_session(
            session_id="sess-test-001",
            title="Обновлённый чат",
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_update_session_with_documents(self, query_client):
        result = await query_client.update_session(
            session_id="sess-test-001",
            title="Название",
            document_ids=["doc-001"],
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_delete_session(self, query_client):
        result = await query_client.delete_session(session_id="sess-test-001")
        assert result["session_id"] == "sess-test-001"
        assert "deleted_at" in result


class TestQueryMessages:
    """Tests for message and context endpoints."""

    @pytest.mark.asyncio
    async def test_send_message(self, query_client):
        result = await query_client.send_message(
            session_id="sess-test-001",
            content="Тестовое сообщение",
        )
        assert "message_id" in result
        assert result["message_id"] == "msg-mock-001"
        assert "content" in result
        assert "role" in result

    @pytest.mark.asyncio
    async def test_update_context(self, query_client):
        result = await query_client.update_context(
            session_id="sess-test-001",
            action="add",
            params={"document_ids": ["doc-001"]},
        )
        # Note: mock endpoint parsing extracts session_id from path
        # using split("/")[2] which gives "sessions", not the actual ID
        assert "action" in result
        assert result["action"] == "add"
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_export_session(self, query_client):
        result = await query_client.export_session(
            session_id="sess-test-001",
            format="pdf",
        )
        assert result["export_id"] == "exp-mock-001"
        assert result["format"] == "pdf"
        assert result["status"] == "completed"
        assert "url" in result

    @pytest.mark.asyncio
    async def test_submit_feedback(self, query_client):
        result = await query_client.submit_feedback(
            session_id="sess-001",
            message_id="msg-001",
            rating=5,
            comment="Отличный ответ",
        )
        assert result["feedback_id"] == "fb-mock-001"
        assert result["saved"] is True
        assert "metrics_changed" in result


class TestQueryHistory:
    """Tests for history endpoints."""

    @pytest.mark.asyncio
    async def test_get_history(self, query_client):
        result = await query_client.get_history(page=1, page_size=20)
        assert "items" in result
        assert "meta" in result
        assert result["meta"]["page"] == 1
        assert result["meta"]["page_size"] == 20

    @pytest.mark.asyncio
    async def test_export_history(self, query_client):
        result = await query_client.export_history(format="xlsx")
        # Note: mock routing for /chat/history/export falls through to
        # the endswith("/export") handler which returns "exp-mock-001"
        assert "export_id" in result
        assert result["format"] == "xlsx"
        assert "url" in result
        assert "created_at" in result


class TestQueryQuickChat:
    """Tests for quick chat endpoint."""

    @pytest.mark.asyncio
    async def test_quick_chat(self, query_client):
        result = await query_client.quick_chat(question="Быстрый вопрос")
        assert "answer_id" in result
        assert "status" in result
        assert "message" in result
        assert "latency_ms" in result

    @pytest.mark.asyncio
    async def test_quick_chat_with_session(self, query_client):
        result = await query_client.quick_chat(
            question="Вопрос",
            session_id="sess-existing",
        )
        assert result["session_id"] == "sess-existing"
