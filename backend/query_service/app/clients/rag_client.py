import asyncio
import time
from dataclasses import dataclass, field
import httpx
from ..config import get_settings

_circuit_open_until: float = 0.0
_CIRCUIT_COOLDOWN = 60.0

_MOCK_CHUNKS = [
    {
        "chunk_id": 420001,
        "document_id": 1,
        "document_title": "Правила классификации и постройки морских судов, Часть II",
        "section_id": 420001,
        "page": 42,
        "content": (
            "Для ледового класса Arc4 толщина обшивки ледового пояса должна быть не менее 12 мм. "
            "Расчёт выполняется с учётом района эксплуатации, материала и ледовой нагрузки."
        ),
        "excerpt": "Для ледового класса Arc4 толщина обшивки ледового пояса должна быть не менее 12 мм.",
        "score": 0.94,
        "clause": "4.2 Требования к обшивке ледового пояса",
        "section_title": "Ледовые усиления корпуса",
        "confidence": 0.91,
    },
    {
        "chunk_id": 420017,
        "document_id": 2,
        "document_title": "НСИ ПКБ, версия 2026",
        "section_id": 420017,
        "page": 17,
        "content": (
            "Класс Arc4: нормативная толщина листов обшивки — не менее 12 мм при стали категории Е. "
            "При других категориях стали расчёт выполняется индивидуально."
        ),
        "excerpt": "Класс Arc4: нормативная толщина — не менее 12 мм при стали категории Е.",
        "score": 0.87,
        "clause": "3.1 Нормативные требования НСИ",
        "section_title": "Нормативные параметры корпуса",
        "confidence": 0.84,
    },
]


@dataclass
class Chunk:
    chunk_id: int
    document_id: int
    document_title: str
    section_id: int
    page: int
    content: str
    excerpt: str
    score: float
    clause: str = ""
    section_title: str = ""
    confidence: float = 0.0


def _parse_chunk(item: dict) -> Chunk:
    """Парсинг результата RAG Search по спецификации RS-6.

    Формат:
    {
      "source": {"document_id": ..., "section_id": ..., "content": ..., ...},
      "retrieval": {"chunk_id": ..., "score": ...},
      "context": [...]
    }
    """
    source = item.get("source", {})
    retrieval = item.get("retrieval", {})
    return Chunk(
        chunk_id=retrieval.get("chunk_id", 0),
        document_id=source.get("document_id", 0),
        document_title=source.get("document_title", ""),
        section_id=source.get("section_id", 0),
        page=source.get("page", 0),
        content=source.get("content", ""),
        excerpt=source.get("content", ""),
        score=retrieval.get("score", 0.0),
        clause=source.get("clause", ""),
        section_title=source.get("section_title", ""),
        confidence=retrieval.get("score", 0.0),
    )


async def search(
    query: str,
    top_k: int = 10,
    filters: dict | None = None,
    valid_at: str | None = None,
    search_type: str = "hybrid",
    rerank: bool = True,
) -> list[Chunk]:
    settings = get_settings()

    global _circuit_open_until

    if settings.MOCK_RAG_ENABLED:
        return [Chunk(**c) for c in _MOCK_CHUNKS[:top_k]]

    if time.monotonic() < _circuit_open_until:
        raise RuntimeError("RAG search circuit open — downstream unavailable")

    backoff = 0.5
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{settings.RAG_SERVICE_URL}/api/v1/rag/search",
                    json={
                        "query": query,
                        "top_k": top_k,
                        "valid_at": valid_at,
                        "filters": filters or {},
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                _circuit_open_until = 0.0
                return [_parse_chunk(r) for r in data.get("results", [])]
        except Exception as exc:
            last_exc = exc
            if attempt < 2:
                await asyncio.sleep(backoff)
                backoff *= 2

    _circuit_open_until = time.monotonic() + _CIRCUIT_COOLDOWN
    raise RuntimeError(f"RAG search failed after 3 attempts: {last_exc}")
