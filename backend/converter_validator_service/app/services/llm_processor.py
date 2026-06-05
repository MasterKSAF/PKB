import logging
import time
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


async def enrich_document(
    document: dict[str, Any],
    *,
    model: str,
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
            timeout=timeout,
        )
        prompt = (
            "Уточни метаданные нормативного документа (код МКС, группа, эра) "
            "на основе JSON. Верни только JSON с ключами: "
            "mks_oks_code, group, era, validity_status."
        )
        response = await client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": prompt},
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
            "model": model,
            "tokens_used": tokens,
            "processing_time_ms": elapsed_ms,
        }
        return document, usage
    except Exception as exc:
        logger.warning("LLM enrichment failed: %s", exc)
        return document, {
            "model": model,
            "tokens_used": 0,
            "processing_time_ms": int((time.perf_counter() - started) * 1000),
        }
