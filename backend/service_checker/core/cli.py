#!/usr/bin/env python3
"""
PKB Neuroassistant — Service Checker: CLI Entry Point & Commands
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from service_checker.core.config import (
    PROJECT_ROOT,
    BACKEND_DIR,
    SERVICE_DEFS,
    DOCKER_COMPOSE_FILE,
    DOCKER_DIR,
    DOCKER_SERVICE_NAMES,
)
from service_checker.core.models import Report, ServiceProcess, ServiceLog, HealthResult, ApiCallLog
from service_checker.core.utils import log_ok, log_warn, log_err, log_info, log_header, log_step
from service_checker.core.services import (
    start_service,
    stop_service,
    wait_for_service,
    check_service_health,
    check_service_health_for_key,
    WebEmulator,
    _collect_logs,
)
from service_checker.core.docker import (
    _check_docker,
    _docker_action,
    _docker_health_check,
    _docker_collect_logs,
    _docker_run_coverage,
    _docker_run_pipeline,
)
from service_checker.core.reports import _generate_full_report
from service_checker.services import SERVICE_KEYS, MODE_PORTS, SERVICE_REGISTRY
from service_checker.core.observability_check import (
    check_service_otel,
    check_service_otel_by_source,
    format_observability_report,
    ObservabilityCheckResult,
)
from service_checker.core.har_validator import HarValidator, format_har_report


# ──────────────────────────────────────────────────────────────────────
#  Argument Parser
# ──────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PKB Neuroassistant — Service Launcher & Web Interface Emulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Примеры:\n"
            "  python tools/service_checker.py all\n"
            "  python tools/service_checker.py start --mocks=gateway\n"
            "  python tools/service_checker.py health\n"
            "  python tools/service_checker.py emulate\n"
        ),
    )

    subparsers = parser.add_subparsers(dest="command", help="Команда")

    # all
    p_all = subparsers.add_parser("all", help="Запустить + health check + эмуляция UI + отчёт")
    p_all.add_argument(
        "--mocks",
        choices=["gateway", "individual", "none"],
        default="individual",
        help="Режим запуска mock-сервисов (по умолч. individual — каждый на своём порту)",
    )
    p_all.add_argument(
        "--with-real",
        action="store_true",
        help="Попробовать запустить реальные сервисы",
    )
    p_all.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Таймаут ожидания запуска сервисов (сек)",
    )
    p_all.add_argument(
        "-o", "--output",
        default=None,
        help="Путь для сохранения отчёта (.md или .html)",
    )

    # start
    p_start = subparsers.add_parser("start", help="Запустить сервисы")
    p_start.add_argument(
        "--mocks",
        choices=["gateway", "individual", "none"],
        default="individual",
        help="Режим запуска mock-сервисов (по умолч. individual)",
    )
    p_start.add_argument(
        "--with-real",
        action="store_true",
        help="Попробовать запустить реальные сервисы",
    )
    p_start.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Таймаут ожидания запуска сервисов (сек)",
    )

    # health
    p_health = subparsers.add_parser("health", help="Проверить здоровье сервисов")
    p_health.add_argument(
        "--port",
        type=int,
        default=None,
        help="Проверить только конкретный порт",
    )

    # emulate
    p_emulate = subparsers.add_parser("emulate", help="Эмуляция веб-интерфейса")
    p_emulate.add_argument(
        "--gateway-url",
        default="http://127.0.0.1:18080",
        help="URL gateway (по умолч. http://127.0.0.1:18080)",
    )
    p_emulate.add_argument(
        "--mode",
        choices=["individual", "gateway"],
        default="individual",
        help="Режим: individual (порты 18081-18084) или gateway (всё на одном)",
    )
    p_emulate.add_argument(
        "-o", "--output",
        default=None,
        help="Путь для сохранения отчёта (.md или .html)",
    )

    # docker — развёртывание всей системы через Docker Compose
    p_docker = subparsers.add_parser(
        "docker",
        help="Развернуть всю систему через Docker Compose",
    )
    p_docker.add_argument(
        "--action",
        choices=["up", "down", "build", "restart", "reset", "logs", "ps", "health", "coverage", "full-report", "db-check", "patch-rag"],
        default="up",
        help="Действие с Docker Compose (по умолч. up — запустить все сервисы)",
    )
    p_docker.add_argument(
        "--build",
        action="store_true",
        help="Пересобрать образы перед запуском",
    )
    p_docker.add_argument(
        "--detach", "-d",
        action="store_true",
        help="Запустить в фоне (detach)",
    )
    p_docker.add_argument(
        "--services",
        nargs="*",
        default=[],
        help="Список конкретных сервисов для coverage (по умолч. все)",
    )
    p_docker.add_argument(
        "--pipelines",
        nargs="*",
        default=[],
        help="Список конкретных пайплайнов (по умолч. все)",
    )
    p_docker.add_argument(
        "--skip-coverage",
        action="store_true",
        help="Пропустить API Coverage",
    )
    p_docker.add_argument(
        "--skip-pipelines",
        action="store_true",
        help="Пропустить Pipeline тесты",
    )
    p_docker.add_argument(
        "--db-only",
        action="store_true",
        help="Запустить только PostgreSQL",
    )
    p_docker.add_argument(
        "--skip-gateway-tests",
        action="store_true",
        help="Пропустить Gateway Integration Tests",
    )
    p_docker.add_argument(
        "--gateway-tests",
        action="store_true",
        help="Запустить Gateway Integration Tests (pytest) даже при пропуске coverage",
    )
    p_docker.add_argument(
        "--spd",
        action="store_true",
        help="Режим SPD: подмена порта rag_search на 18090 (объединённый rag_builder + rag_search)",
    )

    # check — observability / post-deploy проверка
    p_check = subparsers.add_parser(
        "check",
        help="Проверка observability: OTEL, логи, correlation-id, коды ошибок (SC-1)",
    )
    p_check.add_argument(
        "service",
        nargs="?",
        default=None,
        help="Имя сервиса для проверки (по умолч. все)",
    )
    p_check.add_argument(
        "--post-deploy",
        action="store_true",
        help="Режим CI: exit-code 0/1/2 (SC-2)",
    )
    p_check.add_argument(
        "--source-dir",
        default=None,
        help="Директория с исходным кодом для статического анализа OTEL",
    )

    # validate-har — проверка HAR-файла против OpenAPI
    p_validate_har = subparsers.add_parser(
        "validate-har",
        help="Проверить HAR-файл (HTTP Archive) против OpenAPI схемы сервиса",
    )
    p_validate_har.add_argument(
        "har",
        help="Путь к HAR-файлу",
    )
    p_validate_har.add_argument(
        "--openapi-url",
        default=None,
        help="URL OpenAPI схемы (например http://127.0.0.1:18080/openapi.json). "
             "Если не указан, берётся из --service",
    )
    p_validate_har.add_argument(
        "--service",
        default=None,
        help="Ключ сервиса из SERVICE_KEYS (например gateway, registry). "
             "Используется для получения порта из MODE_PORTS."
    )
    p_validate_har.add_argument(
        "--output", "-o",
        default=None,
        help="Путь для сохранения отчёта (.md)",
    )

    # report (из сохранённых данных)
    p_report = subparsers.add_parser("report", help="Сформировать отчёт из сохранённых логов")
    p_report.add_argument(
        "input",
        help="Путь к JSON-файлу с логами",
    )
    p_report.add_argument(
        "-o", "--output",
        default="report.md",
        help="Путь для сохранения отчёта (по умолч. report.md)",
    )
    p_report.add_argument(
        "--format",
        choices=["md", "html"],
        default="md",
        help="Формат отчёта (md или html)",
    )

    return parser.parse_args()


# ──────────────────────────────────────────────────────────────────────
#  CLI Commands
# ──────────────────────────────────────────────────────────────────────


async def cmd_start(
    mocks: str = "gateway",
    with_real: bool = False,
    timeout: int = 60,
) -> List[ServiceProcess]:
    """Запустить сервисы."""
    log_header("Запуск сервисов")

    running: List[ServiceProcess] = []
    keys_to_start: List[str] = []

    if mocks == "gateway":
        keys_to_start.append("gateway")
    elif mocks == "individual":
        keys_to_start.extend(["auth", "orchestrator", "query", "registry"])

    if with_real:
        keys_to_start.extend(["integration", "parser", "rag_builder", "rag_search"])
        # registry_real конфликтует по порту с mock registry, пропускаем

    if not keys_to_start:
        log_warn("Нет сервисов для запуска. Укажите --mocks или --with-real.")
        return running

    # Проверим зависимости
    try:
        import httpx  # noqa
    except ImportError:
        log_err("Не установлен httpx. Выполните: pip install httpx")
        return running

    for key in keys_to_start:
        svc_def = SERVICE_DEFS.get(key)
        if not svc_def:
            log_warn(f"Неизвестный сервис: {key}")
            continue

        sp = start_service(key, svc_def)
        if sp is None:
            continue

        running.append(sp)

    if not running:
        log_err("Не удалось запустить ни один сервис.")
        return running

    # Ожидаем, пока все запустятся
    log_header(f"Ожидание запуска {len(running)} сервисов (таймаут {timeout}с)")

    all_ready = True
    for sp in running:
        log_info(f"Ожидание {sp.name} (порт {sp.port})...")
        ready = await wait_for_service(sp, timeout=timeout)
        if ready:
            log_ok(f"{sp.name} — готов")
        else:
            log_err(f"{sp.name} — не ответил за {timeout}с")
            all_ready = False

    if all_ready:
        log_ok("Все сервисы запущены и готовы к работе!")
    else:
        log_warn("Некоторые сервисы не запустились. Проверьте логи выше.")

    return running


async def cmd_health(port: Optional[int] = None):
    """Проверить здоровье запущенных сервисов."""
    log_header("Health Check сервисов")

    tasks = []
    for key, svc_def in SERVICE_DEFS.items():
        if port is not None and svc_def["port"] != port:
            continue
        # Пробуем подключиться к каждому
        tasks.append(check_service_health_for_key(key, svc_def))

    results = await asyncio.gather(*tasks)

    # Вывод результатов
    print()
    for r in results:
        status_icon = "✓" if r.status == "ok" else "✗" if r.status == "unreachable" else "⚠"
        print(f"  {status_icon}  {r.service_name:35s} :{r.service_key:15s}  ", end="")
        if r.status == "ok":
            resp_status = (r.response or {}).get("status", "ok")
            print(f"{resp_status:12s}  {r.elapsed_ms:4d}ms")
        elif r.status == "unreachable":
            print(f"{'unreachable':12s}  {r.elapsed_ms:4d}ms  ({r.error})")
        else:
            print(f"{'error':12s}  {r.elapsed_ms:4d}ms  ({r.error})")

    # Сводка
    total = len(results)
    ok = sum(1 for r in results if r.status == "ok")
    unreachable = sum(1 for r in results if r.status == "unreachable")
    degraded = sum(1 for r in results if r.status in ("degraded", "error"))

    print(f"\n  {'─' * 60}")
    print(f"  Всего: {total}  |  ✓ ok: {ok}  |  ⚠ degraded: {degraded}  |  ✗ unreachable: {unreachable}")


async def cmd_emulate(
    gateway_url: str,
    mode: str = "individual",
    report: Optional[Report] = None,
    output: Optional[str] = None,
):
    """Запустить эмуляцию UI."""
    import httpx

    # Проверим, что gateway жив (пробуем системный health)
    health_endpoints = [
        f"{gateway_url}/api/v1/system/health",
        f"{gateway_url}/api/v1/health",
        f"{gateway_url}/api/v1/",
    ]
    alive = False
    async with httpx.AsyncClient(
            timeout=5,
            trust_env=False,
    ) as client:
        for url in health_endpoints:
            try:
                resp = await client.get(url)
                if resp.status_code < 500:
                    alive = True
                    break
            except (httpx.ConnectError, httpx.TimeoutException):
                continue

    if not alive:
        log_err(f"Сервис не отвечает ({gateway_url}). Запустите сервисы сначала.")
        log_info("  python tools/service_checker.py start")
        return report

    WebEmulator.ORCHESTRATOR_URL = gateway_url
    async with WebEmulator(mode=mode, report=report) as emu:
        await emu.run_all_scenarios()

    emu.report.close()

    if output:
        fmt = "html" if output.endswith(".html") else "md"
        emu.report.save(output, fmt=fmt)

    return emu.report


async def cmd_docker(
    action: str = "up",
    build: bool = False,
    detach: bool = False,
    services: Optional[List[str]] = None,
    pipelines: Optional[List[str]] = None,
    skip_coverage: bool = False,
    skip_pipelines: bool = False,
    skip_gateway_tests: bool = False,
    gateway_tests: bool = False,
    db_only: bool = False,
    spd: bool = False,
):
    """Развернуть систему через Docker Compose."""
    services = services or []
    pipelines = pipelines or []

    # Нормализация: split по запятой (recheck.bat шлёт "--services a,b" как один элемент)
    _flat = []
    for s in services:
        _flat.extend(x.strip() for x in s.split(",") if x.strip())
    services = sorted(_flat)
    _flat = []
    for p in pipelines:
        _flat.extend(x.strip() for x in p.split(",") if x.strip())
    pipelines = sorted(_flat)

    # Режим SPD: подмена порта rag_search на 18090 (объединённый сервис)
    if spd:
        from service_checker.services import MODE_PORTS
        MODE_PORTS["rag_search"] = 18090

    log_header("Развёртывание PKB Neuroassistant через Docker")

    if not _check_docker():
        return

    if not DOCKER_COMPOSE_FILE.exists():
        log_err(f"Файл {DOCKER_COMPOSE_FILE} не найден.")
        return

    log_info(f"Compose-файл: {DOCKER_COMPOSE_FILE}")

    target_services = list(services)
    if db_only:
        target_services = ["postgres"]
        log_info("Режим --db-only: запускаем только PostgreSQL")

    if action in ("up", "restart") and target_services:
        names = ", ".join(DOCKER_SERVICE_NAMES.get(s, s) for s in target_services)
        log_info(f"Целевые сервисы: {names}")

    if action == "reset":
        log_info("Полный сброс: останавливаем + чистим volumes + запускаем заново...")
        _docker_action("down", target_services, build=False, detach=False)
        # Явно удаляем только известные volumes (не через -v, чтобы не задеть чужие)
        for vol_name in ["pkb_pg_data", "pkb_minio_data", "pkb_app_logs"]:
            subprocess.run(
                ["docker", "volume", "rm", "-f", vol_name],
                capture_output=True, timeout=10,
            )
        log_ok("Volumes очищены. Запускаем...")
        _docker_action("up", target_services, build=False, detach=True)
        return

    if action == "health":
        _docker_health_check(target_services)
        return

    if action == "db-check":
        log_header("🗄️ Проверка состояния БД")
        from service_checker.core.db_check import run_db_check, format_db_report

        result = run_db_check()
        report = format_db_report(result)
        print()
        print(report)
        print()
        if result.error:
            log_warn(f"PostgreSQL недоступен: {result.error}")
        elif result.healthy:
            log_ok("БД инициализирована корректно")
        else:
            log_warn("БД инициализирована не полностью")
        return

    if action == "coverage":
        log_header("📋 Coverage + Logs")
        ok = await _docker_run_coverage()
        if ok:
            log_info("Собираем логи ошибок...")
            log_suffix = "_spd" if spd else ""
            await _docker_collect_logs(target_services, suffix=log_suffix)
        return

    if action == "full-report":
        log_header("📋 Полный отчёт: Coverage + Pipeline + Сводная таблица")

        if spd:
            log_info("Режим SPD: rag_search=18090 (подмена в MODE_PORTS)")

        check_result_dir = BACKEND_DIR / "check_result"
        check_result_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Суффикс для имён файлов при фильтрации по сервисам/пайплайнам
        report_suffix_parts = []
        if spd:
            report_suffix_parts.append("spd")
        if services:
            report_suffix_parts.append("services_" + "_".join(services))
        if pipelines:
            report_suffix_parts.append("pipelines_" + "_".join(pipelines))
        report_suffix = ("_" + "_".join(report_suffix_parts)) if report_suffix_parts else ""

        # 0. Docker health check (статус контейнеров + HTTP + supervisorctl + .err логи)
        _docker_health_check(target_services)
        print()

        # 1. DB Health check (нужен для CheckDb в coverage и сводном отчёте)
        db_result = None
        try:
            from service_checker.core.db_check import run_db_check

            log_info("Проверка состояния БД...")
            db_result = run_db_check()
            if db_result.healthy:
                log_ok("БД инициализирована корректно")
            elif db_result.error:
                log_warn(f"PostgreSQL недоступен: {db_result.error}")
            else:
                log_warn("БД инициализирована не полностью")
        except Exception as e:
            log_err(f"Ошибка проверки БД: {e}")

        # 2. Coverage
        cov_results: Optional[Dict[str, Any]] = None
        tester = None
        if not skip_coverage:
            try:
                sys.path.insert(0, str(BACKEND_DIR))
                from service_checker.core.api_coverage_test import ApiCoverageTester

                log_info("Очистка supervisor-логов...")
                try:
                    subprocess.run(
                        ["docker", "exec", "pkb-neuro", "bash", "-c",
                         "truncate -s 0 /var/log/supervisor/*.log /var/log/supervisor/*.err 2>/dev/null || true"],
                        capture_output=True, timeout=15,
                    )
                except Exception:
                    pass

                cov_services = services or None
                log_info(f"Запуск API Coverage Test..." + (f' (сервисы: {cov_services})' if cov_services else ''))
                tester = ApiCoverageTester(services=cov_services, base_host="127.0.0.1")
                cov_results = await tester.run_all()
                cov_report = tester.generate_report(db_result=db_result)
                cov_path = check_result_dir / f"api_coverage{report_suffix}.md"
                cov_path.write_text(cov_report, encoding="utf-8")
                log_ok(f"API Coverage отчёт сохранён: {cov_path}")
            except Exception as e:
                log_err(f"Ошибка coverage: {e}")
            finally:
                if tester:
                    await tester.close()
        else:
            log_info("API Coverage пропущен (--skip-coverage)")

        # 3. Pipeline
        pipe_results: Dict[str, Any] = {}
        runner = None
        if not skip_pipelines:
            try:
                sys.path.insert(0, str(BACKEND_DIR))
                from service_checker.pipelines import PIPELINE_REGISTRY, PipelineRunner

                log_info("Запуск Pipeline Testing...")
                runner = PipelineRunner(base_host="127.0.0.1")
                for name, cls in sorted(PIPELINE_REGISTRY.items()):
                    if pipelines and name not in pipelines:
                        continue
                    pipeline = cls()
                    result = await runner.run(pipeline, skip_ping=False)
                    pipe_results[name] = result

                if pipe_results:
                    log_ok(f"Pipeline тесты завершены: {len(pipe_results)} пайплайнов")
            except Exception as e:
                log_err(f"Ошибка pipeline: {e}")
            finally:
                if runner:
                    await runner.close()
        else:
            log_info("Pipeline тесты пропущены (--skip-pipelines)")

        # 3a. Gateway Integration Tests (pytest, все тесты, включая Docker)
        gateway_tests_result: Optional[Dict[str, Any]] = None
        if not skip_gateway_tests or gateway_tests:
            try:
                from service_checker.core.docker import _docker_run_gateway_tests

                if gateway_tests:
                    log_info("Запуск Gateway Integration Tests (--gateway-tests)...")
                else:
                    log_info("Запуск Gateway Integration Tests...")
                gateway_tests_result = await _docker_run_gateway_tests()
                gt = gateway_tests_result
                if gt.get("success"):
                    log_ok(f"Gateway тесты пройдены: {gt.get('passed', 0)}/{gt.get('total', 0)}")
                else:
                    log_warn(f"Gateway тесты: {gt.get('failed', 0)} упало из {gt.get('total', 0)}")
            except Exception as e:
                log_err(f"Ошибка gateway тестов: {e}")
                gateway_tests_result = {"success": False, "passed": 0, "failed": 0, "total": 0,
                                        "output_path": "", "error": str(e)}
        else:
            log_info("Gateway тесты пропущены (--skip-gateway-tests)")
            gateway_tests_result = None

        # 3b. Service Contracts Check (реальное взаимодействие сервисов)
        contract_report: Optional[str] = None
        try:
            from service_checker.core.contracts_check import run_all_contract_checks, format_contracts_report

            log_info("Проверка контрактов между сервисами...")
            contract_report_obj = await run_all_contract_checks(timeout=15)
            contract_report = format_contracts_report(contract_report_obj)
            if contract_report_obj.all_passed:
                log_ok(f"Контракты: {contract_report_obj.passed}/{contract_report_obj.total} пройдено")
            else:
                log_warn(f"Контракты: {contract_report_obj.failed}/{contract_report_obj.total} упало")
        except Exception as e:
            log_err(f"Ошибка проверки контрактов: {e}")
            contract_report = f"\n---\n## 🔗 Service Contracts Check\n\n❌ Ошибка: {e}\n"

        # 4. Full report
        if cov_results or pipe_results or contract_report:
            if cov_results is None:
                cov_results = {}
            full_report = _generate_full_report(
                cov_results, pipe_results, timestamp,
                db_result=db_result, contract_report=contract_report,
                gateway_tests_result=gateway_tests_result,
            )
            full_path = check_result_dir / f"full_report{report_suffix}.md"
            full_path.write_text(full_report, encoding="utf-8")
            log_ok(f"Сводный отчёт сохранён: {full_path}")

            # Собираем логи ошибок
            log_info("Собираем логи ошибок...")
            await _docker_collect_logs(target_services, suffix=report_suffix)
        return

    if action == "logs":
        log_suffix = "_spd" if spd else ""
        await _docker_collect_logs(target_services, suffix=log_suffix)
        return

    success = _docker_action(action, target_services, build=build, detach=detach)

    if success:
        if action == "up":
            log_ok("Все сервисы запущены!")
            log_info("Для проверки: python service_checker.py docker --action health")
            log_info("Для остановки: python service_checker.py docker --action down")
        elif action == "down":
            log_ok("Все сервисы остановлены.")
        elif action == "build":
            log_ok("Образы собраны.")
        elif action == "restart":
            log_ok("Сервисы перезапущены.")
    else:
        if action == "up":
            log_err("Не удалось запустить сервисы. Проверьте логи выше.")
        elif action == "build":
            log_err("Не удалось собрать образы.")


async def cmd_all(
    mocks: str,
    with_real: bool,
    timeout: int,
    output: Optional[str] = None,
):
    """Запустить всё: сервисы → health → эмуляция → отчёт."""
    report = Report()

    running = await cmd_start(mocks=mocks, with_real=with_real, timeout=timeout)
    if not running:
        report.add_error("Не удалось запустить сервисы.")
        report.close()
        if output:
            report.save(output)
        return

    # Добавляем сервисы в отчёт
    for sp in running:
        report.add_service(sp)

    # Запускаем сбор логов
    log_collectors = [
        asyncio.create_task(_collect_logs(report, sp))
        for sp in running
    ]

    # Отмечаем готовность
    for sp in running:
        report.set_service_ready(sp.key, True)

    # Небольшая пауза на стабилизацию
    await asyncio.sleep(1)

    # Health check — собираем результаты
    log_header("Health Check сервисов")
    health_tasks = []
    for key, svc_def in SERVICE_DEFS.items():
        health_tasks.append(check_service_health_for_key(key, svc_def))

    health_results = await asyncio.gather(*health_tasks)
    for hr in health_results:
        report.add_health_result(hr)
        report.set_service_health(hr.service_key, hr.status, hr.response)

    # Выводим health check
    print()
    for r in health_results:
        status_icon = "✓" if r.status == "ok" else "✗" if r.status == "unreachable" else "⚠"
        print(f"  {status_icon}  {r.service_name:35s} :{r.service_key:15s}  ", end="")
        if r.status == "ok":
            resp_status = (r.response or {}).get("status", "ok")
            print(f"{resp_status:12s}  {r.elapsed_ms:4d}ms")
        elif r.status == "unreachable":
            print(f"{'unreachable':12s}  {r.elapsed_ms:4d}ms  ({r.error})")
        else:
            print(f"{'error':12s}  {r.elapsed_ms:4d}ms  ({r.error})")

    total_hc = len(health_results)
    ok_hc = sum(1 for r in health_results if r.status == "ok")
    print(f"\n  Health Check: {ok_hc}/{total_hc} ok\n")

    # Эмуляция UI (через Orchestrator — единая точка входа)
    mode = "individual" if mocks == "individual" else "gateway"
    report = await cmd_emulate(
        "http://127.0.0.1:18081",
        mode=mode,
        report=report,
    )

    # Отменяем сбор логов
    for task in log_collectors:
        task.cancel()

    # Остановка
    log_header("Остановка сервисов")
    for sp in running:
        stop_service(sp)
    log_ok("Все сервисы остановлены.")

    # Сохраняем отчёт
    if output:
        fmt = "html" if output.endswith(".html") else "md"
        report.save(output, fmt=fmt)
    else:
        # Сохраняем авто-отчёт
        report_path = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report.save(report_path)


# ──────────────────────────────────────────────────────────────────────
#  Entry Point
# ──────────────────────────────────────────────────────────────────────


async def cmd_check(
    service_name: Optional[str] = None,
    post_deploy: bool = False,
    source_dir: Optional[str] = None,
) -> int:
    """
    Команда `check` — проверка observability сервисов (SC-1, SC-2).

    Возвращает exit-code:
        0 — всё хорошо
        1 — ошибки
        2 — предупреждения (только в --post-deploy)
    """
    log_header(f"Observability Check{' (post-deploy)' if post_deploy else ''}")

    if source_dir and service_name:
        # Статический анализ исходного кода
        log_info(f"Статический анализ OTEL: {service_name} -> {source_dir}")
        result = await check_service_otel_by_source(service_name, source_dir)
        report = format_observability_report([result])
        print(report)
        if result.errors:
            return 1
        if result.warnings and post_deploy:
            return 2
        return 0

    # Динамическая проверка через API
    targets = []
    if service_name:
        if service_name not in SERVICE_KEYS:
            log_err(f"Неизвестный сервис: {service_name}. Доступны: {', '.join(sorted(SERVICE_KEYS))}")
            return 1
        svc_def_func = SERVICE_REGISTRY[service_name]()
        targets.append((service_name, svc_def_func.display_name, MODE_PORTS[service_name]))
    else:
        for key in sorted(SERVICE_KEYS):
            if key == "tei":
                continue  # TEI не проверяем на OTEL
            try:
                svc_def = SERVICE_REGISTRY[key]()
                targets.append((key, svc_def.display_name, MODE_PORTS[key]))
            except Exception:
                targets.append((key, key, MODE_PORTS.get(key, 0)))

    if not targets:
        log_err("Нет сервисов для проверки")
        return 1

    log_info(f"Проверяю {len(targets)} сервисов...")
    results: List[ObservabilityCheckResult] = []
    for key, name, port in targets:
        if not port:
            log_warn(f"Порт для {key} не указан, пропускаю")
            continue
        log_step(f"Проверка {name} (:{port})...")
        try:
            result = await check_service_otel(key, name, port)
            results.append(result)
            if result.passed:
                log_ok(f"{name} — OTEL OK")
            else:
                log_warn(f"{name} — проблемы")
                for e in result.errors:
                    log_err(f"  {e}")
                for w in result.warnings:
                    log_warn(f"  {w}")
        except Exception as e:
            log_err(f"{name}: ошибка проверки — {e}")
            results.append(ObservabilityCheckResult(name, key, port, passed=False,
                                                     errors=[str(e)]))

    # Вывод отчёта
    print()
    report_text = format_observability_report(results)
    print(report_text)

    # Сохраняем отчёт
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = BACKEND_DIR / "check_result" / f"observability_{ts}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_text, encoding="utf-8")
    log_ok(f"Отчёт сохранён: {report_path}")

    # Определяем exit-code
    errors = sum(1 for r in results if r.errors)
    warnings = sum(1 for r in results if r.warnings)
    passed = sum(1 for r in results if r.passed)

    log_info(f"Результаты: {passed}✅ / {warnings}⚠️ / {errors}❌")

    if errors > 0:
        return 1
    if warnings > 0 and post_deploy:
        return 2
    return 0


async def cmd_validate_har(args: argparse.Namespace) -> None:
    """Проверить HAR-файл против OpenAPI схемы."""
    har_path = args.har
    openapi_url = args.openapi_url
    service_key = args.service
    output = args.output

    # Определяем OpenAPI URL
    if not openapi_url:
        if service_key:
            if service_key not in MODE_PORTS:
                log_err(f"Неизвестный сервис: {service_key}. Допустимые: {', '.join(sorted(MODE_PORTS.keys()))}")
                return
            port = MODE_PORTS[service_key]
            openapi_url = f"http://127.0.0.1:{port}/openapi.json"
        else:
            log_err("Укажите --openapi-url или --service")
            return

    log_info(f"Загрузка OpenAPI схемы: {openapi_url}")
    validator = HarValidator(openapi_url)
    success = await validator.load_openapi()

    if not success:
        log_err("Ошибка загрузки OpenAPI схемы:")
        for err in validator._load_errors:
            log_err(f"  - {err}")
        return

    log_info(f"Загрузка HAR: {har_path}")
    if not os.path.exists(har_path):
        log_err(f"Файл не найден: {har_path}")
        return

    report = validator.validate_har(har_path)

    # Вывод отчёта
    report_text = format_har_report(report)
    print(report_text)

    # Сохранение
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_text, encoding="utf-8")
        log_ok(f"Отчёт сохранён: {output_path}")

    # Итоговая статистика
    if report.errors:
        log_err(f"Общих ошибок: {len(report.errors)}")
    if report.failed > 0:
        log_err(f"Провалено: {report.failed} / {report.total_entries}")
    elif report.skipped == report.total_entries:
        log_warn(f"Все записи пропущены (нет соответствия в OpenAPI)")
    else:
        log_ok(f"Все {report.passed} записей успешно прошли валидацию")


async def main():
    # ── Windows cp1251 → UTF-8 для Unicode box-drawing символов ──
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    args = parse_args()

    if args.command == "start":
        running = await cmd_start(
            mocks=args.mocks, with_real=args.with_real, timeout=args.timeout
        )
        if running:
            log_info("Сервисы запущены. Нажмите Ctrl+C для остановки.")
            try:
                while True:
                    await asyncio.sleep(1)
                    # Проверяем, живы ли процессы
                    for sp in list(running):
                        if sp.proc.poll() is not None:
                            log_warn(f"{sp.name} завершился (код {sp.proc.returncode})")
                            running.remove(sp)
                    if not running:
                        log_err("Все сервисы завершились.")
                        break
            except KeyboardInterrupt:
                log_info("\nОстановка...")
                for sp in running:
                    stop_service(sp)
                log_ok("Все сервисы остановлены.")
        return

    if args.command == "health":
        await cmd_health(port=args.port)
        return

    if args.command == "emulate":
        await cmd_emulate(
            gateway_url=args.gateway_url,
            mode=args.mode,
            output=args.output,
        )
        return

    if args.command == "all":
        await cmd_all(
            mocks=args.mocks,
            with_real=args.with_real,
            timeout=args.timeout,
            output=args.output,
        )
        return

    if args.command == "check":
        exit_code = await cmd_check(
            service_name=args.service,
            post_deploy=args.post_deploy,
            source_dir=args.source_dir,
        )
        if args.post_deploy:
            sys.exit(exit_code)
        return

    if args.command == "docker":
        await cmd_docker(
            action=args.action,
            build=args.build,
            detach=args.detach,
            services=args.services,
            pipelines=args.pipelines,
            skip_coverage=args.skip_coverage,
            skip_pipelines=args.skip_pipelines,
            skip_gateway_tests=args.skip_gateway_tests,
            gateway_tests=args.gateway_tests,
            db_only=args.db_only,
            spd=args.spd,
        )
        return

    if args.command == "validate-har":
        await cmd_validate_har(args)
        return

    if args.command == "report":
        # Загрузить сохранённый JSON и сформировать отчёт
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            log_err(f"Не удалось загрузить {args.input}: {e}")
            return

        report = Report()
        report.start_time = data.get("start_time", "")
        report.end_time = data.get("end_time", "")
        for sdata in data.get("services", []):
            sl = ServiceLog(**sdata)
            report.services[sl.service_key] = sl
        for hdata in data.get("health_results", []):
            report.health_results.append(HealthResult(**hdata))
        for cdata in data.get("api_calls", []):
            report.api_calls.append(ApiCallLog(**cdata))
        report.errors = data.get("errors", [])

        report.save(args.output, fmt=args.format)
        return

    # Нет команды — показываем help
    parser = argparse.ArgumentParser(
        description="PKB Neuroassistant — Service Launcher, Health Check & Report Generator"
    )
    parser.print_help()
