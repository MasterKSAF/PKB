"""
Юнит-тесты PipelineRunner.run() — тестируем логику выполнения пайплайна
с замокированными run_step и ping_service, без обращения к Docker.

Проверяет:
- Агрегацию результатов (passed/failed/skipped)
- Определение успеха пайплайна
- Ping-проверку сервисов
- skip_if ветвление
- Auth-token flow между шагами
- Обработку ошибок build_steps
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from service_checker.pipelines.base import (
    PipelineContext,
    PipelineDef,
    PipelineResult,
    PipelineRunner,
    PipelineStep,
    StepStatus,
)


# ────────────────────────────────────────────────────────────────
#  Helpers
# ────────────────────────────────────────────────────────────────


class MockPipeline(PipelineDef):
    """Тестовый пайплайн с контролируемыми шагами."""
    name = "mock_pipeline"
    description = "Тестовый пайплайн"
    services = ["auth", "registry"]

    def __init__(self, steps_to_return=None):
        super().__init__()
        self._steps = steps_to_return or []

    def build_steps(self, context: PipelineContext):
        return self._steps


def make_step(name: str, service: str = "auth",
              needs_auth: bool = False) -> PipelineStep:
    """Создать минимальный шаг."""
    return PipelineStep(
        name=name, service=service, method="GET",
        path="/api/v1/health", port=18082,
        expected_status=200, needs_auth=needs_auth,
    )


def make_passed_step(name: str, **kwargs) -> PipelineStep:
    """Создать шаг со статусом PASSED."""
    step = make_step(name, **kwargs)
    step.status = StepStatus.PASSED
    step.actual_status = 200
    return step


def make_failed_step(name: str, **kwargs) -> PipelineStep:
    """Создать шаг со статусом FAILED."""
    step = make_step(name, **kwargs)
    step.status = StepStatus.FAILED
    step.actual_status = 500
    step.error = "Expected HTTP 200, got 500"
    return step


# ────────────────────────────────────────────────────────────────
#  Fixtures
# ────────────────────────────────────────────────────────────────


@pytest.fixture
def runner():
    """PipelineRunner с замокированным HTTP-клиентом."""
    r = PipelineRunner(base_host="127.0.0.1", timeout=10)
    r.client = AsyncMock()  # не используется (run_step замокирован)
    return r


# ────────────────────────────────────────────────────────────────
#  4.1 все шаги успешны
# ────────────────────────────────────────────────────────────────


class TestRunAllPass:
    """Пайплайн с успешными шагами."""

    @pytest.mark.asyncio
    async def test_all_passed(self, runner):
        """Все 3 шага PASSED → пайплайн пройден."""
        steps = [
            make_passed_step("step1"),
            make_passed_step("step2"),
            make_passed_step("step3"),
        ]
        pipeline = MockPipeline(steps)
        runner.run_step = AsyncMock(side_effect=steps)
        runner.ping_service = AsyncMock(return_value=True)

        result = await runner.run(pipeline)

        assert result.passed is True
        assert result.ping_ok is True
        assert result.passed_steps == 3
        assert result.failed_steps == 0
        assert result.skipped_steps == 0
        assert result.total_steps == 3
        assert result.name == "mock_pipeline"

    @pytest.mark.asyncio
    async def test_ping_fails(self, runner):
        """Ping не проходит → ping_ok=False, пайплайн не пройден."""
        steps = [make_passed_step("step1")]
        pipeline = MockPipeline(steps)
        runner.run_step = AsyncMock(return_value=steps[0])
        runner.ping_service = AsyncMock(return_value=False)

        result = await runner.run(pipeline)

        assert result.ping_ok is False
        assert result.passed is False
        # Шаги всё равно выполняются
        assert result.passed_steps == 1

    @pytest.mark.asyncio
    async def test_skip_ping(self, runner):
        """skip_ping=True пропускает ping."""
        steps = [make_passed_step("step1")]
        pipeline = MockPipeline(steps)
        runner.run_step = AsyncMock(return_value=steps[0])
        runner.ping_service = AsyncMock(side_effect=RuntimeError("Не должен вызываться"))

        result = await runner.run(pipeline, skip_ping=True)

        assert result.ping_ok is True
        assert result.passed is True
        runner.ping_service.assert_not_called()


# ────────────────────────────────────────────────────────────────
#  4.2 часть шагов упала
# ────────────────────────────────────────────────────────────────


class TestRunSomeFail:
    """Часть шагов падает."""

    @pytest.mark.asyncio
    async def test_one_fails(self, runner):
        """1 из 3 шагов упал → пайплайн не пройден."""
        steps = [
            make_passed_step("ok"),
            make_failed_step("fail"),
            make_passed_step("ok2"),
        ]
        pipeline = MockPipeline(steps)
        runner.run_step = AsyncMock(side_effect=steps)
        runner.ping_service = AsyncMock(return_value=True)

        result = await runner.run(pipeline)

        assert result.passed is False
        assert result.passed_steps == 2
        assert result.failed_steps == 1
        assert result.total_steps == 3

    @pytest.mark.asyncio
    async def test_all_fail(self, runner):
        """Все шаги упали."""
        steps = [
            make_failed_step("fail1"),
            make_failed_step("fail2"),
        ]
        pipeline = MockPipeline(steps)
        runner.run_step = AsyncMock(side_effect=steps)
        runner.ping_service = AsyncMock(return_value=True)

        result = await runner.run(pipeline)

        assert result.passed is False
        assert result.passed_steps == 0
        assert result.failed_steps == 2


# ────────────────────────────────────────────────────────────────
#  4.3 ping проверка
# ────────────────────────────────────────────────────────────────


class TestRunPing:
    """Ping-проверка сервисов."""

    @pytest.mark.asyncio
    async def test_ping_all_services(self, runner):
        """Ping вызывается для всех сервисов пайплайна."""
        steps = [
            make_passed_step("auth_op", service="auth"),
            make_passed_step("reg_op", service="registry"),
        ]
        pipeline = MockPipeline(steps)
        runner.run_step = AsyncMock(side_effect=steps)
        runner.ping_service = AsyncMock(return_value=True)

        await runner.run(pipeline)

        # ping_service вызывается для auth и registry
        auth_port = runner._get_service_port("auth")
        reg_port = runner._get_service_port("registry")
        assert runner.ping_service.call_count == 2

    @pytest.mark.asyncio
    async def test_ping_some_down(self, runner):
        """Один сервис не отвечает на ping."""
        steps = [
            make_passed_step("auth_op", service="auth"),
            make_passed_step("reg_op", service="registry"),
        ]
        pipeline = MockPipeline(steps)
        runner.run_step = AsyncMock(side_effect=steps)
        runner.ping_service = AsyncMock()
        runner.ping_service.side_effect = [True, False]  # auth ok, registry down

        result = await runner.run(pipeline)

        assert result.ping_ok is False
        assert result.passed is False


# ────────────────────────────────────────────────────────────────
#  4.5 auth-токен flow
# ────────────────────────────────────────────────────────────────


class TestRunAuthFlow:
    """Auth-токен передаётся между шагами."""

    @pytest.mark.asyncio
    async def test_auth_token_passed(self, runner):
        """Auth-шаг сохраняет токен → последующие шаги его используют."""
        auth_step = make_passed_step("login", service="auth", needs_auth=False)
        auth_step.extract_keys = ["access_token"]
        # После выполнения run_step, токен должен быть в контексте
        # Имитируем, что run_step извлёк токен

        reg_step = make_passed_step("registry_op", service="registry", needs_auth=True)
        reg_step.extract_keys = []

        steps = [auth_step, reg_step]
        pipeline = MockPipeline(steps)

        # В контексте после первого шага должен появиться токен
        async def _run_step_side_effect(step, ctx, auth_token=None):
            if step.name == "login":
                ctx.set("access_token", "test-jwt")
            return step

        runner.run_step = AsyncMock(side_effect=_run_step_side_effect)
        runner.ping_service = AsyncMock(return_value=True)

        await runner.run(pipeline)

        # Второй шаг должен получить auth_token="test-jwt"
        calls = runner.run_step.call_args_list
        assert len(calls) == 2
        # Второй вызов: args = (step, ctx, auth_token)
        second_call_args = calls[1]
        second_token = second_call_args[0][2] if len(second_call_args[0]) > 2 else None
        assert second_token == "test-jwt"


# ────────────────────────────────────────────────────────────────
#  4.6 build_steps упал
# ────────────────────────────────────────────────────────────────


class TestRunBuildStepsError:
    """Ошибка при построении шагов."""

    @pytest.mark.asyncio
    async def test_build_steps_raises(self, runner):
        """build_steps бросил исключение."""

        class BrokenPipeline(PipelineDef):
            name = "broken"
            description = "Broken"
            services = []

            def build_steps(self, ctx):
                raise RuntimeError("Cannot build steps")

        pipeline = BrokenPipeline()
        runner.ping_service = AsyncMock(return_value=True)

        result = await runner.run(pipeline)

        assert result.passed is False
        assert result.error is not None
        assert "Cannot build steps" in result.error


# ────────────────────────────────────────────────────────────────
#  skip_if ветвление (на уровне run)
# ────────────────────────────────────────────────────────────────


class TestRunSkipIf:
    """skip_if ветвление шагов."""

    @pytest.mark.asyncio
    async def test_skip_if_true_skips_step(self, runner):
        """skip_if(ctx) вернул True → шаг пропускается."""
        step1 = make_passed_step("step1")
        step2 = make_passed_step("step2")

        step_skippable = make_step("skippable")
        step_skippable.skip_if = lambda ctx: True  # всегда пропускать

        pipeline = MockPipeline([step1, step_skippable, step2])
        runner.run_step = AsyncMock(side_effect=[step1, step2])  # skippable не вызывается
        runner.ping_service = AsyncMock(return_value=True)

        result = await runner.run(pipeline)

        assert result.passed is True
        assert result.passed_steps == 2  # step1 + step2
        assert result.skipped_steps == 1
        assert runner.run_step.call_count == 2  # skippable не вызывался

    @pytest.mark.asyncio
    async def test_skip_if_false_runs_step(self, runner):
        """skip_if(ctx) вернул False → шаг выполняется."""
        step1 = make_passed_step("step1")
        step2 = make_passed_step("step2")

        step_always_run = make_passed_step("always_run")
        step_always_run.skip_if = lambda ctx: False  # никогда не пропускать

        pipeline = MockPipeline([step1, step_always_run, step2])
        runner.run_step = AsyncMock(side_effect=[step1, step_always_run, step2])
        runner.ping_service = AsyncMock(return_value=True)

        result = await runner.run(pipeline)

        assert result.passed is True
        assert result.skipped_steps == 0
        assert runner.run_step.call_count == 3


# ────────────────────────────────────────────────────────────────
#  Интеграция: run_step реально обрабатывается
# ────────────────────────────────────────────────────────────────


class TestRunIntegration:
    """run() с реальным run_step, но замокированным HTTP."""

    @pytest.mark.asyncio
    async def test_no_services_returns_empty(self, runner):
        """Пайплайн без шагов (total_steps=0) — passed=False."""

        class EmptyPipeline(PipelineDef):
            name = "empty"
            description = "Empty"
            services = []

            def build_steps(self, ctx):
                return []

        runner.ping_service = AsyncMock(return_value=True)

        result = await runner.run(EmptyPipeline())

        assert result.passed is False  # нет шагов
        assert result.total_steps == 0
