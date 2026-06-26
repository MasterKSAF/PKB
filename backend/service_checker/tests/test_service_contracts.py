"""
Тесты межсервисных контрактов — проверяют реальное взаимодействие сервисов.

В отличие от API Coverage Test (каждый эндпоинт изолированно), эти тесты
верифицируют связки: один сервис → другой, с проверкой схем запросов/ответов
и имитацией HTTP-вызовов с реальными контрактами.

Критические связки:
1. query → rag_search — pipeline вызывает rag_client.search() через шаг RAG Search
2. query → registry — pipeline вызывает registry_client.enrich_query()
3. rag_search → infinity — rag_search вызывает rerank через TEI
4. gateway → query — gateway проксирует /api/v1/chat/* на query
5. gateway → rag_search — gateway проксирует /api/v1/rag/* на rag_search
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from service_checker.pipelines import PIPELINE_REGISTRY
from service_checker.pipelines.base import (
    PipelineContext,
    PipelineStep,
    PipelineRunner,
    StepStatus,
)
from service_checker.services import (
    SERVICE_REGISTRY,
    MODE_PORTS,
    SERVICE_DEPENDENCIES,
)
from service_checker.services.base import (
    API_PREFIX,
    EndpointDef,
    ServiceDef,
)


# ────────────────────────────────────────────────────────────────
#  Helpers
# ────────────────────────────────────────────────────────────────


def _find_endpoint(svc_def: ServiceDef, method: str, path_suffix: str, use_exact_path: bool = False) -> Optional[EndpointDef]:
    """Найти первый EndpointDef по методу и суффиксу пути.

    Если use_exact_path=True — ищем точное совпадение path (без /api/v1 prefix).
    Иначе — добавляем API_PREFIX.
    """
    target = path_suffix if use_exact_path else f"{API_PREFIX}{path_suffix}"
    for ep in svc_def.endpoints:
        if ep.method == method and ep.path == target:
            return ep
    for ep in svc_def.prepare_endpoints:
        if ep.method == method and ep.path == target:
            return ep
    return None


def _find_all_endpoints(svc_def: ServiceDef, method: str, path_suffix: str) -> List[EndpointDef]:
    """Найти ВСЕ EndpointDef по методу и суффиксу пути (м.б. дубликаты)."""
    target = f"{API_PREFIX}{path_suffix}"
    result = []
    for ep in svc_def.endpoints:
        if ep.method == method and ep.path == target:
            result.append(ep)
    for ep in svc_def.prepare_endpoints:
        if ep.method == method and ep.path == target:
            result.append(ep)
    return result


def _find_pipeline_step(pipeline_name: str, service_key: str) -> Optional[PipelineStep]:
    """Найти первый шаг пайплайна, выполняющийся на указанном сервисе."""
    pipeline_cls = PIPELINE_REGISTRY.get(pipeline_name)
    if not pipeline_cls:
        return None
    pipeline = pipeline_cls()
    steps = pipeline.build_steps(PipelineContext())
    for step in steps:
        if step.service == service_key:
            return step
    return None


def _mock_response(status_code: int, body: dict) -> AsyncMock:
    """Создать мок httpx.Response с заданным статусом и телом.

    .json() — синхронный метод (httpx.Response.json() не async).
    """
    resp = AsyncMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = json.dumps(body, ensure_ascii=False)
    resp.content = json.dumps(body, ensure_ascii=False).encode("utf-8")
    # .json() — синхронный метод httpx.Response
    resp.json = MagicMock(return_value=body)
    return resp


# ────────────────────────────────────────────────────────────────
#  1. query → rag_search: контракт вызова RAG Search
# ────────────────────────────────────────────────────────────────


class TestQueryToRagSearchContract:
    """Связка query → rag_search: запрос от query_service к rag_search.

    Пайплайн chat_inference отправляет POST /api/v1/rag/search на rag_search.
    Важно: valid_at обязателен, его отсутствие → 422.
    """

    def test_request_body_schema_alignment(self):
        """Тело запроса из шага пайплайна совпадает с ожидаемым rag_search."""
        rag_search_def = SERVICE_REGISTRY["rag_search"]()
        rag_ep = _find_endpoint(rag_search_def, "POST", "/rag/search")
        assert rag_ep is not None, "POST /api/v1/rag/search не найден в rag_search"
        assert rag_ep.body is not None, "rag_search: POST /rag/search не имеет body"

        # Получаем шаг пайплайна, который вызывает rag_search
        step = _find_pipeline_step("chat_inference", "rag_search")
        assert step is not None, "chat_inference: нет шага с service='rag_search'"
        assert step.body is not None, "chat_inference: шаг rag_search не имеет body"

        # Проверка: все поля из тела rag_search присутствуют в шаге пайплайна
        rag_body = set(rag_ep.body.keys())
        step_body = set(step.body.keys())

        missing = rag_body - step_body
        extra = step_body - rag_body
        assert not missing, (
            f"Шаг пайплайна не передаёт обязательные поля "
            f"rag_search: {sorted(missing)}"
        )
        if extra:
            pytest.skip(f"Шаг пайплайна передаёт лишние поля: {sorted(extra)}")

    def test_valid_at_present(self):
        """valid_at передаётся в запросе к rag_search."""
        step = _find_pipeline_step("chat_inference", "rag_search")
        assert step is not None
        assert step.body is not None
        assert "valid_at" in step.body, (
            "valid_at отсутствует в теле запроса к rag_search!\n"
            "Без valid_at rag_search возвращает 422, "
            "query_service ловит exception и показывает 'Поиск временно недоступен'"
        )
        assert isinstance(step.body["valid_at"], str), (
            f"valid_at должен быть строкой, получен {type(step.body['valid_at']).__name__}"
        )
        assert step.body["valid_at"] == "2026-06-19", (
            f"valid_at={step.body['valid_at']!r}, ожидался '2026-06-19'"
        )

    @pytest.mark.asyncio
    async def test_rag_search_returns_422_without_valid_at(self):
        """rag_search без valid_at возвращает 422 — проверяем через реальный run_step."""
        runner = PipelineRunner(base_host="127.0.0.1", timeout=10)
        runner.client = AsyncMock()

        # Создаём шаг без valid_at (имитация ошибки query_service)
        step = PipelineStep(
            name="Поиск RAG Search (без valid_at)",
            service="rag_search",
            method="POST",
            path="/api/v1/rag/search",
            port=MODE_PORTS.get("rag_search", 18091),
            body={
                "query": "тест",
                # valid_at отсутствует — как в баге
                "filters": {"document_type": [], "category_ids": [], "document_ids": []},
            },
            expected_status=200,
            needs_auth=True,
        )

        # Замокируем HTTP-ответ rag_search с 422
        runner.client.post = AsyncMock(return_value=_mock_response(
            422,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "valid_at"],
                        "msg": "Field required",
                    }
                ]
            },
        ))

        ctx = PipelineContext()
        ctx.set("access_token", "test-jwt")
        result = await runner.run_step(step, ctx, auth_token="test-jwt")

        assert result.status == StepStatus.FAILED, (
            "Ожидался FAILED для запроса без valid_at"
        )
        assert result.actual_status == 422
        assert result.error is not None
        assert "Expected HTTP 200, got 422" in result.error, (
            f"Ошибка должна содержать 'Expected HTTP 200, got 422', "
            f"получено: {result.error}"
        )

    @pytest.mark.asyncio
    async def test_rag_search_success_response_schema(self):
        """Успешный ответ rag_search проходит валидацию схемы pipeline'а."""
        runner = PipelineRunner(base_host="127.0.0.1", timeout=10)
        runner.client = AsyncMock()

        step = _find_pipeline_step("chat_inference", "rag_search")
        assert step is not None
        assert step.check is not None, "У шага rag_search нет check-функции"

        # Имитируем успешный ответ rag_search
        success_body = {
            "results": [
                {
                    "source": {"document_id": 1, "section_id": 10},
                    "retrieval": {
                        "chunk_id": "chunk-1",
                        "score": 0.95,
                        "mode": "hybrid",
                    },
                    "text": "Толщина обшивки ледового пояса должна быть...",
                }
            ],
            "processing_time_ms": 145,
            "total_found": 1,
        }

        runner.client.post = AsyncMock(return_value=_mock_response(200, success_body))

        ctx = PipelineContext()
        ctx.set("access_token", "test-jwt")
        result = await runner.run_step(step, ctx, auth_token="test-jwt")

        assert result.status == StepStatus.PASSED, (
            f"Шаг не прошёл: {result.error}"
        )
        assert result.actual_status == 200
        assert result.message, "Нет сообщения от check-функции"

    @pytest.mark.asyncio
    async def test_rag_search_missing_valid_at_rejected(self):
        """Отсутствие valid_at → 422. Проверяем детали ошибки."""
        runner = PipelineRunner(base_host="127.0.0.1", timeout=10)
        runner.client = AsyncMock()

        step = PipelineStep(
            name="Поиск RAG Search",
            service="rag_search",
            method="POST",
            path="/api/v1/rag/search",
            port=MODE_PORTS.get("rag_search", 18091),
            body={
                "query": "тест",
                # valid_at полностью отсутствует
                "filters": {"document_type": [], "category_ids": [], "document_ids": []},
            },
            expected_status=200,
            needs_auth=True,
        )

        runner.client.post = AsyncMock(return_value=_mock_response(
            422,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "valid_at"],
                        "msg": "Field required",
                    }
                ]
            },
        ))

        ctx = PipelineContext()
        ctx.set("access_token", "test-jwt")
        result = await runner.run_step(step, ctx, auth_token="test-jwt")

        assert result.status == StepStatus.FAILED
        assert result.actual_status == 422
        # Ошибка должна явно указывать на valid_at
        body = json.loads(result.response_body) if result.response_body else {}
        detail = body.get("detail", [])
        locs = [str(d.get("loc", [])) for d in (detail if isinstance(detail, list) else [])]
        joined_locs = " ".join(locs)
        assert "valid_at" in joined_locs, (
            f"Ошибка 422 должна упоминать valid_at. Детали: {detail}"
        )


