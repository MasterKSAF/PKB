"""
Юнит-тесты PipelineRunner.run_step() — тестируем логику выполнения шага
с замокированным HTTP-клиентом, без обращения к Docker.

Проверяет:
- Успешный HTTP-вызов с проверкой статуса, извлечением контекста, check-функциями
- Обработку ошибок: неверный статус, ConnectError, TimeoutException
- Retry-логику (retry_on)
- skip_if ветвление (хотя skip_if выполняется до run_step — проверяем на уровне run)
- Разные типы body: json, form, content
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from service_checker.pipelines.base import (
    PipelineContext,
    PipelineRunner,
    PipelineStep,
    StepStatus,
    check_json_field,
)


# ────────────────────────────────────────────────────────────────
#  Fixtures
# ────────────────────────────────────────────────────────────────


@pytest.fixture
def runner():
    """PipelineRunner с замокированным HTTP-клиентом."""
    r = PipelineRunner(base_host="127.0.0.1", timeout=10)
    r.client = AsyncMock(spec=httpx.AsyncClient)
    return r


@pytest.fixture
def ctx():
    return PipelineContext()


def _mock_response(status_code: int = 200, json_data: Optional[Dict] = None,
                   text: Optional[str] = None) -> MagicMock:
    """Создать mock httpx.Response с заданными параметрами."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    if text is not None:
        resp.text = text
        resp.content = text.encode() if text else None
    elif json_data is not None:
        body = json.dumps(json_data)
        resp.text = body
        resp.content = body.encode()
    else:
        resp.text = ""
        resp.content = None
    return resp


# ────────────────────────────────────────────────────────────────
#  3.1 успешный вызов: status check, extract_keys, check
# ────────────────────────────────────────────────────────────────


class TestRunStepSuccess:
    """Успешное выполнение шага."""

    @pytest.mark.asyncio
    async def test_basic_get(self, runner, ctx):
        """GET-запрос с ожидаемым 200."""
        step = PipelineStep(
            name="health", service="auth", method="GET",
            path="/api/v1/health", port=8082,
            expected_status=200,
        )
        runner.client.get = AsyncMock(return_value=_mock_response(200, {"status": "ok"}))

        result = await runner.run_step(step, ctx)

        assert result.status == StepStatus.PASSED
        assert result.actual_status == 200
        assert result.elapsed_ms >= 0
        runner.client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_keys(self, runner, ctx):
        """Извлечение access_token из ответа."""
        step = PipelineStep(
            name="auth", service="auth", method="POST",
            path="/api/v1/auth/token", port=8082,
            body={"username": "admin", "password": "admin"},
            expected_status=200,
            extract_keys=["access_token", "refresh_token"],
        )
        runner.client.post = AsyncMock(return_value=_mock_response(200, {
            "access_token": "jwt123",
            "refresh_token": "ref456",
        }))

        result = await runner.run_step(step, ctx)

        assert result.status == StepStatus.PASSED
        assert ctx.get("access_token") == "jwt123"
        assert ctx.get("refresh_token") == "ref456"

    @pytest.mark.asyncio
    async def test_check_function_passes(self, runner, ctx):
        """check-функция подтверждает поле в ответе."""
        step = PipelineStep(
            name="check_test", service="auth", method="GET",
            path="/api/v1/health", port=8082,
            expected_status=200,
            check=check_json_field("status", str),
        )
        runner.client.get = AsyncMock(return_value=_mock_response(200, {"status": "ok"}))

        result = await runner.run_step(step, ctx)

        assert result.status == StepStatus.PASSED
        assert "status" in (result.message or "")

    @pytest.mark.asyncio
    async def test_post_with_body(self, runner, ctx):
        """POST-запрос с JSON body."""
        step = PipelineStep(
            name="create", service="registry", method="POST",
            path="/api/v1/registry/documents/", port=8084,
            body={"title": "test", "doc_code": "T-001"},
            expected_status=201,
        )
        runner.client.post = AsyncMock(return_value=_mock_response(201, {"id": 1}))

        result = await runner.run_step(step, ctx)

        assert result.status == StepStatus.PASSED
        assert result.actual_status == 201
        # Проверяем, что тело было передано
        call_kwargs = runner.client.post.call_args[1]
        assert "json" in call_kwargs
        assert call_kwargs["json"]["title"] == "test"

    @pytest.mark.asyncio
    async def test_needs_auth_adds_header(self, runner, ctx):
        """needs_auth=True добавляет Authorization header."""
        ctx.set("access_token", "test-token")
        step = PipelineStep(
            name="auth_op", service="registry", method="GET",
            path="/api/v1/registry/documents", port=8084,
            expected_status=200, needs_auth=True,
        )
        runner.client.get = AsyncMock(return_value=_mock_response(200, []))

        result = await runner.run_step(step, ctx, auth_token="test-token")

        assert result.status == StepStatus.PASSED
        call_headers = runner.client.get.call_args[1]["headers"]
        assert call_headers["Authorization"] == "Bearer test-token"


