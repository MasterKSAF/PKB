from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RawJsonRequest(BaseModel):
    task_id: str = Field(..., min_length=1)
    version_id: str = Field(..., min_length=1)
    raw_json: dict[str, Any] = Field(default_factory=dict)


class PreviewMetadataResponse(BaseModel):
    doc_code: str
    title: str
    document_type: str
    year: str
    revision: str | None = None


class ConvertRequest(RawJsonRequest):
    use_llm: bool = False
    llm_model: str = "gpt-4o-mini"
    llm_max_tokens: int = Field(4096, ge=1, le=128000)
    llm_timeout: int = Field(60, ge=1, le=600)


class LlmUsage(BaseModel):
    model: str
    tokens_used: int = 0
    processing_time_ms: int = 0


class ClassificationResult(BaseModel):
    mks_oks_code: str | None = None
    mks_status: str | None = None
    okstu_status: str | None = None
    udk_code: str | None = None
    udk_valid: bool | None = None
    overall_status: str = "CONFIRMED"


class FingerprintResult(BaseModel):
    file_hash_sha256: str
    title_hash_sha256: str


class MatchingResult(BaseModel):
    predecessor_doc_id: str | None = None
    successor_doc_id: str | None = None


class ValidationResult(BaseModel):
    validation_id: str
    structure_valid: bool
    classification: ClassificationResult | dict[str, Any]
    fingerprint: FingerprintResult
    matching: MatchingResult
    cross_references: list[dict[str, Any]] = Field(default_factory=list)
    decision: str
    status: str


class ValidateDocumentResponse(ValidationResult):
    document_id: str


class ConvertResponse(BaseModel):
    task_id: str
    version_id: str
    document_id: str
    metadata: dict[str, Any]
    document: dict[str, Any]
    validation: ValidationResult
    llm_usage: LlmUsage | None = None

    model_config = ConfigDict(extra="allow")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
