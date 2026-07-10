"""Модели ответов RAG Search (RS-6, уточнение 20.06)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SourceLocator(BaseModel):
    """Стабильный локатор для цитирования."""

    document_id: int = Field(..., description="ID документа в Registry")
    section_id: int | None = Field(default=None, description="ID секции")
    clause: str | None = Field(default=None, description="Номер пункта (напр. 6.1)")
    path: str | None = Field(default=None, description="Путь секции (напр. 6/6.1)")
    page: int | None = Field(default=None, description="Номер страницы (1-based)")
    section_title: str | None = Field(default=None, description="Название раздела")
    content: str = Field(..., description="Текст чанка (excerpt для ответа)")


class RetrievalMeta(BaseModel):
    """Технические метаданные поиска."""

    chunk_id: int = Field(..., description="ID чанка в БД (технический)")
    score: float = Field(..., description="Итоговая оценка релевантности (0..1)")
    mode: str = Field(..., description="Режим поиска: dense_rerank, hybrid_rerank, hybrid_rrf")


class ContextChunk(BaseModel):
    """Соседний чанк (context expansion)."""

    chunk_id: int = Field(..., description="ID соседнего чанка")
    content: str = Field(..., description="Содержимое соседнего чанка")
    page: int | None = Field(default=None, description="Номер страницы")


class SearchResult(BaseModel):
    """Один результат поиска: source + retrieval + context."""

    source: SourceLocator
    retrieval: RetrievalMeta
    context: list[ContextChunk] = Field(default_factory=list)


class SearchResponse(BaseModel):
    """Ответ POST /rag/search."""

    query: str
    results: list[SearchResult]
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
