"""
Тесты для нового функционала:
- Автосохранение pipeline_test.py в backend/check_result/
- _generate_full_report() из service_checker.py
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import pytest

from service_checker.pipelines.base import PipelineResult, PipelineStep, PipelineContext, StepStatus


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
        from service_checker.core.pipeline_test import generate_report

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
        from service_checker.core.pipeline_test import generate_report

        results = {
            "document_processing": make_mock_pipeline_result(name="document_processing"),
            "chat_inference": make_mock_pipeline_result(name="chat_inference"),
        }
        report = generate_report(results)
        assert "document_processing" in report
        assert "chat_inference" in report

    def test_generate_report_passed_failed_icons(self):
        """Проверяем иконки: ✅ для passed, ❌ для failed."""
        from service_checker.core.pipeline_test import generate_report

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

    def _get_pipe_table_lines(self, lines):
        """Извлечь строки секции pipeline-таблицы из отчёта."""
        in_pipe = False
        pipe_lines = []
        for line in lines:
            if "### 📋 Pipeline статусы по сервисам" in line:
                in_pipe = True
                continue
            if in_pipe:
                if line.startswith("## "):
                    break
                if line.startswith("|") and "---" not in line:
                    pipe_lines.append(line)
        return pipe_lines

    def test_full_report_pipelines_column(self):
        """Проверяем колонку Pipelines в сводной таблице: ✅ если все пайплайны пройдены, ❌ если нет."""
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

        # В сводной таблице ищем строку сервиса с колонкой Pipelines (index 6)
        reg_ok = [l for l in lines_ok if "Registry" in l][0]
        reg_fail = [l for l in lines_fail if "Registry" in l][0]

        parts_ok = [p.strip() for p in reg_ok.split("|")]
        parts_fail = [p.strip() for p in reg_fail.split("|")]

        # Столбцы сводной таблицы: Service(1) | Port(2) | Ping(3) | CheckDb(4) | API(5) | Pipelines(6) | Status(7)
        assert parts_ok[6] == "✅", f"Expected ✅, got {parts_ok[6]}"
        assert parts_fail[6] == "❌", f"Expected ❌, got {parts_fail[6]}"

        # В pipeline-таблице проверяем колонку Documents (index 2)
        pipe_tbl_ok = self._get_pipe_table_lines(lines_ok)
        pipe_tbl_fail = self._get_pipe_table_lines(lines_fail)
        pipe_line_ok = [l for l in pipe_tbl_ok if "Registry" in l][0]
        pipe_line_fail = [l for l in pipe_tbl_fail if "Registry" in l][0]
        parts_pipe_ok = [p.strip() for p in pipe_line_ok.split("|")]
        parts_pipe_fail = [p.strip() for p in pipe_line_fail.split("|")]
        # Столбцы pipeline-таблицы: Service(1) | Documents(2) | Status(3)
        assert parts_pipe_ok[2] == "✅", f"Expected ✅, got {parts_pipe_ok[2]}"
        assert parts_pipe_fail[2] == "❌", f"Expected ❌, got {parts_pipe_fail[2]}"

    def test_full_report_query_column(self):
        """Проверяем колонку Chat в pipeline-таблице: ✅ если pipeline пройден, ❌ если нет."""
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

        # Ищем строку Auth в pipeline-таблице (где есть колонка Chat)
        pipe_tbl_ok = self._get_pipe_table_lines(lines_ok)
        pipe_tbl_fail = self._get_pipe_table_lines(lines_fail)
        auth_ok = [l for l in pipe_tbl_ok if "Auth" in l][0]
        auth_fail = [l for l in pipe_tbl_fail if "Auth" in l][0]

        # Столбцы pipeline-таблицы (только chat_inference): Service(1) | Chat(2) | Status(3)
        parts_ok = [p.strip() for p in auth_ok.split("|")]
        parts_fail = [p.strip() for p in auth_fail.split("|")]

        assert parts_ok[2] == "✅", f"Expected ✅, got {parts_ok[2]}"
        assert parts_fail[2] == "❌", f"Expected ❌, got {parts_fail[2]}"

    def test_full_report_non_participating_service(self):
        """Сервис не участвующий в пайплайне получает '—'."""
        from service_checker.core.reports import _generate_full_report

        # Gateway не участвует ни в document_processing, ни в chat_inference
        cov_results = {
            "gateway": MockCoverageResult("Gateway", 8080, ping_ok=True),
        }
        # Используем pipeline имена из PIPELINE_SERVICE_COLUMNS для pipe_order
        pipe_results = {
            "document_processing": make_mock_pipeline_result(name="doc", passed=True, services=["parser"]),
            "chat_inference": make_mock_pipeline_result(name="chat", passed=True, services=["auth"]),
        }
        report = _generate_full_report(cov_results, pipe_results, "t")
        lines = report.split("\n")

        # В сводной таблице: Pipelines колонка (index 6) должна быть "—" для Gateway
        gw_line_main = [l for l in lines if "Gateway" in l and "| 8080 |" in l][0]
        parts_main = [p.strip() for p in gw_line_main.split("|")]
        # Столбцы сводной: Service(1) | Port(2) | Ping(3) | CheckDb(4) | API(5) | Pipelines(6) | Status(7)
        assert parts_main[6] == "—", f"Expected '—', got {parts_main[6]}"

        # В pipeline-таблице: все колонки пайплайнов тоже "—" для Gateway
        pipe_tbl = self._get_pipe_table_lines(lines)
        gw_line_pipe = [l for l in pipe_tbl if "Gateway" in l][0]
        parts_pipe = [p.strip() for p in gw_line_pipe.split("|")]
        # Столбцы pipeline-таблицы: Service(1) | Documents(2) | Chat(3) | Status(4)
        assert parts_pipe[2] == "—", f"Expected '—', got {parts_pipe[2]}"
        assert parts_pipe[3] == "—", f"Expected '—', got {parts_pipe[3]}"

    def test_full_report_api_stats_in_summary(self):
        """В сводной таблице в колонке API отображается числовая статистика (passed/total/failed)."""
        from service_checker.core.reports import _generate_full_report

        cov_results = {
            "auth": MockCoverageResult("Auth Service", 8082, ping_ok=True,
                                        endpoints_total=10, endpoints_passed=10,
                                        endpoints_failed=0, endpoints_skipped=0),
        }
        pipe_results = {
            "document_processing": make_mock_pipeline_result(name="doc", passed=True),
        }
        report = _generate_full_report(cov_results, pipe_results, "t")
        lines = report.split("\n")

        # Строка сервиса в сводной таблице: колонка API должна содержать "✅ 10/10/0"
        auth_line = [l for l in lines if "Auth Service" in l][0]
        parts = [p.strip() for p in auth_line.split("|")]
        # Колонка API (index 5): "✅ 10/10/0"
        assert "10/10/0" in parts[5], f"Expected '10/10/0' in API column, got: {parts[5]}"
        assert "✅" in parts[5], f"Expected ✅ in API column, got: {parts[5]}"

    def test_full_report_no_orchestrator_duplicate(self):
        """Секция 'Orchestrator Pipelines' удалена — нет дублирования с Pipeline Testing детализацией."""
        from service_checker.core.reports import _generate_full_report

        cov_results = {
            "auth": MockCoverageResult("Auth Service", 8082, ping_ok=True),
            "orchestrator": MockCoverageResult("Orchestrator", 8081, ping_ok=True),
        }
        pipe_results = {
            "orchestrator_draft_lifecycle": make_mock_pipeline_result(
                name="orchestrator_draft_lifecycle", passed=True, services=["orchestrator"]
            ),
        }
        report = _generate_full_report(cov_results, pipe_results, "t")
        assert "### 🔄 Orchestrator Pipelines" not in report, \
            "Секция Orchestrator Pipelines должна быть удалена"
        assert "### 📋 Pipeline статусы по сервисам" in report




