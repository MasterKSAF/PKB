from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from convertor_validator_service_lama.models.document_structure_extraction import (
    DocumentProfile,
    DocumentStructureExtraction,
    NumberingScopeExtraction,
    NumberingScopeType,
)
from convertor_validator_service_lama.services.document_structure_extraction_merge import (
    merge_document_structure_extractions,
)
from convertor_validator_service_lama.services.document_structure_extraction_stages import (
    DEFAULT_OVERVIEW_MAX_ITEMS,
    DEFAULT_SCOPE_MAX_ITEMS,
    DEFAULT_SCOPE_MAX_WINDOW_ITEMS,
    DEFAULT_SCOPE_OVERLAP_ITEMS,
    DEFAULT_STAGE_ITEM_TEXT_CHARS,
    DEFAULT_STAGE_MARKDOWN_EXCERPT_CHARS,
    build_document_structure_overview_agent_input,
    build_scope_extraction_agent_inputs,
)


DEFAULT_DETERMINISTIC_OVERVIEW_MIN_PAGES = 80


class DocumentStructureExtractionAgent(Protocol):
    """Agent interface for staged document-structure extraction.

    Implementations may call LlamaExtract, another LLM backend, or a fake test
    agent. This protocol intentionally does not know about API keys, transport,
    retry policy, or persistence.
    """

    def extract_overview(
        self,
        overview_input: dict[str, Any],
    ) -> DocumentStructureExtraction | dict[str, Any]:
        """Extract document profile and numbering scopes."""

    def extract_scope(
        self,
        scope_input: dict[str, Any],
    ) -> DocumentStructureExtraction | dict[str, Any]:
        """Extract sections/classifications inside one scope or scope window."""


@dataclass(frozen=True)
class DocumentStructureExtractionWorkflowResult:
    overview_input: dict[str, Any]
    overview_extraction: DocumentStructureExtraction
    scope_inputs: list[dict[str, Any]]
    scope_extractions: list[DocumentStructureExtraction]
    merged_extraction: DocumentStructureExtraction

    @property
    def scope_inputs_count(self) -> int:
        return len(self.scope_inputs)

    @property
    def scope_extractions_count(self) -> int:
        return len(self.scope_extractions)


