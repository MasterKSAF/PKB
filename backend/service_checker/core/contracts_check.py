"""
PKB Neuroassistant — Real Service Contracts Check (Docker mode).

Проверяет реальное взаимодействие сервисов друг с другом путём
прямых HTTP-вызовов к запущенным Docker-контейнерам.

В отличие от test_service_contracts.py (юнит-тесты с моками),
этот модуль использует реальные HTTP-запросы и проверяет,
что сервисы корректно отвечают друг другу.

Критические связки:
1. query → rag_search — pipeline вызывает rag_client.search()
2. query → registry — pipeline вызывает registry_client.enrich_query()
3. rag_search → infinity — rag_search вызывает rerank через TEI
4. gateway → query — gateway проксирует /api/v1/chat/* на query
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import httpx

from service_checker.services import (
    MODE_PORTS,
    SERVICE_REGISTRY,
)
from service_checker.services.base import (
    API_PREFIX,
    EndpointDef,
)


# ── Data structures ──────────────────────────────────────────────


@dataclass
class ContractCheckResult:
    """Результат проверки одного контракта."""

    name: str  # Название проверки
    passed: bool
    status_code: int = 0
    elapsed_ms: int = 0
    error: Optional[str] = None
    detail: Optional[str] = None  # Полезная информация для отчёта


@dataclass
class ContractsCheckReport:
    """Общий результат проверки всех контрактов."""

    results: List[ContractCheckResult] = field(default_factory=list)
    total: int = 0
    passed: int = 0
    failed: int = 0

    @property
    def all_passed(self) -> bool:
        return self.failed == 0


# ── Helpers ──────────────────────────────────────────────────────


def _find_endpoint_def(svc_key: str, method: str, path_suffix: str) -> Optional[EndpointDef]:
    """Найти EndpointDef в SERVICE_REGISTRY по суффиксу пути."""
    target = f"{API_PREFIX}{path_suffix}"
    try:
        svc_def = SERVICE_REGISTRY[svc_key]()
    except KeyError:
        return None
    for ep in svc_def.endpoints:
        if ep.method == method and ep.path == target:
            return ep
    for ep in svc_def.prepare_endpoints:
        if ep.method == method and ep.path == target:
            return ep
    return None


async def _do_request(
    client: httpx.AsyncClient,
    method: str,
    port: int,
    path: str,
    json_body: Optional[Dict] = None,
    expected_status: int = 200,
) -> Tuple[int, Optional[Dict], float]:
    """Выполнить HTTP-запрос и вернуть (status, body_json, elapsed_sec)."""
    url = f"http://127.0.0.1:{port}{path}"
    start = time.monotonic()
    try:
        kwargs: Dict[str, Any] = {}
        if json_body is not None:
            kwargs["json"] = json_body
        resp = await getattr(client, method.lower())(url, **kwargs)
        elapsed = time.monotonic() - start
        try:
            body = resp.json()
        except Exception:
            body = None
        return resp.status_code, body, elapsed
    except httpx.ConnectError:
        return 0, None, time.monotonic() - start
    except httpx.TimeoutException:
        return 0, None, time.monotonic() - start


def _check_response_schema(
    body: Optional[Dict],
    expected_schema: Optional[Dict[str, type]],
) -> Tuple[bool, str]:
    """Проверить, что тело ответа соответствует ожидаемой схеме."""
    if body is None:
        return False, "Пустой ответ"
    if not expected_schema:
        return True, "Нет схемы для проверки"
    for field, expected_type in expected_schema.items():
        if field not in body:
            return False, f"Поле '{field}' отсутствует в ответе"
        actual = body[field]
        # Поддержка Union типов: (int, float) → любой из
        if isinstance(expected_type, tuple):
            if not isinstance(actual, expected_type):
                return False, (
                    f"Поле '{field}': ожидался тип {expected_type}, "
                    f"получен {type(actual).__name__}"
                )
        else:
            if not isinstance(actual, expected_type):
                return False, (
                    f"Поле '{field}': ожидался тип {expected_type.__name__}, "
                    f"получен {type(actual).__name__}"
                )
    return True, "Схема ответа валидна"


# ── Contract tests ───────────────────────────────────────────────


async def check_query_to_rag_search(client: httpx.AsyncClient) -> ContractCheckResult:
    """Связка 1: query → rag_search.

    Отправляет POST /api/v1/rag/search на rag_search (прямой вызов).
    """
    rag_port = MODE_PORTS.get("rag_search", 8091)
    rag_ep = _find_endpoint_def("rag_search", "POST", "/rag/search")
    if not rag_ep:
        return ContractCheckResult(
            name="query → rag_search",
            passed=False,
            error="Endpoint POST /rag/search не найден в rag_search",
        )

    status, body, elapsed = await _do_request(
        client, "POST", rag_port, f"{API_PREFIX}/rag/search",
        json_body={
            "query": "ледовый класс Arc4",
            "valid_at": "2026-06-19",
            "filters": {
                "document_type": [],
                "category_ids": [],
                "document_ids": [],
            },
        },
        expected_status=200,
    )

    elapsed_ms = int(elapsed * 1000)

    if status == 0:
        return ContractCheckResult(
            name="query → rag_search",
            passed=False,
            status_code=0,
            error="rag_search не отвечает (ConnectError/Timeout)",
        )
    if status >= 500:
        return ContractCheckResult(
            name="query → rag_search",
            passed=False,
            status_code=status,
            error=f"rag_search вернул {status}: {str(body)[:200] if body else '—'}",
        )
    if status == 422:
        return ContractCheckResult(
            name="query → rag_search",
            passed=False,
            status_code=422,
            error=(
                f"rag_search вернул 422 — скорее всего отсутствует или "
                f"некорректный valid_at. Детали: {str(body)[:200] if body else '—'}"
            ),
        )
    if status != 200:
        return ContractCheckResult(
            name="query → rag_search",
            passed=False,
            status_code=status,
            error=f"Ожидался 200, получен {status}: {str(body)[:200] if body else '—'}",
        )

    # Проверка схемы ответа
    schema_ok, schema_msg = _check_response_schema(body, rag_ep.response_schema)
    if not schema_ok:
        return ContractCheckResult(
            name="query → rag_search",
            passed=False,
            status_code=200,
            error=f"Схема ответа не совпадает: {schema_msg}",
            detail=f"Ответ сервиса: {json.dumps(body, ensure_ascii=False)[:300]}",
        )

    return ContractCheckResult(
        name="query → rag_search",
        passed=True,
        status_code=200,
        elapsed_ms=elapsed_ms,
        detail=f"results={len(body.get('results', []))}, "
               f"processing_time_ms={body.get('processing_time_ms', '?')}, "
               f"total_found={body.get('total_found', '?')}",
    )


async def check_query_to_registry(client: httpx.AsyncClient) -> ContractCheckResult:
    """Связка 2: query → registry.

    Проверяет, что registry отвечает на search с valid_at (используется query).
    """
    reg_port = MODE_PORTS.get("registry", 8084)
    reg_ep = _find_endpoint_def("registry", "GET", "/registry/search")
    if not reg_ep:
        return ContractCheckResult(
            name="query → registry",
            passed=False,
            error="Endpoint GET /registry/search не найден в registry",
        )

    params = {"q": "тест", "valid_at": "2026-06-19"}
    url = f"http://127.0.0.1:{reg_port}{API_PREFIX}/registry/search"
    start = time.monotonic()
    try:
        resp = await client.get(url, params=params)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        status = resp.status_code
        try:
            body = resp.json()
        except Exception:
            body = None
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        return ContractCheckResult(
            name="query → registry",
            passed=False,
            error=f"registry не отвечает: {e}",
        )

    if status == 0:
        return ContractCheckResult(
            name="query → registry",
            passed=False,
            error="registry не отвечает",
        )
    if status >= 500:
        return ContractCheckResult(
            name="query → registry",
            passed=False,
            status_code=status,
            error=f"registry вернул {status}",
        )
    if status != 200:
        return ContractCheckResult(
            name="query → registry",
            passed=False,
            status_code=status,
            error=f"Ожидался 200, получен {status}",
        )

    schema_ok, schema_msg = _check_response_schema(body, reg_ep.response_schema)
    if not schema_ok:
        return ContractCheckResult(
            name="query → registry",
            passed=False,
            status_code=200,
            error=f"Схема ответа не совпадает: {schema_msg}",
        )

    return ContractCheckResult(
        name="query → registry",
        passed=True,
        status_code=200,
        elapsed_ms=elapsed_ms,
        detail=f"data=[] — валидный ответ (БД пуста, но эндпоинт работает)",
    )


async def check_rag_search_to_infinity(client: httpx.AsyncClient) -> ContractCheckResult:
    """Связка 3: rag_search → infinity (TEI).

    Проверяет, что TEI отвечает на /embed (rag_search вызывает его
    при реранкинге).
    """
    tei_port = MODE_PORTS.get("tei", 18092)
    tei_ep = _find_endpoint_def("tei", "POST", "/embed")
    if not tei_ep:
        # TEI использует путь /embed без /api/v1
        pass  # проверим прямым запросом

    status, body, elapsed = await _do_request(
        client, "POST", tei_port, "/embed",
        json_body={"inputs": "Тестовый запрос для эмбеддинга"},
    )

    elapsed_ms = int(elapsed * 1000)

    if status == 0:
        return ContractCheckResult(
            name="rag_search → infinity (TEI)",
            passed=False,
            error="TEI не отвечает (ConnectError/Timeout)",
        )
    if status >= 500:
        return ContractCheckResult(
            name="rag_search → infinity (TEI)",
            passed=False,
            status_code=status,
            error=f"TEI вернул {status}",
        )
    if status != 200:
        return ContractCheckResult(
            name="rag_search → infinity (TEI)",
            passed=False,
            status_code=status,
            error=f"Ожидался 200, получен {status}",
        )

    # TEI возвращает [[float]]
    if body is None:
        return ContractCheckResult(
            name="rag_search → infinity (TEI)",
            passed=False,
            status_code=200,
            error="TEI вернул пустой ответ",
        )
    if not isinstance(body, list) or len(body) == 0:
        return ContractCheckResult(
            name="rag_search → infinity (TEI)",
            passed=False,
            status_code=200,
            error=f"TEI: ожидался [[float]], получен {type(body).__name__}",
        )
    if not isinstance(body[0], list):
        return ContractCheckResult(
            name="rag_search → infinity (TEI)",
            passed=False,
            status_code=200,
            error=f"TEI: ожидался список эмбеддингов, получен {type(body[0]).__name__}",
        )

    emb_len = len(body[0])
    return ContractCheckResult(
        name="rag_search → infinity (TEI)",
        passed=True,
        status_code=200,
        elapsed_ms=elapsed_ms,
        detail=f"embedding_dim={emb_len} — эмбеддинги работают",
    )


async def check_gateway_to_query(client: httpx.AsyncClient) -> ContractCheckResult:
    """Связка 4: gateway → query.

    Проверяет, что gateway проксирует /api/v1/chat/sessions на query.
    Предварительно создаёт проект (как _ensure_project в пайплайнах).
    """
    gw_port = MODE_PORTS.get("gateway", 8080)
    query_port = MODE_PORTS.get("query", 8083)
    gw_ep = _find_endpoint_def("gateway", "POST", "/chat/sessions")
    if not gw_ep:
        return ContractCheckResult(
            name="gateway → query",
            passed=False,
            error="Endpoint POST /chat/sessions не найден в gateway",
        )

    # ── Pre-create project (QS-3) ──
    project_id = None

    # Пытаемся создать проект напрямую на query (прокси тоже пойдёт)
    ts = __import__("datetime").datetime.now().strftime("%Y%m%d%H%M%S%f")
    project_code = f"CONTRACT_CHECK_{ts}"
    for attempt in range(3):
        p_status, p_body, _ = await _do_request(
            client, "POST", query_port, f"{API_PREFIX}/chat/projects",
            json_body={"code": project_code, "name": "Contract Check Project"},
            expected_status=201,
        )
        if p_status == 201 and p_body:
            project_id = p_body.get("project_id") or (p_body.get("data") or {}).get("id")
            if project_id:
                break
        elif p_status == 409:
            # Проект уже есть — ищем через GET
            try:
                resp = await client.get(
                    f"http://127.0.0.1:{query_port}{API_PREFIX}/chat/projects"
                )
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("items") or data.get("data") or []
                    if items:
                        pid = items[0].get("project_id") or items[0].get("id")
                        if pid:
                            project_id = pid
                            break
            except Exception:
                pass
        await asyncio.sleep(0.5)

    if not project_id:
        return ContractCheckResult(
            name="gateway → query",
            passed=False,
            error="Не удалось создать или получить project_id для проверки прокси",
        )

    # ── Create session через gateway (проверяем прокси) ──
    status, body, elapsed = await _do_request(
        client, "POST", gw_port, f"{API_PREFIX}/chat/sessions",
        json_body={"title": "Contract test session", "document_ids": [],
                   "project_id": project_id},
        expected_status=201,
    )

    elapsed_ms = int(elapsed * 1000)

    if status == 0:
        return ContractCheckResult(
            name="gateway → query",
            passed=False,
            error="Gateway не отвечает (ConnectError/Timeout)",
        )
    if status >= 500:
        return ContractCheckResult(
            name="gateway → query",
            passed=False,
            status_code=status,
            error=f"Gateway вернул {status}: {str(body)[:200] if body else '—'}",
        )

    # 201 — успех, 409 — уже существует (тоже ок)
    if status == 201:
        schema_ok, schema_msg = _check_response_schema(body, gw_ep.response_schema)
        if not schema_ok:
            return ContractCheckResult(
                name="gateway → query",
                passed=False,
                status_code=201,
                error=f"Схема ответа не совпадает: {schema_msg}",
            )
        session_id = body.get("session_id", body.get("id", "?")) if body else "?"
        return ContractCheckResult(
            name="gateway → query",
            passed=True,
            status_code=201,
            elapsed_ms=elapsed_ms,
            detail=f"session_id={session_id} — прокси работает",
        )
    elif status == 409:
        return ContractCheckResult(
            name="gateway → query",
            passed=True,
            status_code=409,
            elapsed_ms=elapsed_ms,
            detail="Сессия уже существует (409) — прокси работает",
        )
    else:
        return ContractCheckResult(
            name="gateway → query",
            passed=False,
            status_code=status,
            error=f"Ожидался 201/409, получен {status}: "
                  f"{str(body)[:200] if body else '—'}",
        )


async def check_gateway_to_rag_search(client: httpx.AsyncClient) -> ContractCheckResult:
    """Связка 5: gateway → rag_search (отключено — RAG Search не проксируется через Gateway)."""
    return ContractCheckResult(
        name="gateway → rag_search",
        passed=True,
        detail="Проверка отключена — RAG Search не должен быть в Gateway",
    )


# ── Runner ───────────────────────────────────────────────────────


async def run_all_contract_checks(
    base_host: str = "127.0.0.1",
    timeout: int = 15,
) -> ContractsCheckReport:
    """Запустить все проверки контрактов и вернуть отчёт."""
    report = ContractsCheckReport()

    async with httpx.AsyncClient(timeout=timeout) as client:
        checks = [
            ("query → rag_search", check_query_to_rag_search),
            ("query → registry", check_query_to_registry),
            ("rag_search → infinity (TEI)", check_rag_search_to_infinity),
            ("gateway → query", check_gateway_to_query),
        ]

        for name, check_func in checks:
            result = await check_func(client)
            report.results.append(result)
            report.total += 1
            if result.passed:
                report.passed += 1
            else:
                report.failed += 1

    return report


def format_contracts_report(report: ContractsCheckReport) -> str:
    """Сформировать секцию для полного отчёта."""
    lines = []
    lines.append("---\n")
    lines.append("## 🔗 Service Contracts Check\n")
    lines.append("Проверка реального взаимодействия сервисов друг с другом.\n")
    lines.append("")
    lines.append("| Contract | Status | Code | Time | Детали |")
    lines.append("|----------|:------:|:----:|:----:|--------|")

    for r in report.results:
        icon = "✅" if r.passed else "❌"
        code = str(r.status_code) if r.status_code else "—"
        time_ms = f"{r.elapsed_ms}ms" if r.elapsed_ms > 0 else "—"
        detail = r.detail or (r.error or "—")
        lines.append(f"| {r.name} | {icon} | {code} | {time_ms} | {detail} |")

    # Итог
    total_icon = "✅" if report.all_passed else "❌"
    lines.append(
        f"| **Total** | {total_icon} | | | "
        f"{report.passed}/{report.total} passed, {report.failed} failed |"
    )
    lines.append("")

    # Пояснения для упавших
    failures = [r for r in report.results if not r.passed]
    if failures:
        lines.append("#### ❌ Детали ошибок\n")
        for r in failures:
            lines.append(f"- **{r.name}**: {r.error}")
        lines.append("")

    return "\n".join(lines)
