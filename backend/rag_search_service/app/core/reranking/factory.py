"""Фабрика reranking-провайдеров (синглтон).

Автоматически выбирает провайдер на основе reranker_base_url:
- infinity:// или http://*infinity* → InfinityRerankerProvider
- иначе → TEIRerankerProvider
"""

from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.core.logging import get_logger
from app.core.reranking.base import RerankerProvider
from app.core.reranking.infinity_provider import InfinityRerankerProvider
from app.core.reranking.tei_provider import TEIRerankerProvider

logger = get_logger("reranking.factory")


@lru_cache(maxsize=1)
def get_reranker() -> RerankerProvider:
    """Возвращает синглтон reranker-провайдера.

    Провайдер выбирается автоматически:
    - если base_url содержит 'infinity' → InfinityRerankerProvider
    - иначе → TEIRerankerProvider
    """
    settings = get_settings()
    base_url = settings.reranker_base_url.lower()

    if "infinity" in base_url:
        logger.info(
            "Using InfinityRerankerProvider (base_url=%s)",
            settings.reranker_base_url,
        )
        return InfinityRerankerProvider()

    logger.info(
        "Using TEIRerankerProvider (base_url=%s)",
        settings.reranker_base_url,
    )
    return TEIRerankerProvider()