def run_document_structure_extraction_workflow(
    parse_result_payload: dict[str, Any],
    *,
    agent: DocumentStructureExtractionAgent,
    overview_max_items: int = DEFAULT_OVERVIEW_MAX_ITEMS,
    scope_max_items: int = DEFAULT_SCOPE_MAX_ITEMS,
    scope_max_window_items: int = DEFAULT_SCOPE_MAX_WINDOW_ITEMS,
    scope_overlap_items: int = DEFAULT_SCOPE_OVERLAP_ITEMS,
    item_text_chars: int = DEFAULT_STAGE_ITEM_TEXT_CHARS,
    markdown_excerpt_chars: int = DEFAULT_STAGE_MARKDOWN_EXCERPT_CHARS,
    use_deterministic_overview_for_large_documents: bool = True,
    deterministic_overview_min_pages: int = DEFAULT_DETERMINISTIC_OVERVIEW_MIN_PAGES,
) -> DocumentStructureExtractionWorkflowResult:
    """Run staged DocumentStructureExtraction workflow.

    This service is an orchestration stub. It does not call LlamaCloud itself.
    The caller supplies an agent implementation.

    The workflow is:

    1. Build overview input from parse result.
    2. Call overview agent.
    3. Build scope/window inputs from overview numbering scopes.
    4. Call scope agent for each scope/window input.
    5. Merge all staged outputs into one DocumentStructureExtraction.
    """

    overview_input = build_document_structure_overview_agent_input(
        parse_result_payload,
        max_preview_items=overview_max_items,
        item_text_chars=item_text_chars,
        markdown_excerpt_chars=markdown_excerpt_chars,
    )

    overview_source = "agent"

    if _should_use_deterministic_overview(
        overview_input,
        enabled=use_deterministic_overview_for_large_documents,
        min_pages=deterministic_overview_min_pages,
    ):
        overview_extraction = build_deterministic_document_structure_overview(
            overview_input
        )
        overview_source = "deterministic"
    else:
        try:
            overview_extraction = _coerce_extraction(
                agent.extract_overview(overview_input)
            )
        except Exception as exc:
            raise RuntimeError(
                "document structure overview extraction failed: "
                f"stage_id={overview_input.get('stage_id')!r}, "
                f"stage_type={overview_input.get('stage_type')!r}, "
                f"job_id={overview_input.get('job_id')!r}, "
                f"page_count={overview_input.get('page_count')!r}, "
                f"items_count={overview_input.get('items_count')!r}, "
                f"items_preview_count={overview_input.get('items_preview_count')!r}, "
                f"markdown_chars={overview_input.get('markdown_chars')!r}, "
                f"error_type={type(exc).__name__}, "
                f"error={exc}"
            ) from exc

    numbering_scopes = [
        scope.model_dump(mode="json")
        for scope in overview_extraction.numbering_scopes
    ]

    scope_inputs = build_scope_extraction_agent_inputs(
        parse_result_payload,
        numbering_scopes=numbering_scopes,
        max_preview_items=scope_max_items,
        max_scope_items_per_window=scope_max_window_items,
        overlap_items=scope_overlap_items,
        item_text_chars=item_text_chars,
        markdown_excerpt_chars=markdown_excerpt_chars,
    )

    scope_extractions: list[DocumentStructureExtraction] = []
    for scope_input in scope_inputs:
        try:
            scope_extractions.append(
                _coerce_extraction(agent.extract_scope(scope_input))
            )
        except Exception as exc:
            raise RuntimeError(
                "document structure scope extraction failed: "
                f"stage_id={scope_input.get('stage_id')!r}, "
                f"namespace_id={scope_input.get('namespace_id')!r}, "
                f"scope_title={scope_input.get('scope_title')!r}, "
                f"page_start={scope_input.get('page_start')!r}, "
                f"page_end={scope_input.get('page_end')!r}, "
                f"window_index={scope_input.get('window_index')!r}, "
                f"windows_count={scope_input.get('windows_count')!r}, "
                f"source_item_index_start={scope_input.get('source_item_index_start')!r}, "
                f"source_item_index_end={scope_input.get('source_item_index_end')!r}, "
                f"items_count={scope_input.get('items_count')!r}, "
                f"items_preview_count={scope_input.get('items_preview_count')!r}, "
                f"error_type={type(exc).__name__}, "
                f"error={exc}"
            ) from exc

    merged_extraction = merge_document_structure_extractions(
        overview_extraction=overview_extraction,
        scope_extractions=scope_extractions,
        page_count=overview_extraction.page_count,
    )

    merged_extraction.diagnostics.update(
        {
            "workflow_overview_items_preview_count": overview_input[
                "items_preview_count"
            ],
            "workflow_page_overview_count": len(overview_input["page_overview"]),
            "workflow_scope_inputs_count": len(scope_inputs),
            "workflow_scope_extractions_count": len(scope_extractions),
            "workflow_overview_source": overview_source,
            "workflow_scope_stage_ids": [
                scope_input["stage_id"]
                for scope_input in scope_inputs
            ],
        }
    )

    return DocumentStructureExtractionWorkflowResult(
        overview_input=overview_input,
        overview_extraction=overview_extraction,
        scope_inputs=scope_inputs,
        scope_extractions=scope_extractions,
        merged_extraction=merged_extraction,
    )


def _should_use_deterministic_overview(
    overview_input: dict[str, Any],
    *,
    enabled: bool,
    min_pages: int,
) -> bool:
    if not enabled:
        return False

    page_count = _positive_int(overview_input.get("page_count"))
    if page_count is None:
        return False

    return page_count >= max(1, min_pages)


def build_deterministic_document_structure_overview(
    overview_input: dict[str, Any],
) -> DocumentStructureExtraction:
    page_count = _positive_int(overview_input.get("page_count"))

    return DocumentStructureExtraction(
        document_profile=(
            DocumentProfile.COMPOUND_RULES
            if (page_count or 0) >= DEFAULT_DETERMINISTIC_OVERVIEW_MIN_PAGES
            else DocumentProfile.UNKNOWN
        ),
        page_count=page_count,
        numbering_scopes=[
            NumberingScopeExtraction(
                namespace_id="main_document",
                title="Main document",
                scope_type=NumberingScopeType.MAIN_DOCUMENT,
                page_start=1 if page_count is not None else None,
                page_end=page_count,
                confidence=0.55,
                reason=(
                    "Deterministic overview generated from parse result page count "
                    "to avoid an unbounded LlamaExtract overview pass."
                ),
            )
        ],
        diagnostics={
            "deterministic_overview": True,
            "deterministic_overview_reason": "large_document_page_threshold",
            "deterministic_overview_page_count": page_count,
        },
    )


def _positive_int(value: Any) -> int | None:
    if type(value) is not int:
        return None

    if value < 1:
        return None

    return value


def _coerce_extraction(
    extraction: DocumentStructureExtraction | dict[str, Any],
) -> DocumentStructureExtraction:
    if isinstance(extraction, DocumentStructureExtraction):
        return extraction

    if isinstance(extraction, dict):
        return DocumentStructureExtraction.model_validate(extraction)

    raise TypeError(f"unsupported extraction type: {type(extraction)!r}")
