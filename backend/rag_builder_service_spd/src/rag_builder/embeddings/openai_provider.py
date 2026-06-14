# src/rag_builder/embeddings/openai_provider.py

from openai import OpenAI

from rag_builder.core.config import settings


class OpenAIEmbeddingProvider:
    """
    Провайдер эмбеддингов через OpenAI API.
    """

    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def create_embedding(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text,
        )

        return response.data[0].embedding
