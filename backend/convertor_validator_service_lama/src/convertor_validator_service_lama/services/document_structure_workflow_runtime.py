from __future__ import annotations

from dataclasses import dataclass

from convertor_validator_service_lama.core.settings import Settings
from convertor_validator_service_lama.models.contracts import LlamaExtractPassName
from convertor_validator_service_lama.models.extract_job import ExtractJobPollingConfig
from convertor_validator_service_lama.services.document_structure_agent_factory import (
    LlamaExtractDocumentStructureAgentFactoryConfig,
    build_llama_extract_document_structure_agent,
)
from convertor_validator_service_lama.services.document_structure_extraction_stages import (
    DEFAULT_OVERVIEW_MAX_ITEMS,
    DEFAULT_SCOPE_MAX_ITEMS,
    DEFAULT_SCOPE_MAX_WINDOW_ITEMS,
    DEFAULT_SCOPE_OVERLAP_ITEMS,
    DEFAULT_STAGE_ITEM_TEXT_CHARS,
    DEFAULT_STAGE_MARKDOWN_EXCERPT_CHARS,
)
from convertor_validator_service_lama.services.document_structure_extraction_workflow import (
    DEFAULT_DETERMINISTIC_OVERVIEW_MIN_PAGES,
    DocumentStructureExtractionWorkflowResult,
    run_document_structure_extraction_workflow,
)
from convertor_validator_service_lama.services.llama_extract_structured_json_backend import (
    LlamaExtractClientLike,
)


@dataclass(frozen=True)
class LlamaExtractDocumentStructureWorkflowRuntimeConfig:
    parse_job_id: str | None = None
    document_hint: str | None = None
    pass_name: LlamaExtractPassName = "sections"
    schema_name: str = "document_structure_extraction_v1"
    expand: list[str] | None = None
    polling_config: ExtractJobPollingConfig | None = None
    include_metadata_in_instructions: bool = True
    overview_max_items: int = DEFAULT_OVERVIEW_MAX_ITEMS
    scope_max_items: int = DEFAULT_SCOPE_MAX_ITEMS
    scope_max_window_items: int = DEFAULT_SCOPE_MAX_WINDOW_ITEMS
    scope_overlap_items: int = DEFAULT_SCOPE_OVERLAP_ITEMS
    item_text_chars: int = DEFAULT_STAGE_ITEM_TEXT_CHARS
    markdown_excerpt_chars: int = DEFAULT_STAGE_MARKDOWN_EXCERPT_CHARS
    use_deterministic_overview_for_large_documents: bool = True
    deterministic_overview_min_pages: int = DEFAULT_DETERMINISTIC_OVERVIEW_MIN_PAGES


def run_llama_extract_document_structure_workflow(
    parse_result_payload: dict,
    *,
    settings: Settings | None = None,
    client: LlamaExtractClientLike | None = None,
    config: LlamaExtractDocumentStructureWorkflowRuntimeConfig | None = None,
) -> DocumentStructureExtractionWorkflowResult:
    """Run staged document-structure workflow using LlamaExtract backend.

    This helper composes already-tested layers:
    - LlamaExtract document-structure agent factory;
    - staged extraction workflow;
    - merge/validator inside the workflow.

    It does not create API endpoints and does not persist results.
    """

    resolved_config = config or LlamaExtractDocumentStructureWorkflowRuntimeConfig()
    parse_job_id = resolved_config.parse_job_id or _parse_job_id_from_payload(
        parse_result_payload
    )

    bundle = build_llama_extract_document_structure_agent(
        settings=settings,
        client=client,
        config=LlamaExtractDocumentStructureAgentFactoryConfig(
            parse_job_id=parse_job_id,
            document_hint=resolved_config.document_hint,
            pass_name=resolved_config.pass_name,
            schema_name=resolved_config.schema_name,
            expand=resolved_config.expand,
            polling_config=resolved_config.polling_config,
            include_metadata_in_instructions=resolved_config.include_metadata_in_instructions,
        ),
    )

    try:
        return run_document_structure_extraction_workflow(
            parse_result_payload,
            agent=bundle.agent,
            overview_max_items=resolved_config.overview_max_items,
            scope_max_items=resolved_config.scope_max_items,
            scope_max_window_items=resolved_config.scope_max_window_items,
            scope_overlap_items=resolved_config.scope_overlap_items,
            item_text_chars=resolved_config.item_text_chars,
            markdown_excerpt_chars=resolved_config.markdown_excerpt_chars,
            use_deterministic_overview_for_large_documents=(
                resolved_config.use_deterministic_overview_for_large_documents
            ),
            deterministic_overview_min_pages=(
                resolved_config.deterministic_overview_min_pages
            ),
        )
    finally:
        bundle.close()


def _parse_job_id_from_payload(parse_result_payload: dict) -> str | None:
    value = parse_result_payload.get("job_id")

    if isinstance(value, str) and value.strip():
        return value.strip()

    return None
