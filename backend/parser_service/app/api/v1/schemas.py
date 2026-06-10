"""
Pydantic схемы для API версии 1.

Определяют структуру запросов и ответов для эндпоинтов:
- ProcessRequest / ProcessResponse
- PreviewRequest / PreviewResponse
- StatusResponse
- ErrorResponse
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime

# ========== ЗАПРОСЫ ==========
class ProcessRequest(BaseModel):
    """
    Запрос на запуск полной обработки документа (v1).
    """
    task_id: int = Field(..., ge=1, description="Идентификатор задачи (целое число >= 1)")
    version_id: str = Field(..., min_length=1, description="Версия документа (не может быть пустой)")
    file_key: str = Field(..., min_length=1, description="Ключ файла в MinIO")
    options: Optional[Dict[str, bool]] = Field(default_factory=dict, description="Опции парсинга")

    @field_validator('version_id')
    @classmethod
    def validate_version_id(cls, v: str) -> str:
        """Проверяет, что version_id не пустой и не состоит из пробелов."""
        if not v or not v.strip():
            raise ValueError('version_id cannot be empty')
        return v

class PreviewRequest(BaseModel):
    """
    Запрос на предпросмотр документа (v1).
    """
    task_id: int = Field(..., ge=1, description="Идентификатор задачи")
    version_id: str = Field(..., min_length=1, description="Версия документа")
    file_key: str = Field(..., min_length=1, description="Ключ файла в MinIO")
    max_pages: int = Field(3, ge=1, le=100, description="Максимальное количество страниц для предпросмотра (1-100)")
    options: Optional[Dict[str, bool]] = Field(default_factory=dict, description="Опции (extract_tables/extract_images запрещены)")

    @field_validator('options')
    @classmethod
    def validate_preview_options(cls, v: dict | None) -> dict:
        """
        Запрещает extract_tables и extract_images в режиме preview.
        """
        if v is None:
            return {}
        if v.get('extract_tables', False):
            raise ValueError('extract_tables cannot be True in preview')
        if v.get('extract_images', False):
            raise ValueError('extract_images cannot be True in preview')
        return v

# ========== ОТВЕТЫ ==========
class ProcessResponse(BaseModel):
    """
    Ответ на запрос запуска полной обработки (v1).
    """
    task_id: int = Field(..., description="ID задачи")
    status: str = Field("accepted", description="Статус ('accepted')")
    version_id: str = Field(..., description="Версия документа")
    estimated_completion: datetime = Field(..., description="Предполагаемое время завершения (UTC)")

class PreviewResponse(BaseModel):
    """
    Ответ на запрос предпросмотра (v1).
    """
    task_id: int = Field(..., description="ID задачи")
    version_id: str = Field(..., description="Версия документа")
    preview: bool = Field(True, description="Флаг предпросмотра")
    max_pages: int = Field(..., description="Максимальное количество обработанных страниц")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные (схема, время создания)")
    document: Dict[str, Any] = Field(..., description="Содержимое документа в стандартизированном формате")

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
    """
    Ответ на запрос статуса задачи (v1).
    """
    task_id: int = Field(..., description="ID задачи")
    status: str = Field(..., description="Статус (accepted, processing, completed, failed)")
    progress_percent: int = Field(0, ge=0, le=100, description="Процент выполнения")
    pages_processed: int = Field(0, ge=0, description="Количество обработанных страниц")
    pages_total: int = Field(0, ge=0, description="Общее количество страниц")
    avg_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Средняя уверенность OCR")
    step: str = Field(..., description="Текущий шаг пайплайна")
    step_detail: str = Field(..., description="Детальное описание шага")
    started_at: datetime = Field(..., description="Время начала задачи")
    completed_at: Optional[datetime] = Field(None, description="Время завершения (если выполнено)")

class ProcessesListResponse(BaseModel):
    """
    Ответ на запрос списка активных процессов.
    """
    processes: List[Dict[str, Any]] = Field(..., description="Список активных задач")


class ErrorDetail(BaseModel):
    """
    Детали ошибки.
    """
    code: str = Field(..., description="Код ошибки")
    message: str = Field(..., description="Сообщение об ошибке")
    details: Optional[Dict[str, Any]] = Field(None, description="Дополнительные детали")


class ErrorResponse(BaseModel):
    """
    Стандартизированный ответ с ошибкой.
    """
    error: ErrorDetail = Field(..., description="Объект с деталями ошибки")