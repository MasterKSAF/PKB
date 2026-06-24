#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline Testing (Сквозные сценарии)

Проверяет сквозные бизнес-пайплайны обработки документов с реальным PDF-файлом.
В отличие от API Coverage Test (каждый эндпоинт изолированно), этот режим
эмулирует реальную работу системы: загрузка → парсинг → конвертация → регистрация → индексация → поиск.

Запуск:
  python pipeline_test.py list                        # Список пайплайнов
  python pipeline_test.py run-all                     # Все пайплайны
  python pipeline_test.py run <name>                  # Конкретный пайплайн
  python pipeline_test.py run <name1,name2>           # Несколько
  python pipeline_test.py run-all --skip-ping         # Без предварительного ping
  python pipeline_test.py run-all -o report.md        # С сохранением отчёта

Основано на: service_checker/description.md → "3. pipeline_test.py — Pipeline Testing"
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Добавляем backend/ в sys.path (нужно для импорта service_checker как пакета)
_backend = Path(__file__).resolve().parent.parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from service_checker.pipelines import PIPELINE_REGISTRY, PipelineRunner, PipelineDef, PipelineResult, PipelineContext


# ──────────────────────────────────────────────────────────────────────
#  CLI
# ──────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PKB Neuroassistant — Pipeline Testing (Сквозные сценарии)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Примеры:\n"
            "  python pipeline_test.py list\n"
            "  python pipeline_test.py run document_processing\n"
            "  python pipeline_test.py run-all\n"
            "  python pipeline_test.py run-all -o report.md\n"
        ),
    )

    sub = parser.add_subparsers(dest="command", help="Команда")

    # list
    sub.add_parser("list", help="Список доступных пайплайнов")

    # run
    run_parser = sub.add_parser("run", help="Запустить один или несколько пайплайнов")
    run_parser.add_argument("names", help="Имя(ена) пайплайнов через запятую")

    # run-all
    all_parser = sub.add_parser("run-all", help="Запустить все пайплайны")
    all_parser.add_argument("--skip-ping", action="store_true", help="Пропустить предварительный ping сервисов")

    # Общие опции
    for p in (run_parser, all_parser):
        p.add_argument("-o", "--output", default=None, help="Сохранить отчёт в .md файл")
        p.add_argument("--host", default="127.0.0.1", help="Хост для подключения (по умолч. 127.0.0.1)")
        p.add_argument("--timeout", type=int, default=30, help="Таймаут HTTP-запроса (сек)")

    return parser.parse_args()


async def cmd_list() -> None:
    """Вывести список доступных пайплайнов."""
    print("\n  Доступные пайплайны:\n")
    print(f"  {'Имя':25s} {'Описание':50s} {'Сервисы':30s} {'Шагов':>6s}")
    print(f"  {'─'*25} {'─'*50} {'─'*30} {'─'*6}")
    for name, cls in sorted(PIPELINE_REGISTRY.items()):
        pipeline = cls()
        services = ", ".join(pipeline.services)
        step_count = len(pipeline.build_steps(PipelineContext())) if hasattr(pipeline, "build_steps") else 0
        print(f"  {name:25s} {pipeline.description:50s} {services:30s} {step_count:6d}")
    print()


