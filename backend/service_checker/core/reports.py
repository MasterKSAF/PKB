#!/usr/bin/env python3
"""
PKB Neuroassistant — Service Checker: Report Generation
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from service_checker.core.config import PIPELINE_SERVICE_MAP, PIPELINE_SERVICE_COLUMNS, SERVICE_DISPLAY_NAMES
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


def _service_pipeline_summary_icon(
    svc_pipe_status: Dict[str, Tuple[int, int, int]],
    pipe_order: List[str],
) -> str:
    """
    Единый статус пайплайнов для сервиса: ✅ если все шаги всех пайплайнов пройдены,
    ❌ если хоть где-то сбой, — если пайплайнов для сервиса нет.
    """
    if not svc_pipe_status:
        return "—"
    all_ok = True
    for pname in pipe_order:
        if pname in svc_pipe_status:
            passed, total, failed = svc_pipe_status[pname]
            if failed > 0:
                all_ok = False
                break
    return "✅" if all_ok else "❌"


def _generate_full_report(
    coverage_results: Dict[str, Any],
    pipeline_results: Dict[str, Any],
    timestamp: str,
    db_result: Any = None,
    contract_report: Optional[str] = None,
) -> str:
    """Сформировать итоговый отчёт: сводная таблица + детали coverage + детали pipeline + БД + контракты."""
    lines: List[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append("# Full Report — API Coverage + Pipeline Testing\n")
    lines.append(f"**Generated:** {now}\n")
    lines.append("---\n")

    # ── 1. Итоговая сводная таблица ─────────────────────────────────
    pipe_columns = PIPELINE_SERVICE_COLUMNS  # имя → заголовок колонки
    pipe_order = [p for p in pipe_columns if p in pipeline_results]

    lines.append("## 📊 Итоговая сводная таблица\n")
    lines.append(f"| Service | Port | Ping | CheckDb | API | Pipelines | Status |")
    lines.append(f"|---------|:----:|:----:|:-------:|:---:|:--------:|:------:|")

    # Собираем per-service per-pipeline статус шагов
    # service_key -> {pipeline_name -> (passed, total, failed)}
    pipe_service_status: Dict[str, Dict[str, Tuple[int, int, int]]] = {}
    for pipe_name, pipe_result in pipeline_results.items():
        steps = getattr(pipe_result, "steps", [])
        svc_steps: Dict[str, list[int]] = {}  # [passed, total, failed]
        for step in steps:
            svc = getattr(step, "service", "")
            if not svc:
                continue
            if svc not in svc_steps:
                svc_steps[svc] = [0, 0, 0]  # [passed, total, failed]
            svc_steps[svc][1] += 1  # total
            status = getattr(step, "status", None)
            if status is not None:
                if status.value == "passed":
                    svc_steps[svc][0] += 1
                elif status.value == "failed":
                    svc_steps[svc][2] += 1
        for svc, (passed, total, failed) in svc_steps.items():
            if svc not in pipe_service_status:
                pipe_service_status[svc] = {}
            pipe_service_status[svc][pipe_name] = (passed, total, failed)

    # Определяем общую успешность пайплайнов (для итоговой строки)
    pipeline_passed: Dict[str, bool] = {}
    for pipe_name, result in pipeline_results.items():
        pipeline_passed[pipe_name] = getattr(result, "passed", False)

    # Строки по каждому сервису (все из SERVICE_DISPLAY_NAMES)
    for svc_key, display_name in sorted(SERVICE_DISPLAY_NAMES.items()):
        if svc_key not in MODE_PORTS:
            continue
        port = MODE_PORTS[svc_key]
        cov = coverage_results.get(svc_key)
        svc_pipe_status = pipe_service_status.get(svc_key, {})

        if cov:
            ping_icon = "✅" if cov.ping_ok else "❌"
            has_failures = cov.endpoints_failed > 0
            has_skips = cov.endpoints_skipped > 0
            passed_icon = "❌" if has_failures else ("⏭️" if has_skips else "✅")
            svc_checkdb = _get_service_checkdb_icon(db_result, svc_key)
            api_cell = f"{passed_icon}"
        else:
            ping_icon = "—"
            api_cell = "—"
            svc_checkdb = _get_service_checkdb_icon(db_result, svc_key) if db_result else "—"

        # Pipeline columns (main table)
        pipe_icons: List[str] = []
        for pname in pipe_order:
            if pname in PIPELINE_SERVICE_MAP and svc_key in PIPELINE_SERVICE_MAP[pname]:
                pstatus = svc_pipe_status.get(pname)
                if pstatus:
                    p_passed, p_total, p_failed = pstatus
                    pipe_icons.append("✅" if p_failed == 0 else "❌")
                else:
                    pipe_icons.append("—")
            else:
                pipe_icons.append("—")

        has_pipe_failures = any(icon not in ("—", "✅") for icon in pipe_icons)
        if cov:
            all_green = cov.ping_ok and not has_failures and not has_pipe_failures
            status_icon = "✅" if all_green else "❌"
        else:
            if svc_pipe_status:
                status_icon = "❌" if has_pipe_failures else "✅"
            else:
                status_icon = "🟡 dev"

        pipe_col = _service_pipeline_summary_icon(svc_pipe_status, pipe_order)
        lines.append(f"| {display_name} | {port} | {ping_icon} | {svc_checkdb} | {api_cell} | {pipe_col} | {status_icon} |")

    # Итоговая строка — только отметки
    total_services = len(coverage_results)
    cov_alive = sum(1 for r in coverage_results.values() if r.ping_ok)
    cov_ok_count = sum(
        1 for r in coverage_results.values()
        if r.ping_ok and r.endpoints_failed == 0
    )
    all_failed = sum(r.endpoints_failed for r in coverage_results.values())
    all_skipped = sum(r.endpoints_skipped for r in coverage_results.values())
    svcs_with_db = [k for k in coverage_results if k in COVERAGE_TO_STARTUP_KEY]
    svcs_checkdb_ok = sum(
        1 for k in svcs_with_db
        if _get_service_checkdb_icon(db_result, k) in ("✅", "—")
    )
    svcs_checkdb_total = len(svcs_with_db)

    all_cov_ok = cov_ok_count == total_services if total_services > 0 else True
    all_pipe_ok = all(pipeline_passed.values()) if pipeline_passed else True
    overall_status = "✅" if (all_cov_ok and all_pipe_ok) else "❌"
    pipe_total_icon = "✅" if all_pipe_ok else "❌"

    ping_total_icon = "✅" if cov_alive == total_services else "❌"
    checkdb_total_icon = "✅" if svcs_checkdb_ok == svcs_checkdb_total else "❌" if svcs_checkdb_total > 0 else "—"
    api_total_icon = "❌" if all_failed > 0 else ("⏭️" if all_skipped > 0 else "✅")

    lines.append(
        f"| **Total** | | {ping_total_icon} "
        f"| {checkdb_total_icon} "
        f"| {api_total_icon} "
        f"| {pipe_total_icon} "
        f"| {overall_status} |\n"
    )

    # ── 1b. Pipeline статусы по сервисам (отдельная таблица) ───────────
    lines.append("### 📋 Pipeline статусы по сервисам\n")
    col_headers = " | ".join(pipe_columns[p] for p in pipe_order)
    col_aligns = " | ".join(":---:" for _ in pipe_order)
    lines.append(f"| Service | {col_headers} | Status |")
    lines.append(f"|---------|{col_aligns}|:------:|")

    for svc_key, display_name in sorted(SERVICE_DISPLAY_NAMES.items()):
        if svc_key not in MODE_PORTS:
            continue
        svc_pipe_status = pipe_service_status.get(svc_key, {})
        pipe_icons: List[str] = []
        for pname in pipe_order:
            if pname in PIPELINE_SERVICE_MAP and svc_key in PIPELINE_SERVICE_MAP[pname]:
                pstatus = svc_pipe_status.get(pname)
                if pstatus:
                    p_passed, p_total, p_failed = pstatus
                    pipe_icons.append("✅" if p_failed == 0 else "❌")
                else:
                    pipe_icons.append("—")
            else:
                pipe_icons.append("—")

        if svc_pipe_status:
            ps_all_green = all(icon in ("—", "✅") for icon in pipe_icons)
            ps_status = "✅" if ps_all_green else "❌"
        else:
            ps_status = "🟡 dev"
        pipe_cols = " | ".join(pipe_icons)
        lines.append(f"| {display_name} | {pipe_cols} | {ps_status} |")

    # Totals row for pipeline table — только отметки
    pipe_totals: List[str] = []
    for pname in pipe_order:
        all_passed = True
        has_data = False
        for svc_key, svc_status in pipe_service_status.items():
            if pname in svc_status:
                has_data = True
                passed, total, failed = svc_status[pname]
                if failed > 0:
                    all_passed = False
        if has_data:
            pipe_totals.append("✅" if all_passed else "❌")
        else:
            pipe_totals.append("—")
    totals_cols = " | ".join(pipe_totals)
    lines.append(f"| **Total** | {totals_cols} | {pipe_total_icon} |\n")

    # ── 1a. Пояснения к ❌ / ⏭️ в сводной таблице ─────────────────
    lines.append("#### 🔍 Пояснения к результатам\n")
    has_notes = False
    for svc_key in sorted(coverage_results.keys()):
        display_name = SERVICE_DISPLAY_NAMES.get(svc_key, svc_key)
        cov = coverage_results[svc_key]
        notes = []

        # Ping
        if not cov.ping_ok:
            notes.append("Ping: сервис не отвечает на health check")

        # CheckDb
        svc_checkdb = _get_service_checkdb_icon(db_result, svc_key)
        if svc_checkdb == "❌":
            startup_key = COVERAGE_TO_STARTUP_KEY.get(svc_key)
            if startup_key == "rag_builder_service":
                notes.append("CheckDb: RAG Builder использует validate_startup_migrations(), не create_all()")
            else:
                notes.append("CheckDb: не найден вызов create_all() при старте сервиса")

        # API failures
        if cov.endpoints_failed > 0:
            notes.append(f"API: {cov.endpoints_failed} эндпоинт(ов) упало")

        # API skips — разбивка по типам
        skipped_new_api = 0
        skipped_context = 0
        if hasattr(cov, 'results'):
            for ep in getattr(cov, 'results', []):
                if ep.skipped:
                    if ep.skip_reason and "Сервис не обновлён" in ep.skip_reason:
                        skipped_new_api += 1
                    else:
                        skipped_context += 1
        if skipped_new_api > 0:
            notes.append(f"⏭️ {skipped_new_api} эндпоинтов пропущено — новые API (задачи 19.06)")
        if skipped_context > 0:
            notes.append(f"⏭️ {skipped_context} эндпоинтов пропущено — нет контекста (prepare не создал данные)")

        # Pipelines
        svc_pipe_status = pipe_service_status.get(svc_key, {})
        pipe_col = _service_pipeline_summary_icon(svc_pipe_status, pipe_order)
        if pipe_col == "❌":
            failed_pipes = [
                pipe_columns.get(p, p) for p in pipe_order
                if p in svc_pipe_status
                and svc_pipe_status[p][2] > 0  # failed > 0
            ]
            if failed_pipes:
                notes.append(f"Pipelines: сбой в {', '.join(failed_pipes)}")
            else:
                notes.append("Pipelines: не все шаги пройдены")

        if notes:
            has_notes = True
            lines.append(f"- **{display_name}**: {'; '.join(notes)}\n")

    if not has_notes:
        lines.append("_Нет замечаний_\n")
    lines.append("")

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
        has_fails = result.endpoints_failed > 0
        has_skps = result.endpoints_skipped > 0
        status_icon = "❌" if has_fails else ("⏭️" if has_skps else "✅")
        svc_checkdb = _get_service_checkdb_icon(db_result, svc_key)
        lines.append(f"| {display_name} | {result.port} | {ping_icon} | {svc_checkdb} | {result.endpoints_total} | {result.endpoints_passed} | {failed_str} | {skipped_str} | {status_icon} |")

    all_alive = sum(1 for r in coverage_results.values() if r.ping_ok)
    all_total_ok = sum(r.endpoints_passed for r in coverage_results.values())
    all_total_ep = sum(r.endpoints_total for r in coverage_results.values())
    all_failed = sum(r.endpoints_failed for r in coverage_results.values())
    all_skipped = sum(r.endpoints_skipped for r in coverage_results.values())
    cov_ok = all_failed == 0
    cov_checkdb_total_icon = "✅" if svcs_checkdb_ok == svcs_checkdb_total else "❌" if db_result is not None else "—"
    total_status = "⏭️" if all_skipped > 0 and cov_ok else ("❌" if not cov_ok else "✅")
    lines.append(f"| **Total** | | **{all_alive}/{len(coverage_results)}** | {cov_checkdb_total_icon} | **{all_total_ep}** | **{all_total_ok}** | **{all_failed}** | **{all_skipped}** | {total_status} |\n")

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

    # ── 5. Service Contracts Check ───────────────────────────────────────
    if contract_report:
        lines.append(contract_report)

    # ── 6. Детальные шаги каждого пайплайна ──────────────────────────
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