# ────────────────────────────────────────────────────────────────
#  3.2, 3.3 неверный статус / статус как set
# ────────────────────────────────────────────────────────────────


class TestRunStepFailedStatus:
    """Обработка неверного HTTP-статуса."""

    @pytest.mark.asyncio
    async def test_wrong_status_int(self, runner, ctx):
        """expected_status=200, получен 500."""
        step = PipelineStep(
            name="fail", service="auth", method="GET",
            path="/api/v1/health", port=8082, expected_status=200,
        )
        runner.client.get = AsyncMock(return_value=_mock_response(500, {"error": "internal"}))

        result = await runner.run_step(step, ctx)

        assert result.status == StepStatus.FAILED
        assert "Expected HTTP 200" in (result.error or "")

    @pytest.mark.asyncio
    async def test_status_set_allows_multiple(self, runner, ctx):
        """expected_status={200, 409} — 409 проходит."""
        step = PipelineStep(
            name="create", service="registry", method="POST",
            path="/api/v1/registry/documents/", port=8084,
            expected_status={200, 409},
        )
        runner.client.post = AsyncMock(return_value=_mock_response(409, {"detail": "conflict"}))

        result = await runner.run_step(step, ctx)

        assert result.status == StepStatus.PASSED
        assert result.actual_status == 409

    @pytest.mark.asyncio
    async def test_status_set_rejects(self, runner, ctx):
        """expected_status={200, 409} — 422 не проходит."""
        step = PipelineStep(
            name="create", service="registry", method="POST",
            path="/api/v1/registry/documents/", port=8084,
            expected_status={200, 409},
        )
        runner.client.post = AsyncMock(return_value=_mock_response(422, {"detail": "validation"}))

        result = await runner.run_step(step, ctx)

        assert result.status == StepStatus.FAILED
        assert "Expected HTTP {200, 409}" in (result.error or "")

    @pytest.mark.asyncio
    async def test_failed_triggers_on_error(self, runner, ctx):
        """on_error вызывается при неверном статусе."""
        on_error_called = False

        def _on_error(body, pipeline_ctx):
            nonlocal on_error_called
            on_error_called = True
            pipeline_ctx.set("error_happened", True)

        step = PipelineStep(
            name="fail", service="rag_builder", method="POST",
            path="/api/v1/rag/build", port=8090,
            expected_status=200, on_error=_on_error,
        )
        runner.client.post = AsyncMock(return_value=_mock_response(500, {"status": "error"}))

        result = await runner.run_step(step, ctx)

        assert result.status == StepStatus.FAILED
        assert on_error_called
        assert ctx.get("error_happened") is True


# ────────────────────────────────────────────────────────────────
#  3.4 Retry-логика
# ────────────────────────────────────────────────────────────────