async def cmd_run(
    names: List[str],
    host: str = "127.0.0.1",
    timeout: int = 30,
    skip_ping: bool = False,
    output: Optional[str] = None,
) -> Dict[str, PipelineResult]:
    """Запустить указанные пайплайны."""
    results: Dict[str, PipelineResult] = {}

    runner = PipelineRunner(base_host=host, timeout=timeout)
    try:
        for name in names:
            if name not in PIPELINE_REGISTRY:
                print(f"\n  ✗ Пайплайн '{name}' не найден. Доступны: {', '.join(PIPELINE_REGISTRY.keys())}")
                continue

            pipeline_cls = PIPELINE_REGISTRY[name]
            pipeline = pipeline_cls()
            result = await runner.run(pipeline, skip_ping=skip_ping)
            results[name] = result

        # Итоговая сводная таблица
        if results:
            print("\n" + "=" * 70)
            print("  ИТОГОВАЯ ТАБЛИЦА ПАЙПЛАЙНОВ")
            print("=" * 70)
            print_report_table(results)

            # Сохраняем отчёт
            report = generate_report(results)
            if output:
                out_path = Path(output)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(report, encoding="utf-8")
                print(f"\n  📄 Отчёт сохранён: {out_path.resolve()}")
            else:
                # Автосохранение в backend/check_result/ (рядом с service_checker/)
                check_dir = Path(__file__).resolve().parent.parent.parent / "check_result"
                check_dir.mkdir(parents=True, exist_ok=True)
                report_path = check_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                report_path.write_text(report, encoding="utf-8")
                print(f"\n  📄 Отчёт сохранён: {report_path.resolve()}")

    finally:
        await runner.close()

    return results


async def cmd_run_all(
    host: str = "127.0.0.1",
    timeout: int = 30,
    skip_ping: bool = False,
    output: Optional[str] = None,
) -> Dict[str, PipelineResult]:
    """Запустить все доступные пайплайны."""
    return await cmd_run(
        names=list(PIPELINE_REGISTRY.keys()),
        host=host,
        timeout=timeout,
        skip_ping=skip_ping,
        output=output,
    )


# ──────────────────────────────────────────────────────────────────────
#  Report Generation
# ──────────────────────────────────────────────────────────────────────


def print_report_table(results: Dict[str, PipelineResult]) -> None:
    """Вывести итоговую таблицу пайплайнов в консоль."""
    if not results:
        return

    # Транспонированная таблица: строки — метрики, колонки — пайплайны
    headers = ["Показатель"] + list(results.keys())
    col_count = len(headers)

    print(f"\n  {' | '.join(f'{h:25s}' if i == 0 else f'{h:20s}' for i, h in enumerate(headers))}")
    print(f"  {' | '.join(['─' * 25] + ['─' * 20] * (col_count - 1))}")

    # Ping
    row_ping = ["Ping"]
    for r in results.values():
        row_ping.append("✅" if r.ping_ok else "❌")

    # API calls
    row_api = ["API calls"]
    for r in results.values():
        row_api.append(f"{r.passed_steps}/{r.total_steps}")

    # Pipeline
    row_pipeline = ["Pipeline"]
    for r in results.values():
        if r.passed:
            row_pipeline.append("✅ Пройден")
        elif r.error:
            row_pipeline.append(f"❌ {r.error[:25]}")
        else:
            row_pipeline.append(f"❌ {r.failed_steps} шагов с ошибками")

    # Status
    row_status = ["Status"]
    for r in results.values():
        row_status.append("✅" if r.passed else "❌")

    for row in (row_ping, row_api, row_pipeline, row_status):
        print(f"  {' | '.join(f'{cell:25s}' if i == 0 else f'{cell:20s}' for i, cell in enumerate(row))}")


