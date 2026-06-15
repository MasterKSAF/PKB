#!/usr/bin/env python3
"""
PKB Neuroassistant — Service Checker: Docker Deployment
"""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from service_checker.core.config import (
    PROJECT_ROOT,
    BACKEND_DIR,
    DOCKER_DIR,
    DOCKER_COMPOSE_FILE,
    DOCKER_SERVICE_NAMES,
)
from service_checker.core.utils import log, log_ok, log_warn, log_err, log_info, log_header, log_step


# ── Docker: HTTP health-check endpoint'ы для каждого сервиса внутри контейнера ──
DOCKER_SUPERVISOR_SERVICES = {
    "auth":                (8082, "/openapi.json", "Auth Service"),
    "gateway":             (8080, "/openapi.json", "Gateway (Mock)"),
    "orchestrator":        (8081, "/openapi.json", "Orchestrator"),
    "query":               (8083, "/openapi.json", "Query Service"),
    "registry":            (8084, "/openapi.json", "Registry Service"),
    "integration":         (8085, "/openapi.json", "Integration Service"),
    "converter-validator": (8086, "/health", "Converter-Validator"),
    "parser":              (8087, "/health", "Parser Service"),
    "rag-builder":         (8090, "/openapi.json", "RAG Builder"),
    "rag-search":          (8091, "/openapi.json", "RAG Search"),
    "tei":                 (8092, "/health", "TEI (Embeddings)"),
}


def _check_docker() -> bool:
    """Проверить, установлен ли Docker и docker-compose."""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            log_err("Docker не найден.")
            return False
        log_ok(f"Docker: {result.stdout.strip()}")

        result2 = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True, text=True, timeout=10
        )
        if result2.returncode == 0:
            log_ok(f"Docker Compose: {result2.stdout.strip()}")
        else:
            log_err("Docker Compose plugin не найден.")
            return False

        return True
    except FileNotFoundError:
        log_err("Docker не найден.")
        return False
    except subprocess.TimeoutExpired:
        log_err("Проверка Docker завершилась по таймауту.")
        return False


# ── Маппинг старых имён volumes → новые (миграция project name docker→pkb) ──
_OLD_VOLUMES = {
    "docker_pg_data": "pkb_pg_data",
    "docker_minio_data": "pkb_minio_data",
    "docker_app_logs": "pkb_app_logs",
    "docker_tei_cache": "pkb_tei_cache",
}


def _migrate_volumes() -> None:
    """Проверить и перенести данные из старых volumes (docker_*) в новые (pkb_*).

    Вызывается перед каждым up/reset для плавной миграции при смене имени проекта.
    Если старый volume используется контейнерами — сначала удаляет их (docker rm -f).
    """
    for old_name, new_name in _OLD_VOLUMES.items():
        # Проверяем существование старого volume
        inspect = subprocess.run(
            ["docker", "volume", "inspect", old_name],
            capture_output=True, text=True, timeout=10,
        )
        if inspect.returncode != 0:
            continue  # старого volume нет — пропускаем

        # Новый volume уже существует? Если нет — создаём
        new_inspect = subprocess.run(
            ["docker", "volume", "inspect", new_name],
            capture_output=True, text=True, timeout=10,
        )
        if new_inspect.returncode != 0:
            subprocess.run(
                ["docker", "volume", "create", new_name],
                capture_output=True, timeout=10,
            )
            log_info(f"  📦 Создан новый volume: {new_name}")

        # Копируем данные из старого volume в новый
        log_info(f"  🔄 Миграция {old_name} → {new_name}...")
        copy = subprocess.run(
            ["docker", "run", "--rm",
             "-v", f"{old_name}:/from",
             "-v", f"{new_name}:/to",
             "alpine", "cp", "-a", "/from/.", "/to/"],
            capture_output=True, text=True, timeout=120,
        )
        if copy.returncode != 0:
            log_warn(f"    ⚠️  Не удалось скопировать данные: {copy.stderr.strip()}")
            # Продолжаем — старый volume не удаляем, раз копия не удалась
            continue

        # Принудительно удаляем контейнеры, использующие старый volume
        containers = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"volume={old_name}",
             "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=10,
        )
        for cname in containers.stdout.strip().split("\n"):
            cname = cname.strip()
            if not cname:
                continue
            log_info(f"    ⏹️  Удаление контейнера {cname} (использует {old_name})...")
            subprocess.run(
                ["docker", "rm", "-f", cname],
                capture_output=True, timeout=10,
            )

        # Удаляем старый volume
        rm_result = subprocess.run(
            ["docker", "volume", "rm", old_name],
            capture_output=True, text=True, timeout=10,
        )
        if rm_result.returncode != 0:
            log_warn(f"    ⚠️  Не удалось удалить {old_name}: {rm_result.stderr.strip()}")
        else:
            log_ok(f"  ✅ {old_name} → {new_name} (старый удалён)")


