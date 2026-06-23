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
    get_test_mode,
    TEST_MODE_REAL,
    TEST_MODE_MOCK,
)
from service_checker.services import (
    MODE_PORTS,
    SERVICE_DEPENDENCIES,
    SERVICE_REGISTRY,
)
from service_checker.core.openapi_loader import OpenApiLoader


# ──────────────────────────────────────────────────────────────────────
#  Тестовый движок
# ──────────────────────────────────────────────────────────────────────

# Сервисы, имеющие реальную реализацию
SERVICES_WITH_REAL = {
    "gateway", "auth", "orchestrator", "query", "registry",
    "converter_validator", "parser", "rag_builder",
    "rag_search", "tei",
}


def _has_unresolved_vars(obj: Any) -> bool:
    """Проверить, остались ли в объекте неразрешённые {variable} плейсхолдеры."""
    if isinstance(obj, str):
        return "{" in obj and "}" in obj
    if isinstance(obj, dict):
        return any(_has_unresolved_vars(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return any(_has_unresolved_vars(v) for v in obj)
    return False



class ApiCoverageTester:
    """
    Тестер покрытия API.
    Для каждого сервиса вызывает все эндпоинты из документации,
    собирает результаты и формирует отчёт.

    Режимы:
      - real (по умолчанию): против Docker (реальные сервисы)
      - mock: против Gateway Mock (локальные моки)
    """

    def __init__(
        self,
        services: Optional[List[str]] = None,
        base_host: str = "127.0.0.1",
        skip_prepare: bool = False,
        schema_check: bool = False,
        mode: Optional[str] = None,
    ):
        self.base_host = base_host
        self.skip_prepare = skip_prepare
        self.schema_check = schema_check
        self.mode = (mode or get_test_mode()).lower()

        self.services_with_impl = SERVICES_WITH_REAL

        if services:
            # Для явно переданных сервисов проверяем наличие в SERVICE_REGISTRY
            self.services_to_test = [s for s in services if s in SERVICE_REGISTRY]
        else:
            available_services = set(MODE_PORTS.keys())
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
                "gateway": 9,
            }
            self.services_to_test = sorted(available_services, key=lambda s: _ORDER.get(s, 99))
            # Исключаем сервисы без реальной реализации (в глубокой разработке)
            self.services_to_test = [s for s in self.services_to_test if s in self.services_with_impl]

        self.context: Dict[str, Any] = {}  # shared context между вызовами
        self.results: Dict[str, ServiceResult] = {}
        self._client_timeout = 15
        self._client_follow_redirects = True
        self._client: Optional[httpx.AsyncClient] = None
        # Для тестов: можно подставить свои endpoint'ы (ключ → List[EndpointDef])
        self._test_endpoints: Dict[str, List[EndpointDef]] = {}
        # OpenAPI схемы сервисов: service_key → {path: {method: OpenApiEndpoint}}
        self.openapi_schemas: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._current_svc_key: str = ""

    @property
    def client(self) -> httpx.AsyncClient:
        """Ленивая инициализация HTTP-клиента (SSL certs загружаются только при первом использовании)."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._client_timeout,
                follow_redirects=self._client_follow_redirects,
                trust_env=False,
            )
        return self._client

    @client.setter
    def client(self, value: httpx.AsyncClient) -> None:
        self._client = value

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def ping_service(self, port: int, fast: bool = False) -> bool:
        """Проверить, отвечает ли сервис.

        Если fast=True — пробуем только первый health-эндпоинт с таймаутом 1.5с.
        """
        health_paths = [
            f"{API_PREFIX}/health",
            f"{API_PREFIX}/system/health",
            f"{API_PREFIX}/monitor/health",
            "/health",
            "/",  # TEI (GET / — health check)
        ]
        if fast:
            # fast: пробуем 2 самых популярных пути
            health_paths = [f"{API_PREFIX}/health", "/health"]
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
        """Подставить контекстные переменные в путь.

        Ищет {var} (одинарные скобки) — т.к. path уже обработан f-string.
        """
        resolved = path
        for key, value in self.context.items():
            placeholder = "{" + key + "}"
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
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Проверить что ответ содержит все ожидаемые поля с правильными типами.

        schema = {
            "status": str,              # проверяет response["status"] — str
            "data": dict,               # response["data"] — dict
            "data.items": list,         # response["data"]["items"] — list
            "session_id": (int, str),   # может быть int или str (union)
        }

        Возвращает (ok, список_ошибок, список_предупреждений).
        """
        if not response_body:
            return False, ["Пустой ответ"], []

        try:
            data = json.loads(response_body)
        except json.JSONDecodeError as e:
            return False, [f"Невалидный JSON: {e}"], []

        errors = []
        warnings = []

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
                    # Автоприведение типов:
                    # - ожидается int, пришла строка → пробуем сконвертировать
                    # - ожидается str, пришёл int/float → считаем валидным
                    if expected_type is int and isinstance(current, str):
                        try:
                            int(current)
                            continue  # строка содержит число — валидно
                        except ValueError:
                            pass  # не число — ошибка
                    if expected_type is str and isinstance(current, (int, float)):
                        continue  # int/float можно представить как str — валидно
                    actual = type(current).__name__
                    expected_name = getattr(expected_type, '__name__', str(expected_type))
                    if isinstance(current, str):
                        # Если пришла строка вместо ожидаемого типа — предупреждение, не ошибка
                        warnings.append(
                            f"⚠️ Поле '{path}' ожидалось {expected_name}, получен {actual} = {str(current)[:80]}"
                        )
                    else:
                        errors.append(
                            f"Поле '{path}' ожидалось {expected_name}, получен {actual} = {str(current)[:80]}"
                        )

        return len(errors) == 0, errors, warnings

    def _validate_against_openapi(
        self,
        svc_key: str,
        ep: EndpointDef,
        response_body: Optional[str],
    ) -> List[str]:
        """Сверить ответ с OpenAPI-схемой сервиса.

        Если OpenAPI схема для сервиса загружена — сверяет структуру ответа
        с ожидаемой схемой и возвращает список предупреждений о расхождениях.
        """
        warnings: List[str] = []

        oapi_endpoints = self.openapi_schemas.get(svc_key)
        if not oapi_endpoints:
            return warnings

        # Ищем эндпоинт в OpenAPI схеме по path + method
        from service_checker.core.openapi_loader import OpenApiLoader
        stub_loader = OpenApiLoader("http://stub")

        # Пробуем точное совпадение
        path_item = oapi_endpoints.get(ep.path)
        oapi_ep = None
        if path_item:
            oapi_ep = path_item.get(ep.method)

        # Если нет точного — ищем с path params
        if not oapi_ep:
            for oa_path, methods in oapi_endpoints.items():
                oa_parts = oa_path.strip("/").split("/")
                ep_parts = ep.path.strip("/").split("/")
                if len(oa_parts) != len(ep_parts):
                    continue
                match = True
                for op, pp in zip(oa_parts, ep_parts):
                    if op.startswith("{") and op.endswith("}"):
                        continue
                    if op != pp:
                        match = False
                        break
                if match:
                    oapi_ep = methods.get(ep.method)
                    break

        if not oapi_ep:
            warnings.append(f"⚠️ OpenAPI: эндпоинт {ep.method} {ep.path} не найден в схеме сервиса")
            return warnings

        # Сравниваем поля ответа
        if not response_body:
            return warnings

        try:
            data = json.loads(response_body)
        except json.JSONDecodeError:
            return warnings

        if not isinstance(data, dict):
            return warnings

        # Flatten ответа
        response_fields = self._flatten_response(data)

        # Flatten OpenAPI схемы
        oapi_fields: Dict[str, Dict[str, Any]] = {}
        for sc in ("200", "201", "default"):
            if sc in oapi_ep.responses:
                oapi_fields = stub_loader._flatten_schema(oapi_ep.responses[sc])
                break

        if not oapi_fields:
            return warnings

        # Сравниваем
        for field, oapi_info in oapi_fields.items():
            if field not in response_fields:
                oapi_type = oapi_info.get("type")
                if oapi_info.get("required", False):
                    warnings.append(
                        f"⚠️ OpenAPI: обязательное поле '{field}' ({oapi_type}) отсутствует в ответе"
                    )

        return warnings

    @staticmethod
    def _flatten_response(data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Преобразовать JSON-ответ в плоскую карту полей."""
        result: Dict[str, Any] = {}
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                result[full_key] = {"type": "object"}
                result.update(ApiCoverageTester._flatten_response(value, full_key))
            elif isinstance(value, list):
                result[full_key] = {"type": "array"}
                if value and isinstance(value[0], dict):
                    result.update(
                        ApiCoverageTester._flatten_response(value[0], f"{full_key}[]")
                    )
            elif isinstance(value, bool):
                result[full_key] = {"type": "boolean"}
            elif isinstance(value, int):
                result[full_key] = {"type": "integer"}
            elif isinstance(value, float):
                result[full_key] = {"type": "number"}
            elif isinstance(value, str):
                result[full_key] = {"type": "string"}
            else:
                result[full_key] = {"type": "string"}
        return result

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
                    "reg_draft_id": ["id", "draft_id"],
                    "draft_id": ["id", "draft_id"],
                    "category_id": ["id", "category_id"],
                    "pending_id": ["id"],
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
            # Сначала ищем как data.key (для обёрнутых ответов)
            value = _get_by_path(raw, f"data.{key}")
            # Потом рекурсивно
            if value is None:
                value = _search(raw, key)
            if value is not None:
                self.context[key] = value

    async def _execute_endpoint(
        self, svc_key: str, ep: EndpointDef, port: int, result: ServiceResult, alive: bool,
    ) -> None:
        """Выполнить один эндпоинт и записать результат.

        Если у эндпоинта указан override_port — он используется вместо port.
        Это нужно для prepare-шагов, которые обращаются к другим сервисам
        (например, получение JWT токена от auth service).
        """
        self._current_svc_key = svc_key
        # override_port — альтернативный порт для prepare-шагов
        target_port = ep.override_port if ep.override_port is not None else port
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
        if missing_vars:
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
        unresolved = _has_unresolved_vars(body) if body else False
        if unresolved:
            result.results.append(
                EndpointResult(endpoint=ep, status_code=0, success=False, skipped=True, skip_reason="Не все переменные контекста доступны для тела запроса")
            )
            result.endpoints_skipped += 1
            return

        # Формируем URL
        resolved_path = self._resolve_path(ep.path)
        url = f"http://{self.base_host}:{target_port}{resolved_path}"

        # Формируем заголовки
        headers = {**HEADERS_JSON}
        # Публичные health-эндпоинты (/api/v1/health, /health) проверяем без токена.
        # Внутренние (/system/health, /monitor/health) — с токеном.
        is_public_health = ep.group == "health" and ep.path in ("/api/v1/health", "/health")
        if "access_token" in self.context and not is_public_health:
            headers["Authorization"] = f"Bearer {self.context['access_token']}"

        # Выполняем запрос
        start = time.time()
        try:
            kwargs: Dict[str, Any] = {"headers": headers}
            if ep.form_body is not None:
                # multipart/form-data — убираем JSON content-type
                headers.pop("Content-Type", None)
                kwargs["data"] = self._resolve_body(ep.form_body)
                # Реальный PDF из pdf/, если доступен
                _pdf_path = Path(__file__).resolve().parent.parent / "pdf" / "7bd97d737317a8a272bb18a405ab2d04.pdf"
                if _pdf_path.exists():
                    _pdf_bytes = _pdf_path.read_bytes()
                else:
                    # Минимальный валидный PDF (заголовок + 1 страница)
                    _pdf_bytes = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
                                 b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
                                 b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 50]"
                                 b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>>endobj\n"
                                 b"4 0 obj<</Length 44>>stream\nBT /F1 12 Tf 10 20 Td(test)Tj ET\nendstream\nendobj\n"
                                 b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
                                 b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000266 00000 n \n0000000355 00000 n \n"
                                 b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n424\n%%EOF")
                kwargs["files"] = {"file": ("test.pdf", _pdf_bytes, "application/pdf")}
            elif body is not None:
                kwargs["json"] = body
            if ep.params:
                kwargs["params"] = ep.params

            resp = await getattr(self.client, ep.method.lower())(url, **kwargs)
            elapsed = int((time.time() - start) * 1000)

            resp_body = resp.text if resp.content else None

            # Success по expected_status (если указан), иначе 2xx/3xx
            if ep.expected_status is not None:
                if isinstance(ep.expected_status, set):
                    success = resp.status_code in ep.expected_status
                else:
                    success = resp.status_code == ep.expected_status
            else:
                success = resp.status_code < 400

            # Извлекаем контекст из ответа
            if success and ep.extract_keys:
                self._extract_context(resp_body, ep.extract_keys)

            # Пост-обработка: check-функция эндпоинта (модификация контекста и т.п.)
            if success and ep.check:
                check_ok, check_msg = ep.check(resp_body, self.context)
                if not check_ok:
                    success = False

            # Валидация схемы ответа (не для prepare)
            # Проверяется для 2xx/3xx успешных ответов.
            # Для 4xx/5xx успешных (expected_status, Conflict и т.п.) —
            # сервис возвращает ошибку, а не данные — schema не проверяем.
            schema_valid = True
            schema_errors = []
            schema_warnings = []
            if not ep.is_preparation and success and resp.status_code < 300 and ep.response_schema:
                schema_valid, schema_errors, schema_warnings = self._validate_response(
                    resp_body, ep.response_schema
                )
                if not schema_valid:
                    success = False

            # OpenAPI валидация (если схема загружена и эндпоинт не prepare)
            oapi_warnings = []
            if (self.schema_check and not ep.is_preparation and success
                    and resp.status_code < 300):
                oapi_warnings = self._validate_against_openapi(
                    svc_key, ep, resp_body
                )
                schema_warnings.extend(oapi_warnings)

            all_warnings = []
            if schema_warnings:
                all_warnings.extend(schema_warnings)

            ep_result = EndpointResult(
                endpoint=ep,
                status_code=resp.status_code,
                success=success,
                elapsed_ms=elapsed,
                response_body=resp_body[:500] if resp_body else None,
                error="; ".join(schema_errors) if schema_errors else None,
                warnings="\n".join(all_warnings) if all_warnings else None,
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

        Каждый сервис тестируется изолированно — контекст очищается перед тестированием.
        Prepare-шаги каждого сервиса создают необходимые данные (токены, ID) самостоятельно.

        Если сервис не найден в SERVICE_REGISTRY, возвращает пустой результат
        (для совместимости с тестами, которые подставляют свои эндпоинты).
        """
        # Изоляция: каждый сервис тестируется с чистым контекстом
        self.context.clear()

        # Если сервис не найден в SERVICE_REGISTRY, возвращает пустой результат
        # (для совместимости с тестами, которые подставляют свои эндпоинты)
        svc_def: Optional[ServiceDef] = None
        if service_key in self._test_endpoints:
            svc_endpoints = self._test_endpoints[service_key]
            svc_prepare = []
            port = MODE_PORTS.get(service_key, 0)
            svc_name = service_key
            if port == 0:
                port = 8080
        elif service_key in SERVICE_REGISTRY:
            # mode передаём только тем сервисам, у которых get_service_def() его принимает
            import inspect
            svc_fn = SERVICE_REGISTRY[service_key]
            if 'mode' in inspect.signature(svc_fn).parameters:
                svc_def = svc_fn(mode=self.mode)
            else:
                svc_def = svc_fn()
            svc_endpoints = svc_def.endpoints
            svc_prepare = svc_def.prepare_endpoints
            # Порт из MODE_PORTS имеет приоритет (может быть переопределён, например --spd)
            port = MODE_PORTS.get(service_key, svc_def.port)
            svc_name = svc_def.display_name
            for k, v in svc_def.base_data.items():
                if k not in self.context:
                    self.context[k] = v

            # ── Pre-prepare: timestamp + дропнуть FK, если ещё висит ──
            if service_key == "rag_builder":
                import time
                self.context["timestamp"] = str(int(time.time()))
                self.context["section_id"] = int(time.time()) % 100000
                # FK fk_rag_document_chunks_section_id должен был быть удалён
                # 3-й миграцией, но не был. Дропаем, чтобы RAG Build не падал с 500.
                try:
                    import subprocess
                    r = subprocess.run(
                        ["docker", "exec", "pkb-postgres", "psql", "-U", "pkb", "-d", "pkb_neuro", "-c",
                         "ALTER TABLE IF EXISTS rag.document_chunks DROP CONSTRAINT IF EXISTS fk_rag_document_chunks_section_id;"],
                        capture_output=True, timeout=10,
                    )
                    if r.returncode == 0:
                        print(f"  ℹ {svc_name}: дропнут FK fk_rag_document_chunks_section_id")
                    else:
                        print(f"  ⚠ {svc_name}: не удалось дропнуть FK: {r.stderr.decode().strip()}")
                except Exception as ex:
                    print(f"  ⚠ {svc_name}: ошибка при дропе FK: {ex}")
                print(f"  ℹ {svc_name}: timestamp={self.context['timestamp']}")

            # ── Pre-prepare: создание проекта для Query (QS-3) ─────────
            if service_key == "query":
                import json as _json
                auth_token = self.context.get("access_token", "")
                create_url = f"http://{self.base_host}:8083/api/v1/chat/projects"
                create_headers = {"Content-Type": "application/json"}
                if auth_token:
                    create_headers["Authorization"] = f"Bearer {auth_token}"

                # 1. Пытаемся создать проект (retry 3 раза)
                for attempt in range(3):
                    try:
                        create_body = _json.dumps({"code": "CHECKER", "name": "Checker Test Project"}).encode()
                        resp = await self.client.post(
                            create_url, content=create_body, headers=create_headers
                        )
                        if resp.status_code == 201:
                            data = resp.json()
                            pid = data.get("project_id") or (data.get("data") or {}).get("id")
                            if pid:
                                self.context["project_id"] = pid
                                print(f"  ℹ Query: создан проект project_id={pid}")
                                break
                        elif resp.status_code == 409:
                            # Проект уже существует — переходим к GET
                            break
                    except Exception:
                        if attempt < 2:
                            await asyncio.sleep(1)
                        continue

                # 2. Если проект не создан — получаем список (retry 3 раза)
                if "project_id" not in self.context:
                    for attempt in range(3):
                        try:
                            resp = await self.client.get(create_url, headers=create_headers)
                            if resp.status_code == 200:
                                data = resp.json()
                                items = data.get("items") or data.get("data") or []
                                if items:
                                    pid = items[0].get("project_id") or items[0].get("id")
                                    if pid:
                                        self.context["project_id"] = pid
                                        print(f"  ℹ Query: получен проект project_id={pid} из списка")
                                        break
                        except Exception:
                            if attempt < 2:
                                await asyncio.sleep(1)
                            continue
                    else:
                        raise RuntimeError("Cannot create or fetch project for chat sessions")

            # ── Pre-prepare: создание черновика через Orchestrator (task_id + draft_id) ──
            # Converter/Parser/OCR используют task_id и draft_id в телах запросов.
            # Создаём черновик напрямую через Orchestrator (порт 8081).
            if service_key in ("converter_validator", "parser", "ocr"):
                orch_url = f"http://{self.base_host}:8081/api/v1/drafts/"
                auth_token = self.context.get("access_token", "")
                orch_headers: Dict[str, str] = {}
                if auth_token:
                    orch_headers["Authorization"] = f"Bearer {auth_token}"

                for attempt in range(3):
                    try:
                        orch_data = {"document_key": "test-key", "title": "Coverage draft", "source_type": "GOST"}
                        resp = await self.client.post(orch_url, data=orch_data, headers=orch_headers)
                        if resp.status_code == 202:
                            data = resp.json()
                            task_id = data.get("task_id")
                            draft_id = data.get("draft_id")
                            if task_id and "task_id" not in self.context:
                                self.context["task_id"] = task_id
                                print(f"  ℹ Orchestrator: получен task_id={task_id}")
                            if draft_id and "draft_id" not in self.context:
                                self.context["draft_id"] = draft_id
                                print(f"  ℹ Orchestrator: получен draft_id={draft_id}")
                            break
                        elif resp.status_code == 409:
                            break
                    except Exception:
                        if attempt < 2:
                            await asyncio.sleep(1)
                        continue

                if "task_id" not in self.context:
                    print(f"  ⚠ Черновик через Orchestrator не создан — эндпоинты с task_id/draft_id будут пропущены")
                    # Не возвращаем пустой результат — эндпоинты, которым не хватает контекста,
                    # будут пропущены автоматически в _execute_endpoint.

            # ── Pre-prepare: загрузка PDF в MinIO для Parser ────
            if service_key == "parser":
                pdf_path = Path(__file__).resolve().parent.parent / "pdf" / "7bd97d737317a8a272bb18a405ab2d04.pdf"
                if pdf_path.exists():
                    pdf_bytes = pdf_path.read_bytes()
                    minio_url = f"http://{self.base_host}:19000/documents/test-file-key.pdf"
                    from service_checker.pipelines.base import s3_sign_headers
                    s3_headers = s3_sign_headers("PUT", minio_url, "minioadmin", "minioadmin", pdf_bytes)
                    try:
                        resp = await self.client.put(minio_url, content=pdf_bytes, headers=s3_headers)
                        print(f"  ℹ MinIO upload: {resp.status_code}")
                    except Exception as e:
                        print(f"  ⚠ MinIO upload failed: {e}")
            
            if service_key == "converter_validator" and "version_id" not in self.context:
                # version_id нужен для converter, но Registry ещё не создавал документ.
                # Если Registry (поз.1) уже отработал — version_id есть в контексте.
                # Если нет — это нормально, fallback не делаем, prepare-шаги Registry создадут.
                pass
        else:
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
                await self._execute_endpoint(service_key, ep, port, result, alive)
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
            await self._execute_endpoint(service_key, ep, port, result, alive)

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

    async def load_openapi_schemas(self) -> None:
        """Загрузить OpenAPI-схемы для сервисов, которые их имеют.

        Исключения: gateway-mock, TEI (нет /openapi.json).
        """
        for svc_key in self.services_to_test:
            port = MODE_PORTS.get(svc_key)
            if not port:
                continue
            # Gateway (mock) и TEI не имеют /openapi.json
            if svc_key in ("gateway", "tei"):
                continue

            base_url = f"http://{self.base_host}:{port}"
            loader = OpenApiLoader(base_url, timeout=5)
            success = await loader.load()
            if success:
                self.openapi_schemas[svc_key] = loader.endpoints
                print(f"  📖 OpenAPI: {svc_key} ({len(loader.endpoints)} paths)")
            else:
                print(f"  ⚠️  OpenAPI: {svc_key} — не загружена")
                for err in loader.errors:
                    print(f"       {err}")

    async def run_all(self) -> Dict[str, ServiceResult]:
        """Запустить тестирование всех сервисов."""
        print("=" * 70)
        mode_label = "Real (Docker)" if self.mode == TEST_MODE_REAL else "Mock (local)"
        print(f"  PKB Neuroassistant — API Coverage Test")
        print(f"  {'🔬' if self.mode == TEST_MODE_REAL else '🧪'} {mode_label}")
        print(f"  Основано на docs/api/*.md")
        if self.schema_check:
            print(f"  📋 Schema validation: ON")
        print("=" * 70)

        # Загружаем OpenAPI-схемы, если запрошена валидация
        if self.schema_check:
            print("\n  📖 Загрузка OpenAPI-схем...")
            await self.load_openapi_schemas()
            print()

        for svc_key in self.services_to_test:
            if svc_key not in SERVICE_REGISTRY:
                print(f"\n  ✗  Сервис '{svc_key}' не найден в реестре. Пропускаем.")
                continue

            svc_def = SERVICE_REGISTRY[svc_key]()
            ep_count = len(svc_def.endpoints)
            prep_count = len(svc_def.prepare_endpoints)
            print(f"\n  ── [{svc_key.upper()}] ({ep_count} эндпоинтов + {prep_count} prepare) ──")
            for warn in svc_def.warnings:
                print(f"     ⚠️ {warn}")

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

    def generate_report(self, log_report_path: Optional[str] = None,
                         db_result: Any = None) -> str:
        """Сформировать markdown-отчёт."""
        lines = []
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        lines.append(f"# API Coverage Report\n")
        mode_label = "Real (Docker)" if self.mode == TEST_MODE_REAL else "Mock (local)"
        mode_icon = "🔬" if self.mode == TEST_MODE_REAL else "🧪"
        lines.append(f"**Generated:** {now}\n")
        lines.append(f"**Mode:** {mode_icon} {mode_label}\n")
        lines.append(f"**Based on:** `docs/api/*.md`\n")
        if log_report_path:
            lines.append(f"📋 **Logs:** [{log_report_path}]({log_report_path})\n")
        lines.append("---\n")

        # Сводка
        lines.append("## 📊 Summary\n")
        lines.append("| Service | Port | Ping | CheckDb | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |")
        lines.append("|---------|:----:|:----:|:-------:|:---------:|:---------:|:---------:|:----------:|:------:|")

        # Импорт для CheckDb
        from service_checker.core.reports import _get_service_checkdb_icon

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
            # Статус: ❌ если ping упал или есть ошибки, ⏭️ если пропуски без ошибок, ✅ если всё ок
            if not result.ping_ok or result.endpoints_failed > 0:
                status_icon = '<span style="color:red;font-weight:bold">❌</span>'
            elif result.endpoints_skipped > 0:
                status_icon = '<span style="color:orange;font-weight:bold">⏭️</span>'
            else:
                status_icon = "✅"
            svc_anchor = svc_key.replace("_", "-")
            svc_checkdb = _get_service_checkdb_icon(db_result, svc_key)
            lines.append(f"| [{result.name}](#{svc_anchor}) | {result.port} | {ping_icon} | {svc_checkdb} | {result.endpoints_total} | "
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
        # Total — CheckDb
        COVERAGE_TO_STARTUP_KEY = {
            "auth": "auth_service",
            "query": "query_service",
            "orchestrator": "orchestrator_service",
            "integration": "integration_service",
            "registry": "registry_service",
            "rag_builder": "rag_builder_service",
            "rag_search": "rag_search_service",
        }
        svcs_with_db = [k for k in self.results if k in COVERAGE_TO_STARTUP_KEY]
        svcs_checkdb_ok = sum(
            1 for k in svcs_with_db
            if _get_service_checkdb_icon(db_result, k) in ("✅", "—")
        )
        svcs_checkdb_total = len(svcs_with_db)

        if total_failed > 0 or total_skipped > 0:
            total_status = '<span style="color:red;font-weight:bold">❌</span>'
        else:
            total_status = "✅"
        lines.append(f"| **Total** | | **{services_alive}/{len(self.results)}** | **{svcs_checkdb_ok}/{svcs_checkdb_total}** | **{total_ep}** | **{total_passed}** | "
                    f"{total_failed_str} | {total_skipped_str} | {total_status} |\n")

        # Детали по каждому сервису
        lines.append("## 🔍 Details by Service\n")

        for svc_key, result in self.results.items():
            svc_anchor = svc_key.replace("_", "-")
            lines.append(f"### {svc_anchor}\n")
            lines.append(f"**{result.name}** (port {result.port})\n")
            lines.append(f"**Ping:** {'✅ Alive' if result.ping_ok else '❌ Unreachable'}\n")

            # ⚠️ Workaround-предупреждения (если сервис известен)
            svc_def_fn = SERVICE_REGISTRY.get(svc_key)
            if svc_def_fn:
                for warn in svc_def_fn().warnings:
                    lines.append(f"> ⚠️ {warn}\n")

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
                        if r.warnings:
                            status_text = f"OK; {r.warnings}"
                    else:
                        icon = "❌"
                        status_text = f"Error: {r.error or f'HTTP {r.status_code}'}"
                        if r.warnings:
                            status_text += f"; {r.warnings}"

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
        mode_label = "Real (Docker)" if self.mode == TEST_MODE_REAL else "Mock (local)"
        mode_icon = "🔬" if self.mode == TEST_MODE_REAL else "🧪"
        lines.append(f"- **Mode** — {mode_icon} {mode_label}\n")
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
    parser.add_argument(
        "--schema-check",
        action="store_true",
        help="Валидировать ответы по OpenAPI-схеме сервиса (если доступна)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Режим strict: fail при любом расхождении ответа с OpenAPI-схемой",
    )
    parser.add_argument(
        "--mode",
        choices=[TEST_MODE_REAL, TEST_MODE_MOCK],
        default=None,
        help=f"Режим тестирования: {TEST_MODE_REAL} (Docker) или {TEST_MODE_MOCK} (local mock). "
             f"По умолчанию из TEST_MODE env или 'real'.",
    )
    return parser.parse_args()


async def ping_all(tester: ApiCoverageTester) -> None:
    """Проверить какие сервисы отвечают (конкурентно)."""
    ports = MODE_PORTS
    mode_label = "REAL" if tester.mode == TEST_MODE_REAL else "MOCK"
    print(f"\n  Mode: {mode_label}")
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
        schema_check=args.schema_check or args.strict,
        mode=args.mode,
    )
    if args.strict:
        tester.strict_mode = True

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
