"""Базовый класс и модели для reranking-провайдеров."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RerankResult:
    """Результат reranking одного документа."""

    index: int
    score: float
    text: str


class RerankingError(Exception):
    """Ошибка при выполнении reranking."""


class RerankerProvider(ABC):
    """Абстрактный базовый класс для reranking-провайдеров."""

    @abstractmethod
    async def rerank(self, query: str, documents: list[str], top_n: int) -> list[RerankResult]:
        """Выполнить reranking документов по запросу.

        Args:
            query: Текстовый запрос
            documents: Список текстов документов для ранжирования
            top_n: Количество результатов для возврата

        Returns:
            Список RerankResult, отсортированный по убыванию score

        Raises:
            RerankingError: При ошибке reranking
        """

    @abstractmethod
    def get_model_name(self) -> str:
        """Возвращает имя используемой модели."""

    async def close(self) -> None:
        """Закрыть ресурсы провайдера."""
