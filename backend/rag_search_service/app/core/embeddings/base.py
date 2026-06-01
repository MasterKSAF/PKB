"""Абстрактный базовый класс для провайдеров эмбеддингов."""

from abc import ABC, abstractmethod



class EmbeddingProvider(ABC):
    """Базовый интерфейс для всех провайдеров эмбеддингов."""

    @abstractmethod
    async def encode(self, text: str) -> list[float]:
        """
        Преобразовать текст в векторное представление.

        Args:
            text: Входной текст для кодирования

        Returns:
            Вектор размерности EMBEDDING_DIM

        Raises:
            EmbeddingError: При ошибке генерации эмбеддинга
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Вернуть размерность вектора."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Вернуть название используемой модели."""
        pass


class EmbeddingError(Exception):
    """Базовое исключение для ошибок генерации эмбеддингов."""

    pass