def _docker_action(
    action: str,
    services: List[str],
    build: bool = False,
    detach: bool = False,
) -> bool:
    """Выполнить действие с docker compose."""
    compose_file = DOCKER_COMPOSE_FILE

    if not compose_file.exists():
        log_err(f"Файл docker-compose.yml не найден: {compose_file}")
        return False

    cmd = ["docker", "compose", "-f", str(compose_file)]

    if action == "up":
        _migrate_volumes()
        cmd.append("up")
        if detach:
            cmd.append("-d")
        if build:
            cmd.append("--build")
        if services:
            cmd.extend(services)
    elif action == "down":
        cmd.append("down")
        if services:
            cmd.extend(services)
    elif action == "build":
        cmd.append("build")
        if services:
            cmd.extend(services)
    elif action == "restart":
        cmd.append("restart")
        if services:
            cmd.extend(services)
    elif action == "logs":
        cmd.extend(["logs", "--tail=100", "-f"])
        if services:
            cmd.extend(services)
    elif action == "ps":
        cmd.append("ps")
    elif action == "health":
        return _docker_health_check(services)

    log_step(f"Выполнение: {' '.join(cmd)}")

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(DOCKER_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in iter(proc.stdout.readline, ""):
            if line:
                print(f"  {line.rstrip()}")
        proc.wait()
        return proc.returncode == 0
    except KeyboardInterrupt:
        log_info("\nПолучен Ctrl+C. Останавливаем...")
        return True
    except Exception as e:
        log_err(f"Ошибка выполнения Docker Compose: {e}")
        return False


def _docker_health_check(services: List[str]) -> bool:
    """Проверить состояние сервисов через Docker."""
    compose_file = DOCKER_COMPOSE_FILE

    if not compose_file.exists():
        log_err(f"Файл docker-compose.yml не найден: {compose_file}")
        return False

    log_header("Docker Health Check: статус контейнеров")

    ps_cmd = ["docker", "compose", "-f", str(compose_file), "ps", "--format", "json"]
    try:
        result = subprocess.run(ps_cmd, capture_output=True, text=True, timeout=15)

        if result.returncode != 0:
            log_err("Не удалось получить статус контейнеров")
            return False

        import json as _json
        try:
            containers = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    containers.append(_json.loads(line))

            if not containers:
                log_info("Нет запущенных контейнеров.")
                return False

            print(f"  {'Контейнер':<30} {'Статус':<50} {'Порты':<20}")
            print(f"  {'─'*30} {'─'*50} {'─'*20}")
            for c in containers:
                name = c.get("Name", c.get("Service", "?"))
                status = c.get("Status", "?")
                ports = c.get("Ports", "")
                is_running = "Up" in status or "running" in status.lower()
                icon = "✓" if is_running else "✗"
                print(f"  {icon} {name:<29} {status:<49} {ports:<19}")

        except _json.JSONDecodeError:
            print(result.stdout)
            return result.returncode == 0

    except subprocess.TimeoutExpired:
        log_err("Проверка контейнеров завершилась по таймауту.")
        return False
    except Exception as e:
        log_err(f"Ошибка: {e}")
        return False

    # ── HTTP health check Python-сервисов (с ожиданием готовности) ──
    log_header("Docker Health Check: HTTP-endpoint'ы Python-сервисов")
    all_ok = True
    for svc_key, (port, path, display_name) in DOCKER_SUPERVISOR_SERVICES.items():
        url = f"http://127.0.0.1:{port}{path}"
        ok = False
        for attempt in range(3):  # до 6 секунд (3 + 3 попытки по 1с)
            try:
                resp = httpx.get(url, timeout=3)
                if resp.status_code < 500:
                    log_ok(f"{display_name:<25} :{port} — HTTP {resp.status_code}")
                    ok = True
                    break
                if attempt < 2:
                    time.sleep(1)
            except httpx.ConnectError:
                if attempt < 2:
                    time.sleep(1)
                else:
                    log_err(f"{display_name:<25} :{port} — Connection refused")
            except httpx.TimeoutException:
                if attempt < 2:
                    time.sleep(1)
                else:
                    log_err(f"{display_name:<25} :{port} — Timeout")
            except Exception as e:
                if attempt < 2:
                    time.sleep(1)
                else:
                    log_err(f"{display_name:<25} :{port} — {e}")
        if not ok:
            all_ok = False

    # ── Supervisorctl status ──
    log_header("Docker Health Check: supervisord (все Python-процессы)")
    try:
        use_shell = sys.platform == "win32"
        sup_cmd = [
            "docker", "compose", "-f", str(compose_file),
            "exec", "-T", "app", "supervisorctl", "status"
        ]
        sup_result = subprocess.run(
            sup_cmd, capture_output=True, text=True, timeout=15,
            shell=use_shell,
        )
        if sup_result.returncode == 0 and sup_result.stdout.strip():
            for line in sup_result.stdout.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0]
                    state = parts[1]
                    icon = "✓" if state == "RUNNING" else "✗"
                    print(f"  {icon} {name:<25} {line[len(name):]}")
                    if state != "RUNNING":
                        all_ok = False
        else:
            # Fallback: попробовать supervisorctl с явным путём к конфигу
            log_info("Пробуем supervisorctl с -c /etc/supervisor/conf.d/supervisord.conf...")
            try:
                sup_cmd_c = [
                    "docker", "compose", "-f", str(compose_file),
                    "exec", "-T", "app", "supervisorctl",
                    "-c", "/etc/supervisor/conf.d/supervisord.conf", "status"
                ]
                sup_result_c = subprocess.run(
                    sup_cmd_c, capture_output=True, text=True, timeout=15,
                    shell=use_shell,
                )
                if sup_result_c.returncode == 0 and sup_result_c.stdout.strip():
                    for line in sup_result_c.stdout.strip().split("\n"):
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split()
                        if len(parts) >= 2:
                            name = parts[0]
                            state = parts[1]
                            icon = "✓" if state == "RUNNING" else "✗"
                            print(f"  {icon} {name:<25} {line[len(name):]}")
                            if state != "RUNNING":
                                all_ok = False
                else:
                    log_warn(f"supervisorctl (-c) вернул код {sup_result_c.returncode}: {sup_result_c.stderr.strip()[:100]}")
                    log_info("Читаем логи supervisord из контейнера...")
                    try:
                        log_cmd = ["docker", "compose", "-f", str(compose_file),
                                   "exec", "-T", "app", "cat", "/var/log/supervisor/supervisord.log"]
                        log_result = subprocess.run(
                            log_cmd, capture_output=True, text=True, timeout=10,
                            shell=use_shell,
                        )
                        lines = log_result.stdout.strip().split("\n")
                        for line in lines[-8:]:
                            if line.strip():
                                print(f"  {line.strip()}")
                    except Exception:
                        pass
            except subprocess.TimeoutExpired:
                log_warn("supervisorctl timeout (контейнер app не запущен?)")
            except Exception as e:
                log_warn(f"supervisorctl error: {e}")
    except subprocess.TimeoutExpired:
        log_warn("supervisorctl timeout (контейнер app не запущен?)")
    except Exception as e:
        log_warn(f"supervisorctl error: {e}")

    # ── Supervisor .err log check ──
    log_header("Docker Health Check: ошибки в supervisor .err логах")
    has_errors = False
    err_files = [
        "auth.err", "gateway.err", "orchestrator.err", "query.err",
        "registry.err", "integration.err", "converter_validator.err",
        "parser.err", "ocr.err", "rag_builder.err", "rag_search.err",
    ]
    try:
        use_shell = sys.platform == "win32"
        for err_file in err_files:
            try:
                err_cmd = ["docker", "compose", "-f", str(compose_file),
                           "exec", "-T", "app", "cat", f"/var/log/supervisor/{err_file}"]
                err_result = subprocess.run(
                    err_cmd, capture_output=True, text=True, timeout=10,
                    shell=use_shell,
                )
                if err_result.returncode == 0 and err_result.stdout.strip():
                    raw_lines = err_result.stdout.strip().split("\n")
                    # Фильтруем: INFO/WARNING логи — не ошибки
                    error_lines = [
                        l for l in raw_lines
                        if not l.startswith("INFO:") and not l.startswith("WARNING:")
                    ]
                    # Если после фильтра остались только пустые или ничего — не показываем
                    if not error_lines:
                        continue
                    lines = error_lines
                    preview = "\n  ".join(lines[:3])
                    log_warn(f"{err_file} — {len(lines)} строк(и) ошибок:")
                    print(f"  {preview}")
                    if len(lines) > 3:
                        print(f"  ... и ещё {len(lines) - 3} строк(и)")
                    has_errors = True
            except Exception:
                pass
        if not has_errors:
            log_ok("Все .err логи пусты — ошибок нет")
    except Exception:
        pass

    print()
    if all_ok:
        log_ok("Все Python-сервисы работают!")
    else:
        log_warn("Некоторые сервисы недоступны. Смотрите логи выше.")

    return all_ok


