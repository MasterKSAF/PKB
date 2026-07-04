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
    expand: list[str] = Field(default_factory=lambda: ["markdown", "items", "metadata", "job_metadata"])
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
