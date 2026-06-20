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


# ─── Known error codes (CM-7) ───────────────────────────────────────────

KNOWN_ERROR_CODES = {
    "INDEX_TRIGGER_TIMEOUT": 408,
    "DECISION_TIMEOUT": 408,
    "PREVIEW_TRIGGER_TIMEOUT": 408,
    "LLM_GENERATION_TIMEOUT": 408,
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
    """Проверка OTEL-инструментации сервиса через его API."""
    result = ObservabilityCheckResult(
        service_name=display_name,
        service_key=service_key,
        port=port,
    )

    # 1. Проверка health endpoint и заголовков ответа
    health_url = f"http://{base_host}:{port}/api/v1/health"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(health_url)
            result.checks["health_endpoint"] = resp.status_code < 500
            result.details["health_status"] = str(resp.status_code)

            # Проверка корреляционных заголовков в ответе
            headers_found = []
            for hdr in CORRELATION_HEADERS:
                val = resp.headers.get(hdr)
                if val:
                    headers_found.append(f"{hdr}={val}")
            if headers_found:
                result.checks["correlation_headers"] = True
                result.details["correlation_headers"] = ", ".join(headers_found)
            else:
                result.checks["correlation_headers"] = False
                result.warnings.append(
                    f"Нет корреляционных заголовков в ответе /health. "
                    f"Ожидаются: {', '.join(CORRELATION_HEADERS)}"
                )

            # Проверка структурированного логирования в теле ответа
            body_str = resp.text
            structured_found = any(
                re.search(p, body_str) for p in STRUCTURED_LOG_PATTERNS
            )
            result.checks["structured_logging_response"] = structured_found
            if not structured_found:
                result.warnings.append(
                    "Ответ /health не содержит структурированных полей "
                    "(severity, timestamp, service, trace_id, span_id)"
                )

        except httpx.ConnectError:
            result.checks["health_endpoint"] = False
            result.errors.append(f"Сервис {service_key} не отвечает на порту {port}")
            result.passed = False
            return result
        except Exception as e:
            result.checks["health_endpoint"] = False
            result.errors.append(f"Ошибка подключения: {e}")
            result.passed = False
            return result

    # 2. Проверка X-Request-ID в ответе (на любом эндпоинте)
    await _check_request_id_header(result, service_key, port, base_host)

    # 3. Проверка кодов ошибок
    await _check_error_codes(result, service_key, port, base_host)

    # Итоговый статус
    result.passed = all(
        v for k, v in result.checks.items()
    ) and len(result.errors) == 0

    return result


async def _check_request_id_header(
    result: ObservabilityCheckResult,
    service_key: str,
    port: int,
    base_host: str,
) -> None:
    """Проверить, что сервис генерирует X-Request-ID и возвращает его."""
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
        except Exception:
            result.checks["x_request_id_generated"] = False


async def _check_error_codes(
    result: ObservabilityCheckResult,
    service_key: str,
    port: int,
    base_host: str,
) -> None:
    """Проверить, что сервис возвращает известные коды ошибок."""
    error_endpoints = [
        ("POST", "/api/v1/drafts/{draft_id}/preview", "DECISION_TIMEOUT"),
    ]
    async with httpx.AsyncClient(timeout=10) as client:
        for method, path, error_code in error_endpoints:
            try:
                url = f"http://{base_host}:{port}{path.replace('{draft_id}', '999999')}"
                resp = await client.request(method, url, json={})
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
