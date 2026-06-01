"""Модели ответов RAG Search."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChunkResult(BaseModel):
    """Один найденный чанк с метаданными."""

    chunk_id: int = Field(..., description="ID чанка")
    document_id: Any = Field(..., description="UUID документа")
    document_title: str = Field(..., description="Название документа")
    doc_code: str | None = Field(default=None, description="Обозначение документа (ГОСТ, ТУ)")
    section_id: int | None = Field(default=None, description="ID секции")
    section_title: str | None = Field(default=None, description="Название раздела")
    page: int | None = Field(default=None, description="Номер страницы")
    content: str = Field(..., description="Полное содержимое чанка")
    score: float = Field(..., description="Оценка релевантности (RRF или raw)")
    clause: str | None = Field(default=None, description="Пункт документа")
    confidence: float | None = Field(default=None, description="Уверенность извлечения")


class SearchResponse(BaseModel):
    """Ответ POST /rag/search."""

    query: str
    results: list[ChunkResult]
    search_type_used: str
    processing_time_ms: int
    total_found: int


class HealthResponse(BaseModel):
    """Ответ GET /health."""

    status: str
    service: str
    version: str
    uptime_seconds: int
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorDetail(BaseModel):
    """Детали ошибки по спецификации common_api.md."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Обёртка ошибки."""

    error: ErrorDetail