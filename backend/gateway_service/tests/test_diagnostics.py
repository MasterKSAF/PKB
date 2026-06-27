"""
Tests for diagnostics module.

ВНИМАНИЕ: Большинство функций диагностики требуют Docker, git, и системного доступа.
Эти тесты — интеграционные, запускаются только при наличии окружения.

Для локального запуска проверяем только KNOWN_SERVICES и базовую структуру.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


class TestKnownServices:
    """KNOWN_SERVICES содержит все ожидаемые сервисы."""

    def test_known_services_contains_gateway(self):
        """KNOWN_SERVICES включает gateway."""
        from gateway.diagnostics import KNOWN_SERVICES
        assert "gateway" in KNOWN_SERVICES

    def test_known_services_core_services(self):
        """KNOWN_SERVICES включает core-сервисы."""
        from gateway.diagnostics import KNOWN_SERVICES
        core = {"auth", "orchestrator", "registry", "query", "parser"}
        assert core.issubset(KNOWN_SERVICES)

    def test_known_services_infrastructure(self):
        """KNOWN_SERVICES включает инфраструктурные сервисы."""
        from gateway.diagnostics import KNOWN_SERVICES
        infra = {"postgres", "redis", "minio"}
        assert infra.issubset(KNOWN_SERVICES)

    def test_known_services_rag_and_converter(self):
        """KNOWN_SERVICES включает rag-builder, rag-search, converter-validator."""
        from gateway.diagnostics import KNOWN_SERVICES
        extra = {"rag-builder", "rag-search", "converter-validator"}
        assert extra.issubset(KNOWN_SERVICES)


class TestStartTime:
    """START_TIME — глобальная метка времени."""

    def test_start_time_is_positive(self):
        """START_TIME > 0 (timestamp)."""
        from gateway.diagnostics import START_TIME
        assert START_TIME > 0

    def test_start_time_is_recent(self):
        """START_TIME — в пределах разумного от сейчас."""
        import time
        from gateway.diagnostics import START_TIME
        # Не более 1 часа назад (для теста)
        assert time.time() - START_TIME < 3600


class TestBuildSummaryIntegration:
    """Интеграционные тесты build_summary — только с реальной системой.

    Пропускаются, если Docker недоступен.
    """

    def test_build_summary_returns_string(self):
        """build_summary() возвращает строку (даже без Docker)."""
        from gateway.diagnostics import build_summary
        result = build_summary(log_lines=5)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "PKB Neuroassistant" in result

    def test_build_summary_verbose(self):
        """build_summary(verbose=True) — расширенный вывод."""
        from gateway.diagnostics import build_summary
        result = build_summary(log_lines=5, verbose=True)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_build_summary_contains_diagnostics_header(self):
        """Сводка содержит заголовок Diagnostics."""
        from gateway.diagnostics import build_summary
        result = build_summary(log_lines=5)
        assert "Diagnostics" in result
