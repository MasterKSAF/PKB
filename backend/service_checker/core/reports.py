#!/usr/bin/env python3
"""
PKB Neuroassistant — Service Checker: Report Generation
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from service_checker.core.config import PIPELINE_SERVICE_MAP, SERVICE_DISPLAY_NAMES


def _generate_full_report(
    coverage_results: Dict[str, Any],
    pipeline_results: Dict[str, Any],
    timestamp: str,
) -> str:
    """Сформировать итоговый отчёт: сводная таблица + детали coverage + детали pipeline."""
    lines: List[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append("# Full Report — API Coverage + Pipeline Testing\n")
    lines.append(f"**Generated:** {now}\n")
    lines.append("---\n")

    # ── 1. Итоговая сводная таблица ─────────────────────────────────
    lines.append("## 📊 Итоговая сводная таблица\n")
    lines.append("| Service | Port | Ping | ✅ Passed | Documents | Query | Status |")
    lines.append("|---------|:----:|:----:|:---------:|:---------:|:-----:|:------:|")

    # Собираем per-service per-pipeline статус шагов
    # service_key -> {pipeline_name -> passed/all_count}
    pipe_service_status: Dict[str, Dict[str, Tuple[int, int]]] = {}
    for pipe_name, pipe_result in pipeline_results.items():
        steps = getattr(pipe_result, "steps", [])
        svc_steps: Dict[str, Tuple[int, int]] = {}
        for step in steps:
            svc = getattr(step, "service", "")
            if not svc:
                continue
            if svc not in svc_steps:
                svc_steps[svc] = [0, 0]  # [passed, total]
            svc_steps[svc][1] += 1
            if getattr(step, "status", None) is not None and step.status.value == "passed":
                svc_steps[svc][0] += 1
        for svc, (passed, total) in svc_steps.items():
            if svc not in pipe_service_status:
                pipe_service_status[svc] = {}
            pipe_service_status[svc][pipe_name] = (passed, total)

    # Определяем общую успешность пайплайнов (для итоговой строки)
    pipeline_passed: Dict[str, bool] = {}
    for pipe_name, result in pipeline_results.items():
        pipeline_passed[pipe_name] = getattr(result, "passed", False)

    # Строки по каждому сервису (только из coverage)
    for svc_key in sorted(coverage_results.keys()):
        display_name = SERVICE_DISPLAY_NAMES.get(svc_key, svc_key)
        cov = coverage_results[svc_key]
        port = cov.port
        ping_icon = "✅" if cov.ping_ok else "❌"
        passed_ratio = f"{cov.endpoints_passed}/{cov.endpoints_total}" if cov.endpoints_total > 0 else "0/0"
        has_failures = cov.endpoints_failed > 0 or cov.endpoints_skipped > 0

        # Documents column — per-service шаги в document_processing
        svc_pipe_status = pipe_service_status.get(svc_key, {})
        doc_icon = "—"
        if "document_processing" in PIPELINE_SERVICE_MAP and svc_key in PIPELINE_SERVICE_MAP["document_processing"]:
            dp_status = svc_pipe_status.get("document_processing")
            if dp_status:
                dp_passed, dp_total = dp_status
                doc_icon = "✅" if dp_passed > 0 and dp_passed == dp_total else "❌"

        # Query column — per-service шаги в chat_inference
        query_icon = "—"
        if "chat_inference" in PIPELINE_SERVICE_MAP and svc_key in PIPELINE_SERVICE_MAP["chat_inference"]:
            ci_status = svc_pipe_status.get("chat_inference")
            if ci_status:
                ci_passed, ci_total = ci_status
                query_icon = "✅" if ci_passed > 0 and ci_passed == ci_total else "❌"

        # Overall status
        all_green = (
            cov.ping_ok and not has_failures
            and (doc_icon == "—" or doc_icon == "✅")
            and (query_icon == "—" or query_icon == "✅")
        )
        status_icon = "✅" if all_green else "❌"

        lines.append(f"| {display_name} | {port} | {ping_icon} | {passed_ratio} | {doc_icon} | {query_icon} | {status_icon} |")

    # Итоговая строка
    total_services = len(coverage_results)
    cov_alive = sum(1 for r in coverage_results.values() if r.ping_ok)
    total_ok = sum(r.endpoints_passed for r in coverage_results.values())
    total_eps = sum(r.endpoints_total for r in coverage_results.values())
    pipe_ok = sum(1 for p in pipeline_passed.values() if p)
    pipe_total = len(pipeline_passed)
    # Все сервисы покрытия ping OK и без ошибок
    all_cov_ok = all(
        r.ping_ok and r.endpoints_failed == 0 and r.endpoints_skipped == 0
        for r in coverage_results.values()
    ) if coverage_results else True
    overall_ok = all_cov_ok and all(pipeline_passed.values())
    overall_status = "✅" if overall_ok else "❌"
    lines.append(f"| **Total** | | **{cov_alive}/{total_services}** | **{total_ok}/{total_eps}** | **{pipe_ok}/{pipe_total}** | **{pipe_ok}/{pipe_total}** | {overall_status} |\n")

    # ── 2. Детали API Coverage ─────────────────────────────────────
    lines.append("---\n")
    lines.append("## 🔬 API Coverage — Детализация\n")
    lines.append("| Service | Port | Ping | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |")
    lines.append("|---------|:----:|:----:|:---------:|:---------:|:---------:|:----------:|:------:|")

    for svc_key, result in sorted(coverage_results.items()):
        display_name = SERVICE_DISPLAY_NAMES.get(svc_key, svc_key)
        ping_icon = "✅" if result.ping_ok else "❌"
        failed_str = str(result.endpoints_failed) if result.endpoints_failed == 0 else f'**{result.endpoints_failed}**'
        skipped_str = str(result.endpoints_skipped) if result.endpoints_skipped == 0 else f'**{result.endpoints_skipped}**'
        status_icon = "✅" if result.ping_ok and result.endpoints_failed == 0 and result.endpoints_skipped == 0 else "❌"
        lines.append(f"| {display_name} | {result.port} | {ping_icon} | {result.endpoints_total} | {result.endpoints_passed} | {failed_str} | {skipped_str} | {status_icon} |")

    all_alive = sum(1 for r in coverage_results.values() if r.ping_ok)
    all_total_ok = sum(r.endpoints_passed for r in coverage_results.values())
    all_total_ep = sum(r.endpoints_total for r in coverage_results.values())
    all_failed = sum(r.endpoints_failed for r in coverage_results.values())
    all_skipped = sum(r.endpoints_skipped for r in coverage_results.values())
    cov_ok = all_failed == 0 and all_skipped == 0
    lines.append(f"| **Total** | | **{all_alive}/{len(coverage_results)}** | **{all_total_ep}** | **{all_total_ok}** | **{all_failed}** | **{all_skipped}** | {'✅' if cov_ok else '❌'} |\n")

    # ── 3. Детали Pipeline Testing ─────────────────────────────────
    lines.append("---\n")
    lines.append("## 📋 Pipeline Testing — Детализация\n")
    lines.append("| Pipeline | Описание | Ping | Шаги | ✅ Passed | ❌ Failed | Status |")
    lines.append("|----------|----------|:----:|:----:|:---------:|:---------:|:------:|")

    for pipe_name, result in sorted(pipeline_results.items()):
        ping_icon = "✅" if getattr(result, "ping_ok", False) else "❌"
        total = getattr(result, "total_steps", 0)
        passed = getattr(result, "passed_steps", 0)
        failed = getattr(result, "failed_steps", 0)
        ok = getattr(result, "passed", False)
        desc = getattr(result, "description", "")
        status_icon = "✅" if ok else "❌"
        lines.append(f"| `{pipe_name}` | {desc} | {ping_icon} | {total} | {passed} | {failed} | {status_icon} |")

    # ── 4. Детальные шаги каждого пайплайна ──────────────────────────
    lines.append("\n---\n")
    lines.append("## 📋 Pipeline Testing — Пошаговая детализация\n")
    for pipe_name, result in sorted(pipeline_results.items()):
        lines.append(f"### Pipeline: `{pipe_name}`\n")
        lines.append(f"**{getattr(result, 'description', '')}**\n")
        lines.append(f"- Ping: {'✅' if getattr(result, 'ping_ok', False) else '❌'}")
        lines.append(f"- Passed: {getattr(result, 'passed_steps', 0)}/{getattr(result, 'total_steps', 0)}")
        lines.append(f"- Failed: {getattr(result, 'failed_steps', 0)}")
        lines.append(f"- Skipped: {getattr(result, 'skipped_steps', 0)}")
        err = getattr(result, 'error', None)
        if err:
            lines.append(f"- Error: {err}")
        lines.append("")

        steps = getattr(result, "steps", [])
        pipe_ok = getattr(result, "passed", False)
        if steps:
            lines.append("| # | Step | Service | Status | Code | Time | Проверка |")
            lines.append("|---|------|---------|:------:|:----:|:----:|----------|")
            icon_map = {
                "passed": "✅", "failed": "❌", "skipped": "⏭️",
                "pending": "⏳", "running": "🔄",
            }
            for i, step in enumerate(steps, 1):
                step_status = getattr(step, "status", None)
                icon = icon_map.get(step_status.value if step_status else "", "❓")
                detail = getattr(step, "error", "") or ""
                if not detail:
                    resp = getattr(step, "response_body", None)
                    if resp:
                        detail = resp[:100]
                lines.append(
                    f"| {i} | {getattr(step, 'name', '')} | {getattr(step, 'service', '')} | {icon} | "
                    f"{getattr(step, 'actual_status', 0)} | {getattr(step, 'elapsed_ms', 0)}ms | {detail} |"
                )
            lines.append("")

        final_icon = "✅ Пройден" if pipe_ok else "❌ Сбой"
        lines.append(f"**Итог:** {final_icon} | Ping: {'✅' if getattr(result, 'ping_ok', False) else '❌'} | "
                    f"Steps: {getattr(result, 'passed_steps', 0)}/{getattr(result, 'total_steps', 0)}\n")

    lines.append("\n---\n")
    lines.append(f"_Report generated by `service_checker.py` at {now}_\n")

    return "\n".join(lines)
