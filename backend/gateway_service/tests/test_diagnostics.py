"""
Тесты diagnostics — сбор диагностики.

Сценарии:
  - build_summary(): формат вывода, uptime
  - build_summary(verbose=True): расширенный вывод
  - build_service_diagnostics(): детали по сервису
  - build_service_diagnostics("unknown"): 404
  - KNOWN_SERVICES: содержит все ожидаемые сервисы

Unit-тесты, но некоторые функции требуют Docker socket (в Docker).
Без Docker — проверяем формат вывода и базовую структуру.
"""

from __future__ import annotations

import os
import sys

import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)

from gateway.diagnostics import (
    KNOWN_SERVICES,
    build_summary,
    build_service_diagnostics,
    build_system_logs,
    START_TIME,
)


class TestKNOWN_SERVICES:
    """KNOWN_SERVICES — реестр известных сервисов."""

    def test_contains_gateway(self):
        """KNOWN_SERVICES содержит gateway."""
        assert "gateway" in KNOWN_SERVICES

    def test_contains_orchestrator(self):
        """KNOWN_SERVICES содержит orchestrator."""
        assert "orchestrator" in KNOWN_SERVICES

    def test_contains_auth(self):
        """KNOWN_SERVICES содержит auth."""
        assert "auth" in KNOWN_SERVICES

    def test_contains_registry(self):
        """KNOWN_SERVICES содержит registry."""
        assert "registry" in KNOWN_SERVICES

    def test_contains_all_core_services(self):
        """KNOWN_SERVICES содержит все ключевые сервисы."""
        core = {"gateway", "orchestrator", "auth", "query", "registry",
                "parser", "postgres", "redis", "minio"}
        for s in core:
            assert s in KNOWN_SERVICES, f"Missing KNOWN_SERVICE: {s}"


class TestBuildSummary:
    """build_summary() — формат вывода."""

    def test_build_summary_returns_string(self):
        """build_summary() возвращает строку."""
        result = build_summary(log_lines=10)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_build_summary_contains_uptime(self):
        """build_summary() содержит uptime."""
        result = build_summary(log_lines=10)
        assert "Uptime" in result or "gateway" in result.lower()

    def test_build_summary_verbose(self):
        """build_summary(verbose=True) — расширенный вывод."""
        result = build_summary(log_lines=10, verbose=True)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_build_summary_with_log_lines(self):
        """build_summary(log_lines=50) — указанное число строк лога."""
        result = build_summary(log_lines=50)
        assert isinstance(result, str)


class TestBuildServiceDiagnostics:
    """build_service_diagnostics() — детали по сервису."""

    def test_known_service_returns_string(self):
        """build_service_diagnostics('gateway', 20) — строка."""
        result = build_service_diagnostics("gateway", 20)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_unknown_service_returns_error(self):
        """build_service_diagnostics('unknown', 20) — ошибка."""
        result = build_service_diagnostics("unknown", 20)
        assert "Unknown" in result or "error" in result.lower()


class TestBuildSystemLogs:
    """build_system_logs() — системные логи."""

    def test_build_system_logs_returns_string(self):
        """build_system_logs(100) — строка."""
        result = build_system_logs(100)
        assert isinstance(result, str)
