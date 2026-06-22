"""Context expansion: добавление соседних чанков для каждого результата."""

from __future__ import annotations

import asyncpg

from app.core.logging import get_logger

logger = get_logger("search.context")


async def expand_context(
    conn: asyncpg.Connection,
    chunk_id: int,
    section_id: int | None,
    chunk_index: int | None,
    expansion: int = 2,
) -> list[dict]:
    """
    Найти соседние чанки (до/после) для context expansion.

    Args:
        conn: Подключение к БД
        chunk_id: ID целевого чанка (исключается из результата)
        section_id: ID секции чанка
        chunk_index: Порядковый номер чанка в секции
        expansion: Количество соседних чанков до и после

    Returns:
        Список соседних чанков [{chunk_id, content, score, page}]
    """
    if section_id is None or chunk_index is None:
        return []

    start_idx = max(0, chunk_index - expansion)
    end_idx = chunk_index + expansion

    rows = await conn.fetch(
        """
        SELECT id, content, page, chunk_index
        FROM rag.document_chunks
        WHERE section_id = $1
          AND chunk_index BETWEEN $2 AND $3
          AND id != $4
        ORDER BY chunk_index
        """,
        section_id,
        start_idx,
        end_idx,
        chunk_id,
    )

    return [
        {
            "chunk_id": row["id"],
            "content": row["content"],
            "score": None,
            "page": row["page"],
        }
        for row in rows
    ]


async def expand_context_batch(
    conn: asyncpg.Connection,
    targets: list[dict],
    expansion: int = 2,
) -> dict[int, list[dict]]:
    """
    Пакетный context expansion для списка результатов.

    Args:
        conn: Подключение к БД
        targets: Список [{chunk_id, section_id, chunk_index}]
        expansion: Количество соседних чанков

    Returns:
        Словарь {chunk_id: [context_chunks]}
    """
    if not targets:
        return {}

    result: dict[int, list[dict]] = {}

    # Группируем по section_id для оптимизации запросов
    by_section: dict[int, list[dict]] = {}
    for t in targets:
        sid = t.get("section_id")
        if sid is not None:
            by_section.setdefault(sid, []).append(t)

    for section_id, items in by_section.items():
        # Находим минимальный и максимальный chunk_index для section
        indices = [t["chunk_index"] for t in items if t.get("chunk_index") is not None]
        if not indices:
            continue

        min_idx = max(0, min(indices) - expansion)
        max_idx = max(indices) + expansion

        rows = await conn.fetch(
            """
            SELECT id, content, page, chunk_index, section_id
            FROM rag.document_chunks
            WHERE section_id = $1
              AND chunk_index BETWEEN $2 AND $3
            ORDER BY chunk_index
            """,
            section_id,
            min_idx,
            max_idx,
        )

        # Маппим chunk_index → row для быстрого поиска
        rows_by_index = {row["chunk_index"]: row for row in rows}

        for t in items:
            target_idx = t.get("chunk_index")
            target_id = t["chunk_id"]
            if target_idx is None:
                result[target_id] = []
                continue

            context = []
            for idx in range(max(0, target_idx - expansion), target_idx + expansion + 1):
                if idx == target_idx:
                    continue
                row = rows_by_index.get(idx)
                if row:
                    context.append({
                        "chunk_id": row["id"],
                        "content": row["content"],
                        "score": None,
                        "page": row["page"],
                    })
            result[target_id] = context

    return result
