"""Тесты базовых классов Pipeline Testing."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from service_checker.pipelines.base import (
    PipelineContext,
    PipelineDef,
    PipelineResult,
    PipelineRunner,
    PipelineStep,
    StepStatus,
    check_contains_text,
    check_json_field,
    check_json_fields,
    check_rag_search_results,
)


class TestPipelineContext:
    """PipelineContext — хранение переменных между шагами."""

    def test_set_and_get(self):
        ctx = PipelineContext()
        ctx.set("token", "abc123")
        assert ctx.get("token") == "abc123"

    def test_get_default(self):
        ctx = PipelineContext()
        assert ctx.get("missing", "default") == "default"

    def test_has(self):
        ctx = PipelineContext()
        ctx.set("key", "value")
        assert ctx.has("key")
        assert not ctx.has("other")


class TestPipelineStep:
    """PipelineStep — определение одного шага."""

    def test_default_status_is_pending(self):
        step = PipelineStep(name="test", service="auth", method="GET", path="/health", port=8082)
        assert step.status == StepStatus.PENDING
        assert step.actual_status == 0
        assert step.elapsed_ms == 0

    def test_step_with_all_fields(self):
        step = PipelineStep(
            name="Auth",
            service="auth",
            method="POST",
            path="/api/v1/auth/token",
            port=8082,
            body={"username": "test", "password": "test"},
            params={"page": 1},
            expected_status=200,
            extract_keys=["access_token"],
            needs_auth=False,
        )
        assert step.name == "Auth"
        assert step.port == 8082
        assert step.expected_status == 200


class TestPipelineResult:
    """PipelineResult — агрегация результатов пайплайна."""

    def test_empty_result(self):
        result = PipelineResult(name="test", description="Test pipeline")
        assert result.passed is False
        assert result.total_steps == 0
        assert result.api_calls_total == 0
        assert result.api_calls_ok == 0

    def test_api_calls_properties(self):
        result = PipelineResult(
            name="test",
            description="Test",
            total_steps=10,
            passed_steps=8,
            failed_steps=2,
        )
        assert result.api_calls_total == 10
        assert result.api_calls_ok == 8


class TestPipelineDef:
    """PipelineDef — базовый класс для пайплайнов."""

    def test_default_attributes(self):
        p = PipelineDef()
        assert p.name == ""
        assert p.description == ""
        assert p.services == []

    def test_build_steps_raises(self):
        p = PipelineDef()
        with pytest.raises(NotImplementedError):
            p.build_steps(PipelineContext())


class TestPipelineRunner:
    """PipelineRunner — движок выполнения (юнит-тесты без HTTP)."""

    def test_get_service_port_known(self):
        runner = PipelineRunner()
        assert runner._get_service_port("auth") == 8082
        assert runner._get_service_port("parser") == 8087
        assert runner._get_service_port("registry") == 8084

    def test_get_service_port_unknown(self):
        runner = PipelineRunner()
        assert runner._get_service_port("nonexistent") is None

    def test_resolve_path_no_vars(self):
        runner = PipelineRunner()
        ctx = PipelineContext()
        assert runner._resolve_path("/api/v1/health", ctx) == "/api/v1/health"

    def test_resolve_path_with_vars(self):
        runner = PipelineRunner()
        ctx = PipelineContext()
        ctx.set("doc_id", "123")
        assert runner._resolve_path("/api/v1/documents/{doc_id}", ctx) == "/api/v1/documents/123"

    def test_resolve_body_no_vars(self):
        runner = PipelineRunner()
        ctx = PipelineContext()
        body = {"key": "value"}
        assert runner._resolve_body(body, ctx) == {"key": "value"}

    def test_resolve_body_with_vars(self):
        runner = PipelineRunner()
        ctx = PipelineContext()
        ctx.set("token", "abc")
        body = {"auth": "{token}"}
        assert runner._resolve_body(body, ctx) == {"auth": "abc"}

    def test_resolve_body_inline_dict(self):
        """__INLINE__ подставляет dict как есть (без обёртки в строку)."""
        runner = PipelineRunner()
        ctx = PipelineContext()
        ctx.set("sections", [{"id": 1, "text": "test"}])
        body = {"document_id": "{doc_id}", "sections": "__INLINE__sections"}
        resolved = runner._resolve_body(body, ctx)
        assert resolved["document_id"] == "{doc_id}"  # doc_id нет в контексте
        assert isinstance(resolved["sections"], list)
        assert resolved["sections"][0]["id"] == 1

    def test_resolve_body_inline_int(self):
        """__INLINE__ подставляет int как число."""
        runner = PipelineRunner()
        ctx = PipelineContext()
        ctx.set("section_id", 42)
        body = {"section_id": "__INLINE__section_id", "nested": {"val": "__INLINE__section_id"}}
        resolved = runner._resolve_body(body, ctx)
        assert resolved["section_id"] == 42
        assert resolved["nested"]["val"] == 42

    def test_resolve_body_inline_bool(self):
        """__INLINE__ подставляет bool."""
        runner = PipelineRunner()
        ctx = PipelineContext()
        ctx.set("flag", True)
        body = {"flag": "__INLINE__flag"}
        resolved = runner._resolve_body(body, ctx)
        assert resolved["flag"] is True

    def test_resolve_body_inline_none(self):
        """__INLINE__ подставляет None как null."""
        runner = PipelineRunner()
        ctx = PipelineContext()
        ctx.set("nothing", None)
        body = {"value": "__INLINE__nothing"}
        resolved = runner._resolve_body(body, ctx)
        assert resolved["value"] is None

    def test_resolve_body_mixed_regular_and_inline(self):
        """Смешанные {key} строковые и __INLINE__ подстановки."""
        runner = PipelineRunner()
        ctx = PipelineContext()
        ctx.set("doc_id", "42")
        ctx.set("sections", [{"id": 1}])
        body = {
            "document_id": "{doc_id}",
            "sections": "__INLINE__sections",
        }
        resolved = runner._resolve_body(body, ctx)
        assert resolved["document_id"] == "42"
        assert resolved["sections"] == [{"id": 1}]

    def test_resolve_body_multiple_inline(self):
        """Несколько __INLINE__ ключей в одном объекте."""
        runner = PipelineRunner()
        ctx = PipelineContext()
        ctx.set("doc_id", 1)
        ctx.set("section_id", 2)
        body = {
            "document_id": "__INLINE__doc_id",
            "sections": [{"section_id": "__INLINE__section_id", "text": "test"}],
        }
        resolved = runner._resolve_body(body, ctx)
        assert resolved["document_id"] == 1
        assert resolved["sections"][0]["section_id"] == 2

    def test_resolve_body_nested_dict_inline(self):
        """__INLINE__ вложенного dict."""
        runner = PipelineRunner()
        ctx = PipelineContext()
        ctx.set("content", {"text": "hello", "type": "text"})
        body = {"content": "__INLINE__content"}
        resolved = runner._resolve_body(body, ctx)
        assert resolved["content"]["text"] == "hello"
        assert resolved["content"]["type"] == "text"

    def test_extract_context_simple(self):
        runner = PipelineRunner()
        ctx = PipelineContext()
        response = json.dumps({"access_token": "jwt123", "refresh_token": "ref456"})
        runner._extract_context(response, ["access_token", "refresh_token"], ctx)
        assert ctx.get("access_token") == "jwt123"
        assert ctx.get("refresh_token") == "ref456"

    def test_extract_context_nested(self):
        runner = PipelineRunner()
        ctx = PipelineContext()
        response = json.dumps({"data": {"id": "doc-001", "title": "Test"}})
        runner._extract_context(response, ["doc_id"], ctx)
        assert ctx.get("doc_id") == "doc-001"

    def test_extract_context_alt_names(self):
        runner = PipelineRunner()
        ctx = PipelineContext()
        response = json.dumps({"sessionId": "session-xyz"})
        runner._extract_context(response, ["session_id"], ctx)
        assert ctx.get("session_id") == "session-xyz"

    def test_extract_context_already_set(self):
        runner = PipelineRunner()
        ctx = PipelineContext()
        ctx.set("doc_id", "existing")
        response = json.dumps({"doc_id": "new"})
        runner._extract_context(response, ["doc_id"], ctx)
        # Не перезаписывает уже существующий
        assert ctx.get("doc_id") == "existing"

    def test_extract_context_data_wrapper(self):
        """Извлечение из обёртки data.key."""
        runner = PipelineRunner()
        ctx = PipelineContext()
        response = json.dumps({"data": {"id": "42", "items": []}})
        runner._extract_context(response, ["doc_id"], ctx)
        # _search находит 'id' в data через alt_map: doc_id → ["id", "document_id", "docId"]
        assert ctx.get("doc_id") == "42"

    def test_extract_context_alt_name_session_id(self):
        """session_id ищется как id/sessionId/session_id."""
        runner = PipelineRunner()
        ctx = PipelineContext()
        response = json.dumps({"sessionId": "sess-001"})
        runner._extract_context(response, ["session_id"], ctx)
        assert ctx.get("session_id") == "sess-001"

    def test_extract_context_alt_name_task_id(self):
        """task_id ищется как task_id/taskId."""
        runner = PipelineRunner()
        ctx = PipelineContext()
        response = json.dumps({"taskId": "task-42"})
        runner._extract_context(response, ["task_id"], ctx)
        assert ctx.get("task_id") == "task-42"

    def test_extract_context_alt_name_message_id(self):
        """message_id ищется как id/messageId/message_id."""
        runner = PipelineRunner()
        ctx = PipelineContext()
        response = json.dumps({"messageId": "msg-001"})
        runner._extract_context(response, ["message_id"], ctx)
        assert ctx.get("message_id") == "msg-001"

    def test_extract_context_alt_name_user_id(self):
        """user_id ищется как id/userId/user_id."""
        runner = PipelineRunner()
        ctx = PipelineContext()
        response = json.dumps({"userId": 5})
        runner._extract_context(response, ["user_id"], ctx)
        assert ctx.get("user_id") == 5

    def test_extract_context_alt_name_classifier_code(self):
        """classifier_code ищется как code/classifier_code."""
        runner = PipelineRunner()
        ctx = PipelineContext()
        response = json.dumps({"code": "OKS-001"})
        runner._extract_context(response, ["classifier_code"], ctx)
        assert ctx.get("classifier_code") == "OKS-001"

    def test_extract_context_nested_list(self):
        """Поиск в списке объектов."""
        runner = PipelineRunner()
        ctx = PipelineContext()
        response = json.dumps({"items": [{"id": 99}]})
        runner._extract_context(response, ["doc_id"], ctx)
        assert ctx.get("doc_id") == 99

    def test_extract_context_returns_none_on_missing(self):
        """Ключ не найден — контекст не меняется."""
        runner = PipelineRunner()
        ctx = PipelineContext()
        response = json.dumps({"status": "ok"})
        runner._extract_context(response, ["missing_key"], ctx)
        assert ctx.has("missing_key") is False

    def test_extract_context_invalid_json(self):
        """Невалидный JSON — ничего не извлекается."""
        runner = PipelineRunner()
        ctx = PipelineContext()
        runner._extract_context("not json", ["key"], ctx)
        assert ctx.has("key") is False

    def test_extract_context_empty_body(self):
        """Пустое тело — ничего не извлекается."""
        runner = PipelineRunner()
        ctx = PipelineContext()
        runner._extract_context(None, ["key"], ctx)
        assert ctx.has("key") is False
        runner._extract_context("", ["key"], ctx)
        assert ctx.has("key") is False

    # ── skip_if: ветвление шагов ──────────────────────────────────

    def test_skip_if_default_is_none(self):
        """По умолчанию skip_if = None (нет ветвления)."""
        step = PipelineStep(name="test", service="auth", method="GET", path="/health", port=8082)
        assert step.skip_if is None

    def test_skip_if_skip_when_true(self):
        """Если skip_if(ctx) вернул True — шаг должен пропускаться."""
        step = PipelineStep(
            name="Skippable", service="auth", method="GET", path="/health", port=8082,
            skip_if=lambda ctx: ctx.get("skip", False),
        )
        ctx = PipelineContext()
        ctx.set("skip", True)
        assert step.skip_if is not None
        assert step.skip_if(ctx) is True

    def test_skip_if_run_when_false(self):
        """Если skip_if(ctx) вернул False — шаг выполняется."""
        step = PipelineStep(
            name="Skippable", service="auth", method="GET", path="/health", port=8082,
            skip_if=lambda ctx: ctx.get("skip", False),
        )
        ctx = PipelineContext()
        ctx.set("skip", False)
        assert step.skip_if(ctx) is False

    def test_skip_if_not_set_still_runs(self):
        """Если skip_if=None — шаг всегда выполняется."""
        step = PipelineStep(name="normal", service="auth", method="GET", path="/health", port=8082)
        # Нет skip_if — выполняется всегда (не пропускается)
        assert step.skip_if is None

    # ── _ensure_project ────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_ensure_project_raises_on_connection_error(self):
        """_ensure_project raises RuntimeError when it can't connect."""
        runner = PipelineRunner()
        ctx = PipelineContext()
        # Mock client to raise exception on both post and get
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        runner.client = mock_client

        with pytest.raises(RuntimeError, match="Cannot create or fetch project"):
            await runner._ensure_project(ctx)

        # Neither project_id should be set
        assert ctx.has("project_id") is False

    @pytest.mark.asyncio
    async def test_ensure_project_succeeds_on_post_201(self):
        """_ensure_project succeeds when POST returns 201."""
        runner = PipelineRunner()
        ctx = PipelineContext()

        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"project_id": 42}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        runner.client = mock_client

        await runner._ensure_project(ctx)

        assert ctx.get("project_id") == 42
        # GET should not be called
        mock_client.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_project_succeeds_on_get_list(self):
        """_ensure_project succeeds when GET list returns items (POST failed)."""
        runner = PipelineRunner()
        ctx = PipelineContext()

        # POST fails with 500 (all 3 attempts)
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 500

        # GET returns items on first attempt
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {"items": [{"project_id": 99}]}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_post_resp)
        mock_client.get = AsyncMock(return_value=mock_get_resp)
        runner.client = mock_client

        await runner._ensure_project(ctx)

        assert ctx.get("project_id") == 99
        # POST should have been called 3 times
        assert mock_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_ensure_project_raises_on_empty_get_list(self):
        """_ensure_project raises when GET list returns empty."""
        runner = PipelineRunner()
        ctx = PipelineContext()

        # POST fails with 500 (all 3 attempts)
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 500

        # GET returns empty list (all 3 attempts)
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {"items": []}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_post_resp)
        mock_client.get = AsyncMock(return_value=mock_get_resp)
        runner.client = mock_client

        with pytest.raises(RuntimeError, match="Cannot create or fetch project"):
            await runner._ensure_project(ctx)

        assert ctx.has("project_id") is False
        # POST should have been called 3 times, GET 3 times
        assert mock_client.post.call_count == 3
        assert mock_client.get.call_count == 3


