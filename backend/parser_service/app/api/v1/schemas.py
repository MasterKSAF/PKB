from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime

# ========== ЗАПРОСЫ ==========
class ProcessRequest(BaseModel):
    task_id: int = Field(..., ge=1)
    version_id: str = Field(..., min_length=1)
    file_key: str = Field(..., min_length=1)
    options: Optional[Dict[str, bool]] = Field(default_factory=dict)

    @field_validator('version_id')
    @classmethod
    def validate_version_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('version_id cannot be empty')
        return v

class PreviewRequest(BaseModel):
    task_id: int = Field(..., ge=1)
    version_id: str = Field(..., min_length=1)
    file_key: str = Field(..., min_length=1)
    max_pages: int = Field(3, ge=1, le=100)
    options: Optional[Dict[str, bool]] = Field(default_factory=dict)

    @field_validator('options')
    @classmethod
    def validate_preview_options(cls, v: dict | None) -> dict:
        if v is None:
            return {}
        if v.get('extract_tables', False):
            raise ValueError('extract_tables cannot be True in preview')
        if v.get('extract_images', False):
            raise ValueError('extract_images cannot be True in preview')
        return v

# ========== ОТВЕТЫ ==========
class ProcessResponse(BaseModel):
    task_id: int
    status: str = "accepted"
    version_id: str
    estimated_completion: datetime

class PreviewResponse(BaseModel):
    task_id: int
    version_id: str
    preview: bool = True
    max_pages: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    document: Dict[str, Any]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": 420000,
                "version_id": "d5e0f3a2-1234",
                "preview": True,
                "max_pages": 3,
                "metadata": {"schema": "raw_ocr_v4", "created_at": "2026-05-17T09:15:00Z"},
                "document": {"source": {"file_name": "1_scan.pdf", "page_count": 2}}
            }
        }
    )

class StatusResponse(BaseModel):
    task_id: int
    status: str
    progress_percent: int = Field(0, ge=0, le=100)
    pages_processed: int = Field(0, ge=0)
    pages_total: int = Field(0, ge=0)
    avg_confidence: float = Field(0.0, ge=0.0, le=1.0)
    step: str
    step_detail: str
    started_at: datetime
    completed_at: Optional[datetime]

class ProcessesListResponse(BaseModel):
    processes: List[Dict[str, Any]]

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail