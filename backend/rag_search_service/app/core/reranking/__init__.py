"""Модуль reranking (TEI / Infinity v2).

Провайдер выбирается автоматически в factory.get_reranker()
на основе RERANKER_BASE_URL:
- infinity → InfinityRerankerProvider
- иначе → TEIRerankerProvider
"""

from app.core.reranking.base import RerankResult, RerankerProvider, RerankingError
from app.core.reranking.factory import get_reranker
from app.core.reranking.infinity_provider import InfinityRerankerProvider
from app.core.reranking.tei_provider import TEIRerankerProvider

__all__ = [
    "RerankResult", "RerankerProvider", "RerankingError",
    "get_reranker",
    "InfinityRerankerProvider", "TEIRerankerProvider",
]
