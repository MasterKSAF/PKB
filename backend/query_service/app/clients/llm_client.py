import asyncio
import httpx
from ..config import get_settings


async def complete(messages: list[dict], cache_key: str | None = None) -> str:
    settings = get_settings()

    payload = {
        "model": settings.LLM_MODEL,
        "messages": messages,
        "temperature": settings.LLM_TEMPERATURE,
        "max_tokens": settings.LLM_MAX_TOKENS,
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
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{settings.LLM_API_URL}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as exc:
            last_exc = exc
            if attempt < 2:
                await asyncio.sleep(backoff)
                backoff *= 2

    raise RuntimeError(f"LLM completion failed after 3 attempts: {last_exc}")
