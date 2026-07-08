from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RawJsonRequest(BaseModel):
    task_id: int = Field(..., ge=1)
    version_id: int | None = Field(None)
    document_id: int | None = Field(None, ge=1)
    raw_json: dict[str, Any] = Field(default_factory=dict)


class PreviewMetadataResponse(BaseModel):
    doc_code: str | None = None
    title: str | None = None
    mks_oks_code: str | None = None
    okstu_code: str | None = None
    udk_code: str | None = None
    pkb_codes: list[str] = Field(default_factory=list)
    document_type: str | None = None
    year: int | None = None
    era: str | None = None
    validity_status: str | None = None
    issuing_body: str | None = None
    jurisdiction: str | None = None
    source_type: str | None = None
    language: str | None = None


class ConvertRequest(RawJsonRequest):
    use_llm: bool = True
    llm_max_tokens: int | None = Field(None, ge=1, le=128000)
    llm_timeout: int | None = Field(None, ge=1, le=600)


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


class ValidateMetadataRequest(BaseModel):
    era: str = Field(..., min_length=1)
    source_type: str = Field(..., min_length=1)
    doc_code: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    mks_oks_code: str | None = None
    okstu_code: str | None = None


class ValidateMetadataResponse(BaseModel):
    title_hash_sha256: str
    title_key: str
    normalized_title: str
    source_type_normalized: str
    era_normalized: str


class FingerprintResult(BaseModel):
    file_hash_sha256: str
    title_hash_sha256: str
    title_key: str


class MatchingResult(BaseModel):
    predecessor_doc_id: int | None = None
    successor_doc_id: int | None = None


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
    document_id: int | None = None


class ConvertResponse(BaseModel):
    task_id: int
    version_id: int | None = None
    document_id: int | None = None
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
