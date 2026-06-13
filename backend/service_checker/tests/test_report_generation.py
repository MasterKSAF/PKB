"""
Тесты для api_coverage_test.py — генерация отчёта.

Проверяют:
- Статус-колонка ❌ если ping_ok=False, даже при 0 failed/0 skipped
- Иконки ✅/❌ для ping в сводной таблице
- Иконки ✅/❌ в консольном выводе run_all
"""
from pathlib import Path

import pytest

from service_checker.api_coverage_test import ApiCoverageTester, ServiceResult, EndpointResult


def test_report_status_column_reflects_ping(make_endpoint):
    """
    Статус-колонка в отчёте должна быть ❌ если ping_ok=False,
    даже если все эндпоинты формально прошли (0 failed, 0 skipped).
    """
    tester = ApiCoverageTester()
    tester.results = {}
    tester.services_with_impl = set()

    ep = make_endpoint("/api/v1/ocr/process", "ocr", method="POST")

    # Сервис где ping упал, но эндпоинты "прошли"
    dead_result = ServiceResult(
        name="OCR Service", port=8088, ping_ok=False,
        endpoints_total=5, endpoints_passed=5, endpoints_failed=0, endpoints_skipped=0,
        results=[EndpointResult(endpoint=ep, status_code=404, success=True)],
    )
    # Сервис где ping жив и всё ок
    alive_result = ServiceResult(
        name="Parser Service", port=8087, ping_ok=True,
        endpoints_total=5, endpoints_passed=5, endpoints_failed=0, endpoints_skipped=0,
        results=[EndpointResult(endpoint=ep, status_code=200, success=True)],
    )

    tester.results = {"ocr": dead_result, "parser": alive_result}

    report = tester.generate_report()

    ocr_line_found = False
    parser_line_found = False
    for line in report.split("\n"):
        if not line.startswith("|"):
            continue
        if line.strip() == "|" or "---" in line or "| **Total**" in line:
            continue

        if "OCR" in line:
            ocr_line_found = True
            assert "❌" in line, f"OCR с ping_ok=False должен иметь ❌ в сводке, но строка: {line}"
        if "Parser" in line:
            parser_line_found = True
            assert "✅" in line and "❌" not in line, (
                f"Parser с ping_ok=True и 0 ошибок должен иметь ✅, но строка: {line}"
            )

    assert ocr_line_found, "Строка с OCR не найдена в сводной таблице"
    assert parser_line_found, "Строка с Parser не найдена в сводной таблице"


def test_ping_icons_in_report():
    """Проверить что в отчёте используются иконки ✅/❌ для ping."""
    tester = ApiCoverageTester()
    tester.results = {}
    tester.services_with_impl = set()

    ok_result = ServiceResult(name="Test OK", port=8080, ping_ok=True)
    fail_result = ServiceResult(name="Test Fail", port=8081, ping_ok=False)

    tester.results = {"ok": ok_result, "fail": fail_result}

    report = tester.generate_report()

    assert "✅" in report, "В отчёте должна быть ✅ для успешного ping"
    assert "❌" in report, "В отчёте должна быть ❌ для неудачного ping"

    for line in report.split("\n"):
        if "Test OK" in line and "✅" in line:
            break
    else:
        pytest.fail("Не найдена строка с Test OK и ✅")


def test_ping_icons_in_console():
    """Проверить что в консольном выводе используются иконки ✅/❌ для ping."""
    test_dir = Path(__file__).resolve().parent
    with open(test_dir.parent / "api_coverage_test.py", "r", encoding="utf-8") as f:
        source = f.read()

    assert '"✅" if result.ping_ok else "❌"' in source, (
        "В коде должна быть строка с иконками ✅/❌ для ping"
    )
