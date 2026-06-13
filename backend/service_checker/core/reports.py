#!/usr/bin/env python3
"""
PKB Neuroassistant — Service Checker: Report Generation
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from service_checker.core.config import PIPELINE_SERVICE_MAP, SERVICE_DISPLAY_NAMES
from service_checker.services import MODE_PORTS, SERVICE_REGISTRY


# Тип для опционального результата проверки БД
DbCheckResult = Any  # runtime import to avoid circular

# Маппинг ключей coverage → ключи startup check
COVERAGE_TO_STARTUP_KEY = {
    "auth": "auth_service",
    "query": "query_service",
    "orchestrator": "orchestrator_service",
    "integration": "integration_service",
    "registry": "registry_service",
    "rag_builder": "rag_builder_service",
    "rag_search": "rag_search_service",
}


def _get_db_icon(db_result: Any) -> str:
    if db_result is None:
        return "—"
    if hasattr(db_result, "error") and db_result.error:
        return "⚠️"
    if hasattr(db_result, "healthy"):
        return "✅" if db_result.healthy else "❌"
    return "—"


def _get_service_checkdb_icon(db_result: Any, svc_key: str) -> str:
    """
    Per-service статус CheckDb: есть ли у сервиса create_all().

    Consumer-сервисы (rag_search) не должны создавать таблицы — для них "—".
    """
    if db_result is None:
        return "—"
    startup_key = COVERAGE_TO_STARTUP_KEY.get(svc_key)
    if startup_key is None:
        return "—"  # сервис без БД (gateway, parser, tei...)
    create_all_map = getattr(db_result, "services_create_all", {})
    has_it = create_all_map.get(startup_key)
    if has_it is None:
        return "—"
    # Проверка: consumer-сервисы не должны иметь create_all
    from service_checker.core.db_check import SERVICE_STARTUP_CHECKS
    svc_info = SERVICE_STARTUP_CHECKS.get(startup_key, {})
    if svc_info.get("must_not_have_create_all", False):
        return "—"  # consumer, не создаёт таблицы
    return "✅" if has_it else "❌"


def _generate_full_report(
    coverage_results: Dict[str, Any],
    pipeline_results: Dict[str, Any],
    timestamp: str,
    db_result: Any = None,
) -> str:
    """Сформировать итоговый отчёт: сводная таблица + детали coverage + детали pipeline + БД."""
    lines: List[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append("# Full Report — API Coverage + Pipeline Testing\n")
    lines.append(f"**Generated:** {now}\n")
    lines.append("---\n")

    db_icon = _get_db_icon(db_result)

    # ── 1. Итоговая сводная таблица ─────────────────────────────────
    lines.append("## 📊 Итоговая сводная таблица\n")
    lines.append("| Service | Port | Ping | CheckDb | API | Documents | Query | Status |")
    lines.append("|---------|:----:|:----:|:-------:|:---:|:---------:|:-----:|:------:|")

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

        # ✅ Passed column — true/false вместо 10/10
        passed_icon = "✅" if not has_failures else "❌"

        svc_checkdb = _get_service_checkdb_icon(db_result, svc_key)
        lines.append(f"| {display_name} | {port} | {ping_icon} | {svc_checkdb} | {passed_icon} | {doc_icon} | {query_icon} | {status_icon} |")

    # Сервисы в глубокой разработке (не тестируются, с прочерками)
    for svc_key, display_name in SERVICE_DISPLAY_NAMES.items():
        if svc_key not in coverage_results and svc_key in MODE_PORTS:
            port = MODE_PORTS[svc_key]
            lines.append(f"| {display_name} | {port} | — | — | — | — | — | 🟡 dev |")

    # Итоговая строка — количества по всем столбцам
    total_services = len(coverage_results)
    cov_alive = sum(1 for r in coverage_results.values() if r.ping_ok)

    # ✅ Passed: кол-во сервисов без ошибок (endpoints)
    cov_ok_count = sum(
        1 for r in coverage_results.values()
        if r.ping_ok and r.endpoints_failed == 0 and r.endpoints_skipped == 0
    )

    # CheckDb: кол-во сервисов у которых есть create_all (или consumer)
    svcs_with_db = [k for k in coverage_results if k in COVERAGE_TO_STARTUP_KEY]
    svcs_checkdb_ok = sum(
        1 for k in svcs_with_db
        if _get_service_checkdb_icon(db_result, k) in ("✅", "—")
    )
    svcs_checkdb_total = len(svcs_with_db)

    # Documents: кол-во успешно пройденных шагов document_processing
    doc_passed_total = 0
    doc_steps_total = 0
    for svc_key, svc_status in pipe_service_status.items():
        if "document_processing" in svc_status:
            passed, total = svc_status["document_processing"]
            doc_passed_total += passed
            doc_steps_total += total

    # Query: кол-во успешно пройденных шагов chat_inference
    query_passed_total = 0
    query_steps_total = 0
    for svc_key, svc_status in pipe_service_status.items():
        if "chat_inference" in svc_status:
            passed, total = svc_status["chat_inference"]
            query_passed_total += passed
            query_steps_total += total

    all_cov_ok = cov_ok_count == total_services
    all_pipe_ok = all(pipeline_passed.values()) if pipeline_passed else True
    pipe_ok_count = sum(1 for p in pipeline_passed.values() if p) if pipeline_passed else 0
    pipe_total = len(pipeline_passed) if pipeline_passed else 0

    # Общий статус: ❌ если есть проблемы
    overall_status = "✅" if (
        cov_ok_count == total_services 
        and all(pipeline_passed.values()) if pipeline_passed else True
    ) else "❌"

    lines.append(
        f"| **Total** | | **{cov_alive}/{total_services}** "
        f"| **{svcs_checkdb_ok}/{svcs_checkdb_total}** "
        f"| **{cov_ok_count}/{total_services}** "
        f"| **{doc_passed_total}/{doc_steps_total}** "
        f"| **{query_passed_total}/{query_steps_total}** "
        f"| {overall_status} |\n"
    )

    # ── 2. Детали API Coverage ─────────────────────────────────────
    lines.append("---\n")
    lines.append("## 🔬 API Coverage — Детализация\n")
    lines.append("| Service | Port | Ping | CheckDb | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |")
    lines.append("|---------|:----:|:----:|:-------:|:---------:|:---------:|:---------:|:----------:|:------:|")

    for svc_key, result in sorted(coverage_results.items()):
        display_name = SERVICE_DISPLAY_NAMES.get(svc_key, svc_key)
        ping_icon = "✅" if result.ping_ok else "❌"
        failed_str = str(result.endpoints_failed) if result.endpoints_failed == 0 else f'**{result.endpoints_failed}**'
        skipped_str = str(result.endpoints_skipped) if result.endpoints_skipped == 0 else f'**{result.endpoints_skipped}**'
        status_icon = "✅" if result.ping_ok and result.endpoints_failed == 0 and result.endpoints_skipped == 0 else "❌"
        svc_checkdb = _get_service_checkdb_icon(db_result, svc_key)
        lines.append(f"| {display_name} | {result.port} | {ping_icon} | {svc_checkdb} | {result.endpoints_total} | {result.endpoints_passed} | {failed_str} | {skipped_str} | {status_icon} |")

    all_alive = sum(1 for r in coverage_results.values() if r.ping_ok)
    all_total_ok = sum(r.endpoints_passed for r in coverage_results.values())
    all_total_ep = sum(r.endpoints_total for r in coverage_results.values())
    all_failed = sum(r.endpoints_failed for r in coverage_results.values())
    all_skipped = sum(r.endpoints_skipped for r in coverage_results.values())
    cov_ok = all_failed == 0 and all_skipped == 0
    cov_checkdb_total_icon = "✅" if svcs_checkdb_ok == svcs_checkdb_total else "❌" if db_result is not None else "—"
    lines.append(f"| **Total** | | **{all_alive}/{len(coverage_results)}** | {cov_checkdb_total_icon} | **{all_total_ep}** | **{all_total_ok}** | **{all_failed}** | **{all_skipped}** | {'✅' if cov_ok else '❌'} |\n")

    # ⚠️ Workaround-предупреждения (заглушки)
    lines.append("### ⚠️ Workaround-предупреждения по сервисам\n")
    has_warnings = False
    for svc_key in sorted(coverage_results.keys()):
        try:
            svc_def = SERVICE_REGISTRY[svc_key]()
            if svc_def.warnings:
                has_warnings = True
                display_name = SERVICE_DISPLAY_NAMES.get(svc_key, svc_key)
                for warn in svc_def.warnings:
                    lines.append(f"- **{display_name}**: {warn}\n")
        except (KeyError, Exception):
            pass  # Сервис не в реестре — пропускаем
    if not has_warnings:
        lines.append("_Нет предупреждений_\n")
    lines.append("")

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

    # ── 4. Детали проверки БД ────────────────────────────────────────
    if db_result is not None:
        lines.append("---\n")
        from service_checker.core.db_check import format_db_report
        db_section = format_db_report(db_result)
        lines.append(db_section)

    # ── 5. Детальные шаги каждого пайплайна ──────────────────────────
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
                step_error = getattr(step, "error", "") or ""
                step_msg = getattr(step, "message", "") or ""
                step_resp = getattr(step, "response_body", None)
                
                if step_status and step_status.value == "failed":
                    # Для ошибок: показываем error + (response_body если есть)
                    detail = step_error
                    if step_resp:
                        resp_snippet = step_resp[:300].replace("\n", " ").replace("|", "\\|")
                        detail = f"{detail} | body: {resp_snippet}"
                else:
                    # Для успешных: message (если есть), иначе response_body
                    detail = step_msg
                    if not detail and step_resp:
                        detail = step_resp[:300]
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
