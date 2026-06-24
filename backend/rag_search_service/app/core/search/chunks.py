"""Хелпер для получения содержимого чанков из БД."""

from __future__ import annotations

import asyncpg


async def fetch_chunk_contents(conn: asyncpg.Connection, chunk_ids: list[int]) -> dict[int, str]:
    """Получить тексты чанков по их ID.

    Args:
        conn: Подключение к БД
        chunk_ids: Список ID чанков

    Returns:
        Словарь {chunk_id: content}
    """
    if not chunk_ids:
        return {}
    rows = await conn.fetch(
        "SELECT id, content FROM rag.document_chunks WHERE id = ANY($1::bigint[])",
        chunk_ids,
    )
    return {row["id"]: row["content"] for row in rows}