async def _docker_collect_logs(services: List[str] = None) -> bool:
    """Собрать все логи (info + error) из supervisor в отчёт."""
    log_header("Docker: сбор логов (info + error)")

    check_result_dir = BACKEND_DIR / "check_result"
    check_result_dir.mkdir(parents=True, exist_ok=True)

    report_path = check_result_dir / "errors.md"

    container_name = "pkb-neuro"
    docker_cmd_prefix = ["docker", "exec", container_name]

    lines = []
    lines.append("# Supervisor Logs\n")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).isoformat()}\n")
    lines.append(f"\n---\n")

    # Проверяем, запущен ли контейнер
    try:
        inspect = subprocess.run(
            ["docker", "inspect", container_name, "--format", "{{.State.Status}}"],
            capture_output=True, text=True, timeout=10,
        )
        if inspect.returncode != 0 or inspect.stdout.strip() != "running":
            log_err(f"Контейнер {container_name} не запущен")
            lines.append(f"_Контейнер {container_name} не запущен. Логи недоступны._\n")
            report_text = "\n".join(lines)
            report_path.write_text(report_text, encoding="utf-8")
            log_ok(f"Отчёт сохранён: {report_path}")
            return True
    except Exception as e:
        log_err(f"Не удалось проверить контейнер: {e}")
        lines.append(f"_Ошибка проверки контейнера: {e}_\n")
        report_text = "\n".join(lines)
        report_path.write_text(report_text, encoding="utf-8")
        log_ok(f"Отчёт сохранён: {report_path}")
        return True

    # Ищем все файлы в /var/log/supervisor
    find_cmd = docker_cmd_prefix + [
        "find", "/var/log/supervisor",
        "-type", "f", "-not", "-name", "supervisord.log"
    ]
    try:
        result = subprocess.run(
            find_cmd, capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0 or not result.stdout.strip():
            log_info("Нет файлов в /var/log/supervisor/")
            lines.append("_Нет файлов логов._\n")
        else:
            log_files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]

            entries = []  # (fname, log_path, label, content, anchor)
            has_errors = False

            for log_file in sorted(log_files):
                fname = Path(log_file).name
                anchor = fname.replace(".", "-")

                # Читаем только последние 50 строк — весь файл может быть гигантским
                read_cmd = docker_cmd_prefix + ["tail", "-50", log_file]
                try:
                    r = subprocess.run(
                        read_cmd, capture_output=True, encoding='utf-8', errors='replace', timeout=30,
                    )
                    content = r.stdout.strip()
                except Exception as e:
                    entries.append((fname, log_file, "⚠️ ERROR", f"(ошибка чтения: {e})", anchor))
                    has_errors = True
                    continue

                if content and re.search(r"(Traceback|Error|ERROR|except|panic|FATAL)", content, re.IGNORECASE):
                    entries.append((fname, log_file, "❌ ERROR", content, anchor))
                    has_errors = True
                else:
                    entries.append((fname, log_file, "ℹ️ INFO", content, anchor))

            # 2. Навигация (TOC)
            toc_items = [f"- [{label} — {fname}](#{anchor})" for fname, _, label, _, anchor in entries]
            lines.append("## 📋 Быстрая навигация\n\n")
            lines.append("\n".join(toc_items) + "\n")
            lines.append("\n---\n")

            # 3. INFO-файлы не выводим — они только шум (access-логи каждого запроса).
            # Если в файле нет ERROR-паттерна, он не представляет диагностической ценности.
            lines.append("## ℹ️ Info-логи\n")
            info_count = sum(1 for _, _, label, _, _ in entries if label == "ℹ️ INFO")
            if info_count:
                names = [fname for fname, _, label, _, _ in entries if label == "ℹ️ INFO"]
                lines.append(f"_{info_count} файл(ов) без ошибок (пропущены): {', '.join(names)}_\n")
            else:
                lines.append("_Нет info-файлов._\n")

            # 4. Выводим ERROR-файлы только если есть ошибки
            if has_errors:
                lines.append("\n## ❌ Error-логи\n")
                err_count = 0
                for fname, log_path, label, content, anchor in entries:
                    if label not in ("❌ ERROR", "⚠️ ERROR"):
                        continue
                    err_count += 1
                    lines.append(f"\n### {anchor}\n")
                    lines.append(f"**{label}** — `{log_path}`\n")
                    lines.append(f"\n```\n")
                    if content:
                        lines.append(content)
                    else:
                        lines.append("(пусто)")
                    lines.append("\n```\n")

                if err_count == 0:
                    lines.append("_Нет error-файлов._\n")
            else:
                lines.append("\n---\n")
                lines.append("_✅ Ошибки не обнаружены. Все файлы содержат только info-сообщения._\n")

    except Exception as e:
        log_err(f"Не удалось получить список логов: {e}")
        lines.append(f"_Ошибка получения логов: {e}_\n")

    # Сохраняем отчёт в любом случае
    report_text = "\n".join(lines)
    report_path.write_text(report_text, encoding="utf-8")
    log_ok(f"Отчёт сохранён: {report_path}")

    return True