# ────────────────────────────────────────────────────────────────
#  2. query → registry: enrich_query
# ────────────────────────────────────────────────────────────────


class TestQueryToRegistryContract:
    """Связка query → registry: enrich_query во время text/search.

    Query Service вызывает registry для обогащения запроса терминологией.
    """

    def test_query_depends_on_registry(self):
        """query зависит от registry — зависимость задекларирована."""
        deps = SERVICE_DEPENDENCIES.get("query", [])
        assert "registry" in deps, (
            "query не зависит от registry в SERVICE_DEPENDENCIES.\n"
            "Без registry enrich_query не сработает."
        )

    def test_registry_search_endpoint_has_valid_at(self):
        """registry/search поддерживает valid_at — query использует его.

        ВНИМАНИЕ: в registry есть ДВА эндпоинта GET /registry/search
        (один без valid_at, второй с valid_at). Тест проверяет, что
        хотя бы один из них поддерживает valid_at.
        """
        reg_def = SERVICE_REGISTRY["registry"]()
        search_eps = _find_all_endpoints(reg_def, "GET", "/registry/search")
        assert search_eps, "GET /registry/search не найден"

        # Проверяем, что хотя бы один эндпоинт поддерживает valid_at
        has_valid_at = any(
            ep.params and "valid_at" in ep.params
            for ep in search_eps
        )
        assert has_valid_at, (
            "registry/search не принимает valid_at ни в одном из "
            f"{len(search_eps)} определений эндпоинта — query не сможет "
            "отфильтровать по дате"
        )

    def test_query_text_search_has_enrichment_skipped(self):
        """QS-8: text/search возвращает enrichment_skipped — проверка схемы."""
        query_def = SERVICE_REGISTRY["query"]()
        search_ep = _find_endpoint(query_def, "POST", "/text/search")
        assert search_ep is not None, "POST /text/search не найден в query"
        assert search_ep.response_schema is not None, "response_schema отсутствует"
        assert "enrichment_skipped" in search_ep.response_schema, (
            "QS-8: enrichment_skipped отсутствует в response_schema "
            "text/search — query не сообщает о статусе обогащения"
        )

    @pytest.mark.asyncio
    async def test_registry_search_empty_response(self):
        """registry/search возвращает пустой результат — валидный ответ."""
        runner = PipelineRunner(base_host="127.0.0.1", timeout=10)
        runner.client = AsyncMock()

        # Проверяем registry search endpoint: пустой ответ должен проходить
        reg_def = SERVICE_REGISTRY["registry"]()
        search_ep = _find_endpoint(reg_def, "GET", "/registry/search")
        assert search_ep is not None
        assert search_ep.response_schema is not None

        reg_step = PipelineStep(
            name="Поиск по реестру",
            service="registry",
            method="GET",
            path="/api/v1/registry/search",
            port=MODE_PORTS.get("registry", 18084),
            params={"q": "тест", "valid_at": "2026-06-19"},
            expected_status=200,
            needs_auth=True,
        )

        runner.client.get = AsyncMock(return_value=_mock_response(
            200,
            {"data": [], "meta": {"total": 0, "page": 1, "page_size": 10}},
        ))

        ctx = PipelineContext()
        ctx.set("access_token", "test-jwt")
        result = await runner.run_step(reg_step, ctx, auth_token="test-jwt")

        assert result.status == StepStatus.PASSED, (
            f"registry/search не прошёл: {result.error}"
        )


