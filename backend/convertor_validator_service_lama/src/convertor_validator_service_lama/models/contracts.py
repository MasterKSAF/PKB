from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "convertor_validator_service_lama"


class PipelineStep(BaseModel):
    name: str
    description: str
    uses_parse_job_id: bool = False


class DryRunResponse(BaseModel):
    service: str = "convertor_validator_service_lama"
    mode: Literal["dry_run"] = "dry_run"
    accepted_input: Literal["source_pdf"] = "source_pdf"
    output_package: str = "rich_document_package.json"
    planned_steps: list[PipelineStep] = Field(default_factory=list)


class ParseJobDryRunRequest(BaseModel):
    source_pdf_path: str
    document_code: str | None = None


class ParseJobDryRunResponse(BaseModel):
    service: str = "convertor_validator_service_lama"
    mode: Literal["parse_job_dry_run"] = "parse_job_dry_run"
    source_pdf_path: str
    expected_parser: str = "LlamaParse"
    expected_parse_job_id: str = "dry-run-parse-job-id"
    next_step: str = "run LlamaExtract passes by parse_job_id"
    parse_payload: dict[str, Any] = Field(default_factory=dict)


class ParseJobRequest(BaseModel):
    source_pdf_path: str
    expand: list[str] = Field(default_factory=lambda: ["markdown", "markdown_full", "text", "text_full", "items", "metadata", "job_metadata"])
    max_attempts: int = Field(default=60, ge=1)
    interval_seconds: float = Field(default=2.0, ge=0.0)


LlamaExtractPassName = Literal[
    "document_boundaries",
    "title_metadata",
    "table_of_contents",
    "sections",
    "tables",
    "images",
    "formulas",
    "cross_references",
    "validation_critic",
]


class ExtractPassPlanItem(BaseModel):
    name: LlamaExtractPassName
    uses_parse_job_id: bool = True
    output_key: str


class ExtractPassPlanResponse(BaseModel):
    service: str = "convertor_validator_service_lama"
    mode: Literal["extract_pass_plan"] = "extract_pass_plan"
    source: Literal["parse_job_id"] = "parse_job_id"
    passes: list[ExtractPassPlanItem] = Field(default_factory=list)


class ExtractPassDryRunRequest(BaseModel):
    parse_job_id: str
    pass_name: LlamaExtractPassName


class ExtractPassDryRunResponse(BaseModel):
    service: str = "convertor_validator_service_lama"
    mode: Literal["extract_pass_dry_run"] = "extract_pass_dry_run"
    parse_job_id: str
    pass_name: LlamaExtractPassName
    extract_payload: dict[str, Any] = Field(default_factory=dict)


class ExtractPassRunRequest(BaseModel):
    parse_job_id: str = Field(min_length=1)
    pass_name: LlamaExtractPassName
    extraction_schema: dict[str, Any] = Field(default_factory=dict)
    instructions: str | None = None
    schema_name: str | None = None
    expand: list[str] = Field(default_factory=lambda: ["extract_result"])
    max_attempts: int = Field(default=60, ge=1)
    interval_seconds: float = Field(default=2.0, ge=0.0)


class ExtractPassesDryRunRequest(BaseModel):
    parse_job_id: str


class ExtractPassesDryRunResponse(BaseModel):
    service: str = "convertor_validator_service_lama"
    mode: Literal["extract_passes_dry_run"] = "extract_passes_dry_run"
    parse_job_id: str
    extract_payloads: list[dict[str, Any]] = Field(default_factory=list)


class ExtractPassesRunRequest(BaseModel):
    parse_job_id: str = Field(min_length=1)
    extraction_schemas: dict[str, dict[str, Any]] = Field(default_factory=dict)
    instructions_by_pass: dict[str, str] = Field(default_factory=dict)
    schema_names_by_pass: dict[str, str] = Field(default_factory=dict)
    expand: list[str] = Field(default_factory=lambda: ["extract_result"])
    max_attempts: int = Field(default=60, ge=1)
    interval_seconds: float = Field(default=2.0, ge=0.0)


class RichDocumentPackageDryRunRequest(BaseModel):
    source_pdf_path: str
    document_code: str | None = None