class TestStepStatus:
    """StepStatus — enum статусов шага."""

    def test_values(self):
        assert StepStatus.PENDING.value == "pending"
        assert StepStatus.RUNNING.value == "running"
        assert StepStatus.PASSED.value == "passed"
        assert StepStatus.FAILED.value == "failed"
        assert StepStatus.SKIPPED.value == "skipped"

    def test_all_members(self):
        assert len(StepStatus) == 5


# ── Тесты вспомогательных проверок ────────────────────────────────────


class TestCheckJsonField:
    """check_json_field — проверка поля в JSON-ответе."""

    def test_field_exists_string(self):
        check = check_json_field("status", str)
        ok, msg = check(json.dumps({"status": "ok"}), PipelineContext())
        assert ok
        assert "status" in msg

    def test_field_exists_int(self):
        check = check_json_field("count", int)
        ok, msg = check(json.dumps({"count": 42}), PipelineContext())
        assert ok

    def test_field_missing(self):
        check = check_json_field("missing_field", str)
        ok, msg = check(json.dumps({"status": "ok"}), PipelineContext())
        assert not ok
        assert "не найдено" in msg

    def test_field_wrong_type(self):
        check = check_json_field("status", int)
        ok, msg = check(json.dumps({"status": "ok"}), PipelineContext())
        assert not ok
        assert "ожидалось int" in msg

    def test_empty_body(self):
        check = check_json_field("status", str)
        ok, msg = check(None, PipelineContext())
        assert not ok
        assert "Пустой ответ" in msg

    def test_invalid_json(self):
        check = check_json_field("status", str)
        ok, msg = check("not json", PipelineContext())
        assert not ok
        assert "Невалидный JSON" in msg

    def test_nested_field(self):
        check = check_json_field("data.id", str)
        ok, msg = check(json.dumps({"data": {"id": "abc"}}), PipelineContext())
        assert ok

    def test_nested_field_missing(self):
        check = check_json_field("data.missing", str)
        ok, msg = check(json.dumps({"data": {"id": "abc"}}), PipelineContext())
        assert not ok