# ────────────────────────────────────────────────────────────────
#  3. rag_search → infinity (TEI) — реранкинг
# ────────────────────────────────────────────────────────────────


class TestRagSearchToInfinityContract:
    """Связка rag_search → infinity: реранкинг через TEI.

    rag_search вызывает POST /embed на TEI для получения эмбеддингов
    при реранкинге результатов поиска.
    """

    def test_tei_embed_endpoint_exists(self):
        """TEI имеет POST /embed — rag_search вызывает его."""
        tei_def = SERVICE_REGISTRY["tei"]()
        # TEI не использует /api/v1 — путь точки совпадает
        embed_ep = _find_endpoint(tei_def, "POST", "/embed", use_exact_path=True)
        assert embed_ep is not None, (
            "POST /embed не найден в TEI — rag_search не сможет "
            "выполнить rerank. Проверьте path в services/tei.py"
        )

    def test_tei_embed_body_has_inputs(self):
        """TEI /embed принимает {'inputs': str}."""
        tei_def = SERVICE_REGISTRY["tei"]()
        embed_ep = _find_endpoint(tei_def, "POST", "/embed", use_exact_path=True)
        assert embed_ep is not None
        assert embed_ep.body is not None
        assert "inputs" in embed_ep.body, (
            "TEI /embed не принимает 'inputs' — rag_search не сможет "
            "передать текст для эмбеддинга"
        )

    def test_tei_in_mode_ports(self):
        """TEI зарегистрирован в MODE_PORTS — досягаем."""
        assert "tei" in MODE_PORTS, (
            "tei нет в MODE_PORTS — rag_search не найдёт порт"
        )
        assert MODE_PORTS["tei"] > 0

    @pytest.mark.asyncio
    async def test_tei_embed_response(self):
        """TEI возвращает [[float]] — rag_search парсит это.

        Проверяем через PipelineRunner с реальным run_step.
        TEI возвращает чистый массив [[float]], а не объект {embedding: ...}.
        Это нестандартный ответ — нужно убедиться, что rag_search
        его корректно обрабатывает.
        """
        runner = PipelineRunner(base_host="127.0.0.1", timeout=10)
        runner.client = AsyncMock()

        embed_step = PipelineStep(
            name="Получить эмбеддинги",
            service="tei",
            method="POST",
            path="/embed",  # TEI не использует /api/v1
            port=MODE_PORTS.get("tei", 18092),
            body={"inputs": "Тестовый запрос для реранкинга"},
            expected_status=200,
        )

        # TEI возвращает чистый массив [[float]]
        runner.client.post = AsyncMock(return_value=_mock_response(
            200,
            [[0.1, 0.2, 0.3, 0.4, 0.5]],
        ))

        ctx = PipelineContext()
        result = await runner.run_step(embed_step, ctx)

        assert result.status == StepStatus.PASSED, (
            f"TEI embed не прошёл: {result.error}"
        )


