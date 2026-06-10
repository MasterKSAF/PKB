"""
Pydantic схемы для API версии 2.

Основные отличия от v1:
- В ProcessRequest нет version_id, добавлен mode (full/preview) и max_pages.
- Ответы упрощены (например, ProcessResponse не содержит version_id).
- Добавлены ResultResponse и ParserInfo.
"""
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ProcessingMode(str, Enum):
    """
    Режим обработки документа.
    """
    FULL = "full"          # Полная обработка (асинхронная)
    PREVIEW = "preview"    # Предпросмотр (синхронный)


class ProcessRequest(BaseModel):
    """
    Запрос на обработку документа (v2).
    """
    task_id: int = Field(..., ge=1, description="Идентификатор задачи")
    file_key: str = Field(..., min_length=1, description="Ключ файла в MinIO")
    mode: ProcessingMode = Field(default=ProcessingMode.FULL, description="Режим обработки")
    max_pages: Optional[int] = Field(None, ge=1, le=100, description="Максимальное количество страниц (обязательно для preview)")
    options: Optional[Dict[str, bool]] = Field(default_factory=dict, description="Опции парсинга")

    @field_validator('mode', mode='before')
    @classmethod
    def validate_mode(cls, v):
        """Преобразует строковое значение в enum."""
        if isinstance(v, str):
            return ProcessingMode(v)
        return v

    @model_validator(mode='after')
    def check_max_pages_for_preview(self):
        """В режиме preview max_pages обязателен."""
        if self.mode == ProcessingMode.PREVIEW and self.max_pages is None:
            raise ValueError('max_pages is required for preview mode')
        return self

    @model_validator(mode='after')
    def check_options_for_preview(self):
        """Запрещает extract_tables и extract_images в режиме preview."""
        if self.mode == ProcessingMode.PREVIEW:
            opts = self.options or {}
            if opts.get('extract_tables', False):
                raise ValueError('extract_tables cannot be True in preview mode')
            if opts.get('extract_images', False):
                raise ValueError('extract_images cannot be True in preview mode')
        return self


class ProcessResponse(BaseModel):
    """
    Ответ на запрос запуска полной обработки (v2).
    """
    task_id: int = Field(..., description="ID задачи")
    status: str = Field("accepted", description="Статус ('accepted')")
    estimated_completion: datetime = Field(..., description="Предполагаемое время завершения (UTC)")


class PreviewResponse(BaseModel):
    """
    Ответ на синхронный предпросмотр (v2).
    """
    task_id: int = Field(..., description="ID задачи")
    version_id: str = Field("", description="Версия документа (в v2 всегда пустая строка)")
    preview: bool = Field(True, description="Флаг предпросмотра")
    max_pages: int = Field(..., description="Максимальное количество обработанных страниц")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные")
    document: Dict[str, Any] = Field(..., description="Содержимое документа")


class StatusResponse(BaseModel):
    """
    Ответ на запрос статуса задачи (v2, аналогичен v1).
    """
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
    """
    Ответ на запрос списка активных процессов (v2).
    """
    processes: List[Dict[str, Any]]


class ErrorDetail(BaseModel):
    """
    Детали ошибки.
    """
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """
    Стандартизированный ответ с ошибкой.
    """
    error: ErrorDetail


class ParserInfo(BaseModel):
    """
    Информация о парсере, использованном для обработки.
    """
    name: str = Field(..., description="Название парсера")
    version: str = Field(..., description="Версия парсера")
    ocr_engine: Optional[str] = Field(None, description="Используемый OCR-движок")
    ocr_fallback: bool = Field(False, description="Был ли использован fallback OCR")


class ResultMetadata(BaseModel):
    """
    Метаданные результата (v2).
    """
    schema_version: str = Field(..., alias="schema", description="Версия схемы вывода")
    mode: str = Field(..., description="Режим обработки (full/preview)")
    preview_not_supported: bool = Field(..., description="Флаг, что предпросмотр не поддерживается (если max_pages < total_pages)")
    created_at: datetime = Field(..., description="Время создания результата")
    parser: ParserInfo = Field(..., description="Информация о парсере")

    model_config = ConfigDict(populate_by_name=True)


class ResultResponse(BaseModel):
    """
    Полный ответ на запрос результата (v2).
    """
    task_id: int = Field(..., description="ID задачи")
    metadata: ResultMetadata = Field(..., description="Метаданные")
    document: Dict[str, Any] = Field(..., description="Стандартизированный документ")
    quality: Dict[str, Any] = Field(..., description="Метрики качества")
    errors: List[Any] = Field(default_factory=list, description="Список ошибок")
    status: str = Field(..., description="Статус завершения (completed/failed)")