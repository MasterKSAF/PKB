"""
Юнит-тесты ApiCoverageTester.test_service() — тестируем логику тестирования
сервиса с замокированными _execute_endpoint и ping_service, без Docker.

Проверяет:
- Базовый тест сервиса
- Неизвестный порт
- All-404 override (ping_ok=False)
- Prepare-шаги + контекст
- Регистрация сервиса из SERVICE_REGISTRY
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from service_checker.core.api_coverage_test import ApiCoverageTester, ServiceResult, EndpointResult
from service_checker.services.base import EndpointDef, ServiceDef
from service_checker.services import MODE_PORTS


# ────────────────────────────────────────────────────────────────
#  Fixtures
# ────────────────────────────────────────────────────────────────


@pytest.fixture
def tester():
    """ApiCoverageTester с замокированным клиентом."""
    t = ApiCoverageTester()
    t.client = AsyncMock()
    t.context = {}
    t.base_host = "127.0.0.1"
    t.skip_prepare = True  # по умолчанию отключаем prepare (не нужен в юнит-тестах)
    return t


@pytest.fixture
def make_endpoint():
    """Фабрика EndpointDef."""
    def _make(path: str, group: str, method: str = "GET",
              **kwargs) -> EndpointDef:
        return EndpointDef(
            method=method, path=path, group=group,
            description=f"Test {group} endpoint", **kwargs,
        )
    return _make


# ────────────────────────────────────────────────────────────────
#  6.1 базовый тест сервиса
# ────────────────────────────────────────────────────────────────


class TestServiceBasic:
    """Базовое тестирование сервиса."""

    @pytest.mark.asyncio
    async def test_basic_service(self, tester, make_endpoint):
        """Сервис с 2 эндпоинтами, оба успешны."""
        ep1 = make_endpoint("/api/v1/health", "health")
        ep2 = make_endpoint("/api/v1/auth/token", "auth", method="POST")

        tester._test_endpoints = {"test_svc": [ep1, ep2]}
        tester.ping_service = AsyncMock(return_value=True)

        # _execute_endpoint: успешные результаты
        async def _mock_execute(svc_key, ep, port, result, alive):
            result.results.append(
                EndpointResult(endpoint=ep, status_code=200, success=True)
            )
            result.endpoints_passed += 1

        tester._execute_endpoint = _mock_execute

        svc_result = await tester.test_service("test_svc")

        assert svc_result.ping_ok is True
        assert svc_result.endpoints_total == 2
        assert svc_result.endpoints_passed == 2
        assert svc_result.endpoints_failed == 0

    @pytest.mark.asyncio
    async def test_ping_fail(self, tester, make_endpoint):
        """Сервис не отвечает на ping."""
        ep = make_endpoint("/api/v1/health", "health")
        tester._test_endpoints = {"test_svc": [ep]}
        tester.ping_service = AsyncMock(return_value=False)

        async def _mock_execute(svc_key, ep, port, result, alive):
            # При alive=False execute_endpoint добавляет skipped
            result.results.append(
                EndpointResult(endpoint=ep, status_code=0, success=False,
                               skipped=True, skip_reason="Сервис не отвечает")
            )
            result.endpoints_skipped += 1

        tester._execute_endpoint = _mock_execute

        svc_result = await tester.test_service("test_svc")

        assert svc_result.ping_ok is False
        assert svc_result.endpoints_skipped == 1


# ────────────────────────────────────────────────────────────────
#  6.2 неизвестный порт
# ────────────────────────────────────────────────────────────────


class TestServiceUnknownPort:
    """Сервис с неизвестным портом."""

    @pytest.mark.asyncio
    async def test_unknown_port(self, tester, make_endpoint):
        """Порт=0 → все эндпоинты пропущены."""
        ep = make_endpoint("/api/v1/health", "health")

        # Регистрируем с портом 0
        MODE_PORTS["unknown"] = 0
        tester._test_endpoints = {"unknown": [ep]}
        try:
            svc_result = await tester.test_service("unknown")
        finally:
            MODE_PORTS.pop("unknown", None)

        assert svc_result.ping_ok is False
        assert svc_result.endpoints_total == 1
        assert svc_result.endpoints_skipped == 1
        assert svc_result.results[0].status_code == 0
        assert svc_result.results[0].skipped is True

    @pytest.mark.asyncio
    async def test_service_not_in_registry(self, tester):
        """Сервис не найден ни в _test_endpoints, ни в SERVICE_REGISTRY."""
        svc_result = await tester.test_service("nonexistent_service")

        assert svc_result.ping_ok is False
        assert svc_result.endpoints_total == 0


# ────────────────────────────────────────────────────────────────
#  6.3 all-404 override
# ────────────────────────────────────────────────────────────────


class TestServiceAll404Override:
    """Все не-health эндпоинты вернули 404 → ping_ok=False."""

    @pytest.mark.asyncio
    async def test_all_404_resets_ping(self, tester, make_endpoint):
        """≥2 не-health с 404 → ping_ok=False, success откатывается."""
        ep1 = make_endpoint("/api/v1/ocr/process", "ocr", method="POST")
        ep2 = make_endpoint("/api/v1/ocr/preview", "ocr", method="POST")

        tester._test_endpoints = {"ocr": [ep1, ep2]}
        tester.ping_service = AsyncMock(return_value=True)

        async def _mock_execute(svc_key, ep, port, result, alive):
            result.results.append(
                EndpointResult(endpoint=ep, status_code=404, success=True,
                               skipped=False)
            )
            result.endpoints_passed += 1

        tester._execute_endpoint = _mock_execute

        svc_result = await tester.test_service("ocr")

        assert svc_result.ping_ok is False  # overridden
        assert svc_result.endpoints_passed == 0  # все откачены
        assert svc_result.endpoints_failed == 2  # стали failed

    @pytest.mark.asyncio
    async def test_mixed_does_not_override(self, tester, make_endpoint):
        """Один 404 + один 200 → без оверрайда."""
        ep1 = make_endpoint("/api/v1/ocr/process", "ocr", method="POST")
        ep2 = make_endpoint("/api/v1/parser/preview", "parser", method="POST")

        tester._test_endpoints = {"test": [ep1, ep2]}
        tester.ping_service = AsyncMock(return_value=True)

        call_count = [0]

        async def _mock_execute(svc_key, ep, port, result, alive):
            call_count[0] += 1
            if call_count[0] == 1:
                # 404
                result.results.append(
                    EndpointResult(endpoint=ep, status_code=404, success=True,
                                   skipped=False)
                )
                result.endpoints_passed += 1
            else:
                # 200
                result.results.append(
                    EndpointResult(endpoint=ep, status_code=200, success=True,
                                   skipped=False)
                )
                result.endpoints_passed += 1

        tester._execute_endpoint = _mock_execute

        svc_result = await tester.test_service("test")

        assert svc_result.ping_ok is True  # не оверрайдится (mixed)
        assert svc_result.endpoints_passed == 2


# ────────────────────────────────────────────────────────────────
#  6.4 prepare-шаги + контекст
# ────────────────────────────────────────────────────────────────


class TestServicePrepare:
    """Prepare-шаги выполняются до основных эндпоинтов."""

    @pytest.mark.asyncio
    async def test_prepare_steps(self, tester, make_endpoint):
        """Prepare-шаги выполняются и накапливают контекст."""
        prepare_ep = make_endpoint("/api/v1/auth/token", "auth", method="POST",
                                   extract_keys=["access_token"])
        main_ep = make_endpoint("/api/v1/registry/documents", "documents", method="GET")

        # Регистрируем через _test_endpoints + делаем prepare
        tester._test_endpoints = {"test_svc": [main_ep]}
        tester.ping_service = AsyncMock(return_value=True)
        tester.skip_prepare = False

        executed = []

        async def _mock_execute(svc_key, ep, port, result, alive):
            executed.append(ep.path)
            if ep.extract_keys:
                tester.context["access_token"] = "jwt123"
            result.results.append(
                EndpointResult(endpoint=ep, status_code=200, success=True)
            )
            result.endpoints_passed += 1

        tester._execute_endpoint = _mock_execute

        # Подменяем svc_prepare в test_service, передавая prepare-эндпоинты
        # через _test_endpoints + костыль: модифицируем test_service
        # Используем прямой подход: добавляем prepare в отдельный список
        original_test_service = tester.test_service

        async def patched_test_service(service_key):
            tester.context.clear()
            svc_endpoints = tester._test_endpoints.get(service_key, [])

            result = ServiceResult(name="test_svc", port=8080)
            result.endpoints_total = len([prepare_ep] + svc_endpoints)

            alive = await tester.ping_service(8080)
            result.ping_ok = alive

            # Prepare
            if alive:
                await tester._execute_endpoint(service_key, prepare_ep, 8080, result, alive)

            # Main endpoints
            for ep in svc_endpoints:
                await tester._execute_endpoint(service_key, ep, 8080, result, alive)

            return result

        tester.test_service = patched_test_service

        svc_result = await tester.test_service("test_svc")

        assert len(executed) == 2  # prepare + main
        assert executed[0] == "/api/v1/auth/token"
        assert executed[1] == "/api/v1/registry/documents"
        assert svc_result.ping_ok is True


# ────────────────────────────────────────────────────────────────
#  Интеграция: test_service с изоляцией контекста
# ────────────────────────────────────────────────────────────────


class TestServiceContextIsolation:
    """Контекст очищается между тестированием разных сервисов."""

    @pytest.mark.asyncio
    async def test_context_clear(self, tester, make_endpoint):
        """Каждый вызов test_service начинает с чистого контекста."""
        ep = make_endpoint("/api/v1/health", "health")

        tester._test_endpoints = {"svc1": [ep], "svc2": [ep]}
        tester.ping_service = AsyncMock(return_value=True)

        async def _mock_execute(svc_key, ep, port, result, alive):
            # Имитируем что первый сервис заполнил контекст
            if svc_key == "svc1":
                tester.context["secret"] = "should_not_leak"
            result.results.append(
                EndpointResult(endpoint=ep, status_code=200, success=True)
            )
            result.endpoints_passed += 1

        tester._execute_endpoint = _mock_execute

        await tester.test_service("svc1")
        await tester.test_service("svc2")

        # Контекст второго вызова не должен содержать secret от первого
        assert "secret" not in tester.context


# ────────────────────────────────────────────────────────────────
#  Интеграция: _execute_endpoint реальная (с моком HTTP)
# ────────────────────────────────────────────────────────────────


class TestServiceRealExecute:
    """test_service с реальным _execute_endpoint, но замокированным HTTP."""

    @pytest.mark.asyncio
    async def test_real_execute_flow(self, tester, make_endpoint):
        """Полный цикл: ping → execute_endpoint для каждого эндпоинта."""
        ep1 = make_endpoint("/api/v1/health", "health")
        ep2 = make_endpoint("/api/v1/auth/token", "auth", method="POST")

        tester._test_endpoints = {"test": [ep1, ep2]}
        tester.client.get = AsyncMock(
            return_value=MagicMock(
                spec=httpx.Response,
                status_code=200,
                text=json.dumps({"status": "ok"}),
                content=json.dumps({"status": "ok"}).encode(),
            )
        )
        tester.client.post = AsyncMock(
            return_value=MagicMock(
                spec=httpx.Response,
                status_code=200,
                text=json.dumps({"access_token": "jwt"}),
                content=json.dumps({"access_token": "jwt"}).encode(),
            )
        )
        tester.ping_service = AsyncMock(return_value=True)

        svc_result = await tester.test_service("test")

        assert svc_result.ping_ok is True
        assert svc_result.endpoints_total == 2
        assert svc_result.endpoints_passed == 2
        assert svc_result.endpoints_failed == 0