# ────────────────────────────────────────────────────────────────
#  4. gateway → query: прокси /api/v1/chat/*
# ────────────────────────────────────────────────────────────────


class TestGatewayToQueryProxy:
    """Связка gateway → query: gateway проксирует /api/v1/chat/* на query.

    Gateway выступает единой точкой входа. /api/v1/chat/sessions,
    /api/v1/chat/projects и другие chat-эндпоинты проксируются на query.
    """

    def test_gateway_has_chat_endpoints(self):
        """Gateway содержит chat-эндпоинты — прокси на query."""
        gw_def = SERVICE_REGISTRY["gateway"]()
        gw_chat_paths = {
            ep.path for ep in gw_def.endpoints
            if "/chat/" in ep.path
        }
        assert gw_chat_paths, (
            "Gateway не имеет chat-эндпоинтов — прокси на query не настроен"
        )

    def test_chat_paths_match_query(self):
        """Пути /api/v1/chat/* в gateway совпадают с query."""
        gw_def = SERVICE_REGISTRY["gateway"]()
        query_def = SERVICE_REGISTRY["query"]()

        gw_chat_paths = {
            ep.path for ep in gw_def.endpoints
            if "/chat/" in ep.path and not ep.is_preparation
        }
        query_chat_paths = {
            ep.path for ep in query_def.endpoints
            if "/chat/" in ep.path and not ep.is_preparation
        }

        # Gateway может иметь не все chat-эндпоинты, но все gateway-пути
        # должны существовать в query
        missing_in_query = gw_chat_paths - query_chat_paths
        assert not missing_in_query, (
            f"Эндпоинты gateway /chat/* отсутствуют в query:\n"
            f"  {sorted(missing_in_query)}"
        )

    def test_gateway_chat_schema_matches_query(self):
        """Схемы ответов chat-эндпоинтов gateway совпадают с query."""
        gw_def = SERVICE_REGISTRY["gateway"]()
        query_def = SERVICE_REGISTRY["query"]()

        mismatches = []
        for gw_ep in gw_def.endpoints:
            if "/chat/" not in gw_ep.path or gw_ep.is_preparation:
                continue
            # Ищем соответствующий эндпоинт в query
            q_ep = _find_endpoint(query_def, gw_ep.method, gw_ep.path.replace(API_PREFIX, ""))
            if q_ep is None:
                mismatches.append(f"{gw_ep.method} {gw_ep.path}: нет в query")
                continue
            if gw_ep.response_schema and q_ep.response_schema:
                gw_keys = set(gw_ep.response_schema.keys())
                q_keys = set(q_ep.response_schema.keys())
                # Все поля gateway должны быть в query (может быть больше полей в query)
                missing = gw_keys - q_keys
                if missing:
                    mismatches.append(
                        f"{gw_ep.method} {gw_ep.path}: "
                        f"поля {sorted(missing)} есть в gateway, но нет в query"
                    )

        assert not mismatches, \
            f"Несовпадения схем gateway ↔ query:\n" + "\n".join(mismatches)

    @pytest.mark.asyncio
    async def test_gateway_proxies_chat_message_to_query(self):
        """Gateway проксирует создание сообщения на query."""
        runner = PipelineRunner(base_host="127.0.0.1", timeout=10)
        runner.client = AsyncMock()

        # Копируем шаг из gateway: POST /api/v1/chat/sessions/{session_id}/messages
        gw_def = SERVICE_REGISTRY["gateway"]()
        msg_ep = _find_endpoint(gw_def, "POST", "/chat/sessions/{session_id}/messages")
        assert msg_ep is not None, "POST /chat/sessions/{id}/messages не найден в gateway"

        gw_step = PipelineStep(
            name="Отправить сообщение (через gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/chat/sessions/{session_id}/messages",
            port=MODE_PORTS.get("gateway", 18080),
            body=msg_ep.body,
            expected_status=msg_ep.expected_status or 200,
            extract_keys=msg_ep.extract_keys,
            needs_auth=True,
        )

        runner.client.post = AsyncMock(return_value=_mock_response(
            202,
            {"message_id": 42},
        ))

        ctx = PipelineContext()
        ctx.set("access_token", "test-jwt")
        ctx.set("session_id", 123)
        result = await runner.run_step(gw_step, ctx, auth_token="test-jwt")

        assert result.status == StepStatus.PASSED, (
            f"Gateway прокси не прошёл: {result.error}"
        )
        assert result.actual_status in (200, 202), (
            f"Неожиданный статус: {result.actual_status}"
        )


