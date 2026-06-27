"""
Pydantic schemas for Documents API.

В оркестраторе остались pipeline-операции:
- `POST /documents/{id}/reprocess` (P2I-9) — переиндексация
- `GET /documents/{id}/errors` — журнал ошибок обработки

Все остальные CRUD-операции над документами перенесены в `registry-service`
(см. docs/api/registry_service_api.md, группа documents).
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.schemas.common import PaginationMeta


class ReprocessMode(str, Enum):
    """Document reprocessing modes."""

    FULL = "full"
    OCR_ONLY = "ocr_only"
    CHUNKING_ONLY = "chunking_only"
    VALIDATION_ONLY = "validation_only"
    REINDEX = "reindex"


class ReprocessRequest(BaseModel):
    """Request body for reprocess."""

    mode: ReprocessMode = Field(
        ReprocessMode.FULL, description="Режим переобработки"
    )
    options: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Доп. опции: engine (paddleocr, tesseract), "
            "language (ru, en), pages (1-5)"
        ),
    )


class ReprocessResponse(BaseModel):
    """Response for reprocess (202 Accepted)."""

    mode: ReprocessMode = Field(..., description="Режим переобработки")
    document_id: str = Field(..., description="UUID документа")
    task_id: str = Field(..., description="ID задачи")
    status: str = Field(..., description="Статус")
    created_at: datetime = Field(..., description="Время создания")


class DocumentErrorItem(BaseModel):
    """Single error entry for GET /documents/{doc_id}/errors."""

    error_id: str = Field(..., description="Идентификатор ошибки")
    stage: str = Field(..., description="Этап: ocr, parsing, indexing, upload")
    page: int = Field(default=0, description="Номер страницы (0 — неизвестно)")
    error_code: str = Field(..., description="Код ошибки, напр. LOW_CONFIDENCE")
    error_message: str = Field(..., description="Описание ошибки")
    severity: str = Field(..., description="Серьёзность: warning, error, critical, info")
    retry_attempt: int = Field(default=0, description="Число повторов")
    timestamp: datetime = Field(..., description="Время возникновения")


class DocumentErrorsResponse(BaseModel):
    """Response for GET /documents/{doc_id}/errors."""

    errors: list[DocumentErrorItem] = Field(default_factory=list, description="Список ошибок")
    meta: PaginationMeta = Field(
        default_factory=lambda: PaginationMeta(total=0, page=1, page_size=50),
        description="Метаданные пагинации",
    )


class CreateVersionResponse(BaseModel):
    """Response for POST /documents/{doc_id}/versions (202 Accepted)."""

    document_id: int = Field(..., description="ID документа")
    version_id: int = Field(..., description="ID версии")
    version_number: int = Field(..., description="Номер версии")
    status: str = Field(..., description="Статус: uploaded")
    task_id: int = Field(..., description="ID задачи")
    file_hash_sha256: str = Field(..., description="SHA-256 хеш файла")
    is_duplicate_file: bool = Field(False, description="Файл-дубликат")
    created_at: datetime = Field(..., description="Время создания")


class DocumentStatusResponse(BaseModel):
    """Response for GET /documents/{doc_id}/status.

    Формат steps.pipeline зависит от статуса:
    - `processing`: formation + indexation с вложенными этапами
    - `approval_required`: только formation.preview
    - `completed`: formation + indexation + chunk_summary
    """

    document_id: int = Field(..., description="ID документа")
    status: str = Field(..., description="Статус: processing, approval_required, completed")
    progress_percent: float = Field(0.0, description="Прогресс (0-100)")
    steps: Dict[str, Any] = Field(default_factory=dict, description="Шаги pipeline")
    chunk_summary: Optional[Dict[str, Any]] = Field(None, description="Сводка по чанкам (только completed)")
    started_at: Optional[datetime] = Field(None, description="Время начала")
    completed_at: Optional[datetime] = Field(None, description="Время завершения")
    estimated_completion: Optional[datetime] = Field(None, description="Ожидаемое время завершения")
