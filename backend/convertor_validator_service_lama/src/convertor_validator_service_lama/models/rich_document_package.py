from typing import Any, Literal

from pydantic import BaseModel, Field

from convertor_validator_service_lama.models.extract_job import ExtractJobResult
from convertor_validator_service_lama.models.parse_job import ParseJobResult


class RichDocumentPackageArtifact(BaseModel):
    artifact_key: str = Field(min_length=1)
    produced_by: str = Field(min_length=1)
    source: Literal["parse_result", "extract_pass", "python_validator"]
    content: Any | None = None
    raw_response: dict[str, Any] = Field(default_factory=dict)


class RichDocumentPackage(BaseModel):
    package_name: str = "rich_document_package.json"
    parse_job_id: str = Field(min_length=1)
    source_pdf_path: str | None = None
    document_code: str | None = None
    parse_result: ParseJobResult
    extract_results: dict[str, ExtractJobResult] = Field(default_factory=dict)
    artifacts: dict[str, RichDocumentPackageArtifact] = Field(default_factory=dict)
    final_correction_policy: str = "python_validator_assembler_applies_final_corrections"


class RichDocumentPackageAssemblyRequest(BaseModel):
    source_pdf_path: str | None = None
    document_code: str | None = None
    parse_result: ParseJobResult
    extract_results: dict[str, ExtractJobResult] = Field(default_factory=dict)


class RichDocumentPackageAssemblyResult(BaseModel):
    package: RichDocumentPackage
    artifact_count: int = Field(ge=0)