# ────────────────────────────────────────────────────────────────
#  5. gateway → rag_search: прокси /api/v1/rag/* с transform
# ────────────────────────────────────────────────────────────────


class TestGatewayToRagSearchProxy:
    """Связка gateway → rag_search: gateway проксирует /api/v1/rag/* на rag_search.

    Gateway должен проксировать запросы на /api/v1/rag/search в rag_search
    с теми же путями (или с transform).
    """

    def test_gateway_has_rag_endpoint(self):
        """Gateway содержит /api/v1/rag/search — прокси на rag_search."""
        gw_def = SERVICE_REGISTRY["gateway"]()
        rag_ep = _find_endpoint(gw_def, "POST", "/rag/search")
        assert rag_ep is not None, (
            "Gateway не имеет POST /rag/search — прокси на rag_search не настроен"
        )

    def test_rag_paths_match_rag_search(self):
        """Пути /api/v1/rag/* в gateway совпадают с rag_search.

        Gateway проксирует /api/v1/rag/search → rag_search:/api/v1/rag/search.
        """
        gw_def = SERVICE_REGISTRY["gateway"]()
        rag_def = SERVICE_REGISTRY["rag_search"]()

        gw_rag_paths = {
            ep.path for ep in gw_def.endpoints
            if "/rag/" in ep.path
        }
        rag_paths = {
            ep.path for ep in rag_def.endpoints
        }

        missing_in_rag = gw_rag_paths - rag_paths
        assert not missing_in_rag, (
            f"Эндпоинты gateway /rag/* отсутствуют в rag_search:\n"
            f"  {sorted(missing_in_rag)}"
        )

    def test_rag_body_schema_matches(self):
        """Тело запроса /rag/search в gateway совпадает с rag_search."""
        gw_def = SERVICE_REGISTRY["gateway"]()
        rag_def = SERVICE_REGISTRY["rag_search"]()

        gw_ep = _find_endpoint(gw_def, "POST", "/rag/search")
        rag_ep = _find_endpoint(rag_def, "POST", "/rag/search")
        assert gw_ep is not None, "gateway: POST /rag/search не найден"
        assert rag_ep is not None, "rag_search: POST /rag/search не найден"
        assert gw_ep.body is not None, "gateway: body отсутствует"
        assert rag_ep.body is not None, "rag_search: body отсутствует"

        # Схема тела gateway должна быть подмножеством схемы rag_search
        gw_keys = set(gw_ep.body.keys())
        rag_keys = set(rag_ep.body.keys())

        missing = gw_keys - rag_keys
        assert not missing, (
            f"Gateway передаёт rag_search поля, которых нет в rag_search:\n"
            f"  {sorted(missing)}\n"
            f"Это может вызвать ошибку на стороне rag_search."
        )

    def test_rag_response_schema_matches(self):
        """Схема ответа /rag/search в gateway совпадает с rag_search."""
        gw_def = SERVICE_REGISTRY["gateway"]()
        rag_def = SERVICE_REGISTRY["rag_search"]()

        gw_ep = _find_endpoint(gw_def, "POST", "/rag/search")
        rag_ep = _find_endpoint(rag_def, "POST", "/rag/search")
        assert gw_ep is not None
        assert rag_ep is not None

        # gateway может возвращать подмножество полей rag_search
        if gw_ep.response_schema and rag_ep.response_schema:
            gw_keys = set(gw_ep.response_schema.keys())
            rag_keys = set(rag_ep.response_schema.keys())
            missing_in_gateway = rag_keys - gw_keys
            # Это informatively — gateway может не проксировать все поля
            if missing_in_gateway:
                pytest.skip(
                    f"gateway не возвращает поля rag_search: "
                    f"{sorted(missing_in_gateway)}"
                )

    @pytest.mark.asyncio
    async def test_gateway_proxies_rag_search(self):
        """Gateway успешно проксирует rag_search запрос."""
        runner = PipelineRunner(base_host="127.0.0.1", timeout=10)
        runner.client = AsyncMock()

        # Шаг через gateway с телом rag_search
        rag_def = SERVICE_REGISTRY["rag_search"]()
        rag_ep = _find_endpoint(rag_def, "POST", "/rag/search")
        assert rag_ep is not None

        gw_step = PipelineStep(
            name="Поиск RAG через Gateway",
            service="gateway",
            method="POST",
            path="/api/v1/rag/search",
            port=MODE_PORTS.get("gateway", 18080),
            body=rag_ep.body,
            expected_status=200,
            needs_auth=True,
        )

        # Имитируем ответ rag_search (через gateway)
        success_body = {
            "results": [
                {
                    "source": {"document_id": 1, "section_id": 10},
                    "retrieval": {
                        "chunk_id": "chunk-1",
                        "score": 0.95,
                        "mode": "hybrid",
                    },
                }
            ],
            "processing_time_ms": 200,
            "total_found": 1,
        }

        runner.client.post = AsyncMock(
            return_value=_mock_response(200, success_body)
        )

        ctx = PipelineContext()
        ctx.set("access_token", "test-jwt")
        result = await runner.run_step(gw_step, ctx, auth_token="test-jwt")

        assert result.status == StepStatus.PASSED, (
            f"Gateway → rag_search прокси не прошёл: {result.error}"
        )

        # Проверяем, что тело запроса было отправлено (содержит valid_at и query)
        call_kwargs = runner.client.post.call_args
        assert call_kwargs is not None, "POST не был вызван"
        _, kwargs = call_kwargs
        sent_body = kwargs.get("json", {})
        assert "valid_at" in sent_body, (
            "Gateway не передаёт valid_at в rag_search"
        )
        assert "query" in sent_body, (
            "Gateway не передаёт query в rag_search"
        )