class TestCheckJsonFields:
    """check_json_fields — проверка нескольких полей."""

    def test_all_fields_valid(self):
        schema = {"status": str, "data": dict}
        check = check_json_fields(schema)
        ok, msg = check(json.dumps({"status": "ok", "data": {"id": 1}}), PipelineContext())
        assert ok

    def test_one_field_invalid(self):
        schema = {"status": str, "count": int}
        check = check_json_fields(schema)
        ok, msg = check(json.dumps({"status": "ok"}), PipelineContext())
        assert not ok

    def test_empty_nested(self):
        schema = {"data.items": list}
        check = check_json_fields(schema)
        ok, msg = check(json.dumps({"data": {"items": []}}), PipelineContext())
        assert ok


class TestCheckContainsText:
    """check_contains_text — поиск подстроки в ответе."""

    def test_contains(self):
        check = check_contains_text("success")
        ok, msg = check(json.dumps({"result": "success"}), PipelineContext())
        assert ok

    def test_not_contains(self):
        check = check_contains_text("error")
        ok, msg = check(json.dumps({"result": "success"}), PipelineContext())
        assert not ok

    def test_empty_body(self):
        check = check_contains_text("text")
        ok, msg = check(None, PipelineContext())
        assert not ok


class TestCheckRagSearchResults:
    """check_rag_search_results — валидация RAG Search по source-индексам."""

    def test_empty_body(self):
        check = check_rag_search_results()
        ok, msg = check(None, PipelineContext())
        assert not ok
        assert "Пустой ответ" in msg

    def test_not_json(self):
        check = check_rag_search_results()
        ok, msg = check("not json", PipelineContext())
        assert not ok
        assert "Невалидный JSON" in msg

    def test_results_is_not_list(self):
        check = check_rag_search_results()
        ok, msg = check(json.dumps({"results": "not_a_list"}), PipelineContext())
        assert not ok
        assert "должен быть списком" in msg

    def test_empty_results_is_ok(self):
        check = check_rag_search_results()
        ok, msg = check(json.dumps({"results": []}), PipelineContext())
        assert ok
        assert "results=[]" in msg

    def test_empty_results_with_require_sources_fails(self):
        check = check_rag_search_results(require_sources=True)
        ok, msg = check(json.dumps({"results": []}), PipelineContext())
        assert not ok
        assert "требовались source-индексы" in msg

    def test_valid_result_with_source_retrieval(self):
        check = check_rag_search_results()
        body = json.dumps({
            "results": [
                {
                    "source": {
                        "document_id": 420000,
                        "section_id": 8,
                        "clause": "6.1",
                        "path": "6/6.1",
                        "page": 2,
                        "bbox": None,
                        "section_title": "Допуск",
                        "content": "Текст...",
                        "content_hash": "sha256-abc",
                    },
                    "retrieval": {
                        "chunk_id": 119,
                        "score": 0.87,
                        "mode": "dense_rerank",
                    },
                    "context": [
                        {"chunk_id": 118, "content": "Контекст...", "score": 0.45, "page": 2}
                    ],
                }
            ],
            "processing_time_ms": 120,
            "total_found": 1,
        })
        ok, msg = check(body, PipelineContext())
        assert ok
        assert "source-индексам" in msg

    def test_missing_source_fails(self):
        check = check_rag_search_results()
        body = json.dumps({
            "results": [
                {
                    "retrieval": {"chunk_id": 119, "score": 0.87, "mode": "dense_rerank"},
                }
            ],
        })
        ok, msg = check(body, PipelineContext())
        assert not ok
        assert "source отсутствует" in msg

    def test_missing_document_id_fails(self):
        check = check_rag_search_results()
        body = json.dumps({
            "results": [
                {
                    "source": {"section_id": 8},
                    "retrieval": {"chunk_id": 119, "score": 0.87, "mode": "dense_rerank"},
                }
            ],
        })
        ok, msg = check(body, PipelineContext())
        assert not ok
        assert "document_id или section_id отсутствуют" in msg

    def test_missing_retrieval_chunk_id_fails(self):
        check = check_rag_search_results()
        body = json.dumps({
            "results": [
                {
                    "source": {"document_id": 1, "section_id": 8},
                    "retrieval": {"score": 0.87, "mode": "dense_rerank"},  # нет chunk_id
                }
            ],
        })
        ok, msg = check(body, PipelineContext())
        assert not ok
        assert "chunk_id/score/mode обязательны" in msg

    def test_multiple_results_all_valid(self):
        check = check_rag_search_results()
        body = json.dumps({
            "results": [
                {
                    "source": {"document_id": 1, "section_id": 10},
                    "retrieval": {"chunk_id": 1, "score": 0.9, "mode": "dense_rerank"},
                },
                {
                    "source": {"document_id": 2, "section_id": 20},
                    "retrieval": {"chunk_id": 2, "score": 0.8, "mode": "hybrid_rrf"},
                },
            ],
        })
        ok, msg = check(body, PipelineContext())
        assert ok
        assert "results[2/2]" in msg
