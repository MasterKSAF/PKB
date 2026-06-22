"""Фабрика reranking-провайдеров (синглтон)."""

from __future__ import annotations

from functools import lru_cache

from app.core.reranking.tei_provider import TEIRerankerProvider


@lru_cache(maxsize=1)
def get_reranker() -> TEIRerankerProvider:
    """Возвращает синглтон TEI-reranker."""
    return TEIRerankerProvider()
