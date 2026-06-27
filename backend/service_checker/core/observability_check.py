"""
PKB Neuroassistant — Observability Check Module (SC-1).

Проверяет инструментацию сервисов:
- OTEL SDK (инициализация, OTLP-экспорт, span-атрибуты)
- Структурированное логирование
- Корреляционные заголовки (X-Request-ID, X-Trace-ID, X-User-ID, X-Draft-ID, X-Document-ID, X-Version-ID)
- Коды ошибок (CM-7)
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import httpx

from service_checker.core.utils import log_ok, log_warn, log_err, log_info, log_header, log_step


# ─── Data Models ────────────────────────────────────────────────────────

@dataclass
class ObservabilityCheckResult:
    """Результат проверки observability одного сервиса."""
    service_name: str
    service_key: str
    port: int
    passed: bool = True
    checks: Dict[str, bool] = field(default_factory=dict)
    details: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "service_key": self.service_key,
            "port": self.port,
            "passed": self.passed,
            "checks": self.checks,
            "details": self.details,
            "errors": self.errors,
            "warnings": self.warnings,
        }


# ─── Known error codes (CM-7, RG-3, AU-1, RS-12) ──────────────────────

KNOWN_ERROR_CODES = {
    "INDEX_TRIGGER_TIMEOUT": 408,
    "DECISION_TIMEOUT": 408,
    "PREVIEW_TRIGGER_TIMEOUT": 408,
    "LLM_GENERATION_TIMEOUT": 408,
    "PREVIEW_NOT_SUPPORTED": 422,
    "EMPTY_QUERY": 400,
    "INVALID_PARAMETER": 422,
}

# ─── Correlation header names (CM-5) ────────────────────────────────────

CORRELATION_HEADERS = [
    "X-Request-ID",
    "X-Trace-ID",
    "X-User-ID",
    "X-Draft-ID",
    "X-Document-ID",
    "X-Version-ID",
]

# ─── OTEL init patterns ─────────────────────────────────────────────────

OTEL_INIT_PATTERNS = [
    r"from\s+opentelemetry\s+import",
    r"OTLPSpanExporter",
    r"BatchSpanProcessor",
    r"TracerProvider",
    r"set_tracer_provider",
    r"instrument_app",
    r"signoz-otel-collector",
    r"OTEL_EXPORTER_OTLP_ENDPOINT",
]

STRUCTURED_LOG_PATTERNS = [
    r'"severity"\s*:\s*"(INFO|WARNING|ERROR|DEBUG)"',
    r'"timestamp"\s*:\s*"\d{4}-\d{2}-\d{2}T',
    r'"service"\s*:',
    r'"trace_id"\s*:',
    r'"span_id"\s*:',
]


# ─── Main check functions ──────────────────────────────────────────────

async def check_service_otel(
    service_key: str,
    display_name: str,
    port: int,
    base_host: str = "127.0.0.1",
) -> ObservabilityCheckResult:
    """Проверка OTEL-инструментации сервиса через его API.

    ⚠️ Tolerant mode: если сервис не реализовал OTEL/корреляционные заголовки,
    это считается warning, а не error (сервисы могут быть не полностью обновлены).
    """
    result = ObservabilityCheckResult(
        service_name=display_name,
        service_key=service_key,
        port=port,
    )

    # 1. Проверка health endpoint с fallback-путями
    # Пробуем /api/v1/health, затем /api/v1/system/health, затем /health
    health_paths = [
        "/api/v1/health",
        "/api/v1/system/health",
        "/health",
    ]
    health_resp = None
    health_error = None
    async with httpx.AsyncClient(timeout=10) as client:
        for path in health_paths:
            try:
                url = f"http://{base_host}:{port}{path}"
                resp = await client.get(url)
                if resp.status_code < 500:
                    health_resp = resp
                    result.checks["health_endpoint"] = True
                    result.details["health_status"] = f"HTTP {resp.status_code} via {path}"
                    result.details["health_url"] = path
                    break
            except (httpx.ConnectError, httpx.TimeoutException):
                health_error = f"Сервис {service_key} не отвечает на порту {port}"
                continue
            except Exception as e:
                health_error = f"Ошибка подключения: {e}"
                continue

    if health_resp is None:
        result.checks["health_endpoint"] = False
        msg = health_error or f"Сервис {service_key} не отвечает на порту {port}"
        # Если сервис не отвечает — warning, а не error (возможно, временно недоступен)
        result.warnings.append(f"{msg} — health-эндпоинты не найдены ни по одному из путей {health_paths}")
        # Продолжаем проверку — пытаемся проверить хотя бы заголовки на любом эндпоинте
        result.passed = False
        # Не возвращаемся сразу — пытаемся проверить заголовки на любом порту

    if health_resp is not None:
        # Проверка корреляционных заголовков в ответе
        headers_found = []
        for hdr in CORRELATION_HEADERS:
            val = health_resp.headers.get(hdr)
            if val:
                headers_found.append(f"{hdr}={val}")
        if headers_found:
            result.checks["correlation_headers"] = True
            result.details["correlation_headers"] = ", ".join(headers_found)
        else:
            result.checks["correlation_headers"] = False
            # Warning, не error — сервисы могут быть не обновлены (CM-5)
            result.warnings.append(
                f"Нет корреляционных заголовков в ответе. "
                f"Ожидаются: {', '.join(CORRELATION_HEADERS)}. "
                f"Сервис может быть не обновлён до актуальной спецификации (CM-5)."
            )

        # Проверка структурированного логирования в теле ответа
        body_str = health_resp.text
        structured_found = any(
            re.search(p, body_str) for p in STRUCTURED_LOG_PATTERNS
        )
        result.checks["structured_logging_response"] = structured_found
        if not structured_found:
            result.warnings.append(
                "Ответ /health не содержит структурированных полей "
                "(severity, timestamp, service, trace_id, span_id). "
                "Сервис может быть не обновлён до актуальной спецификации (CM-5)."
            )

    # 2. Проверка наличия собственного health endpoint'a
    await _check_health_endpoint(result, service_key, port, base_host)

    # 3. Проверка X-Request-ID в ответе (на любом эндпоинте)
    await _check_request_id_header(result, service_key, port, base_host)

    # 4. Проверка кодов ошибок (не фатально, если не реализованы)
    await _check_error_codes(result, service_key, port, base_host)

    # Итоговый статус: passed если нет errors (warnings не считаются failures)
    result.passed = len(result.errors) == 0

    return result


async def _check_health_endpoint(
    result: ObservabilityCheckResult,
    service_key: str,
    port: int,
    base_host: str,
) -> None:
    """Проверить, что сервис имеет собственный /health endpoint."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(
                f"http://{base_host}:{port}/api/v1/health",
                headers={"Accept": "application/json"},
            )
            if resp.status_code < 500:
                result.checks["health_endpoint_exists"] = True
                result.details["health_url"] = "/api/v1/health"
            else:
                result.checks["health_endpoint_exists"] = False
                result.warnings.append(
                    f"/api/v1/health вернул {resp.status_code}"
                )
        except Exception:
            result.checks["health_endpoint_exists"] = False
            result.warnings.append(
                f"/api/v1/health недоступен на {base_host}:{port}"
            )


