import logging
import time
from typing import Any

from app.config import settings
from app.core.exceptions import MetadataExtractionFailedError

logger = logging.getLogger(__name__)

try:
    from openai import AuthenticationError as _OpenAIAuthError
except ImportError:
    _OpenAIAuthError = type("_OpenAIAuthError", (Exception,), {})

_LLM_SYSTEM_PROMPT = (
    "Ты — ассистент по инженерным нормативно-техническим документам ПКБ. "
    "Извлеки из текста: 1) название документа, 2) код документа, 3) год издания. "
    "Верни JSON."
)


async def enrich_document(
    document: dict[str, Any],
    *,
    max_tokens: int,
    timeout: int,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if not settings.openai_api_key:
        logger.info("LLM skipped: OPENAI_API_KEY is not set")
        return document, None

    started = time.perf_counter()
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.llm_base_url,
            timeout=timeout,
        )
        response = await client.chat.completions.create(
            model=settings.llm_model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": _LLM_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": str(document.get("metadata", {}))[:8000],
                },
            ],
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        tokens = 0
        if response.usage:
            tokens = response.usage.total_tokens or 0
        usage = {
            "model": settings.llm_model,
            "tokens_used": tokens,
            "processing_time_ms": elapsed_ms,
        }
        return document, usage
    except _OpenAIAuthError:
        raise MetadataExtractionFailedError(
            "LLM API key is invalid or revoked"
        )
    except Exception as exc:
        logger.warning("LLM enrichment failed: %s", exc)
        return document, {
            "model": settings.llm_model,
            "tokens_used": 0,
            "processing_time_ms": int((time.perf_counter() - started) * 1000),
        }
