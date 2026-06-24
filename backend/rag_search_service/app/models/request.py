"""Модели запросов для RAG Search."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    """Фильтры поиска: тип документа, категории, конкретные документы."""

    document_type: list[str] | None = Field(
        default=None, description="Типы документов (normative, technical, ...)"
    )
    category_ids: list[int] | None = Field(
        default=None, description="ID категорий для фильтрации"
    )
    document_ids: list[int] | None = Field(
        default=None, description="Ограничить поиск конкретными документами"
    )


class SearchRequest(BaseModel):
    """Запрос к POST /rag/search."""

    query: str = Field(..., max_length=2000, description="Поисковый запрос")
    valid_at: date = Field(..., description="Дата, на которую документы должны быть действующими")
    filters: SearchFilters | None = Field(default=None, description="Фильтры")

    model_config = {"json_schema_extra": {"examples": [
        {
            "query": "ледовый класс Arc4",
            "valid_at": "2026-06-18",
            "filters": {
                "document_type": ["normative"],
                "category_ids": [5, 12],
            },
        }
    ]}}
