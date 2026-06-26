import httpx
from openai import OpenAI

from rag_search.core.config import settings
from rag_search.embeddings.base import EmbeddingResult


class OpenAICompatibleEmbeddingProvider:
    supports_dense = True

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        embedding_dim: int | None = None,
    ) -> None:
        self.model = model or settings.EMBEDDING_MODEL
        self.embedding_dim = embedding_dim or int(settings.EMBEDDING_DIM)

        client_kwargs = {
            "api_key": api_key or settings.EMBEDDING_API_KEY or "sk-noop",
            "http_client": httpx.Client(
                timeout=30.0,
                trust_env=False,
            ),
        }

        resolved_base_url = base_url or settings.effective_embedding_api_base_url

        if resolved_base_url:
            client_kwargs["base_url"] = resolved_base_url.rstrip("/")

        self.client = OpenAI(**client_kwargs)

    def create_embedding_with_usage(self, text: str) -> EmbeddingResult:
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
            dimensions=self.embedding_dim,
        )

        embedding = list(response.data[0].embedding)

        if len(embedding) != self.embedding_dim:
            raise ValueError(
                "Embedding dimension mismatch: "
                f"expected {self.embedding_dim}, got {len(embedding)}"
            )

        usage = getattr(response, "usage", None)
        token_count = int(getattr(usage, "prompt_tokens", 0) or 0)

        return EmbeddingResult(
            embedding=embedding,
            token_count=token_count,
            cost_usd=0.0,
        )