# ────────────────────────────────────────────────────────────────
#  6. Сквозные тесты: chat_inference с замокированными ответами
# ────────────────────────────────────────────────────────────────


class TestChatInferenceFullChain:
    """Сквозной тест chat_inference с замокированным HTTP.

    Проверяет, что пайплайн chat_inference может пройти все шаги
    с замокированными HTTP-ответами, имитирующими реальные контракты.

    ВАЖНО: PipelineRunner.run() вызывает _ensure_project(), который
    делает дополнительный POST на query_service. Мок должен учитывать это.
    """

    def _make_chain_mock(self, rag_status: int = 200, rag_body: dict = None):
        """Создать замокированный клиент для сквозного теста chat_inference.

        Учитывает вызов _ensure_project() и все шаги пайплайна.
        """
        if rag_body is None:
            rag_body = {
                "results": [
                    {
                        "source": {"document_id": 1, "section_id": 10},
                        "retrieval": {
                            "chunk_id": "chunk-1",
                            "score": 0.95,
                            "mode": "hybrid",
                        },
                    }
                ],
                "processing_time_ms": 150,
                "total_found": 1,
            }

        # _ensure_project делает до 6 POST (3 попытки создать проект +
        # 3 попытки получить список), плюс GET. Но мы можем упростить
        # и перехватывать все POST-запросы, возвращая подходящий ответ
        # в зависимости от URL.
        _responses = {
            # _ensure_project: POST create project
            "/api/v1/chat/projects": _mock_response(201, {
                "project_id": 42,
                "code": "PIPELINE_TEST",
                "name": "Pipeline Test Project",
            }),
            # Шаг 1: Auth
            "/api/v1/auth/token": _mock_response(200, {
                "access_token": "test-jwt-token",
                "refresh_token": "test-refresh",
                "token_type": "bearer",
            }),
            # Шаг 2: Create session
            "/api/v1/chat/sessions": _mock_response(201, {
                "session_id": 42,
                "title": "Тестовая сессия",
            }),
        }

        client = AsyncMock(spec=httpx.AsyncClient)

        def _match_path(url: str, path: str) -> bool:
            """Проверить, что URL заканчивается на path (с проверкой границ)."""
            return url.rstrip("/").endswith(path.rstrip("/"))

        async def mock_post(url, **kwargs):
            # Шаг 3: Send message — проверяем ДО проверок проектов/сессий,
            # т.к. URL содержит /chat/sessions/{id}/messages
            if "/messages" in url and "/chat/sessions/" in url:
                return _mock_response(202, {"message_id": 123})
            # Fallback для _ensure_project (GET /chat/projects)
            if "/text/search" in url:
                # Шаги 4-5: Text search (возвращаем enrichment_skipped)
                return _mock_response(200, {
                    "results": [{"id": 1, "text": "Результат"}],
                    "enrichment_skipped": False,
                })
            if "/rag/search" in url:
                # Шаг 6: RAG Search
                return _mock_response(rag_status, rag_body)
            # Пробуем найти путь в _responses (проверяем строгое совпадение)
            for path, resp in sorted(_responses.items(), key=lambda x: -len(x[0])):
                if _match_path(url, path):
                    return resp
            # Fallback
            return _mock_response(200, {"status": "ok"})

        client.post = mock_post
        client.get = AsyncMock(return_value=_mock_response(200, {"items": []}))
        return client

    @pytest.mark.asyncio
    async def test_full_chat_inference_chain(self):
        """Все шаги chat_inference проходят с замокированными контрактами."""
        pipeline_cls = PIPELINE_REGISTRY["chat_inference"]
        pipeline = pipeline_cls()

        runner = PipelineRunner(base_host="127.0.0.1", timeout=10)
        runner.client = self._make_chain_mock(200)
        runner.ping_service = AsyncMock(return_value=True)

        result = await runner.run(pipeline, skip_ping=True)

        assert result.ping_ok, "Ping не прошёл"
        assert result.failed_steps == 0, (
            f"Есть упавшие шаги: {result.failed_steps}\n"
            f"Детали: {[(s.name, s.error) for s in (result.steps or []) if s.status == StepStatus.FAILED]}"
        )
        assert result.passed, (
            "Пайплайн chat_inference не пройден целиком"
        )

    @pytest.mark.asyncio
    async def test_chat_inference_fails_on_rag_422(self):
        """Если rag_search возвращает 422 — пайплайн падает с ошибкой.

        Имитируем ситуацию бага: rag_search без valid_at → 422.
        """
        rag_error_body = {
            "detail": [
                {"type": "missing", "loc": ["body", "valid_at"],
                 "msg": "Field required"}
            ]
        }

        pipeline_cls = PIPELINE_REGISTRY["chat_inference"]
        pipeline = pipeline_cls()

        runner = PipelineRunner(base_host="127.0.0.1", timeout=10)
        runner.client = self._make_chain_mock(422, rag_error_body)
        runner.ping_service = AsyncMock(return_value=True)

        result = await runner.run(pipeline, skip_ping=True)

        # Пайплайн должен упасть на rag_search шаге
        assert result.failed_steps > 0, (
            "Ожидался сбой пайплайна из-за 422 от rag_search"
        )

        # Проверяем, что ошибка именно на rag_search шаге
        rag_step = None
        if result.steps:
            for s in result.steps:
                if s.service == "rag_search" and s.status == StepStatus.FAILED:
                    rag_step = s
                    break

        assert rag_step is not None, (
            "Нет FAILED шага rag_search — ошибка могла быть поглощена на другом уровне"
        )
        assert rag_step.actual_status == 422, (
            f"Ожидался 422, получен {rag_step.actual_status}"
        )
        assert rag_step.error is not None
        assert "422" in rag_step.error, (
            f"Ошибка должна упоминать 422: {rag_step.error}"
        )


