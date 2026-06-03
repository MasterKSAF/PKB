#!/usr/bin/env python3
"""
PKB Neuroassistant — Service Launcher, Health Check & Report Generator

Утилита для:
  1. Запуска сервисов (backend/gateway_service mocks и/или реальные сервисы)
  2. Проверки их работоспособности (health check)
  3. Эмуляции работы веб-интерфейса (API-вызовы, как из фронтенда)
  4. Сбора логов и формирования отчёта

Использование:
  python tools/service_checker.py --help
  python tools/service_checker.py all --report report.md   # запустить всё + отчёт
  python tools/service_checker.py report                   # сформировать отчёт из сохранённых логов
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO, Tuple

import httpx
import tempfile

# ──────────────────────────────────────────────────────────────────────
#  Config
# ──────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GATEWAY_DIR = PROJECT_ROOT / "backend" / "gateway_service"
BACKEND_DIR = PROJECT_ROOT / "backend"

# Все сервисы, которые мы умеем запускать/проверять
SERVICE_DEFS: Dict[str, Dict[str, Any]] = {
    "gateway": {
        "name": "Gateway (Mock All-in-One)",
        "type": "mock",
        "port": 8081,
        "health_url": "http://127.0.0.1:8081/api/v1/system/health",
        "cwd": GATEWAY_DIR,
        "run_cmd": lambda: [
            sys.executable,
            "-m",
            "uvicorn",
            "mocks.gateway:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8081",
        ],
    },
    "auth": {
        "name": "Auth Service",
        "type": "mock",
        "port": 8082,
        "health_url": "http://127.0.0.1:8082/api/v1/system/health",
        "cwd": GATEWAY_DIR,
        "run_cmd": lambda: [
            sys.executable,
            "-m",
            "uvicorn",
            "mocks.auth_service.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8082",
        ],
    },
    "orchestrator": {
        "name": "Orchestrator Service",
        "type": "mock",
        "port": 8081,
        "health_url": "http://127.0.0.1:8081/api/v1/monitor/health",
        "cwd": GATEWAY_DIR,
        "run_cmd": lambda: [
            sys.executable,
            "-m",
            "uvicorn",
            "mocks.orchestrator_service.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8081",
        ],
    },
    "query": {
        "name": "Query Service",
        "type": "mock",
        "port": 8083,
        "health_url": "http://127.0.0.1:8083/api/v1/system/health",
        "cwd": GATEWAY_DIR,
        "run_cmd": lambda: [
            sys.executable,
            "-m",
            "uvicorn",
            "mocks.query_service.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8083",
        ],
    },
    "registry": {
        "name": "Registry Service",
        "type": "mock",
        "port": 8084,
        "health_url": "http://127.0.0.1:8084/api/v1/classifiers",  # нет /health, проверяем через рабочий эндпоинт
        "cwd": GATEWAY_DIR,
        "run_cmd": lambda: [
            sys.executable,
            "-m",
            "uvicorn",
            "mocks.registry_service.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8084",
        ],
    },
    # Реальные сервисы (требуют настройки окружения)
    "integration": {
        "name": "Integration Service",
        "type": "real",
        "port": 8085,
        "health_url": "http://127.0.0.1:8085/api/v1/integration/",
        "cwd": BACKEND_DIR / "integration_service",
        "run_cmd": lambda: [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8085",
        ],
    },
    "registry_real": {
        "name": "Registry Service (real)",
        "type": "real",
        "port": 8084,
        "health_url": "http://127.0.0.1:8084/api/v1/",
        "cwd": BACKEND_DIR / "registry_service",
        "run_cmd": lambda: [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8084",
        ],
    },
    "parser": {
        "name": "Parser Service",
        "type": "real",
        "port": 8087,
        "health_url": "http://127.0.0.1:8087/health",
        "cwd": BACKEND_DIR / "parser_service",
        "run_cmd": lambda: [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8087",
        ],
    },
    "rag_builder": {
        "name": "RAG Builder Service",
        "type": "real",
        "port": 8090,
        "health_url": "http://127.0.0.1:8090/api/v1/rag/",
        "cwd": BACKEND_DIR,  # нужно из backend/ для корректного импорта модуля rag_builder
        "run_cmd": lambda: [
            sys.executable,
            "-m",
            "uvicorn",
            "rag_builder.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8090",
        ],
    },
    "rag_search": {
        "name": "RAG Search Service",
        "type": "real",
        "port": 8091,
        "health_url": "http://127.0.0.1:8091/",
        "cwd": BACKEND_DIR / "rag_search_service",
        "run_cmd": lambda: [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8091",
        ],
    },
}

# Тестовые учётные данные (из README gateway_service)
TEST_CREDENTIALS = {
    "username": "petrova@example.com",
    "password": "secret456",
}

# Стандартные заголовки
HEADERS_JSON = {"Content-Type": "application/json", "Accept": "application/json"}


# ──────────────────────────────────────────────────────────────────────
#  Data classes
# ──────────────────────────────────────────────────────────────────────


@dataclass
class ServiceProcess:
    """Запущенный процесс сервиса."""

    key: str
    name: str
    port: int
    proc: subprocess.Popen
    health_url: str
    type: str  # "mock" or "real"


@dataclass
class HealthResult:
    """Результат health check."""

    service_key: str
    service_name: str
    status: str  # "ok", "degraded", "error", "unreachable"
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    elapsed_ms: int = 0


@dataclass
class ApiCallLog:
    """Детальный лог одного API-вызова."""

    scenario: str
    method: str
    url: str
    status_code: int
    request_headers: Optional[Dict[str, str]] = None
    request_body: Optional[str] = None
    response_headers: Optional[Dict[str, str]] = None
    response_body: Optional[str] = None
    elapsed_ms: int = 0
    success: bool = False
    error: Optional[str] = None


@dataclass
class ServiceLog:
    """Собранные логи одного сервиса."""

    service_key: str
    service_name: str
    port: int
    pid: Optional[int] = None
    type: str = "mock"
    started: bool = False
    ready: bool = False
    log_tail: List[str] = field(default_factory=list)
    health_status: Optional[str] = None
    health_response: Optional[Dict[str, Any]] = None


class Report:
    """
    Отчёт о проверке сервисов.
    Собирает логи, health check и результаты эмуляции UI.
    """

    def __init__(self):
        self.start_time: str = utcnow()
        self.end_time: str = ""
        self.services: Dict[str, ServiceLog] = {}
        self.health_results: List[HealthResult] = []
        self.api_calls: List[ApiCallLog] = []
        self.errors: List[str] = []

    def close(self):
        self.end_time = utcnow()

    def add_service(self, sp: ServiceProcess):
        self.services[sp.key] = ServiceLog(
            service_key=sp.key,
            service_name=sp.name,
            port=sp.port,
            pid=sp.proc.pid,
            type=sp.type,
            started=True,
        )

    def set_service_ready(self, key: str, ready: bool):
        if key in self.services:
            self.services[key].ready = ready

    def add_service_log_line(self, key: str, line: str):
        if key in self.services:
            sl = self.services[key].log_tail
            sl.append(line)
            # Держим последние 100 строк
            if len(sl) > 100:
                sl[:] = sl[-100:]

    def set_service_health(self, key: str, status: str, response: Optional[Dict] = None):
        if key in self.services:
            self.services[key].health_status = status
            self.services[key].health_response = response

    def add_health_result(self, hr: HealthResult):
        self.health_results.append(hr)

    def add_api_call(self, call: ApiCallLog):
        self.api_calls.append(call)

    def add_error(self, msg: str):
        self.errors.append(msg)

    @property
    def duration_seconds(self) -> float:
        fmt = "%Y-%m-%dT%H:%M:%S"
        try:
            start = datetime.strptime(self.start_time[:19], fmt)
            end = datetime.strptime(self.end_time[:19], fmt)
            return (end - start).total_seconds()
        except (ValueError, IndexError):
            return 0.0

    # ── Markdown report ────────────────────────────────────────────

    def to_markdown(self) -> str:
        """Сформировать отчёт в Markdown."""
        lines: List[str] = []
        w = lines.append

        w(f"# Отчёт о проверке сервисов PKB Neuroassistant\n")
        w(f"")
        w(f"- **Начало:** {self.start_time}")
        w(f"- **Окончание:** {self.end_time}")
        w(f"- **Длительность:** {self.duration_seconds:.0f} с")
        w(f"")

        # ── 1. Сводка ──
        w(f"## 1. Сводка\n")

        total_services = len(self.services)
        started = sum(1 for s in self.services.values() if s.started)
        ready = sum(1 for s in self.services.values() if s.ready)
        healthy = sum(1 for s in self.services.values() if s.health_status == "ok")
        api_total = len(self.api_calls)
        api_ok = sum(1 for c in self.api_calls if c.success)
        api_fail = api_total - api_ok

        w(f"| Показатель | Значение |")
        w(f"|---|---|")
        w(f"| Сервисов в конфигурации | {total_services} |")
        w(f"| Запущено | {started} |")
        w(f"| Готовы к работе | {ready} |")
        w(f"| Health check ok | {healthy} |")
        w(f"| Ошибок | {len(self.errors)} |")
        w(f"| API-вызовов | {api_total} |")
        w(f"| API успешно | {api_ok} |")
        w(f"| API с ошибками | {api_fail} |")
        w(f"")

        # ── 2. Сервисы ──
        w(f"## 2. Состояние сервисов\n")
        w(f"| Сервис | Порт | Тип | Запущен | Готов | Health | Логов |")
        w(f"|---|---|---|---|---|---|---|")
        for key in sorted(self.services.keys()):
            s = self.services[key]
            w(f"| {s.service_name} | {s.port} | {s.type} "
              f"| {'✓' if s.started else '✗'} "
              f"| {'✓' if s.ready else '—'} "
              f"| {s.health_status or '—'} "
              f"| {len(s.log_tail)} |")
        w(f"")

        # ── 3. Health Check ──
        w(f"## 3. Health Check детально\n")
        if self.health_results:
            w(f"| Сервис | Статус | Время (ms) | Ответ/Ошибка |")
            w(f"|---|---|---|---|")
            for hr in self.health_results:
                icon = {"ok": "✓", "degraded": "⚠", "error": "✗", "unreachable": "✗"}.get(
                    hr.status, "?"
                )
                detail = ""
                if hr.response:
                    detail = json.dumps(hr.response, ensure_ascii=False)[:120]
                elif hr.error:
                    detail = hr.error
                w(f"| {icon} {hr.service_name} | {hr.status} | {hr.elapsed_ms} | {detail} |")
        else:
            w(f"_Health check не выполнялся_\n")
        w(f"")

        # ── 4. Эмуляция UI ──
        w(f"## 4. Результаты эмуляции веб-интерфейса\n")

        if self.api_calls:
            # Группируем по сценариям
            from collections import OrderedDict
            scenarios: Dict[str, List[ApiCallLog]] = OrderedDict()
            for call in self.api_calls:
                scenarios.setdefault(call.scenario, []).append(call)

            for scenario_name, calls in scenarios.items():
                scenario_ok = all(c.success for c in calls)
                icon = "✓" if scenario_ok else "✗"
                w(f"### {icon} {scenario_name}\n")

                for i, call in enumerate(calls):
                    status_icon = "✓" if call.success else "✗"
                    w(f"**{status_icon} {call.method} {call.url}** — "
                      f"HTTP {call.status_code} ({call.elapsed_ms}ms)\n")

                    if call.request_body:
                        try:
                            pretty = json.dumps(
                                json.loads(call.request_body),
                                ensure_ascii=False, indent=2
                            )
                            w(f"```json\n{pretty}\n```\n")
                        except (json.JSONDecodeError, TypeError):
                            w(f"```\n{call.request_body}\n```\n")

                    if call.response_body:
                        try:
                            pretty = json.dumps(
                                json.loads(call.response_body),
                                ensure_ascii=False, indent=2
                            )
                            w(f"**Ответ:**\n```json\n{pretty}\n```\n")
                        except (json.JSONDecodeError, TypeError):
                            w(f"**Ответ:**\n```\n{call.response_body[:500]}\n```\n")

                    if call.error:
                        w(f"> ⚠ Ошибка: {call.error}\n")

                    w(f"")
        else:
            w(f"_Эмуляция UI не выполнялась_\n")

        # ── 5. Логи сервисов ──
        w(f"## 5. Логи сервисов\n")
        for key in sorted(self.services.keys()):
            s = self.services[key]
            if s.log_tail:
                w(f"### {s.service_name} (порт {s.port})\n")
                w(f"Последние {len(s.log_tail)} строк:\n")
                w(f"```\n")
                for line in s.log_tail:
                    w(line.rstrip())
                w(f"\n```\n")
                w(f"")

        # ── 6. Ошибки ──
        if self.errors:
            w(f"## 6. Ошибки\n")
            for i, err in enumerate(self.errors, 1):
                w(f"{i}. {err}\n")
            w(f"")

        w(f"---\n")
        w(f"*Отчёт сгенерирован {utcnow()}*\n")

        return "\n".join(lines)

    def to_html(self) -> str:
        """Конвертировать Markdown-отчёт в простой HTML."""
        md = self.to_markdown()
        html = textwrap.dedent(f"""\
        <!DOCTYPE html>
        <html lang="ru">
        <head>
        <meta charset="utf-8">
        <title>Отчёт PKB Neuroassistant</title>
        <style>
          body {{ font-family: -apple-system, sans-serif; max-width: 1000px; margin: 40px auto; padding: 0 20px; }}
          h1 {{ color: #1a1a2e; }}
          h2 {{ color: #16213e; border-bottom: 1px solid #ddd; padding-bottom: 6px; }}
          table {{ border-collapse: collapse; width: 100%; }}
          th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
          th {{ background: #f5f5f5; }}
          pre {{ background: #f8f8f8; padding: 12px; border-radius: 4px; overflow-x: auto; }}
          code {{ font-size: 13px; }}
          .ok {{ color: #2e7d32; }} .fail {{ color: #c62828; }}
          blockquote {{ border-left: 4px solid #ffa726; padding-left: 12px; margin-left: 0; }}
        </style>
        </head>
        <body>
        {md_to_html(md)}
        </body>
        </html>
        """)
        return html

    def save(self, path: str, fmt: str = "md"):
        """Сохранить отчёт в файл."""
        path = Path(path)
        if fmt == "html":
            path.write_text(self.to_html(), encoding="utf-8")
        else:
            path.write_text(self.to_markdown(), encoding="utf-8")
        print(f"  ✓ Отчёт сохранён: {path.resolve()}")


# ──────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────


def md_to_html(md: str) -> str:
    """Простая конвертация Markdown → HTML (без external libs)."""
    import html as html_mod
    import re

    lines = md.split("\n")
    out: List[str] = []
    in_code = False

    for line in lines:
        stripped = line.strip()

        # Code block
        if stripped.startswith("```"):
            if in_code:
                out.append("</pre>")
                in_code = False
            else:
                lang = stripped[3:].strip()
                out.append(f"<pre><code>")
                in_code = True
            continue

        if in_code:
            out.append(html_mod.escape(line))
            continue

        # Headers
        if stripped.startswith("# "):
            out.append(f"<h1>{stripped[2:]}</h1>")
        elif stripped.startswith("## "):
            out.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("### "):
            out.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped.startswith("| ") and "---|---" in line:
            continue
        elif stripped.startswith("| ") and stripped.endswith(" |"):
            # Table row
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if any("---" in c for c in cells):
                continue
            out.append("<tr>" + "".join(f"<td>{html_mod.escape(c)}</td>" for c in cells) + "</tr>")
        elif "|---" in stripped:
            continue
        elif stripped.startswith("> "):
            out.append(f"<blockquote>{stripped[2:]}</blockquote>")
        elif stripped == "---":
            out.append("<hr>")
        elif stripped.startswith("- "):
            out.append(f"<li>{stripped[2:]}</li>")
        elif stripped.startswith("*Отчёт"):
            out.append(f"<p><em>{stripped.strip('*')}</em></p>")
        elif stripped == "":
            out.append("<br>")
        else:
            out.append(f"<p>{html_mod.escape(stripped)}</p>")

    return "\n".join(out)


# ──────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(msg: str, emoji: str = "•"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  {emoji} [{ts}] {msg}")


def log_ok(msg: str):
    log(msg, "✓")


def log_warn(msg: str):
    log(msg, "⚠")


def log_err(msg: str):
    log(msg, "✗")


def log_info(msg: str):
    log(msg, "ℹ")


def log_step(msg: str):
    log(msg, "→")


def log_header(title: str):
    width = 70
    print(f"\n  {'═' * width}")
    print(f"  ┃  {title}")
    print(f"  {'═' * width}\n")


# ──────────────────────────────────────────────────────────────────────
#  Service Management
# ──────────────────────────────────────────────────────────────────────


def find_available_python() -> str:
    """Найти доступный python с установленными зависимостями."""
    return sys.executable


def start_service(svc_key: str, svc_def: Dict[str, Any]) -> Optional[ServiceProcess]:
    """Запустить один сервис. Возвращает ServiceProcess или None."""
    name = svc_def["name"]
    port = svc_def["port"]
    cwd = svc_def["cwd"]
    run_cmd = svc_def["run_cmd"]()

    if not cwd.exists():
        log_warn(f"Директория не найдена: {cwd}. Пропускаем {name}")
        return None

    log_info(f"Запуск {name} (порт {port})...")

    try:
        proc = subprocess.Popen(
            run_cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return ServiceProcess(
            key=svc_key,
            name=name,
            port=port,
            proc=proc,
            health_url=svc_def["health_url"],
            type=svc_def.get("type", "mock"),
        )
    except FileNotFoundError as e:
        log_err(f"Не удалось запустить {name}: {e}")
        return None


def stop_service(sp: ServiceProcess):
    """Остановить один сервис."""
    try:
        sp.proc.terminate()
        sp.proc.wait(timeout=5)
        log_ok(f"Остановлен {sp.name} (PID {sp.proc.pid})")
    except subprocess.TimeoutExpired:
        sp.proc.kill()
        log_warn(f"Принудительно остановлен {sp.name} (PID {sp.proc.pid})")
    except Exception as e:
        log_err(f"Ошибка при остановке {sp.name}: {e}")


async def wait_for_service(
    sp: ServiceProcess, timeout: int = 30, poll_interval: float = 0.5
) -> bool:
    """Дождаться, пока сервис начнёт отвечать на health-check."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(sp.health_url)
                if resp.status_code < 500:
                    return True
        except (httpx.ConnectError, httpx.TimeoutException):
            pass

        # Проверим, жив ли процесс
        if sp.proc.poll() is not None:
            # Процесс умер — прочитаем последние строки лога
            stdout, _ = sp.proc.communicate(timeout=2)
            last_lines = stdout.split("\n")[-5:]
            log_err(f"Процесс {sp.name} завершился (код {sp.proc.returncode})")
            for line in last_lines:
                if line.strip():
                    print(f"         {line.strip()}")
            return False

        await asyncio.sleep(poll_interval)

    return False


async def check_service_health(
    sp: ServiceProcess, timeout: int = 10
) -> HealthResult:
    """Проверить health одного сервиса."""
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(sp.health_url)
        elapsed = int((time.time() - start) * 1000)
        data = resp.json() if resp.content else None
        status = "ok" if resp.status_code < 400 else "error"
        return HealthResult(
            service_key=sp.key,
            service_name=sp.name,
            status=status,
            response=data,
            elapsed_ms=elapsed,
        )
    except httpx.ConnectError:
        elapsed = int((time.time() - start) * 1000)
        return HealthResult(
            service_key=sp.key,
            service_name=sp.name,
            status="unreachable",
            error="Connection refused",
            elapsed_ms=elapsed,
        )
    except httpx.TimeoutException:
        elapsed = int((time.time() - start) * 1000)
        return HealthResult(
            service_key=sp.key,
            service_name=sp.name,
            status="unreachable",
            error="Timeout",
            elapsed_ms=elapsed,
        )
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return HealthResult(
            service_key=sp.key,
            service_name=sp.name,
            status="error",
            error=str(e),
            elapsed_ms=elapsed,
        )


# ──────────────────────────────────────────────────────────────────────
#  Web Interface Emulation
# ──────────────────────────────────────────────────────────────────────


class WebEmulator:
    """
    Эмуляция работы веб-интерфейса.
    Делает те же вызовы, что и фронтенд.
    Принимает URL базового сервиса (Orchestrator на порту 8081).
    """

    ORCHESTRATOR_URL: str = "http://127.0.0.1:8081"
    AUTH_URL: str = "http://127.0.0.1:8082"
    QUERY_URL: str = "http://127.0.0.1:8083"
    REGISTRY_URL: str = "http://127.0.0.1:8084"

    def __init__(self, mode: str = "individual", report: Optional[Report] = None):
        self.mode = mode
        self.report = report or Report()
        self.access_token: Optional[str] = None
        self.headers: Dict[str, str] = {**HEADERS_JSON}
        self.documents: List[Dict[str, Any]] = []
        self.client = httpx.AsyncClient(timeout=30)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    def _base(self) -> str:
        """Базовый URL в зависимости от режима."""
        return self.ORCHESTRATOR_URL

    def _auth_base(self) -> str:
        return self.AUTH_URL if self.mode == "individual" else self.ORCHESTRATOR_URL

    def _registry_base(self) -> str:
        return self.REGISTRY_URL if self.mode == "individual" else self.ORCHESTRATOR_URL

    def _query_base(self) -> str:
        return self.QUERY_URL if self.mode == "individual" else self.ORCHESTRATOR_URL

    async def _request(
        self,
        scenario: str,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        """
        Выполнить HTTP-запрос, замерить время и записать в отчёт.
        Возвращает response для дальнейшей обработки.
        """
        start = time.time()
        request_body = None
        if "json" in kwargs:
            request_body = json.dumps(kwargs["json"], ensure_ascii=False)
        elif "data" in kwargs and isinstance(kwargs["data"], dict):
            request_body = json.dumps(kwargs["data"], ensure_ascii=False)
        elif "files" in kwargs:
            request_body = f"<multipart: {list(kwargs.get('data', {}).keys())}>"

        try:
            resp = await getattr(self.client, method.lower())(url, **kwargs)
            elapsed = int((time.time() - start) * 1000)

            call = ApiCallLog(
                scenario=scenario,
                method=method.upper(),
                url=url,
                status_code=resp.status_code,
                request_body=request_body,
                response_body=resp.text if resp.content else None,
                elapsed_ms=elapsed,
                success=resp.status_code < 500,
            )
            self.report.add_api_call(call)
            return resp

        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            call = ApiCallLog(
                scenario=scenario,
                method=method.upper(),
                url=url,
                status_code=0,
                request_body=request_body,
                elapsed_ms=elapsed,
                success=False,
                error=str(e),
            )
            self.report.add_api_call(call)
            raise

    # ── Auth ────────────────────────────────────────────────────────

    async def scenario_auth(self) -> bool:
        """Сценарий аутентификации: логин + профиль + рефреш."""
        base = self._auth_base()

        log_step(f"POST {base}/api/v1/auth/token — получение JWT-токенов...")
        resp = await self._request(
            "auth", "post", f"{base}/api/v1/auth/token",
            json=TEST_CREDENTIALS,
        )
        if resp.status_code != 200:
            log_err(
                f"Аутентификация не удалась: HTTP {resp.status_code} — {resp.text[:200]}"
            )
            return False

        data = resp.json()
        self.access_token = data.get("access_token", "")
        self.headers["Authorization"] = f"Bearer {self.access_token}"
        log_ok(
            f"Токен получен (expires_in={data.get('expires_in', '?')}с, тип={data.get('token_type', '?')})"
        )

        # GET /auth/me — профиль
        log_step(f"GET {base}/api/v1/auth/me — профиль пользователя...")
        resp = await self._request(
            "auth", "get", f"{base}/api/v1/auth/me",
            headers=self.headers,
        )
        if resp.status_code == 200:
            profile = resp.json()
            log_ok(
                f"Профиль: {profile.get('email', '?')} — роль {profile.get('role', '?')}"
            )
        else:
            log_warn(f"Не удалось получить профиль: HTTP {resp.status_code}")

        return True

    # ── Classifiers ─────────────────────────────────────────────────

    async def scenario_classifiers(self) -> bool:
        """Сценарий: просмотр классификаторов."""
        base = self._registry_base()
        log_step(f"GET {base}/api/v1/classifiers — список классификаторов...")
        resp = await self._request(
            "classifiers", "get", f"{base}/api/v1/classifiers",
            headers=self.headers,
        )
        if resp.status_code != 200:
            log_warn(f"Не удалось получить классификаторы: HTTP {resp.status_code}")
            return False

        data = resp.json()
        items = self._extract_items(data)
        log_ok(f"Классификаторы: {len(items)} записей")
        if items:
            sample = items[0]
            log_info(
                f"  Пример: код={sample.get('code', '?')}, "
                f"название={sample.get('full_name', sample.get('name', '?'))[:60]}"
            )
        return True

    # ── Terminology ─────────────────────────────────────────────────

    async def scenario_terminology(self) -> bool:
        """Сценарий: просмотр терминологии."""
        base = self._registry_base()
        log_step(f"GET {base}/api/v1/terminology — список терминов...")
        resp = await self._request(
            "terminology", "get", f"{base}/api/v1/terminology",
            headers=self.headers,
        )
        if resp.status_code != 200:
            log_warn(f"Не удалось получить термины: HTTP {resp.status_code}")
            return False

        data = resp.json()
        items = self._extract_items(data)
        log_ok(f"Термины: {len(items)} записей")
        if items:
            sample = items[0]
            log_info(
                f"  Пример: термин={sample.get('term', '?')}, "
                f"определение={sample.get('definition', '?')[:80]}"
            )
        return True

    # ── Documents ───────────────────────────────────────────────────

    async def scenario_documents(self) -> bool:
        """Сценарий: работа с документами (список, детали)."""
        base = self._base()
        log_step(f"GET {base}/api/v1/documents — список документов...")
        resp = await self._request(
            "documents", "get", f"{base}/api/v1/documents",
            headers=self.headers,
        )
        if resp.status_code != 200:
            log_warn(f"Не удалось получить документы: HTTP {resp.status_code}")
            return False

        data = resp.json()
        items = self._extract_items(data)
        log_ok(f"Документы: {len(items)} записей")
        self.documents = items

        if items:
            # Детали первого документа
            doc_id = items[0].get("id")
            if doc_id:
                log_step(f"GET {base}/api/v1/documents/{doc_id} — детали документа...")
                resp = await self._request(
                    "documents", "get", f"{base}/api/v1/documents/{doc_id}",
                    headers=self.headers,
                )
                if resp.status_code == 200:
                    doc = resp.json()
                    doc_data = doc.get("data", doc)
                    log_ok(
                        f"Документ: {doc_data.get('doc_code', '?')} — "
                        f"{doc_data.get('title', doc_data.get('name', '?'))[:60]}"
                    )
                else:
                    log_warn(
                        f"Не удалось получить детали документа: HTTP {resp.status_code}"
                    )
        else:
            log_info("Нет документов. Возможно, требуется загрузить хотя бы один.")

        return True

    # ── Upload document ─────────────────────────────────────────────

    async def scenario_upload(self) -> bool:
        """Сценарий: загрузка документа (POST /documents)."""
        base = self._base()
        log_step(f"POST {base}/api/v1/documents — загрузка файла...")

        # Создаём тестовый файл
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(
                "Пробный документ для тестирования системы ПКБ Нейроассистент.\n"
                "Содержит тестовые данные для проверки работы сервисов."
            )
            tmp_path = Path(f.name)

        try:
            files = {
                "file": ("test_document.txt", tmp_path.read_bytes(), "text/plain"),
            }
            data = {
                "source_type": "OTHER",
                "title": "Тестовый документ",
            }

            resp = await self._request(
                "upload", "post", f"{base}/api/v1/documents",
                headers={"Authorization": self.headers.get("Authorization", "")},
                files=files,
                data=data,
            )

            if resp.status_code in (200, 201, 202):
                log_ok(f"Документ загружен: HTTP {resp.status_code}")
                resp_data = resp.json()
                log_info(f"  task_id={resp_data.get('task_id', '?')}")
                log_info(f"  status={resp_data.get('status', '?')}")
            else:
                log_warn(
                    f"Загрузка не удалась (ожидаемо при отсутствии реального MinIO): "
                    f"HTTP {resp.status_code}"
                )
                if resp.status_code == 422:
                    log_info("  (Mock-сервис может не поддерживать multipart-загрузку)")

        finally:
            if tmp_path.exists():
                tmp_path.unlink()

        return True

    # ── Chat & Search ───────────────────────────────────────────────

    async def scenario_search(self) -> bool:
        """Сценарий: текстовый поиск (POST /text/search)."""
        base = self._query_base()
        log_step(f"POST {base}/api/v1/text/search — поиск по тексту...")
        resp = await self._request(
            "search", "post", f"{base}/api/v1/text/search",
            headers=self.headers,
            json={"text": "толщина обшивки ледового пояса"},
        )
        if resp.status_code != 200:
            log_warn(f"Поиск не выполнен: HTTP {resp.status_code} — {resp.text[:200]}")
            return False

        data = resp.json()
        items = self._extract_items(data)
        log_ok(f"Поиск выполнен: {len(items)} результатов")
        if items:
            for i, item in enumerate(items[:3], 1):
                score = item.get("score", item.get("relevance", "?"))
                snippet = (
                    item.get("text", item.get("content", item.get("snippet", "")))[:80]
                )
                log_info(f"  [{i}] score={score} — {snippet}...")
        return True

    async def scenario_chat(self) -> bool:
        """Сценарий: чат-сессия (создать, отправить сообщение, longpoll)."""
        base = self._query_base()
        log_step(f"POST {base}/api/v1/chat/sessions — создание чат-сессии...")
        resp = await self._request(
            "chat", "post", f"{base}/api/v1/chat/sessions",
            headers=self.headers,
            json={"title": "Тестовая сессия"},
        )
        if resp.status_code not in (200, 201):
            log_warn(f"Не удалось создать сессию: HTTP {resp.status_code}")
            return False

        session = resp.json()
        session_id = session.get("id") or (session.get("data") or {}).get("id")
        if not session_id:
            session_id = session.get("session_id")
        log_ok(f"Сессия создана: ID={session_id}")

        if not session_id:
            log_warn("ID сессии не найден в ответе, пропускаем отправку сообщения")
            return True

        # Отправляем сообщение
        log_step(f"POST {base}/api/v1/chat/sessions/{session_id}/messages — отправка сообщения...")
        resp = await self._request(
            "chat", "post", f"{base}/api/v1/chat/sessions/{session_id}/messages",
            headers=self.headers,
            json={"text": "Какая толщина обшивки ледового пояса по ГОСТ?"},
        )

        if resp.status_code in (200, 201, 202):
            msg_data = resp.json()
            log_ok(f"Сообщение отправлено. Ответ: {json.dumps(msg_data)[:150]}")
        else:
            log_warn(
                f"Не удалось отправить сообщение: HTTP {resp.status_code} — {resp.text[:200]}"
            )

        return True

    # ── System Health ───────────────────────────────────────────────

    async def scenario_system_health(self) -> bool:
        """Сценарий: проверка системного health."""
        base = self._base()
        log_step(f"GET {base}/api/v1/system/health — общее состояние системы...")
        resp = await self._request(
            "system_health", "get", f"{base}/api/v1/system/health",
        )
        if resp.status_code != 200:
            log_warn(
                f"System health недоступен: HTTP {resp.status_code} — {resp.text[:200]}"
            )
            return False

        data = resp.json()
        status = data.get("status", "?")
        services = data.get("services", {})
        endpoints = data.get("endpoints_total", "?")
        log_ok(f"Система: {status.upper()}, endpoints: {endpoints}")
        for svc, st in services.items():
            icon = "✓" if st == "ok" else "✗"
            log_info(f"  {icon} {svc}: {st}")

        return True

    # ── Monitor ────────────────────────────────────────────────────

    async def scenario_monitor(self) -> bool:
        """Сценарий: мониторинг Orchestrator."""
        base = self._base()
        log_step(f"GET {base}/api/v1/monitor/health — health Orchestrator...")
        resp = await self._request(
            "monitor", "get", f"{base}/api/v1/monitor/health",
            headers=self.headers,
        )
        if resp.status_code != 200:
            log_warn(f"Monitor health недоступен: HTTP {resp.status_code}")
            return False

        data = resp.json()
        log_ok(f"Orchestrator health: {data.get('status', '?')}")
        return True

    # ── Run all scenarios ──────────────────────────────────────────

    async def run_all_scenarios(self):
        """Запустить все сценарии эмуляции UI."""
        log_header("Эмуляция работы веб-интерфейса")

        results: List[Tuple[str, bool]] = []

        # 1. Системный health (без токена)
        ok = await self.scenario_system_health()
        results.append(("system_health", ok))

        # 2. Аутентификация
        ok = await self.scenario_auth()
        results.append(("auth", ok))
        if not ok:
            log_err(
                "Аутентификация не пройдена — дальнейшие сценарии будут использовать "
                "заглушки"
            )

        # 3. Классификаторы
        ok = await self.scenario_classifiers()
        results.append(("classifiers", ok))

        # 4. Терминология
        ok = await self.scenario_terminology()
        results.append(("terminology", ok))

        # 5. Документы
        ok = await self.scenario_documents()
        results.append(("documents", ok))

        # 6. Загрузка документа
        ok = await self.scenario_upload()
        results.append(("upload", ok))

        # 7. Мониторинг
        ok = await self.scenario_monitor()
        results.append(("monitor", ok))

        # 8. Поиск
        ok = await self.scenario_search()
        results.append(("search", ok))

        # 9. Чат
        ok = await self.scenario_chat()
        results.append(("chat", ok))

        # ── Итог ──
        log_header("Результаты эмуляции UI")
        total = len(results)
        passed = sum(1 for _, ok in results if ok)
        for name, ok in results:
            icon = "✓" if ok else "✗"
            print(f"  {icon}  {name}")

        print(f"\n  {'─' * 40}")
        print(f"  Итого: {passed}/{total} сценариев успешно\n")

    @staticmethod
    def _extract_items(data: Any) -> List[Dict]:
        """Извлечь список элементов из разных форматов ответов."""
        if isinstance(data, dict):
            for key in ("items", "data", "results"):
                if key in data and isinstance(data[key], list):
                    return data[key]
        return data if isinstance(data, list) else []


# ──────────────────────────────────────────────────────────────────────
#  Log collector
# ──────────────────────────────────────────────────────────────────────


async def _collect_logs(report: Report, sp: ServiceProcess):
    """Фоновая задача: читает stdout процесса и сохраняет в отчёт."""
    try:
        while True:
            line = await asyncio.get_event_loop().run_in_executor(
                None, sp.proc.stdout.readline
            )
            if not line:
                break
            report.add_service_log_line(sp.key, line.rstrip())
    except (ValueError, AttributeError, RuntimeError):
        pass


# ──────────────────────────────────────────────────────────────────────
#  Main Application Logic
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
        default="http://127.0.0.1:8081",
        help="URL gateway (по умолч. http://127.0.0.1:8081)",
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


async def check_service_health_for_key(key: str, svc_def: Dict) -> HealthResult:
    """Проверить health сервиса по его определению."""
    sp = ServiceProcess(
        key=key,
        name=svc_def["name"],
        port=svc_def["port"],
        proc=None,  # type: ignore
        health_url=svc_def["health_url"],
        type=svc_def.get("type", "mock"),
    )
    return await check_service_health(sp)


async def cmd_emulate(
    gateway_url: str,
    mode: str = "individual",
    report: Optional[Report] = None,
    output: Optional[str] = None,
):
    """Запустить эмуляцию UI."""
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


if __name__ == "__main__":
    asyncio.run(main())
