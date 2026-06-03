import asyncio
import httpx
from ..config import get_settings

_MOCK_TERMS: dict[str, str] = {
    "обшивка": "обшивка корпуса",
    "ледовый пояс": "ледовый пояс корпуса",
    "толщина": "толщина листа",
    "ледовый класс": "ледовый класс судна",
    "arc4": "Arc4",
    "arc5": "Arc5",
    "arc6": "Arc6",
    "корпус": "корпус судна",
    "шпангоут": "шпангоут корпуса",
    "настил": "настил палубы",
    "переборка": "водонепроницаемая переборка",
    "флор": "флор корпуса",
    "стрингер": "стрингер днища",
    "киль": "кильсон",
}


async def normalize_term(term: str) -> str:
    settings = get_settings()

    if settings.MOCK_REGISTRY_ENABLED:
        return _MOCK_TERMS.get(term.lower(), term)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{settings.REGISTRY_SERVICE_URL}/registry/terminology/normalize",
                params={"term": term},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("standard_term", term)
    except Exception:
        return term


async def enrich_query(query: str) -> tuple[str, list[str]]:
    words = query.split()
    normalized_words: list[str] = []
    synonyms: list[str] = []

    tasks = [normalize_term(w) for w in words]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for word, result in zip(words, results):
        norm = result if isinstance(result, str) else word
        normalized_words.append(norm)
        if norm.lower() != word.lower():
            synonyms.append(norm)

    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]
    bigram_tasks = [normalize_term(bg) for bg in bigrams]
    bigram_results = await asyncio.gather(*bigram_tasks, return_exceptions=True)
    for bg, result in zip(bigrams, bigram_results):
        if isinstance(result, str) and result.lower() != bg.lower():
            synonyms.append(result)

    return " ".join(normalized_words), list(dict.fromkeys(synonyms))
