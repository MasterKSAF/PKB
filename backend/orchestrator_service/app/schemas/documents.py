"""
Pydantic schemas for Documents API.

В оркестраторе осталась только одна операция над документами —
`POST /documents/{id}/reprocess` (P2I-9), pipeline-операция переиндексации.
Все остальные CRUD-операции над документами перенесены в `registry-service`
(см. docs/api/registry_service_api.md, группа documents).
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


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