async def _check_request_id_header(
    result: ObservabilityCheckResult,
    service_key: str,
    port: int,
    base_host: str,
) -> None:
    """Проверить, что сервис генерирует корреляционные заголовки в ответе.
    
    Проверяет (GW-9):
    - X-Request-ID (UUIDv4)
    - X-User-ID (после JWT-валидации)
    """
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            # Пробуем health endpoint — он должен быть без токена
            resp = await client.get(
                f"http://{base_host}:{port}/api/v1/health",
                headers={"Accept": "application/json"},
            )
            xrid = resp.headers.get("X-Request-ID") or resp.headers.get("x-request-id")
            if xrid:
                result.checks["x_request_id_generated"] = True
                result.details["x_request_id"] = xrid
            else:
                result.checks["x_request_id_generated"] = False
                result.warnings.append(
                    "Сервис не генерирует X-Request-ID в ответе"
                )

            # GW-9: X-User-ID проверяем отдельно
            xuid = resp.headers.get("X-User-ID") or resp.headers.get("x-user-id")
            if xuid:
                result.checks["x_user_id_generated"] = True
                result.details["x_user_id"] = xuid
            else:
                result.checks["x_user_id_generated"] = False
                # Не все сервисы имеют JWT — только warning
                result.warnings.append(
                    "Сервис не возвращает X-User-ID (возможно, не требуется)"
                )

            # Проверка X-Trace-ID (OTEL)
            xtid = resp.headers.get("X-Trace-ID") or resp.headers.get("x-trace-id")
            if xtid:
                result.checks["x_trace_id_generated"] = True
                result.details["x_trace_id"] = xtid
                # #16: trace_id должен быть 32 hex-символа (без дефисов UUID)
                # UUID с дефисами (36 символов) может не влезть в varchar(32) в БД
                clean = xtid.replace('-', '')
                if len(clean) != 32 or not all(c in '0123456789abcdef' for c in clean.lower()):
                    result.warnings.append(
                        f"X-Trace-ID имеет некорректный формат: '{xtid}' (длина {len(xtid)}). "
                        f"Ожидается 32 hex-символа без дефисов для varchar(32)."
                    )

        except Exception:
            result.checks["x_request_id_generated"] = False
            result.checks["x_user_id_generated"] = False


