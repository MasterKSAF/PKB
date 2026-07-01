import asyncio
import logging
import time
import httpx
from ..config import get_settings

logger = logging.getLogger("query_service.llm")


class LLMResult:
    __slots__ = ("content", "prompt_tokens", "completion_tokens", "duration_ms")

    def __init__(self, content: str, prompt_tokens: int, completion_tokens: int, duration_ms: int):
        self.content = content
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.duration_ms = duration_ms


async def complete(
    messages: list[dict],
    cache_key: str | None = None,
    max_tokens: int | None = None,
) -> LLMResult:
    settings = get_settings()

    payload = {
        "model": settings.LLM_MODEL,
        "messages": messages,
        "temperature": settings.LLM_TEMPERATURE,
        "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
        "top_p": settings.LLM_TOP_P,
        "stream": False,
    }
    if cache_key:
        payload["user"] = cache_key
    headers = {"Content-Type": "application/json"}
    if settings.LLM_API_KEY:
        headers["Authorization"] = f"Bearer {settings.LLM_API_KEY}"

    backoff = 1.0
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            t0 = time.monotonic()
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{settings.LLM_API_URL}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
            duration_ms = int((time.monotonic() - t0) * 1000)
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            content = data["choices"][0]["message"]["content"]
            logger.info(
                "llm_complete model=%s prompt_tokens=%d completion_tokens=%d duration_ms=%d",
                settings.LLM_MODEL, prompt_tokens, completion_tokens, duration_ms,
            )
            return LLMResult(content, prompt_tokens, completion_tokens, duration_ms)
        except Exception as exc:
            last_exc = exc
            if attempt < 2:
                await asyncio.sleep(backoff)
                backoff *= 2

    raise RuntimeError(f"LLM completion failed after 3 attempts: {last_exc}")
