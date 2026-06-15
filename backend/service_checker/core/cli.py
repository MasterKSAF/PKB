#!/usr/bin/env python3
"""
PKB Neuroassistant — Service Checker: CLI Entry Point & Commands
"""

from __future__ import annotations

import argparse
import asyncio
import json
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
        default="http://127.0.0.1:8080",
        help="URL gateway (по умолч. http://127.0.0.1:8080)",
    )
    p_emulate.add_argument(
        "--mode",
        choices=["individual", "gateway"],
        default="individual",
        help="Режим: individual (порты 8081-8084) или gateway (всё на одном)",
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
        help="Список конкретных сервисов (по умолч. все)",
    )
    p_docker.add_argument(
        "--db-only",
        action="store_true",
        help="Запустить только PostgreSQL",
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
        f"{gateway_url}/api/v1/monitor/health",
        f"{gateway_url}/api/v1/",
    ]
    alive = False
    async with httpx.AsyncClient(timeout=5) as client:
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
    db_only: bool = False,
):
    """Развернуть систему через Docker Compose."""
    services = services or []

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

    if action == "patch-rag":
        log_header("🔧 Патч RAG Builder: создание таблиц и alembic_version")
        from service_checker.docker.patch_rag_tables import patch_rag_tables
        ok = await patch_rag_tables()
        if ok:
            log_ok("RAG таблицы готовы")
        return

    if action == "coverage":
        log_header("📋 Coverage + Logs")
        ok = await _docker_run_coverage()
        if ok:
            log_info("Собираем логи ошибок...")
            await _docker_collect_logs(target_services)
        return

    if action == "full-report":
        log_header("📋 Полный отчёт: Coverage + Pipeline + Сводная таблица")
        check_result_dir = BACKEND_DIR / "check_result"
        check_result_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

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
        try:
            sys.path.insert(0, str(BACKEND_DIR))
            from service_checker.core.api_coverage_test import ApiCoverageTester

            # 1a. RAG Builder patch (создание таблиц, если нет)
            try:
                from service_checker.docker.patch_rag_tables import patch_rag_tables
                log_info("Проверка RAG таблиц...")
                await patch_rag_tables()
            except Exception as e:
                log_warn(f"RAG patch не сработал: {e}")

            log_info("Очистка supervisor-логов...")
            try:
                subprocess.run(
                    ["docker", "exec", "pkb-neuro", "bash", "-c",
                     "truncate -s 0 /var/log/supervisor/*.log /var/log/supervisor/*.err 2>/dev/null || true"],
                    capture_output=True, timeout=15,
                )
            except Exception:
                pass

            log_info("Запуск API Coverage Test...")
            tester = ApiCoverageTester(base_host="127.0.0.1")
            cov_results = await tester.run_all()
            cov_report = tester.generate_report(db_result=db_result)
            cov_path = check_result_dir / "api_coverage.md"
            cov_path.write_text(cov_report, encoding="utf-8")
            log_ok(f"API Coverage отчёт сохранён: {cov_path}")
        except Exception as e:
            log_err(f"Ошибка coverage: {e}")
        finally:
            if tester:
                await tester.close()

        # 3. Pipeline
        pipe_results: Dict[str, Any] = {}
        runner = None
        try:
            sys.path.insert(0, str(BACKEND_DIR))
            from service_checker.pipelines import PIPELINE_REGISTRY, PipelineRunner

            log_info("Запуск Pipeline Testing...")
            runner = PipelineRunner(base_host="127.0.0.1")
            for name, cls in sorted(PIPELINE_REGISTRY.items()):
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

        # 4. Full report
        if cov_results or pipe_results:
            if cov_results is None:
                cov_results = {}
            full_report = _generate_full_report(cov_results, pipe_results, timestamp, db_result=db_result)
            full_path = check_result_dir / "full_report.md"
            full_path.write_text(full_report, encoding="utf-8")
            log_ok(f"Сводный отчёт сохранён: {full_path}")

            # Собираем логи ошибок
            log_info("Собираем логи ошибок...")
            await _docker_collect_logs(target_services)
        return

    if action == "logs":
        await _docker_collect_logs(target_services)
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
        "http://127.0.0.1:8081",
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

    if args.command == "docker":
        await cmd_docker(
            action=args.action,
            build=args.build,
            detach=args.detach,
            services=args.services,
            db_only=args.db_only,
        )
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