def generate_report(results: Dict[str, PipelineResult]) -> str:
    """Сформировать Markdown-отчёт по результатам пайплайнов."""
    lines: List[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append("# Pipeline Testing Report\n")
    lines.append(f"**Generated:** {now}\n")
    lines.append("---\n")

    # ── 1. Сводная таблица ──
    lines.append("## 📊 Summary\n")
    lines.append("| Показатель | " + " | ".join(results.keys()) + " |")
    lines.append("|-----------|" + "|".join(":---------------------:" for _ in results) + "|")

    # Ping
    ping_row = "| **Ping** |"
    for r in results.values():
        ping_row += " ✅ |" if r.ping_ok else " ❌ |"
    lines.append(ping_row)

    # API calls
    api_row = "| **API calls** |"
    for r in results.values():
        api_row += f" {r.passed_steps}/{r.total_steps} |"
    lines.append(api_row)

    # Pipeline
    pipe_row = "| **Pipeline** |"
    for r in results.values():
        if r.passed:
            pipe_row += " ✅ Пройден |"
        elif r.error:
            pipe_row += f" ❌ {r.error} |"
        else:
            pipe_row += f" ❌ {r.failed_steps} failed |"
    lines.append(pipe_row)

    # Status
    status_row = "| **Status** |"
    for r in results.values():
        status_row += " ✅ |" if r.passed else " ❌ |"
    lines.append(status_row)

    lines.append("")

    # ── 2. Детализация по пайплайнам ──
    for name, result in results.items():
        lines.append(f"---\n")
        lines.append(f"## Pipeline: `{name}`\n")
        lines.append(f"**{result.description}**\n")
        lines.append(f"- Ping: {'✅' if result.ping_ok else '❌'}")
        lines.append(f"- Passed: {result.passed_steps}/{result.total_steps}")
        lines.append(f"- Failed: {result.failed_steps}")
        lines.append(f"- Skipped: {result.skipped_steps}")
        if result.error:
            lines.append(f"- Error: {result.error}")
        lines.append("")

        if result.steps:
            lines.append("| # | Step | Service | Status | Code | Time | Проверка |")
            lines.append("|---|------|---------|:------:|:----:|:----:|----------|")
            for i, step in enumerate(result.steps, 1):
                icon_map = {
                    "passed": "✅",
                    "failed": "❌",
                    "skipped": "⏭️",
                    "pending": "⏳",
                    "running": "🔄",
                }
                icon = icon_map.get(step.status.value, "❓")
                if step.status.value == "failed":
                    # Для ошибок: показываем error + (response_body если есть)
                    detail = step.error or ""
                    if step.response_body:
                        resp_snippet = step.response_body[:300].replace("\n", " ").replace("|", "\\|")
                        detail = f"{detail} | body: {resp_snippet}"
                else:
                    # Для успешных: message (если есть), иначе response_body
                    detail = step.message or ""
                    if not detail and step.response_body:
                        detail = step.response_body[:300]
                lines.append(
                    f"| {i} | {step.name} | {step.service} | {icon} | "
                    f"{step.actual_status} | {step.elapsed_ms}ms | {detail} |"
                )
            lines.append("")

            # Итог
            final_icon = "✅ Пройден" if result.passed else "❌ Сбой"
            lines.append(f"**Итог:** {final_icon} | Ping: {'✅' if result.ping_ok else '❌'} | "
                        f"Steps: {result.passed_steps}/{result.total_steps}\n")

    # Легенда
    lines.append("---\n")
    lines.append("## 📖 Legend\n")
    lines.append("- **✅ Passed** — шаг выполнен успешно\n")
    lines.append("- **❌ Failed** — ошибка выполнения шага (неверный статус, проверка, таймаут)\n")
    lines.append("- **⏭️ Skipped** — шаг пропущен\n")
    lines.append("- **Ping** — проверка health-эндпоинта сервиса перед запуском пайплайна\n")
    lines.append("- **Pipeline** — сквозной сценарий пройден, только если все шаги ✅\n")

    lines.append("---\n")
    lines.append(f"_Report generated by `pipeline_test.py` at {now}_\n")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────────────────────────────


async def main() -> None:
    args = parse_args()

    if args.command == "list":
        await cmd_list()

    elif args.command == "run":
        names = [n.strip() for n in args.names.split(",") if n.strip()]
        if not names:
            print("  ✗ Укажите имена пайплайнов через запятую")
            sys.exit(1)
        await cmd_run(
            names=names,
            host=args.host,
            timeout=args.timeout,
            output=args.output,
        )

    elif args.command == "run-all":
        await cmd_run_all(
            host=args.host,
            timeout=args.timeout,
            skip_ping=args.skip_ping,
            output=args.output,
        )

    else:
        print("  ✗ Неизвестная команда. Используйте: list, run, run-all")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