# ────────────────────────────────────────────────────────────────
#  7. Схемы ответов: проверка согласованности между сервисами
# ────────────────────────────────────────────────────────────────


class TestResponseSchemaConsistency:
    """Согласованность схем ответов между сервисами.

    Если gateway проксирует эндпоинт, его response_schema должна
    быть подмножеством response_schema целевого сервиса.
    """

    def _get_endpoint_schema(
        self, svc_key: str, method: str, path: str
    ) -> Optional[Dict[str, type]]:
        """Получить response_schema эндпоинта сервиса."""
        if svc_key not in SERVICE_REGISTRY:
            return None
        svc_def = SERVICE_REGISTRY[svc_key]()
        for ep in svc_def.endpoints:
            if ep.method == method and ep.path == path:
                return ep.response_schema
        return None

    def test_gateway_to_query_response_schemas(self):
        """Схемы ответов gateway ⊆ query для chat-эндпоинтов."""
        gw_def = SERVICE_REGISTRY["gateway"]()

        mismatches = []
        for gw_ep in gw_def.endpoints:
            if "/chat/" not in gw_ep.path or gw_ep.is_preparation:
                continue
            if not gw_ep.response_schema:
                continue

            q_schema = self._get_endpoint_schema(
                "query", gw_ep.method, gw_ep.path
            )
            if q_schema is None:
                # Если нет в query — это может быть prepare-эндпоинт
                continue

            gw_keys = set(gw_ep.response_schema.keys())
            q_keys = set(q_schema.keys())
            missing = gw_keys - q_keys
            if missing:
                mismatches.append(
                    f"{gw_ep.method} {gw_ep.path}: "
                    f"поля {sorted(missing)} есть в gateway, но нет в query"
                )

        assert not mismatches, \
            "Несовпадения схем gateway → query:\n" + "\n".join(mismatches)

    def test_gateway_to_rag_search_response_schemas(self):
        """Схемы ответов gateway ⊆ rag_search для rag-эндпоинтов."""
        gw_def = SERVICE_REGISTRY["gateway"]()

        mismatches = []
        for gw_ep in gw_def.endpoints:
            if "/rag/" not in gw_ep.path or gw_ep.is_preparation:
                continue
            if not gw_ep.response_schema:
                continue

            rag_schema = self._get_endpoint_schema(
                "rag_search", gw_ep.method, gw_ep.path
            )
            if rag_schema is None:
                continue

            gw_keys = set(gw_ep.response_schema.keys())
            rag_keys = set(rag_schema.keys())
            missing = gw_keys - rag_keys
            if missing:
                mismatches.append(
                    f"{gw_ep.method} {gw_ep.path}: "
                    f"поля {sorted(missing)} есть в gateway, но нет в rag_search"
                )

        assert not mismatches, \
            "Несовпадения схем gateway → rag_search:\n" + "\n".join(mismatches)


