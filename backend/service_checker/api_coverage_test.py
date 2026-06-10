#!/usr/bin/env python3
"""
PKB Neuroassistant — API Coverage Test (based on docs/api/*.md)

Скрипт проверяет вызов каждого эндпоинта из документации API.
Для каждого сервиса определяется полный список эндпоинтов (метод + путь + тело запроса),
после чего выполняется HTTP-вызов, и результат записывается в отчёт.

Поддержка prepare-эндпоинтов: перед вызовом основных эндпоинтов выполняются
prepare-шаги, которые создают необходимые данные (классификаторы, документы, термины
и т.д.) и сохраняют ID в контекст для последующих вызовов.

Запуск:
  # Все сервисы (моки должны быть запущены)
  python backend/service_checker/api_coverage_test.py

  # Только конкретные сервисы
  python backend/service_checker/api_coverage_test.py --services auth,registry

  # С сохранением отчёта
  python backend/service_checker/api_coverage_test.py -o coverage_report.md

  # Только здоровье — проверить какие сервисы отвечают
  python backend/service_checker/api_coverage_test.py --ping-only
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import httpx

from service_checker.services.base import (
    API_PREFIX,
    EndpointDef,
    EndpointResult,
    ServiceDef,
    ServiceResult,
    HEADERS_JSON,
)
from service_checker.services import (
    MODE_PORTS,
    SERVICE_DEPENDENCIES,
    SERVICE_REGISTRY,
)


# ──────────────────────────────────────────────────────────────────────
#  Тестовый движок
# ──────────────────────────────────────────────────────────────────────

# Сервисы, имеющие реальную реализацию
SERVICES_WITH_REAL = {
    "gateway", "auth", "orchestrator", "query", "registry",
    "converter_validator", "parser", "ocr", "rag_builder", "rag_search", "tei",
}


class ApiCoverageTester:
    """
    Тестер покрытия API.
    Для каждого сервиса вызывает все эндпоинты из документации,
    собирает результаты и формирует отчёт.

    Запуск только в Docker (real-режим).
    """

    def __init__(
        self,
        services: Optional[List[str]] = None,
        base_host: str = "127.0.0.1",
        skip_prepare: bool = False,
    ):
        self.base_host = base_host
        self.skip_prepare = skip_prepare

        available_services = set(MODE_PORTS.keys())
        self.services_with_impl = SERVICES_WITH_REAL

        if services:
            self.services_to_test = [s for s in services if s in available_services]
        else:
            # Сортируем так, чтобы сервисы-зависимости шли до зависимых от них
            # (контекст prepare-шагов накапливается для downstream сервисов)
            _ORDER = {
                "auth": 0,
                "registry": 1,      # создаёт doc_id, classifier_code, term_id
                "converter_validator": 2,
                "parser": 3,
                "ocr": 4,
                "orchestrator": 5,   # использует doc_id из Registry
                "query": 6,
                "rag_builder": 7,
                "rag_search": 8,
                "tei": 9,
                "gateway": 10,
            }
            self.services_to_test = sorted(available_services, key=lambda s: _ORDER.get(s, 99))

        self.context: Dict[str, Any] = {}  # shared context между вызовами
        self.results: Dict[str, ServiceResult] = {}
        self.client = httpx.AsyncClient(timeout=15)
        # Для тестов: можно подставить свои endpoint'ы (ключ → List[EndpointDef])
        self._test_endpoints: Dict[str, List[EndpointDef]] = {}

    async def close(self) -> None:
        await self.client.aclose()

    async def ping_service(self, port: int, fast: bool = False) -> bool:
        """Проверить, отвечает ли сервис.

        Если fast=True — пробуем только первый health-эндпоинт с таймаутом 1.5с.
        """
        health_paths = [
            f"{API_PREFIX}/health",
            f"{API_PREFIX}/system/health",
            f"{API_PREFIX}/monitor/health",
        ]
        if fast:
            health_paths = health_paths[:1]
        timeout = 1.5 if fast else 2
        for path in health_paths:
            try:
                resp = await self.client.get(
                    f"http://{self.base_host}:{port}{path}",
                    timeout=timeout,
                )
                if resp.status_code < 500:  # сервис отвечает (даже 404 — жив, просто нет такого пути)
                    return True
            except Exception:
                continue
        return False

    def _resolve_path(self, path: str) -> str:
        """Подставить контекстные переменные в путь."""
        resolved = path
        for key, value in self.context.items():
            placeholder = "{{" + key + "}}"
            resolved = resolved.replace(placeholder, str(value))
        return resolved

    def _resolve_body(self, body: Optional[Dict]) -> Optional[Dict]:
        """Подставить контекстные переменные в тело."""
        if body is None:
            return None
        resolved = json.dumps(body)
        for key, value in self.context.items():
            placeholder = "{" + key + "}"
            resolved = resolved.replace(placeholder, str(value))
        return json.loads(resolved)

    def _validate_response(
        self,
        response_body: Optional[str],
        schema: Dict[str, type],
    ) -> Tuple[bool, List[str]]:
        """
        Проверить что ответ содержит все ожидаемые поля с правильными типами.

        schema = {
            "status": str,              # проверяет response["status"] — str
            "data": dict,               # response["data"] — dict
            "data.items": list,         # response["data"]["items"] — list
            "session_id": (int, str),   # может быть int или str (union)
        }

        Возвращает (ok, список_ошибок).
        """
        if not response_body:
            return False, ["Пустой ответ"]

        try:
            data = json.loads(response_body)
        except json.JSONDecodeError as e:
            return False, [f"Невалидный JSON: {e}"]

        errors = []

        for path, expected_type in schema.items():
            # Идём по точечному пути
            parts = path.split(".")
            current = data
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    errors.append(
                        f"Поле '{path}' обязательно, но не найдено в ответе"
                    )
                    break
            else:
                # Проверяем тип (поддержка union: (int, str) — любой из)
                if not isinstance(current, expected_type):
                    actual = type(current).__name__
                    expected_name = getattr(expected_type, '__name__', str(expected_type))
                    errors.append(
                        f"Поле '{path}' ожидалось {expected_name}, получен {actual} = {str(current)[:80]}"
                    )

        return len(errors) == 0, errors

    def _extract_context(self, response_body: Optional[str], extract_keys: Optional[List[str]]) -> None:
        """Извлечь ID из ответа и сохранить в контекст.

        Поддержка обёрток: если ответ = {"data": {"id": "xxx"}},
        а ключ "id" — сначала ищем "data.id", потом рекурсивно "id".
        """
        if not response_body or not extract_keys:
            return
        try:
            raw = json.loads(response_body)
        except json.JSONDecodeError:
            return

        def _get_by_path(obj: Any, path: str) -> Optional[Any]:
            """Достать значение по точечному пути ("data.id")."""
            parts = path.split(".")
            current = obj
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
            return current

        def _search(obj: Any, key: str) -> Optional[Any]:
            """Рекурсивный поиск ключа в любом месте объекта."""
            if isinstance(obj, dict):
                if key in obj:
                    return obj[key]
                for v in obj.values():
                    result = _search(v, key)
                    if result is not None:
                        return result
                # Альтернативные имена
                alt_map = {
                    "session_id": ["id", "sessionId", "session_id"],
                    "doc_id": ["id", "document_id", "docId"],
                    "user_id": ["id", "userId", "user_id"],
                    "classifier_code": ["code", "classifier_code"],
                    "term_id": ["id", "term_id", "termId"],
                    "message_id": ["id", "messageId", "message_id"],
                    "task_id": ["task_id", "taskId"],
                }
                for alt in alt_map.get(key, []):
                    if alt in obj:
                        return obj[alt]
            elif isinstance(obj, list):
                for item in obj:
                    result = _search(item, key)
                    if result is not None:
                        return result
            return None

        for key in extract_keys:
            if key not in self.context:
                # Сначала ищем как data.key (для обёрнутых ответов)
                value = _get_by_path(raw, f"data.{key}")
                # Потом рекурсивно
                if value is None:
                    value = _search(raw, key)
                if value is not None:
                    self.context[key] = value

    async def _execute_endpoint(
        self, ep: EndpointDef, port: int, result: ServiceResult, alive: bool,
    ) -> None:
        """Выполнить один эндпоинт и записать результат."""
        # Если сервис не отвечает — пропускаем все эндпоинты
        if not alive:
            result.results.append(
                EndpointResult(endpoint=ep, status_code=0, success=False, skipped=True, skip_reason="Сервис не отвечает")
            )
            result.endpoints_skipped += 1
            return

        # Для эндпоинтов, требующих ID из контекста, проверяем наличие
        path_placeholders = [p.strip("{}") for p in ep.path.split("/") if "{" in p and "}" in p]
        missing_vars = [v for v in path_placeholders if v not in self.context]
        if missing_vars and "{{" in ep.path:
            result.results.append(
                EndpointResult(
                    endpoint=ep, status_code=0, success=False, skipped=True,
                    skip_reason=f"Нет в контексте: {', '.join(missing_vars)}. "
                                f"Требуется предварительный вызов создающего эндпоинта."
                )
            )
            result.endpoints_skipped += 1
            return

        # Если тело содержит неподставленные переменные — пропускаем
        body = self._resolve_body(ep.body)
        if body and isinstance(body, str):
            if "{" in body and "}" in body:
                result.results.append(
                    EndpointResult(endpoint=ep, status_code=0, success=False, skipped=True, skip_reason="Не все переменные контекста доступны для тела запроса")
                )
                result.endpoints_skipped += 1
                return

        # Формируем URL
        resolved_path = self._resolve_path(ep.path)
        url = f"http://{self.base_host}:{port}{resolved_path}"

        # Формируем заголовки
        headers = {**HEADERS_JSON}
        if "access_token" in self.context:
            headers["Authorization"] = f"Bearer {self.context['access_token']}"

        # Выполняем запрос
        start = time.time()
        try:
            kwargs: Dict[str, Any] = {"headers": headers}
            if ep.form_body is not None:
                # multipart/form-data — убираем JSON content-type
                headers.pop("Content-Type", None)
                kwargs["data"] = self._resolve_body(ep.form_body)
                # Минимальный валидный PDF (заголовок + 1 страница)
                pdf_bytes = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
                             b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
                             b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 50]"
                             b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>>endobj\n"
                             b"4 0 obj<</Length 44>>stream\nBT /F1 12 Tf 10 20 Td(test)Tj ET\nendstream\nendobj\n"
                             b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
                             b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000266 00000 n \n0000000355 00000 n \n"
                             b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n424\n%%EOF")
                kwargs["files"] = {"file": ("test.pdf", pdf_bytes, "application/pdf")}
            elif body is not None:
                kwargs["json"] = body
            if ep.params:
                kwargs["params"] = ep.params

            resp = await getattr(self.client, ep.method.lower())(url, **kwargs)
            elapsed = int((time.time() - start) * 1000)

            resp_body = resp.text if resp.content else None
            # Для prepare-шагов: success по expected_status (201 или 409 — данные созданы)
            # Для основных endpoints: только 2xx/3xx
            if ep.is_preparation and ep.expected_status:
                if isinstance(ep.expected_status, set):
                    success = resp.status_code in ep.expected_status
                else:
                    success = resp.status_code == ep.expected_status
            else:
                success = resp.status_code < 400

            # Извлекаем контекст из ответа
            if success and ep.extract_keys:
                self._extract_context(resp_body, ep.extract_keys)

            # Валидация схемы ответа (только для 2xx, не для prepare)
            schema_valid = True
            schema_errors = []
            if not ep.is_preparation and resp.status_code < 300 and ep.response_schema:
                schema_valid, schema_errors = self._validate_response(
                    resp_body, ep.response_schema
                )
                if not schema_valid:
                    success = False

            ep_result = EndpointResult(
                endpoint=ep,
                status_code=resp.status_code,
                success=success,
                elapsed_ms=elapsed,
                response_body=resp_body[:500] if resp_body else None,
                error="; ".join(schema_errors) if schema_errors else None,
            )

            if success:
                result.endpoints_passed += 1
            else:
                result.endpoints_failed += 1

        except httpx.ConnectError as e:
            elapsed = int((time.time() - start) * 1000)
            ep_result = EndpointResult(
                endpoint=ep, status_code=0, success=False, elapsed_ms=elapsed,
                error=f"ConnectError: {e}", skipped=True, skip_reason="Сервис не отвечает"
            )
            result.endpoints_skipped += 1
        except httpx.TimeoutException as e:
            elapsed = int((time.time() - start) * 1000)
            ep_result = EndpointResult(
                endpoint=ep, status_code=0, success=False, elapsed_ms=elapsed,
                error=f"Timeout: {e}", skipped=True, skip_reason="Таймаут"
            )
            result.endpoints_skipped += 1
        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            ep_result = EndpointResult(
                endpoint=ep, status_code=0, success=False, elapsed_ms=elapsed,
                error=str(e)
            )
            result.endpoints_failed += 1

        result.results.append(ep_result)

    async def test_service(self, service_key: str) -> ServiceResult:
        """Протестировать все эндпоинты сервиса.

        Если сервис не найден в SERVICE_REGISTRY, возвращает пустой результат
        (для совместимости с тестами, которые подставляют свои эндпоинты).
        """
        # Если есть тестовые endpoint'ы — используем их (для совместимости)
        svc_def: Optional[ServiceDef] = None
        if service_key in self._test_endpoints:
            svc_endpoints = self._test_endpoints[service_key]
            svc_prepare = []
            port = MODE_PORTS.get(service_key, 0)
            svc_name = service_key
            # Определяем порт из MODE_PORTS или берём 8080 по умолчанию
            if port == 0:
                port = 8080
        elif service_key in SERVICE_REGISTRY:
            svc_def = SERVICE_REGISTRY[service_key]()
            svc_endpoints = svc_def.endpoints
            svc_prepare = svc_def.prepare_endpoints
            port = svc_def.port
            svc_name = svc_def.display_name
        else:
            # Неизвестный сервис — пустой результат
            result = ServiceResult(name=service_key, port=MODE_PORTS.get(service_key, 0))
            result.endpoints_total = 0
            result.ping_ok = False
            return result

        result = ServiceResult(name=svc_name, port=port)
        result.endpoints_total = len(svc_endpoints) + len(svc_prepare)

        if port == 0:
            result.ping_ok = False
            for ep in svc_endpoints:
                result.results.append(
                    EndpointResult(endpoint=ep, status_code=0, success=False, skipped=True, skip_reason="Неизвестный порт")
                )
            result.endpoints_skipped = len(svc_endpoints)
            return result

        # Проверяем жив ли сервис
        alive = await self.ping_service(port, fast=True)
        result.ping_ok = alive

        # ── 1. Prepare-этап: создаём необходимые данные ──────────────
        if not self.skip_prepare and alive and svc_prepare:
            for ep in svc_prepare:
                await self._execute_endpoint(ep, port, result, alive)
            # Проверяем, что prepare-шаги извлекли контекст
            if svc_def and svc_def.base_data:
                missing = [k for k in svc_def.base_data if k not in self.context]
                if missing:
                    print(f"     ⚠️  Prepare не извлёк контекст: {', '.join(missing)}")
            # Эвристика: если prepare-эндпоинты указали extract_keys, но контекст пуст — warning
            expected_keys = set()
            for ep in svc_prepare:
                if ep.extract_keys:
                    expected_keys.update(ep.extract_keys)
            if expected_keys and not any(k in self.context for k in expected_keys):
                print(f"     ⚠️  Все prepare-шаги вернули ошибки — контекст не создан (будут пропуски)")

        # ── 2. Основные эндпоинты ────────────────────────────────────
        for ep in svc_endpoints:
            await self._execute_endpoint(ep, port, result, alive)

        # Если сервис ответил на ping, но все не-health эндпоинты вернули 404 —
        # значит сервиса по факту нет (на порту что-то есть, но не то).
        if result.ping_ok:
            non_health_results = [
                r for r in result.results
                if r.endpoint.group != "health" and not r.skipped
            ]
            if len(non_health_results) >= 2 and all(
                r.status_code == 404 for r in non_health_results
            ):
                result.ping_ok = False
                for r in result.results:
                    if not r.skipped and r.success:
                        r.success = False
                        result.endpoints_passed -= 1
                        result.endpoints_failed += 1

        return result

    async def run_all(self) -> Dict[str, ServiceResult]:
        """Запустить тестирование всех сервисов."""
        print("=" * 70)
        print(f"  PKB Neuroassistant — API Coverage Test")
        print(f"  🔬 Real mode (Docker)")
        print(f"  Основано на docs/api/*.md")
        print("=" * 70)

        for svc_key in self.services_to_test:
            if svc_key not in SERVICE_REGISTRY:
                print(f"\n  ✗  Сервис '{svc_key}' не найден в реестре. Пропускаем.")
                continue

            svc_def = SERVICE_REGISTRY[svc_key]()
            ep_count = len(svc_def.endpoints)
            prep_count = len(svc_def.prepare_endpoints)
            print(f"\n  ── [{svc_key.upper()}] ({ep_count} эндпоинтов + {prep_count} prepare) ──")

            result = await self.test_service(svc_key)
            self.results[svc_key] = result

            status = "✅" if result.ping_ok else "❌"
            print(f"     Ping: {status}  |  Passed: {result.endpoints_passed}/{result.endpoints_total}  "
                  f"|  Failed: {result.endpoints_failed}  |  Skipped: {result.endpoints_skipped}")

            # Если сервис не отвечает — уточняем причину (без ввода в заблуждение)
            deps = svc_def.depends_on
            if not result.ping_ok:
                print(f"     ❌ Сервис не отвечает на порту {svc_def.port}")
            if not result.ping_ok and deps:
                print(f"     📎 Включает эндпоинты: {', '.join(deps)}")

        return self.results

    def generate_report(self, log_report_path: Optional[str] = None) -> str:
        """Сформировать markdown-отчёт."""
        lines = []
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        lines.append(f"# API Coverage Report\n")
        lines.append(f"**Generated:** {now}\n")
        lines.append(f"**Mode:** 🔬 Real (Docker)\n")
        lines.append(f"**Based on:** `docs/api/*.md`\n")
        if log_report_path:
            lines.append(f"📋 **Logs:** [{log_report_path}]({log_report_path})\n")
        lines.append("---\n")

        # Сводка
        lines.append("## 📊 Summary\n")
        lines.append("| Service | Port | Ping | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |")
        lines.append("|---------|:----:|:----:|:---------:|:---------:|:---------:|:----------:|:------:|")

        total_ep = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        services_alive = 0

        for svc_key, result in self.results.items():
            total_ep += result.endpoints_total
            total_passed += result.endpoints_passed
            total_failed += result.endpoints_failed
            total_skipped += result.endpoints_skipped
            if result.ping_ok:
                services_alive += 1
            ping_icon = "✅" if result.ping_ok else "❌"
            failed_str = (
                f'<span style="color:red;font-weight:bold">{result.endpoints_failed}</span>'
                if result.endpoints_failed > 0 else str(result.endpoints_failed)
            )
            skipped_str = (
                f'<span style="color:red;font-weight:bold">{result.endpoints_skipped}</span>'
                if result.endpoints_skipped > 0 else str(result.endpoints_skipped)
            )
            # Статус: ❌ если ping упал или есть ошибки/пропуски, ✅ если всё ок
            if not result.ping_ok or result.endpoints_failed > 0 or result.endpoints_skipped > 0:
                status_icon = '<span style="color:red;font-weight:bold">❌</span>'
            else:
                status_icon = "✅"
            svc_anchor = svc_key.replace("_", "-")
            lines.append(f"| [{result.name}](#{svc_anchor}) | {result.port} | {ping_icon} | {result.endpoints_total} | "
                        f"{result.endpoints_passed} | {failed_str} | "
                        f"{skipped_str} | {status_icon} |")

        total_failed_str = (
            f'<span style="color:red;font-weight:bold">{total_failed}</span>'
            if total_failed > 0 else str(total_failed)
        )
        total_skipped_str = (
            f'<span style="color:red;font-weight:bold">{total_skipped}</span>'
            if total_skipped > 0 else str(total_skipped)
        )
        if total_failed > 0 or total_skipped > 0:
            total_status = '<span style="color:red;font-weight:bold">❌</span>'
        else:
            total_status = "✅"
        lines.append(f"| **Total** | | **{services_alive}/{len(self.results)}** | **{total_ep}** | **{total_passed}** | "
                    f"{total_failed_str} | {total_skipped_str} | {total_status} |\n")

        # Детали по каждому сервису
        lines.append("## 🔍 Details by Service\n")

        for svc_key, result in self.results.items():
            svc_anchor = svc_key.replace("_", "-")
            lines.append(f"### {svc_anchor}\n")
            lines.append(f"**{result.name}** (port {result.port})\n")
            lines.append(f"**Ping:** {'✅ Alive' if result.ping_ok else '❌ Unreachable'}\n")
            failed_detail = (
                f'<span style="color:red;font-weight:bold">{result.endpoints_failed}</span>'
                if result.endpoints_failed > 0 else str(result.endpoints_failed)
            )
            skipped_detail = (
                f'<span style="color:red;font-weight:bold">{result.endpoints_skipped}</span>'
                if result.endpoints_skipped > 0 else str(result.endpoints_skipped)
            )
            lines.append(f"**Total:** {result.endpoints_total} | **Passed:** {result.endpoints_passed} | "
                        f"**Failed:** {failed_detail} | **Skipped:** {skipped_detail}\n")

            # Группируем по группам
            groups: Dict[str, List[EndpointResult]] = {}
            for r in result.results:
                groups.setdefault(r.endpoint.group, []).append(r)

            for group_name, group_results in groups.items():
                lines.append(f"<details>")
                lines.append(f"<summary><b>{group_name.upper()}</b> ({len(group_results)} эндпоинтов)</summary>\n")
                lines.append("| # | Method | Path | Status | Code | Time |")
                lines.append("|---|--------|------|--------|:----:|:----:|")

                for i, r in enumerate(group_results, 1):
                    if r.skipped:
                        icon = "⏭️"
                        status_text = f"Skipped: {r.skip_reason or ''}"
                    elif r.success:
                        icon = "✅"
                        status_text = "OK"
                    else:
                        icon = "❌"
                        status_text = f"Error: {r.error or f'HTTP {r.status_code}'}"

                    # Сокращаем path для читаемости
                    path_short = r.endpoint.path.replace(API_PREFIX, "")
                    lines.append(f"| {i} | {r.endpoint.method} | `{path_short}` | {icon} {status_text} | {r.status_code} | {r.elapsed_ms}ms |")

                lines.append("</details>\n")

            lines.append("---\n")

        # Контекст
        lines.append("## 🔗 Context Variables\n")
        if self.context:
            lines.append("| Variable | Value |")
            lines.append("|----------|-------|")
            for k, v in self.context.items():
                lines.append(f"| `{k}` | `{v}` |")
        else:
            lines.append("_No context variables extracted._\n")

        # Легенда
        lines.append("## 📖 Legend\n")
        lines.append("- **✅ Passed** — 2xx/3xx, либо 4xx/5xx с валидным JSON (эндпоинт существует)\n")
        lines.append("- **❌ Failed** — 4xx/5xx без JSON, ошибка подключения, "
                     "или все не-health эндпоинты вернули 404 (сервис не существует)\n")
        lines.append("- **⏭️ Skipped** — эндпоинт пропущен (сервис не отвечает, нет ID в контексте)\n")
        lines.append("- **Ping** — проверка health-эндпоинта на порту сервиса\n")
        lines.append("- **Mode** — Real (Docker): проверяются только запущенные в Docker сервисы\n")
        lines.append("- ⏸️ **Analyse Service** — временно не тестируется (нет контейнера)\n")

        # Секция зависимостей
        lines.append("\n## 🔗 Dependency Map\n")
        lines.append("| Сервис | Зависит от |")
        lines.append("|--------|-----------|")
        for svc, deps in sorted(SERVICE_DEPENDENCIES.items()):
            deps_str = ", ".join(deps) if deps else "—"
            lines.append(f"| `{svc}` | {deps_str} |")

        # Обратные зависимости (кто пострадал от недоступных сервисов)
        down_services = [k for k, r in self.results.items() if not r.ping_ok]
        if down_services:
            reverse_deps = {}
            for svc, deps in SERVICE_DEPENDENCIES.items():
                for dep in deps:
                    reverse_deps.setdefault(dep, []).append(svc)
            lines.append("\n### ⚠️ Каскадные проблемы\n")
            lines.append("Недоступный сервис → страдают:")
            lines.append("")
            for svc in down_services:
                affected = reverse_deps.get(svc, [])
                affected_ok = [s for s in affected if s in self.results and self.results[s].ping_ok]
                if affected_ok:
                    lines.append(f"- ❌ **{svc}** → ⚠️ {' '.join(affected_ok)}")
                elif affected:
                    lines.append(f"- ❌ **{svc}** → 🔴 {' '.join(affected)}")
                else:
                    lines.append(f"- ❌ **{svc}** — от него никто не зависит")
            lines.append("")

        lines.append("\n---\n")
        lines.append(f"_Report generated by `api_coverage_test.py` at {now}_\n")

        return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────
#  CLI
# ──────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PKB Neuroassistant — API Coverage Test (based on docs)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Примеры:\n"
            "  python backend/service_checker/api_coverage_test.py\n"
                    "  python backend/service_checker/api_coverage_test.py --ping-only\n"
                    "  python backend/service_checker/api_coverage_test.py -o coverage_report.md\n"
        ),
    )
    parser.add_argument(
        "--services",
        default=None,
        help="Список сервисов через запятую (по умолч. все)",
    )

    parser.add_argument(
        "--ping-only",
        action="store_true",
        help="Только проверить какие сервисы отвечают",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Сохранить отчёт в файл (.md)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Хост для подключения (по умолч. 127.0.0.1)",
    )
    parser.add_argument(
        "--skip-prepare",
        action="store_true",
        help="Пропустить prepare-шаги (не создавать данные)",
    )
    return parser.parse_args()


async def ping_all(tester: ApiCoverageTester) -> None:
    """Проверить какие сервисы отвечают (конкурентно)."""
    ports = MODE_PORTS
    print(f"\n  Mode: REAL")
    print(f"  {'Service':30s} Port  Status")
    print(f"  {'─'*50}")

    async def _ping_one(svc_key: str, port: int) -> Tuple[str, int, bool]:
        alive = await tester.ping_service(port, fast=True)
        return svc_key, port, alive

    results = await asyncio.gather(*[
        _ping_one(svc_key, port) for svc_key, port in sorted(ports.items())
    ])

    for svc_key, port, alive in sorted(results, key=lambda x: x[0]):
        icon = "✅" if alive else "❌"
        name = svc_key.replace("_", " ").title()
        has_impl = svc_key in tester.services_with_impl
        impl = "*" if has_impl else " "
        print(f"  {icon} {name:28s} {port}   {'Alive' if alive else 'Unreachable'} {impl}")
    print(f"\n  * — сервис имеет реализацию в этом режиме")


async def main():
    args = parse_args()

    services_list = None
    if args.services:
        services_list = [s.strip() for s in args.services.split(",")]

    tester = ApiCoverageTester(
        services=services_list,
        base_host=args.host,
        skip_prepare=args.skip_prepare,
    )

    try:
        if args.ping_only:
            await ping_all(tester)
            return

        await tester.run_all()

        # Вывод сводки
        print("\n" + "=" * 70)
        print("  ITEMS COVERAGE SUMMARY")
        print("=" * 70)
        total_ep = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        for svc_key, result in tester.results.items():
            total_ep += result.endpoints_total
            total_passed += result.endpoints_passed
            total_failed += result.endpoints_failed
            total_skipped += result.endpoints_skipped
            status = "✅" if result.ping_ok else "❌"
            print(f"  {status} {result.name:35s} [{result.endpoints_passed:2d}/{result.endpoints_total:2d}]  "
                  f"failed={result.endpoints_failed}  skipped={result.endpoints_skipped}")
        print(f"\n  {'─'*60}")
        print(f"  TOTAL: {total_passed}/{total_ep} passed, "
              f"{total_failed} failed, {total_skipped} skipped\n")

        # Сводка по недоступным сервисам и их зависимостям
        down_services = [k for k, r in tester.results.items() if not r.ping_ok]
        if down_services:
            print("  🔗 Сервис недоступен → кто от него зависит:")
            # Построим обратный словарь зависимостей
            reverse_deps = {}
            for svc, deps in SERVICE_DEPENDENCIES.items():
                for dep in deps:
                    reverse_deps.setdefault(dep, []).append(svc)
            for svc in down_services:
                affected = reverse_deps.get(svc, [])
                affected_ok = [s for s in affected if s in tester.results and tester.results[s].ping_ok]
                if affected_ok:
                    print(f"    ❌ {svc:25s} → ⚠️  {' '.join(affected_ok)}")
                elif affected:
                    print(f"    ❌ {svc:25s} → 🔴 {' '.join(affected)}")

        # Сохраняем отчёт
        report = tester.generate_report()
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report, encoding="utf-8")
            print(f"  📄 Report saved: {output_path.resolve()}")
        else:
            # Сохраняем в check_result с автоименем
            check_dir = Path("check_result")
            check_dir.mkdir(parents=True, exist_ok=True)
            report_path = check_dir / f"api_coverage_real_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            report_path.write_text(report, encoding="utf-8")
            print(f"  📄 Report saved: {report_path.resolve()}")

    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
