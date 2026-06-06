"""Модели запросов для RAG Search."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SearchFilters(BaseModel):
    """Фильтры поиска: тип документа, диапазон дат принятия."""

    document_type: list[str] | None = Field(
        default=None, description="Типы документов (normative, technical, ...)"
    )
    date_from: date | None = Field(default=None, description="Дата выпуска документа (от)")
    date_to: date | None = Field(default=None, description="Дата выпуска документа (до)")

    @field_validator("date_from", "date_to")
    @classmethod
    def validate_dates(cls, v: date | None, info) -> date | None:
        return v

    def model_post_init(self, __context) -> None:
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be earlier than date_to")


class SearchRequest(BaseModel):
    """Запрос к POST /rag/search."""

    query: str = Field(..., min_length=1, max_length=2000, description="Поисковый запрос")
    top_k: int = Field(default=10, ge=1, le=100, description="Количество результатов")
    filters: SearchFilters | None = Field(default=None, description="Фильтры")
    search_type: Literal["hybrid", "dense", "sparse"] = Field(
        default="hybrid", description="Тип поиска"
    )
    rerank: bool = Field(default=True, description="Применять RRF-реранжирование")

    model_config = {"json_schema_extra": {"examples": [
        {
            "query": "ледовый класс Arc4",
            "top_k": 10,
            "filters": {
                "document_type": ["normative"],
                "date_from": "2000-01-01",
                "date_to": "2026-12-31",
            },
            "search_type": "hybrid",
            "rerank": True,
        }
    ]}}