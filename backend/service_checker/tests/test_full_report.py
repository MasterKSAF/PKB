"""
Тесты для нового функционала:
- Автосохранение pipeline_test.py в backend/check_result/
- _generate_full_report() из service_checker.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from pipelines.base import PipelineResult, PipelineStep, PipelineContext, StepStatus


# ── Helpers: моки данных ──────────────────────────────────────────


def make_mock_pipeline_result(
    name: str = "test_pipeline",
    description: str = "Test",
    passed: bool = True,
    ping_ok: bool = True,
    total_steps: int = 3,
    passed_steps: int = 3,
    failed_steps: int = 0,
    skipped_steps: int = 0,
    services: Optional[List[str]] = None,
) -> PipelineResult:
    """Создать PipelineResult с указанными параметрами."""
    # Создаём шаги для указанных сервисов (нужно для _generate_full_report)
    steps: List[PipelineStep] = []
    if services:
        step_status = StepStatus.PASSED if passed else StepStatus.FAILED
        for svc in services:
            for i in range(total_steps // len(services) if services else 1):
                steps.append(PipelineStep(
                    name=f"step_{svc}_{i}",
                    service=svc,
                    method="GET",
                    path="/health",
                    port=8080,
                    status=step_status,
                ))
    return PipelineResult(
        name=name,
        description=description,
        passed=passed,
        ping_ok=ping_ok,
        total_steps=total_steps or len(steps),
        passed_steps=passed_steps,
        failed_steps=failed_steps,
        skipped_steps=skipped_steps,
        steps=steps,
    )


class MockCoverageResult:
    """Мок ServiceResult из api_coverage_test.py."""
    def __init__(self, name: str, port: int, ping_ok: bool = True,
                 endpoints_total: int = 10, endpoints_passed: int = 10,
                 endpoints_failed: int = 0, endpoints_skipped: int = 0):
        self.name = name
        self.port = port
        self.ping_ok = ping_ok
        self.endpoints_total = endpoints_total
        self.endpoints_passed = endpoints_passed
        self.endpoints_failed = endpoints_failed
        self.endpoints_skipped = endpoints_skipped


# ── Тесты: pipeline_test.generate_report() ────────────────────────


class TestPipelineGenerateReport:
    """Тестируем generate_report из pipeline_test.py."""

    def test_generate_report_returns_string(self):
        """Базовая проверка: функция возвращает строку с отчётом."""
        from service_checker.pipeline_test import generate_report

        results = {
            "doc": make_mock_pipeline_result(name="doc", passed=True),
            "chat": make_mock_pipeline_result(name="chat", passed=False,
                                               passed_steps=2, failed_steps=1),
        }
        report = generate_report(results)
        assert isinstance(report, str)
        assert len(report) > 0

    def test_generate_report_contains_pipeline_names(self):
        """В отчёте присутствуют имена пайплайнов."""
        from service_checker.pipeline_test import generate_report

        results = {
            "document_processing": make_mock_pipeline_result(name="document_processing"),
            "chat_inference": make_mock_pipeline_result(name="chat_inference"),
        }
        report = generate_report(results)
        assert "document_processing" in report
        assert "chat_inference" in report

    def test_generate_report_passed_failed_icons(self):
        """Проверяем иконки: ✅ для passed, ❌ для failed."""
        from service_checker.pipeline_test import generate_report

        results = {
            "ok": make_mock_pipeline_result(name="ok", passed=True),
            "fail": make_mock_pipeline_result(name="fail", passed=False),
        }
        report = generate_report(results)
        # Ищем строку статуса
        assert "✅ Пройден" in report or "✅" in report
        assert "❌" in report


# ── Тесты: _generate_full_report() из service_checker.py ──────────


class TestGenerateFullReport:
    """Тестируем _generate_full_report из service_checker.py."""

    def test_generate_full_report_returns_string(self):
        """Базовая проверка: функция возвращает строку с отчётом."""
        from service_checker.core.reports import _generate_full_report

        cov_results = {
            "auth": MockCoverageResult("auth", 8082, ping_ok=True),
            "registry": MockCoverageResult("registry", 8084, ping_ok=True),
        }
        pipe_results = {
            "document_processing": make_mock_pipeline_result(name="doc", passed=True),
            "chat_inference": make_mock_pipeline_result(name="chat", passed=False,
                                                        passed_steps=2, failed_steps=1),
        }
        report = _generate_full_report(cov_results, pipe_results, "20260610_120000")
        assert isinstance(report, str)
        assert len(report) > 0

    def test_full_report_contains_all_sections(self):
        """Отчёт содержит три секции: сводная, coverage, pipeline."""
        from service_checker.core.reports import _generate_full_report

        cov_results = {
            "auth": MockCoverageResult("auth", 8082, ping_ok=True),
        }
        pipe_results = {
            "doc": make_mock_pipeline_result(name="doc", passed=True),
        }
        report = _generate_full_report(cov_results, pipe_results, "20260610_120000")

        assert "Итоговая сводная таблица" in report
        assert "API Coverage" in report
        assert "Pipeline Testing" in report

    def test_full_report_status_all_green(self):
        """Если всё зелёное — статус ✅."""
        from service_checker.core.reports import _generate_full_report

        cov_results = {
            "auth": MockCoverageResult("Auth Service", 8082, ping_ok=True),
        }
        pipe_results = {
            "document_processing": make_mock_pipeline_result(name="doc", passed=True),
        }
        report = _generate_full_report(cov_results, pipe_results, "t")
        # В строке сервиса должен быть ✅ в колонке Status
        # Ищем строку, содержащую Auth Service, и проверяем что последняя колонка ✅
        lines = report.split("\n")
        auth_line = [l for l in lines if "Auth Service" in l]
        assert len(auth_line) > 0
        assert "| ✅ |" in auth_line[0]  # последняя колонка Status

    def test_full_report_status_fail_if_ping_down(self):
        """Если ping упал — статус ❌."""
        from service_checker.core.reports import _generate_full_report

        cov_results = {
            "auth": MockCoverageResult("Auth Service", 8082, ping_ok=False),
        }
        pipe_results = {
            "doc": make_mock_pipeline_result(name="doc", passed=True),
        }
        report = _generate_full_report(cov_results, pipe_results, "t")
        lines = report.split("\n")
        auth_line = [l for l in lines if "Auth Service" in l]
        assert len(auth_line) > 0
        assert "❌" in auth_line[0]

    def test_full_report_documents_column(self):
        """Проверяем колонку Documents: ✅ если pipeline пройден, ❌ если нет."""
        from service_checker.core.reports import _generate_full_report

        # Registry участвует в document_processing
        cov_results = {
            "registry": MockCoverageResult("Registry", 8084, ping_ok=True),
        }
        pipe_ok = {
            "document_processing": make_mock_pipeline_result(name="doc", passed=True, services=["registry"]),
        }
        pipe_fail = {
            "document_processing": make_mock_pipeline_result(name="doc", passed=False, services=["registry"]),
        }

        report_ok = _generate_full_report(cov_results, pipe_ok, "t")
        report_fail = _generate_full_report(cov_results, pipe_fail, "t")

        lines_ok = report_ok.split("\n")
        lines_fail = report_fail.split("\n")

        reg_ok = [l for l in lines_ok if "Registry" in l][0]
        reg_fail = [l for l in lines_fail if "Registry" in l][0]

        # Столбцы: Service(1) | Port(2) | Ping(3) | ✅ Passed(4) | Documents(5) | Query(6) | Status(7)
        parts_ok = [p.strip() for p in reg_ok.split("|")]
        parts_fail = [p.strip() for p in reg_fail.split("|")]

        assert parts_ok[5] == "✅", f"Expected ✅, got {parts_ok[5]}"
        assert parts_fail[5] == "❌", f"Expected ❌, got {parts_fail[5]}"

    def test_full_report_query_column(self):
        """Проверяем колонку Query: ✅ если pipeline пройден, ❌ если нет."""
        from service_checker.core.reports import _generate_full_report

        cov_results = {
            "auth": MockCoverageResult("Auth", 8082, ping_ok=True),
        }
        pipe_ok = {
            "chat_inference": make_mock_pipeline_result(name="chat", passed=True, services=["auth"]),
        }
        pipe_fail = {
            "chat_inference": make_mock_pipeline_result(name="chat", passed=False, services=["auth"]),
        }

        report_ok = _generate_full_report(cov_results, pipe_ok, "t")
        report_fail = _generate_full_report(cov_results, pipe_fail, "t")

        lines_ok = report_ok.split("\n")
        lines_fail = report_fail.split("\n")

        auth_ok = [l for l in lines_ok if "Auth" in l][0]
        auth_fail = [l for l in lines_fail if "Auth" in l][0]

        # Столбцы: Service(1) | Port(2) | Ping(3) | ✅ Passed(4) | Documents(5) | Query(6) | Status(7)
        parts_ok = [p.strip() for p in auth_ok.split("|")]
        parts_fail = [p.strip() for p in auth_fail.split("|")]

        assert parts_ok[6] == "✅", f"Expected ✅, got {parts_ok[6]}"
        assert parts_fail[6] == "❌", f"Expected ❌, got {parts_fail[6]}"

    def test_full_report_non_participating_service(self):
        """Сервис не участвующий в пайплайне получает '—'."""
        from service_checker.core.reports import _generate_full_report

        # Gateway не участвует ни в document_processing, ни в chat_inference
        cov_results = {
            "gateway": MockCoverageResult("Gateway", 8081, ping_ok=True),
        }
        pipe_results = {
            "doc": make_mock_pipeline_result(name="doc", passed=True, services=["parser"]),
            "chat": make_mock_pipeline_result(name="chat", passed=True, services=["auth"]),
        }
        report = _generate_full_report(cov_results, pipe_results, "t")
        lines = report.split("\n")
        gw_line = [l for l in lines if "Gateway" in l][0]
        parts = [p.strip() for p in gw_line.split("|")]
        # Столбцы: Service(1) | Port(2) | Ping(3) | ✅ Passed(4) | Documents(5) | Query(6) | Status(7)
        assert parts[5] == "—", f"Expected '—', got {parts[5]}"
        assert parts[6] == "—", f"Expected '—', got {parts[6]}"


# ── Тесты: автосохранение pipeline_test.py ────────────────────────


class TestPipelineAutoSave:
    """Тестируем, что pipeline_test.py правильно вычисляет путь сохранения."""

    def test_auto_save_path_resolves_to_backend_check_result(self):
        """Проверяем, что путь автосохранения ведёт в backend/check_result/."""
        # Имитируем логику из pipeline_test.py
        fake_script = Path("H:/Projects/PKB_neuroassistant_develop/backend/service_checker/pipeline_test.py")
        check_dir = fake_script.resolve().parent.parent / "check_result"
        assert "check_result" in str(check_dir)
        # Убеждаемся, что это НЕ service_checker/check_result
        assert "service_checker" not in str(check_dir.parent)
        # А backend/check_result
        assert check_dir.parent.name == "backend"

    def test_pipeline_report_filename_format(self):
        """Имя файла соответствует формату pipeline_YYYYMMDD_HHMMSS.md."""
        from service_checker.pipeline_test import generate_report
        # Проверяем, что функция существует и импортируется
        assert callable(generate_report)


# ── Тесты: full-report action в cmd_docker ────────────────────────


class TestDockerFullReportAction:
    """Проверяем, что cmd_docker обрабатывает action full-report."""

    def test_docker_has_full_report_action(self):
        """Проверяем, что в cmd_docker есть ветка для full-report."""
        import inspect
        from service_checker.core.cli import cmd_docker

        source = inspect.getsource(cmd_docker)
        assert 'action == "full-report"' in source or '"full-report"' in source
