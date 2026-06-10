"""Тесты базовых классов Pipeline Testing."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

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
