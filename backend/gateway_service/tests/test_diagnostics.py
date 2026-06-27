"""
Тесты diagnostics: KNOWN_SERVICES, GATEWAY_START_TIME, build_summary().

Часть тестов интеграционные (требуют Docker/git для полного build_summary).

Unit + интеграционные тесты Gateway.
"""

from __future__ import annotations

import os
import sys

import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)

from gateway.main import GATEWAY_START_TIME
from gateway.diagnostics import KNOWN_SERVICES, build_summary


class TestKnownServices:
    """KNOWN_SERVICES — список известных сервисов."""

    def test_known_services_contains_gateway(self):
        """KNOWN_SERVICES включает 'gateway'."""
        assert "gateway" in KNOWN_SERVICES

    def test_known_services_core_services(self):
        """KNOWN_SERVICES включает core-сервисы."""
        for svc in ("auth", "orchestrator", "registry", "query"):
            assert svc in KNOWN_SERVICES, f"Missing core service: {svc}"

    def test_known_services_infrastructure(self):
        """KNOWN_SERVICES включает инфраструктуру."""
        for svc in ("redis", "postgres"):
            assert svc in KNOWN_SERVICES, f"Missing infra: {svc}"

    def test_known_services_rag_and_converter(self):
        """KNOWN_SERVICES включает rag и converter (c дефисами)."""
        for svc in ("rag-builder", "rag-search", "converter-validator"):
            assert svc in KNOWN_SERVICES, f"Missing: {svc}"


class TestStartTime:
    """GATEWAY_START_TIME — время старта Gateway."""

    def test_start_time_is_positive(self):
        """GATEWAY_START_TIME > 0."""
        assert GATEWAY_START_TIME > 0

    def test_start_time_is_recent(self):
        """GATEWAY_START_TIME не в будущем."""
        import time
        assert GATEWAY_START_TIME <= time.time() + 1


class TestBuildSummaryIntegration:
    """build_summary — интеграционные тесты (Docker/git)."""

    def test_build_summary_returns_string(self):
        """build_summary() возвращает строку."""
        result = build_summary(log_lines=5, verbose=False)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_build_summary_verbose(self):
        """build_summary(verbose=True) длиннее краткой версии."""
        brief = build_summary(log_lines=5, verbose=False)
        verbose = build_summary(log_lines=5, verbose=True)
        assert len(verbose) >= len(brief)

    def test_build_summary_contains_diagnostics_header(self):
        """build_summary содержит заголовок диагностики."""
        result = build_summary(log_lines=5, verbose=False)
        assert "Gateway" in result or "gateway" in result or "Diagnostics" in result