class RichDocumentPackageDryRunResponse(BaseModel):
    service: str = "convertor_validator_service_lama"
    mode: Literal["rich_document_package_dry_run"] = "rich_document_package_dry_run"
    package_name: str = "rich_document_package.json"
    source_pdf_path: str
    parse_job_id: str = "dry-run-parse-job-id"
    parse_payload: dict[str, Any] = Field(default_factory=dict)
    extract_payloads: list[dict[str, Any]] = Field(default_factory=list)
    final_correction_policy: str = "python_validator_assembler_applies_final_corrections"


class RichDocumentArtifactPlanItem(BaseModel):
    artifact_key: str
    produced_by: str
    source: Literal["parse_job_id", "extract_pass", "python_validator"]


class RichDocumentPackagePlanResponse(BaseModel):
    service: str = "convertor_validator_service_lama"
    mode: Literal["rich_document_package_plan"] = "rich_document_package_plan"
    package_name: str = "rich_document_package.json"
    final_correction_policy: str = "python_validator_assembler_applies_final_corrections"
    artifacts: list[RichDocumentArtifactPlanItem] = Field(default_factory=list)

class DocumentStructureWorkflowStageSummary(BaseModel):
    stage_id: str
    stage_type: str
    namespace_id: str | None = None
    scope_title: str | None = None
    scope_type: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    window_index: int | None = None
    windows_count: int | None = None
    items_count: int | None = None
    items_preview_count: int | None = None
    source_item_index_start: int | None = None
    source_item_index_end: int | None = None
    markdown_excerpt_chars: int = 0


class DocumentStructureWorkflowDryRunRequest(BaseModel):
    parse_result_payload: dict[str, Any] = Field(default_factory=dict)
    numbering_scopes: list[dict[str, Any]] | None = None
    overview_max_items: int = Field(default=180, ge=1)
    scope_max_items: int = Field(default=350, ge=1)
    scope_max_window_items: int = Field(default=300, ge=1)
    scope_overlap_items: int = Field(default=20, ge=0)
    item_text_chars: int = Field(default=700, ge=1)
    markdown_excerpt_chars: int = Field(default=12_000, ge=1)


class DocumentStructureWorkflowDryRunResponse(BaseModel):
    service: str = "convertor_validator_service_lama"
    mode: Literal["document_structure_workflow_dry_run"] = "document_structure_workflow_dry_run"
    parse_job_id: str | None = None
    page_count: int | None = None
    items_count: int = 0
    stages_count: int = 0
    requires_overview_agent_output: bool = True
    overview_items_preview_count: int = 0
    overview_page_overview_count: int = 0
    overview_markdown_excerpt_chars: int = 0
    scope_inputs_count: int = 0
    scope_stage_summaries: list[DocumentStructureWorkflowStageSummary] = Field(default_factory=list)

class DocumentStructureWorkflowRunRequest(BaseModel):
    parse_result_payload: dict[str, Any] = Field(default_factory=dict)
    parse_job_id: str | None = Field(default=None, min_length=1)
    document_hint: str | None = None
    pass_name: LlamaExtractPassName = "sections"
    schema_name: str = "document_structure_extraction_v1"
    expand: list[str] = Field(default_factory=lambda: ["extract_result"])
    max_attempts: int = Field(default=60, ge=1)
    interval_seconds: float = Field(default=2.0, ge=0.0)
    include_metadata_in_instructions: bool = True
    overview_max_items: int = Field(default=180, ge=1)
    scope_max_items: int = Field(default=350, ge=1)
    scope_max_window_items: int = Field(default=300, ge=1)
    scope_overlap_items: int = Field(default=20, ge=0)
    item_text_chars: int = Field(default=700, ge=1)
    markdown_excerpt_chars: int = Field(default=12_000, ge=1)


class DocumentStructureWorkflowRunResponse(BaseModel):
    service: str = "convertor_validator_service_lama"
    mode: Literal["document_structure_workflow_run"] = "document_structure_workflow_run"
    parse_job_id: str | None = None
    document_profile: str = "unknown"
    page_count: int | None = None
    numbering_scopes_count: int = 0
    item_classifications_count: int = 0
    sections_count: int = 0
    issues_count: int = 0
    scope_inputs_count: int = 0
    scope_extractions_count: int = 0
    overview_items_preview_count: int = 0
    overview_page_overview_count: int = 0
    scope_stage_ids: list[str] = Field(default_factory=list)
    merged_extraction: dict[str, Any] = Field(default_factory=dict)