class TestRunStepRetry:
    """Повторные попытки при retry_on."""

    @pytest.mark.asyncio
    async def test_retry_succeeds(self, runner, ctx):
        """После 2 неудач — успех на 3-й."""
        step = PipelineStep(
            name="retry", service="auth", method="GET",
            path="/api/v1/health", port=8082,
            expected_status=200, retry_on={503}, retry_max=3, retry_delay=0.01,
        )
        responses = [
            _mock_response(503, {"error": "unavailable"}),
            _mock_response(503, {"error": "unavailable"}),
            _mock_response(200, {"status": "ok"}),
        ]
        runner.client.get = AsyncMock(side_effect=responses)

        result = await runner.run_step(step, ctx)

        assert result.status == StepStatus.PASSED
        assert result.actual_status == 200
        assert runner.client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self, runner, ctx):
        """Все retry исчерпаны — шаг падает."""
        step = PipelineStep(
            name="retry", service="auth", method="GET",
            path="/api/v1/health", port=8082,
            expected_status=200, retry_on={503}, retry_max=2, retry_delay=0.01,
        )
        runner.client.get = AsyncMock(return_value=_mock_response(503, {"error": "unavailable"}))

        result = await runner.run_step(step, ctx)

        assert result.status == StepStatus.FAILED
        # initial + retry_max retries = 3 total (range(retry_max) = 0,1)
        assert runner.client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_on_different_status(self, runner, ctx):
        """retry_on={503}, но сервер вернул 500 — без повторов."""
        step = PipelineStep(
            name="retry", service="auth", method="GET",
            path="/api/v1/health", port=8082,
            expected_status=200, retry_on={503}, retry_max=3, retry_delay=0.01,
        )
        runner.client.get = AsyncMock(return_value=_mock_response(500, {"error": "internal"}))

        result = await runner.run_step(step, ctx)

        assert result.status == StepStatus.FAILED
        assert runner.client.get.call_count == 1  # без повтора


# ────────────────────────────────────────────────────────────────
#  3.5, 3.6 Ошибки подключения / таймаут
# ────────────────────────────────────────────────────────────────


class TestRunStepErrors:
    """Сетевые ошибки."""

    @pytest.mark.asyncio
    async def test_connect_error(self, runner, ctx):
        """ConnectError — шаг FAILED."""
        step = PipelineStep(
            name="conn", service="auth", method="GET",
            path="/api/v1/health", port=8082, expected_status=200,
        )
        runner.client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

        result = await runner.run_step(step, ctx)

        assert result.status == StepStatus.FAILED
        assert "ConnectError" in (result.error or "")

    @pytest.mark.asyncio
    async def test_timeout(self, runner, ctx):
        """TimeoutException — шаг FAILED."""
        step = PipelineStep(
            name="timeout", service="auth", method="GET",
            path="/api/v1/health", port=8082, expected_status=200,
        )
        runner.client.get = AsyncMock(side_effect=httpx.TimeoutException("Timed out"))

        result = await runner.run_step(step, ctx)

        assert result.status == StepStatus.FAILED
        assert "Timeout" in (result.error or "")

    @pytest.mark.asyncio
    async def test_unexpected_exception(self, runner, ctx):
        """Неизвестное исключение — шаг FAILED."""
        step = PipelineStep(
            name="crash", service="auth", method="GET",
            path="/api/v1/health", port=8082, expected_status=200,
        )
        runner.client.get = AsyncMock(side_effect=RuntimeError("Unexpected error"))

        result = await runner.run_step(step, ctx)

        assert result.status == StepStatus.FAILED


# ────────────────────────────────────────────────────────────────
#  3.7 check-функция возвращает False
# ────────────────────────────────────────────────────────────────


