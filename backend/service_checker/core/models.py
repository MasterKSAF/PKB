"""
PKB Neuroassistant — Service Checker Data Models.
"""

from __future__ import annotations

import json
import subprocess
import textwrap
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


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


def utcnow() -> str:
    """Текущее время в UTC ISO-формате."""
    return datetime.now(timezone.utc).isoformat()


def md_to_html(md: str) -> str:
    """Простая конвертация Markdown → HTML (без external libs)."""
    import html as html_mod
    import re

    lines = md.split("\n")
    out: List[str] = []
    in_code = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                out.append("</pre>")
                in_code = False
            else:
                out.append("<pre><code>")
                in_code = True
            continue

        if in_code:
            out.append(html_mod.escape(line))
            continue

        if stripped.startswith("# "):
            out.append(f"<h1>{stripped[2:]}</h1>")
        elif stripped.startswith("## "):
            out.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("### "):
            out.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped.startswith("| ") and "---|---" in line:
            continue
        elif stripped.startswith("| ") and stripped.endswith(" |"):
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

        w(f"## 4. Результаты эмуляции веб-интерфейса\n")
        if self.api_calls:
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
