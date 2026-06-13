# src/rag_builder/services/embedding_service.py

from rag_builder.models.domain import Chunk, EmbeddedChunk

class EmbeddingService:
    """
    Сервис генерации эмбеддингов.

    Текущая версия является заглушкой.

    В будущем здесь будет:
        - OpenAI Embeddings API
        - локальная модель BGE
        - Sentence Transformers
        - другая embedding-модель

    На этапе MVP возвращается фиктивный вектор.
    """

    def create_embedding(self, text: str) -> list[float]:
        """
        Создает эмбеддинг текста.

        Пока возвращает тестовый вектор.
        """

        return [0.0] * 1536


    def enrich_chunk(self, chunk: Chunk) -> EmbeddedChunk:
        """
        Добавляет эмбеддинг к чанку.
        """

        return EmbeddedChunk(
            chunk=chunk,
            embedding=self.create_embedding(chunk.content),
        )