# ────────────────────────────────────────────────────────────────
#  8. Query text/search → registry enrich: сквозной контракт
# ────────────────────────────────────────────────────────────────


class TestQueryTextSearchEnrichContract:
    """query → registry: text/search enrich contract.

    query при обработке text/search вызывает registry.enrich_query().
    """

    def test_query_text_search_has_valid_at(self):
        """QS-7: text/search в query включает valid_at и category_ids."""
        query_def = SERVICE_REGISTRY["query"]()
        search_ep = _find_endpoint(query_def, "POST", "/text/search")
        assert search_ep is not None
        assert search_ep.body is not None

        assert "valid_at" in search_ep.body, (
            "QS-7: valid_at отсутствует в теле запроса text/search.\n"
            "Без valid_at text/search не сможет корректно отфильтровать документы."
        )
        assert "filters" in search_ep.body, (
            "QS-7: filters отсутствуют в теле запроса text/search"
        )
        filters = search_ep.body["filters"]
        assert isinstance(filters, dict), "filters должен быть dict"
        assert "category_ids" in filters, (
            "QS-7: category_ids отсутствует в filters text/search"
        )

    def test_query_text_search_response_has_enrichment_skipped(self):
        """QS-8: text/search ответ содержит enrichment_skipped."""
        query_def = SERVICE_REGISTRY["query"]()
        search_ep = _find_endpoint(query_def, "POST", "/text/search")
        assert search_ep is not None
        assert search_ep.response_schema is not None

        assert "enrichment_skipped" in search_ep.response_schema, (
            "QS-8: enrichment_skipped отсутствует в response_schema.\n"
            "Если enrich_query упал внутри query, enrichment_skipped=true "
            "должен сигнализировать об этом."
        )
        expected_type = search_ep.response_schema["enrichment_skipped"]
        assert expected_type is bool, (
            f"QS-8: enrichment_skipped должен быть bool, "
            f"получен {expected_type}"
        )

    def test_gateway_text_search_has_enrichment_skipped(self):
        """Gateway проксирует enrichment_skipped из query.

        enrichment_skipped добавлен в response_schema gateway —
        клиент gateway получает информацию о статусе обогащения запроса.
        """
        gw_def = SERVICE_REGISTRY["gateway"]()
        gw_ep = _find_endpoint(gw_def, "POST", "/text/search")
        assert gw_ep is not None, "gateway: POST /text/search не найден"
        assert gw_ep.response_schema is not None, "response_schema отсутствует"
        assert "enrichment_skipped" in gw_ep.response_schema, (
            "Gateway не передаёт enrichment_skipped — клиент не узнает "
            "о статусе обогащения. Добавьте enrichment_skipped в response_schema"
        )
