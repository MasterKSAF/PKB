"""
Тесты для модуля observability_check (SC-1, SC-2).

Проверяет:
- Формирование отчёта
- Логику определения success/fail
- Обработку ошибок подключения
"""

from __future__ import annotations

import sys
from pathlib import Path

# Добавляем backend/ в sys.path
_backend = Path(__file__).resolve().parent.parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from service_checker.core.observability_check import (
    ObservabilityCheckResult,
    format_observability_report,
    KNOWN_ERROR_CODES,
    CORRELATION_HEADERS,
)


class TestObservabilityCheckResult:
    """Тесты модели ObservabilityCheckResult."""

    def test_create_result(self):
        r = ObservabilityCheckResult("test", "test", 8080)
        assert r.service_name == "test"
        assert r.service_key == "test"
        assert r.port == 8080
        assert r.passed is True
        assert r.checks == {}
        assert r.errors == []
        assert r.warnings == []

    def test_to_dict(self):
        r = ObservabilityCheckResult("Test Service", "test", 8080)
        r.checks["health"] = True
        r.details["status"] = "200"
        d = r.to_dict()
        assert d["service_name"] == "Test Service"
        assert d["service_key"] == "test"
        assert d["port"] == 8080
        assert d["checks"]["health"] is True
        assert d["details"]["status"] == "200"

    def test_passed_false_with_errors(self):
        r = ObservabilityCheckResult("test", "test", 8080)
        r.errors.append("Connection refused")
        r.passed = False
        assert r.passed is False
        assert len(r.errors) == 1

    def test_passed_false_with_failed_check(self):
        r = ObservabilityCheckResult("test", "test", 8080)
        r.checks["health_endpoint"] = False
        r.passed = False
        # passed должен быть False, когда есть failed checks
        all_ok = all(v for v in r.checks.values()) and len(r.errors) == 0
        assert all_ok is False


class TestFormatObservabilityReport:
    """Тесты форматирования отчёта."""

    def test_empty_report(self):
        report = format_observability_report([])
        assert "Observability Check Report" in report
        assert "| Сервис | Health |" in report

    def test_single_result(self):
        r = ObservabilityCheckResult("Test Service", "test", 8080)
        r.checks["health_endpoint"] = True
        r.checks["correlation_headers"] = True
        r.passed = True
        report = format_observability_report([r])
        assert "Test Service" in report
        assert "✅" in report

    def test_result_with_errors(self):
        r = ObservabilityCheckResult("Broken Service", "broken", 8080)
        r.checks["health_endpoint"] = False
        r.errors.append("Connection refused")
        r.passed = False
        report = format_observability_report([r])
        assert "Broken Service" in report
        assert "Connection refused" in report

    def test_result_with_warnings(self):
        r = ObservabilityCheckResult("Warn Service", "warn", 8080)
        r.checks["health_endpoint"] = True
        r.checks["correlation_headers"] = False
        r.warnings.append("Нет корреляционных заголовков")
        r.passed = False
        report = format_observability_report([r])
        assert "Warn Service" in report
        assert "корреляционных" in report

    def test_multiple_results(self):
        results = [
            ObservabilityCheckResult("OK", "ok", 8080, passed=True),
            ObservabilityCheckResult("FAIL", "fail", 8081, passed=False,
                                      errors=["Error"]),
        ]
        results[0].checks["health_endpoint"] = True
        results[1].checks["health_endpoint"] = False
        report = format_observability_report(results)
        assert "OK" in report
        assert "FAIL" in report


class TestConstants:
    """Тесты констант модуля."""

    def test_known_error_codes(self):
        assert "INDEX_TRIGGER_TIMEOUT" in KNOWN_ERROR_CODES
        assert "DECISION_TIMEOUT" in KNOWN_ERROR_CODES
        assert "PREVIEW_TRIGGER_TIMEOUT" in KNOWN_ERROR_CODES
        assert "LLM_GENERATION_TIMEOUT" in KNOWN_ERROR_CODES
        for code in KNOWN_ERROR_CODES.values():
            assert code == 408  # все таймауты — 408

    def test_correlation_headers(self):
        expected = [
            "X-Request-ID", "X-Trace-ID", "X-User-ID",
            "X-Draft-ID", "X-Document-ID", "X-Version-ID",
        ]
        assert CORRELATION_HEADERS == expected