async def _docker_run_coverage() -> bool:
    """Запустить API Coverage Test для Docker-окружения. Возвращает True при успехе."""
    log_header("Docker: API Coverage Test")

    # Очищаем supervisor-логи перед запуском тестов — чтобы в отчёт
    # попали только логи текущего запуска, а не накопленные за дни
    log_info("Очистка supervisor-логов в контейнере...")
    try:
        subprocess.run(
            ["docker", "exec", "pkb-neuro", "bash", "-c",
             "truncate -s 0 /var/log/supervisor/*.log /var/log/supervisor/*.err 2>/dev/null || true"],
            capture_output=True, timeout=15,
        )
    except Exception:
        pass  # если контейнер не запущен — не критично

    check_result_dir = BACKEND_DIR / "check_result"
    check_result_dir.mkdir(parents=True, exist_ok=True)

    output_path = check_result_dir / "api_coverage.md"

    log_info(f"Отчёт будет сохранён: {output_path}")

    # Импортируем напрямую ApiCoverageTester
    sys.path.insert(0, str(BACKEND_DIR))
    from service_checker.api_coverage_test import ApiCoverageTester

    log_path = check_result_dir / "errors.md"

    try:
        tester = ApiCoverageTester(base_host="127.0.0.1")
        await tester.run_all()
        report = tester.generate_report(log_report_path=str(log_path.name))
        output_path.write_text(report, encoding="utf-8")
        await tester.close()
        log_ok(f"API Coverage отчёт сохранён: {output_path}")
        return True
    except Exception as e:
        log_err(f"Ошибка при запуске coverage test: {e}")
        return False


async def _docker_run_pipeline() -> Dict[str, Any]:
    """Запустить Pipeline Testing для Docker-окружения. Возвращает результаты пайплайнов."""
    log_header("Docker: Pipeline Testing")

    sys.path.insert(0, str(BACKEND_DIR))
    from service_checker.pipelines import PIPELINE_REGISTRY, PipelineRunner

    results: Dict[str, Any] = {}
    runner = PipelineRunner(base_host="127.0.0.1")
    try:
        for name, cls in sorted(PIPELINE_REGISTRY.items()):
            log_info(f"Запуск пайплайна: {name}...")
            pipeline = cls()
            result = await runner.run(pipeline, skip_ping=False)
            results[name] = result
    except Exception as e:
        log_err(f"Ошибка при запуске pipeline test: {e}")
    finally:
        await runner.close()

    return results
