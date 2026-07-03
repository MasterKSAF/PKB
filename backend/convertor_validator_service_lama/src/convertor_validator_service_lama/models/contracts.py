from typing import Literal

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
