"""
Юнит-тесты ApiCoverageTester._execute_endpoint() — тестируем логику выполнения
одного эндпоинта с замокированным HTTP-клиентом, без обращения к Docker.

Проверяет:
- Сервис жив/мёртв → выполнение/пропуск
- Known new endpoints 404 → tolerant warning
- Извлечение контекста из ответа
- Валидация схемы ответа (response_schema)
- Check-функции
- ConnectError / TimeoutException
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from service_checker.core.api_coverage_test import ApiCoverageTester, ServiceResult, EndpointResult
from service_checker.services.base import EndpointDef


# ────────────────────────────────────────────────────────────────
#  Fixtures
# ────────────────────────────────────────────────────────────────


@pytest.fixture
def tester():
    """ApiCoverageTester с замокированным клиентом."""
    t = ApiCoverageTester()
    t.client = AsyncMock(spec=httpx.AsyncClient)
    t.context = {}
    t.base_host = "127.0.0.1"
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


def _mock_response(status_code: int = 200, json_data: Optional[Dict] = None,
                   text: Optional[str] = None) -> MagicMock:
    """Создать mock httpx.Response."""
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
    resp.json.return_value = json_data or {}
    return resp


# ────────────────────────────────────────────────────────────────
#  5.1 alive + success
# ────────────────────────────────────────────────────────────────


class TestExecuteAliveSuccess:
    """Сервис жив, эндпоинт успешен."""

    @pytest.mark.asyncio
    async def test_basic_get(self, tester, make_endpoint):
        """GET с 200."""
        ep = make_endpoint("/api/v1/health", "health")
        result = ServiceResult(name="test", port=8080)
        tester.client.get = AsyncMock(return_value=_mock_response(200, {"status": "ok"}))

        await tester._execute_endpoint("test", ep, 8080, result, alive=True)

        assert len(result.results) == 1
        assert result.results[0].success is True
        assert result.endpoints_passed == 1

    @pytest.mark.asyncio
    async def test_expected_status_set(self, tester, make_endpoint):
        """expected_status={201, 409}, 409 проходит."""
        ep = make_endpoint("/api/v1/registry/documents/", "documents",
                           method="POST", expected_status={201, 409})
        result = ServiceResult(name="test", port=8080)
        tester.client.post = AsyncMock(return_value=_mock_response(409, {"detail": "conflict"}))

        await tester._execute_endpoint("test", ep, 8080, result, alive=True)

        assert result.results[0].success is True
        assert result.results[0].status_code == 409

    @pytest.mark.asyncio
    async def test_expected_status_override_2xx(self, tester, make_endpoint):
        """expected_status=201, получен 200 → fail."""
        ep = make_endpoint("/api/v1/registry/documents/", "documents",
                           method="POST", expected_status=201)
        result = ServiceResult(name="test", port=8080)
        tester.client.post = AsyncMock(return_value=_mock_response(200, {"id": 1}))

        await tester._execute_endpoint("test", ep, 8080, result, alive=True)

        assert result.results[0].success is False
        assert result.endpoints_failed == 1

    @pytest.mark.asyncio
    async def test_override_port(self, tester, make_endpoint):
        """override_port меняет целевой порт."""
        ep = make_endpoint("/api/v1/auth/token", "auth", method="POST",
                           override_port=8082, body={"user": "admin", "pass": "admin"})
        result = ServiceResult(name="test", port=8080)  # port=8080, но override=8082
        tester.client.post = AsyncMock(return_value=_mock_response(200, {"token": "jwt"}))

        await tester._execute_endpoint("test", ep, 8080, result, alive=True)

        # Проверяем что вызов был на порт 8082 (override), не 8080
        call_url = tester.client.post.call_args[0][0]
        assert ":8082" in call_url


# ────────────────────────────────────────────────────────────────
#  5.2 dead service
# ────────────────────────────────────────────────────────────────


class TestExecuteDeadService:
    """Сервис не отвечает."""

    @pytest.mark.asyncio
    async def test_dead_service_skips(self, tester, make_endpoint):
        """alive=False → все эндпоинты пропущены."""
        ep = make_endpoint("/api/v1/health", "health")
        result = ServiceResult(name="test", port=8080)

        await tester._execute_endpoint("test", ep, 8080, result, alive=False)

        assert result.results[0].skipped is True
        assert "не отвечает" in (result.results[0].skip_reason or "")
        assert result.endpoints_skipped == 1


# ────────────────────────────────────────────────────────────────
#  5.3 404 is error
# ────────────────────────────────────────────────────────────────


class Test404IsError:
    """Любой 404 — error (tolerant mode удалён)."""

    @pytest.mark.asyncio
    async def test_404_is_error(self, tester, make_endpoint):
        """404 → error."""
        ep = make_endpoint("/api/v1/health", "health", method="GET")
        ep.is_preparation = False
        result = ServiceResult(name="auth", port=8082)
        tester.client.get = AsyncMock(
            return_value=_mock_response(404, {"error": "Not Found"})
        )

        await tester._execute_endpoint("auth", ep, 8082, result, alive=True)

        assert result.results[0].success is False
        assert result.endpoints_failed == 1


# ────────────────────────────────────────────────────────────────
#  5.4 context extraction
# ────────────────────────────────────────────────────────────────


class TestExecuteContextExtraction:
    """Извлечение контекста из ответа."""

    @pytest.mark.asyncio
    async def test_extract_context(self, tester, make_endpoint):
        """extract_keys извлекает значения из ответа."""
        ep = make_endpoint("/api/v1/auth/token", "auth", method="POST",
                           body={"user": "admin", "pass": "admin"},
                           extract_keys=["access_token", "refresh_token"])
        result = ServiceResult(name="auth", port=8082)
        tester.client.post = AsyncMock(
            return_value=_mock_response(200, {
                "access_token": "jwt123",
                "refresh_token": "ref456",
            })
        )

        await tester._execute_endpoint("auth", ep, 8082, result, alive=True)

        assert tester.context.get("access_token") == "jwt123"
        assert tester.context.get("refresh_token") == "ref456"

    @pytest.mark.asyncio
    async def test_context_path_placeholder(self, tester, make_endpoint):
        """{doc_id} в пути подставляется из контекста."""
        tester.context["doc_id"] = "42"
        ep = make_endpoint("/api/v1/registry/documents/{doc_id}", "documents",
                           method="GET")
        result = ServiceResult(name="registry", port=8084)
        tester.client.get = AsyncMock(return_value=_mock_response(200, {"id": 42}))

        await tester._execute_endpoint("registry", ep, 8084, result, alive=True)

        # Проверяем что URL содержит подставленный doc_id
        call_url = tester.client.get.call_args[0][0]
        assert "/42" in call_url

    @pytest.mark.asyncio
    async def test_missing_context_skips(self, tester, make_endpoint):
        """Нет {doc_id} в контексте → skipped."""
        ep = make_endpoint("/api/v1/registry/documents/{doc_id}", "documents",
                           method="GET")
        result = ServiceResult(name="registry", port=8084)

        await tester._execute_endpoint("registry", ep, 8084, result, alive=True)

        assert result.results[0].skipped is True
        assert "Нет в контексте" in (result.results[0].skip_reason or "")
        assert result.endpoints_skipped == 1


# ────────────────────────────────────────────────────────────────
#  5.5 schema validation
# ────────────────────────────────────────────────────────────────


class TestExecuteSchemaValidation:
    """Валидация схемы ответа."""

    @pytest.mark.asyncio
    async def test_schema_valid(self, tester, make_endpoint):
        """Ответ соответствует схеме."""
        ep = make_endpoint("/api/v1/health", "health", method="GET",
                           response_schema={"status": str})
        ep.is_preparation = False
        result = ServiceResult(name="auth", port=8082)
        tester.client.get = AsyncMock(
            return_value=_mock_response(200, {"status": "ok"})
        )

        await tester._execute_endpoint("auth", ep, 8082, result, alive=True)

        assert result.results[0].success is True

    @pytest.mark.asyncio
    async def test_schema_invalid(self, tester, make_endpoint):
        """Ответ не соответствует схеме."""
        ep = make_endpoint("/api/v1/health", "health", method="GET",
                           response_schema={"status": str, "data": dict})
        ep.is_preparation = False
        result = ServiceResult(name="auth", port=8082)
        tester.client.get = AsyncMock(
            return_value=_mock_response(200, {"status": "ok"})  # нет "data"
        )

        await tester._execute_endpoint("auth", ep, 8082, result, alive=True)

        assert result.results[0].success is False
        assert result.endpoints_failed == 1


# ────────────────────────────────────────────────────────────────
#  5.6 connect error
# ────────────────────────────────────────────────────────────────


class TestExecuteErrors:
    """Сетевые ошибки."""

    @pytest.mark.asyncio
    async def test_connect_error(self, tester, make_endpoint):
        """ConnectError → skipped."""
        ep = make_endpoint("/api/v1/health", "health")
        result = ServiceResult(name="test", port=8080)
        tester.client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

        await tester._execute_endpoint("test", ep, 8080, result, alive=True)

        assert result.results[0].skipped is True
        assert result.results[0].status_code == 0
        assert "ConnectError" in (result.results[0].error or "")
        assert result.endpoints_skipped == 1

    @pytest.mark.asyncio
    async def test_timeout(self, tester, make_endpoint):
        """Timeout → skipped."""
        ep = make_endpoint("/api/v1/health", "health")
        result = ServiceResult(name="test", port=8080)
        tester.client.get = AsyncMock(side_effect=httpx.TimeoutException("Timed out"))

        await tester._execute_endpoint("test", ep, 8080, result, alive=True)

        assert result.results[0].skipped is True
        assert "Timeout" in (result.results[0].error or "")
        assert result.endpoints_skipped == 1

    @pytest.mark.asyncio
    async def test_exception_during_request(self, tester, make_endpoint):
        """Общее исключение → failed."""
        ep = make_endpoint("/api/v1/health", "health")
        result = ServiceResult(name="test", port=8080)
        tester.client.get = AsyncMock(side_effect=RuntimeError("Unexpected"))

        await tester._execute_endpoint("test", ep, 8080, result, alive=True)

        # Общие исключения counted as failed, not skipped
        assert result.results[0].success is False
        assert result.endpoints_failed == 1


# ────────────────────────────────────────────────────────────────
#  Check-функция
# ────────────────────────────────────────────────────────────────


class TestExecuteCheck:
    """Check-функция эндпоинта."""

    @pytest.mark.asyncio
    async def test_check_passes(self, tester, make_endpoint):
        """check вернул True → success."""
        def _check(body, ctx):
            return True, "ok"

        ep = make_endpoint("/api/v1/health", "health", method="GET",
                           check=_check)
        result = ServiceResult(name="auth", port=8082)
        tester.client.get = AsyncMock(return_value=_mock_response(200, {"status": "ok"}))

        await tester._execute_endpoint("auth", ep, 8082, result, alive=True)

        assert result.results[0].success is True

    @pytest.mark.asyncio
    async def test_check_fails(self, tester, make_endpoint):
        """check вернул False → success=False."""
        def _check(body, ctx):
            return False, "проверка не пройдена"

        ep = make_endpoint("/api/v1/health", "health", method="GET",
                           check=_check)
        result = ServiceResult(name="auth", port=8082)
        tester.client.get = AsyncMock(return_value=_mock_response(200, {"status": "ok"}))

        await tester._execute_endpoint("auth", ep, 8082, result, alive=True)

        assert result.results[0].success is False
        assert result.endpoints_failed == 1


# ────────────────────────────────────────────────────────────────
#  _validate_response — полная проверка схемы ответа
# ────────────────────────────────────────────────────────────────


class TestValidateResponse:
    """ApiCoverageTester._validate_response() — валидация схемы ответа."""

    def test_empty_body(self, tester):
        ok, errors, warnings = tester._validate_response(None, {"status": str})
        assert not ok
        assert "Пустой ответ" in str(errors)

    def test_invalid_json(self, tester):
        ok, errors, warnings = tester._validate_response("not json", {"status": str})
        assert not ok
        assert "Невалидный JSON" in str(errors)

    def test_field_missing(self, tester):
        ok, errors, warnings = tester._validate_response(
            '{"other": "val"}', {"status": str}
        )
        assert not ok
        assert "status" in str(errors)
        assert "не найдено" in str(errors)

    def test_field_present_correct_type(self, tester):
        ok, errors, warnings = tester._validate_response(
            '{"status": "ok", "count": 42}', {"status": str, "count": int}
        )
        assert ok
        assert not errors

    def test_field_wrong_type_int_as_str_allowed(self, tester):
        """Int вместо str — автоприведение (валидно, без warning)."""
        ok, errors, warnings = tester._validate_response(
            '{"status": 123}', {"status": str}
        )
        assert ok  # int/float можно представить как str — валидно
        assert not errors
        assert len(warnings) == 0

    def test_field_wrong_type_str_as_int_convertible(self, tester):
        """Строка вместо int, но строка конвертируется → ok."""
        ok, errors, warnings = tester._validate_response(
            '{"count": "42"}', {"count": int}
        )
        assert ok

    def test_field_wrong_type_str_as_int_not_convertible(self, tester):
        """Строка вместо int, строка НЕ конвертируется → warning (строка → warning)."""
        ok, errors, warnings = tester._validate_response(
            '{"count": "abc"}', {"count": int}
        )
        assert ok  # строка вместо int → warning, не error
        assert len(warnings) >= 1

    def test_field_wrong_type_bool_as_dict(self, tester):
        """bool вместо dict → error (не строка, не автоприводится)."""
        ok, errors, warnings = tester._validate_response(
            '{"data": true}', {"data": dict}
        )
        assert not ok
        assert len(errors) >= 1

    def test_nested_field_present(self, tester):
        ok, errors, warnings = tester._validate_response(
            '{"data": {"id": 1, "name": "test"}}', {"data.id": int, "data.name": str}
        )
        assert ok

    def test_nested_field_missing(self, tester):
        ok, errors, warnings = tester._validate_response(
            '{"data": {"id": 1}}', {"data.id": int, "data.name": str}
        )
        assert not ok
        assert "data.name" in str(errors)

    def test_field_is_dict(self, tester):
        ok, errors, warnings = tester._validate_response(
            '{"data": {"key": "val"}}', {"data": dict}
        )
        assert ok

    def test_field_is_list(self, tester):
        ok, errors, warnings = tester._validate_response(
            '{"items": [1, 2, 3]}', {"items": list}
        )
        assert ok


# ────────────────────────────────────────────────────────────────
#  _extract_context — ApiCoverageTester версия
# ────────────────────────────────────────────────────────────────


class TestApiTesterExtractContext:
    """ApiCoverageTester._extract_context() — извлечение контекста."""

    def test_extract_simple(self, tester):
        tester._extract_context(
            '{"access_token": "jwt", "refresh_token": "ref"}',
            ["access_token", "refresh_token"],
        )
        assert tester.context["access_token"] == "jwt"
        assert tester.context["refresh_token"] == "ref"

    def test_extract_data_wrapper(self, tester):
        """Извлечение из обёртки data.key."""
        tester._extract_context(
            '{"data": {"id": 42}}', ["doc_id"]
        )
        assert tester.context["doc_id"] == 42

    def test_extract_alt_name_session_id(self, tester):
        """session_id через alt_map: sessionId."""
        tester._extract_context(
            '{"sessionId": "sess-001"}', ["session_id"]
        )
        assert tester.context["session_id"] == "sess-001"

    def test_extract_alt_name_draft_id(self, tester):
        """draft_id через alt_map: draft_id/id."""
        tester._extract_context(
            '{"draft_id": 77}', ["draft_id"]
        )
        assert tester.context["draft_id"] == 77

    def test_extract_alt_name_reg_draft_id(self, tester):
        """reg_draft_id через alt_map: id/draft_id."""
        tester._extract_context(
            '{"id": 88}', ["reg_draft_id"]
        )
        assert tester.context["reg_draft_id"] == 88

    def test_extract_alt_name_category_id(self, tester):
        """category_id через alt_map: id/category_id."""
        tester._extract_context(
            '{"category_id": 99}', ["category_id"]
        )
        assert tester.context["category_id"] == 99

    def test_extract_alt_name_pending_id(self, tester):
        """pending_id через alt_map: id."""
        tester._extract_context(
            '{"id": 111}', ["pending_id"]
        )
        assert tester.context["pending_id"] == 111

    def test_extract_search_in_list(self, tester):
        """Поиск ключа внутри списка объектов."""
        tester._extract_context(
            '{"items": [{"id": 222}]}', ["doc_id"]
        )
        assert tester.context["doc_id"] == 222

    def test_extract_none_on_missing(self, tester):
        """Ключ не найден — контекст не меняется."""
        tester._extract_context('{"status": "ok"}', ["missing_key"])
        assert "missing_key" not in tester.context

    def test_extract_invalid_json(self, tester):
        """Невалидный JSON — игнорируется."""
        tester.context["existing"] = "val"
        tester._extract_context("not json", ["key"])
        assert "key" not in tester.context
        assert tester.context["existing"] == "val"

    def test_extract_none_body(self, tester):
        tester._extract_context(None, ["key"])
        assert "key" not in tester.context

    def test_extract_no_keys(self, tester):
        tester._extract_context('{"id": 1}', None)
        assert "id" not in tester.context