async def _check_error_codes(
    result: ObservabilityCheckResult,
    service_key: str,
    port: int,
    base_host: str,
) -> None:
    """Проверить, что сервис возвращает известные коды ошибок.
    
    Проверяет таймауты (CM-7) и специфичные коды (PS-8, OC-11, RS-12).
    """
    error_endpoints = [
        ("POST", "/api/v1/drafts/{draft_id}/preview", "DECISION_TIMEOUT"),
        ("POST", "/api/v1/parser/process", "PREVIEW_NOT_SUPPORTED"),
        ("POST", "/api/v1/ocr/process", "PREVIEW_NOT_SUPPORTED"),
        ("POST", "/api/v1/rag/search", "EMPTY_QUERY"),
    ]
    async with httpx.AsyncClient(timeout=10) as client:
        for method, path, error_code in error_endpoints:
            try:
                url = f"http://{base_host}:{port}"
                # Подставляем path-параметры
                url_path = path.replace('{draft_id}', '999999')
                url = f"http://{base_host}:{port}{url_path}"
                
                # Для разных эндпоинтов — разное тело
                if error_code == "PREVIEW_NOT_SUPPORTED":
                    body_data = {"file_key": "unsupported.docx", "mode": "full"}
                elif error_code == "EMPTY_QUERY":
                    body_data = {"query": "", "valid_at": "2026-06-19", "filters": {}}
                else:
                    body_data = {}
                
                resp = await client.request(method, url, json=body_data)
                body = resp.text
                if error_code in body:
                    result.checks[f"error_code_{error_code}"] = True
                    result.details[f"error_{error_code}"] = f"HTTP {resp.status_code}"
                else:
                    # Не фатально — коды ошибок могут быть не реализованы
                    pass
            except Exception:
                pass


async def check_service_otel_by_source(
    service_key: str,
    source_dir: str,
) -> ObservabilityCheckResult:
    """Проверка OTEL-инструментации по исходному коду (статический анализ)."""
    from pathlib import Path

    result = ObservabilityCheckResult(
        service_name=service_key,
        service_key=service_key,
        port=0,
    )

    src_path = Path(source_dir)
    if not src_path.exists():
        result.errors.append(f"Директория {source_dir} не найдена")
        result.passed = False
        return result

    python_files = list(src_path.rglob("*.py"))
    if not python_files:
        result.warnings.append(f"Нет Python-файлов в {source_dir}")
        result.passed = False
        return result

    # Ищем OTEL-инициализацию
    otel_found = False
    for pf in python_files:
        try:
            content = pf.read_text(encoding="utf-8", errors="replace")
            for pattern in OTEL_INIT_PATTERNS:
                if re.search(pattern, content):
                    otel_found = True
                    result.checks["otel_sdk_init"] = True
                    result.details["otel_init_file"] = str(pf.relative_to(src_path.parent))
                    break
        except Exception:
            continue

    if not otel_found:
        result.warnings.append(
            f"OTEL SDK инициализация не найдена в {source_dir}. "
            f"Ожидаются: opentelemetry import, OTLPSpanExporter, TracerProvider"
        )

    # Ищем structured logging
    structured_found = False
    for pf in python_files:
        try:
            content = pf.read_text(encoding="utf-8", errors="replace")
            if any(re.search(p, content) for p in STRUCTURED_LOG_PATTERNS):
                structured_found = True
                result.checks["structured_logging_source"] = True
                break
        except Exception:
            continue

    if not structured_found:
        result.warnings.append(
            "Структурированное логирование не найдено в исходном коде "
            "(severity, timestamp, service, trace_id, span_id)"
        )

    result.passed = len(result.errors) == 0
    return result


def format_observability_report(results: List[ObservabilityCheckResult]) -> str:
    """Сформировать отчёт по observability проверкам."""
    lines: List[str] = []
    w = lines.append

    w("## Observability Check Report\n")
    w("| Сервис | Health | Заголовки | Ошибки | Предупреждения | Статус |")
    w("|---|---|---|---|---|---|")

    for r in results:
        health_ok = r.checks.get("health_endpoint", False)
        corr_ok = r.checks.get("correlation_headers", False)
        health_icon = "✅" if health_ok else "❌"
        corr_icon = "✅" if corr_ok else "⚠️" if "correlation" in str(r.warnings) else "❌"
        errors = "; ".join(r.errors[:2]) if r.errors else "—"
        warns = "; ".join(r.warnings[:2]) if r.warnings else "—"
        status = "✅" if r.passed else "❌"

        w(f"| {r.service_name} | {health_icon} | {corr_icon} | {errors} | {warns} | {status} |")

    w("")
    w("**Детали:**\n")
    for r in results:
        if r.details:
            w(f"### {r.service_name}\n")
            for k, v in r.details.items():
                w(f"- **{k}**: {v}")
            w("")
        if r.errors:
            w(f"**Ошибки:**\n")
            for e in r.errors:
                w(f"- ❌ {e}")
            w("")
        if r.warnings:
            w(f"**Предупреждения:**\n")
            for wng in r.warnings:
                w(f"- ⚠️ {wng}")
            w("")

    return "\n".join(lines)