class TestRunStepCheckFails:
    """Проверка check-функции."""

    @pytest.mark.asyncio
    async def test_check_fails_marks_failed(self, runner, ctx):
        """check вернул False — шаг FAILED."""
        def _check(body, pipeline_ctx):
            return False, "поле status не найдено"

        step = PipelineStep(
            name="check_fail", service="auth", method="GET",
            path="/api/v1/health", port=8082,
            expected_status=200, check=_check,
        )
        runner.client.get = AsyncMock(return_value=_mock_response(200, {}))

        result = await runner.run_step(step, ctx)

        assert result.status == StepStatus.FAILED
        assert "поле status не найдено" in (result.error or "")

    @pytest.mark.asyncio
    async def test_check_with_body_ref(self, runner, ctx):
        """check-функция получает тело ответа."""
        received_body = [None]

        def _check(body, pipeline_ctx):
            received_body[0] = body
            return True, "ok"

        step = PipelineStep(
            name="check_body", service="auth", method="GET",
            path="/api/v1/health", port=8082,
            expected_status=200, check=_check,
        )
        runner.client.get = AsyncMock(
            return_value=_mock_response(200, {"status": "ok"})
        )

        await runner.run_step(step, ctx)

        assert received_body[0] is not None
        parsed = json.loads(received_body[0])
        assert parsed["status"] == "ok"


# ────────────────────────────────────────────────────────────────
#  3.8 skip_if — на уровне run (run_step НЕ знает о skip_if)
# ────────────────────────────────────────────────────────────────


class TestRunStepSkipIf:
    """skip_if обрабатывается на уровне PipelineRunner.run(), не run_step().

    run_step всегда выполняет HTTP-вызов. Проверяем что skip_if=None
    и шаг проходит нормально.
    """

    @pytest.mark.asyncio
    async def test_step_with_skip_if_attr(self, runner, ctx):
        """Шаг с skip_if не пропускается run_step (пропускает run)."""
        step = PipelineStep(
            name="skippable", service="auth", method="GET",
            path="/api/v1/health", port=8082,
            expected_status=200,
            skip_if=lambda ctx: True,
        )
        runner.client.get = AsyncMock(return_value=_mock_response(200, {"status": "ok"}))

        result = await runner.run_step(step, ctx)

        # run_step всё равно выполняет HTTP-вызов (skip_if — ответственность run)
        assert result.status == StepStatus.PASSED
        assert result.actual_status == 200


# ────────────────────────────────────────────────────────────────
#  3.9, 3.10 form_body и content
# ────────────────────────────────────────────────────────────────


class TestRunStepBodyTypes:
    """Разные типы тела запроса."""

    @pytest.mark.asyncio
    async def test_form_body(self, runner, ctx):
        """form_body передаётся как data."""
        step = PipelineStep(
            name="form", service="gateway", method="POST",
            path="/api/v1/documents", port=8080,
            expected_status=200,
            form_body={"key": "value"},
            form_files={"file": ("test.pdf", b"%PDF", "application/pdf")},
        )
        runner.client.post = AsyncMock(return_value=_mock_response(200, {"status": "ok"}))

        result = await runner.run_step(step, ctx)

        assert result.status == StepStatus.PASSED
        call_kwargs = runner.client.post.call_args[1]
        assert "data" in call_kwargs
        assert "files" in call_kwargs
        assert "json" not in call_kwargs

    @pytest.mark.asyncio
    async def test_content_body(self, runner, ctx):
        """content передаётся как raw bytes."""
        step = PipelineStep(
            name="raw", service="parser", method="POST",
            path="/api/v1/parser/process", port=8087,
            expected_status=200,
            content=b"raw data",
        )
        runner.client.post = AsyncMock(return_value=_mock_response(200, {"status": "ok"}))

        result = await runner.run_step(step, ctx)

        assert result.status == StepStatus.PASSED
        call_kwargs = runner.client.post.call_args[1]
        assert "content" in call_kwargs
        assert call_kwargs["content"] == b"raw data"

    @pytest.mark.asyncio
    async def test_params(self, runner, ctx):
        """Query-параметры передаются."""
        step = PipelineStep(
            name="params", service="registry", method="GET",
            path="/api/v1/registry/classifiers/tree", port=8084,
            expected_status=200, params={"classifier_system": "OKS"},
        )
        runner.client.get = AsyncMock(return_value=_mock_response(200, []))

        result = await runner.run_step(step, ctx)

        assert result.status == StepStatus.PASSED
        call_kwargs = runner.client.get.call_args[1]
        assert "params" in call_kwargs
        assert call_kwargs["params"]["classifier_system"] == "OKS"
