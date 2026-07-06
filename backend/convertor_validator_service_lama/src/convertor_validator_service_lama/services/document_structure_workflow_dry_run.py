from __future__ import annotations

from typing import Any

from convertor_validator_service_lama.models.contracts import (
    DocumentStructureWorkflowDryRunRequest,
    DocumentStructureWorkflowDryRunResponse,
    DocumentStructureWorkflowStageSummary,
)
from convertor_validator_service_lama.services.document_structure_extraction_stages import (
    build_document_structure_stage_plan,
)


def build_document_structure_workflow_dry_run_response(
    request: DocumentStructureWorkflowDryRunRequest,
) -> DocumentStructureWorkflowDryRunResponse:
    """Build staged document-structure workflow plan without LlamaCloud calls."""

    plan = build_document_structure_stage_plan(
        request.parse_result_payload,
        numbering_scopes=request.numbering_scopes,
        overview_max_items=request.overview_max_items,
        scope_max_items=request.scope_max_items,
        scope_max_window_items=request.scope_max_window_items,
        scope_overlap_items=request.scope_overlap_items,
        item_text_chars=request.item_text_chars,
        markdown_excerpt_chars=request.markdown_excerpt_chars,
    )

    overview_input = _as_dict(plan.get("overview_input"))
    scope_inputs = _as_list_of_dicts(plan.get("scope_inputs"))

    return DocumentStructureWorkflowDryRunResponse(
        parse_job_id=_first_str(
            plan.get("job_id"),
            request.parse_result_payload.get("job_id"),
        ),
        page_count=_as_optional_int(plan.get("page_count")),
        items_count=_as_int(plan.get("items_count")),
        stages_count=_as_int(plan.get("stages_count")),
        requires_overview_agent_output=bool(
            plan.get("requires_overview_agent_output", True)
        ),
        overview_items_preview_count=_as_int(
            overview_input.get("items_preview_count")
        ),
        overview_page_overview_count=len(
            _as_list(overview_input.get("page_overview"))
        ),
        overview_markdown_excerpt_chars=len(
            _as_str(overview_input.get("markdown_excerpt"))
        ),
        scope_inputs_count=len(scope_inputs),
        scope_stage_summaries=[
            _build_scope_stage_summary(scope_input)
            for scope_input in scope_inputs
        ],
    )


def _build_scope_stage_summary(
    scope_input: dict[str, Any],
) -> DocumentStructureWorkflowStageSummary:
    return DocumentStructureWorkflowStageSummary(
        stage_id=_as_str(scope_input.get("stage_id")),
        stage_type=_as_str(scope_input.get("stage_type")),
        namespace_id=_as_optional_str(scope_input.get("namespace_id")),
        scope_title=_as_optional_str(scope_input.get("scope_title")),
        scope_type=_as_optional_str(scope_input.get("scope_type")),
        page_start=_as_optional_int(scope_input.get("page_start")),
        page_end=_as_optional_int(scope_input.get("page_end")),
        window_index=_human_window_index(scope_input),
        windows_count=_as_optional_int(scope_input.get("windows_count")),
        items_count=_as_optional_int(scope_input.get("items_count")),
        items_preview_count=_as_optional_int(scope_input.get("items_preview_count")),
        source_item_index_start=_as_optional_int(
            scope_input.get("source_item_index_start")
        ),
        source_item_index_end=_as_optional_int(
            scope_input.get("source_item_index_end")
        ),
        markdown_excerpt_chars=len(_as_str(scope_input.get("markdown_excerpt"))),
    )


def _human_window_index(scope_input: dict[str, Any]) -> int | None:
    window_index = _as_optional_int(scope_input.get("window_index"))

    if window_index is None:
        return None

    return window_index + 1



def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    return [
        item
        for item in value
        if isinstance(item, dict)
    ]


def _as_int(value: Any) -> int:
    parsed = _as_optional_int(value)
    return parsed if parsed is not None else 0


def _as_optional_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float) and value.is_integer():
        return int(value)

    return None


def _as_str(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _as_optional_str(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value

    return None


def _first_str(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()

    return None
