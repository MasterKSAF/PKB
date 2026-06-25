#!/usr/bin/env python3
"""
Скрипт для генерации реальных эмбеддингов в seed_data.sql.

Заменяет random()-векторы на настоящие эмбеддинги через Infinity (OpenAI-compatible API).
Требует запущенный сервис Infinity.

Запуск:
    cd rag_search
    python scripts/generate_seed_embeddings.py
    # или с явным URL:
    python scripts/generate_seed_embeddings.py --base-url http://localhost:7997

Результат: обновлённый migrations/seed_data.sql с реальными эмбеддингами.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import httpx

# Добавляем корень проекта в sys.path, чтобы можно было импортировать настройки
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ──────────────────────────────────────────────────────────────────────
# Конфигурация
# ──────────────────────────────────────────────────────────────────────
SEED_FILE = PROJECT_ROOT / "migrations" / "seed_data.sql"
MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"
EMBEDDING_DIM = 1024


def extract_chunk_contents(sql: str) -> list[dict]:
    """
    Извлечь содержимое чанков из INSERT-ов seed_data.sql.

    Парсит блоки VALUES после INSERT INTO rag.document_chunks.
    Возвращает список словарей с id, content и позицией random-выражения.
    """
    chunks = []

    # Находим блок INSERT INTO rag.document_chunks
    insert_match = re.search(
        r"INSERT INTO rag\.document_chunks\s*\([^)]+\)\s*VALUES\s*\n(.+?)(?:\nON CONFLICT|\n--|\Z)",
        sql,
        re.DOTALL,
    )
    if not insert_match:
        print("ERROR: Не найден INSERT INTO rag.document_chunks в seed_data.sql")
        sys.exit(1)

    values_block = insert_match.group(1)

    # Каждый чанк — это строка в скобках, начинающаяся с UUID/числа
    chunk_blocks = []
    depth = 0
    current = []
    for line in values_block.split("\n"):
        for ch in line:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
        current.append(line)
        if depth == 0 and current:
            chunk_blocks.append("\n".join(current))
            current = []
    if current:
        chunk_blocks.append("\n".join(current))

    for block in chunk_blocks:
        block = block.strip().rstrip(",")

        # Извлекаем id чанка (первый аргумент — число или UUID)
        id_match = re.search(r"'?([0-9a-f-]{36})'?|(\d+)", block)
        if not id_match:
            continue
        chunk_id = id_match.group(1) or id_match.group(2)

        # Извлекаем content (текстовое поле)
        content_match = re.search(
            r"'(Для ледового класса[^']*|Ледовые усиления[^']*|Метрическая резьба[^']*|Ледовые классы[^']*|"
            r"Настоящий[^']*|Оборудование[^']*|Движущиеся[^']*|Ограждения[^']*|Сигнальные[^']*|"
            r"Защитные[^']*|Расстояние[^']*|Номинальные[^']*|Для диаметров[^']*|Посадки[^']*|"
            r"Поле допуска[^']*|Степени точности[^']*|Контроль[^']*|Стыковые[^']*|"
            r"Угол разделки[^']*|Угловые[^']*|Длина усиления[^']*|Сварные швы[^']*)'",
            block,
        )
        if not content_match:
            print(f"WARNING: Не удалось извлечь content для чанка {chunk_id}")
            continue

        content = content_match.group(1)

        # Находим позицию random()-выражения для замены
        random_expr_match = re.search(
            r"\(SELECT ARRAY_AGG\(random\(\)::float - 0\.5 ORDER BY g\) FROM generate_series\(1, 1024\) g\)::halfvec\(1024\)",
            block,
        )
        if not random_expr_match:
            print(f"WARNING: Не найдено random-выражение для чанка {chunk_id}")
            continue

        chunks.append(
            {
                "id": chunk_id,
                "content": content,
                "random_start": random_expr_match.start(),
                "random_end": random_expr_match.end(),
                "block_start": block,
            }
        )

    return chunks


def generate_embedding(text: str, base_url: str, api_key: str) -> list[float]:
    """
    Сгенерировать эмбеддинг через Infinity (OpenAI-compatible API).
    """
    print(f"  Генерация эмбеддинга для: {text[:60]}...")

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "input": text,
        "model": MODEL_NAME,
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(f"{base_url}/embeddings", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    embedding = data["data"][0]["embedding"]
    if len(embedding) != EMBEDDING_DIM:
        print(f"  WARNING: Размерность ответа ({len(embedding)}) != ожидаемой ({EMBEDDING_DIM})")

    return list(embedding)


def format_vector(embedding: list[float]) -> str:
    """Форматировать вектор как PostgreSQL-литерал (pgvector)."""
    values = ",".join(f"{v:.6f}" for v in embedding)
    return f"'[{values}]'::halfvec({EMBEDDING_DIM})"


def main():
    parser = argparse.ArgumentParser(description="Сгенерировать эмбеддинги для seed_data.sql через Infinity")
    parser.add_argument("--base-url", default="http://localhost:7997", help="Infinity base URL")
    parser.add_argument("--api-key", default="", help="API key (если требуется)")
    args = parser.parse_args()

    print("=" * 60)
    print("Генерация реальных эмбеддингов для seed_data.sql")
    print(f"Infinity: {args.base_url}")
    print("=" * 60)

    # Проверяем доступность Infinity
    try:
        with httpx.Client(timeout=5) as client:
            resp = client.get(f"{args.base_url}/health", headers={"Content-Type": "application/json"})
            print(f"  Health check: {resp.status_code}")
    except Exception as e:
        print(f"WARNING: Infinity не отвечает ({e}), продолжаем...")

    if not SEED_FILE.exists():
        print(f"ERROR: Файл {SEED_FILE} не найден")
        sys.exit(1)

    # Читаем seed_data.sql
    sql = SEED_FILE.read_text(encoding="utf-8")
    print(f"\nФайл прочитан: {SEED_FILE}")

    # Извлекаем чанки
    chunks = extract_chunk_contents(sql)
    print(f"\nНайдено чанков: {len(chunks)}")
    for ch in chunks:
        print(f"  - {ch['id']}: {ch['content'][:60]}...")

    # Генерируем эмбеддинги
    print("\nГенерация эмбеддингов через Infinity...")
    for i, ch in enumerate(chunks):
        print(f"\n[{i + 1}/{len(chunks)}] Чанк {ch['id'][:8]}...")
        embedding = generate_embedding(ch["content"], args.base_url, args.api_key)
        vector_str = format_vector(embedding)
        ch["vector_str"] = vector_str

    # Заменяем random-выражения на реальные векторы
    print("\nОбновление seed_data.sql...")

    all_random_exprs = list(
        re.finditer(
            r"\(SELECT ARRAY_AGG\(random\(\)::float - 0\.5 ORDER BY g\) FROM generate_series\(1, 1024\) g\)::halfvec\(1024\)",
            sql,
        )
    )

    if len(all_random_exprs) != len(chunks):
        print(
            f"WARNING: Найдено {len(all_random_exprs)} random-выражений, "
            f"но ожидалось {len(chunks)}"
        )

    # Заменяем справа налево, чтобы не сбивались позиции
    for match, ch in zip(reversed(all_random_exprs), reversed(chunks)):
        start = match.start()
        end = match.end()
        sql = sql[:start] + ch["vector_str"] + sql[end:]

    # Записываем обратно
    SEED_FILE.write_text(sql, encoding="utf-8")
    print(f"\n✅ Готово! Файл {SEED_FILE} обновлён.")
    print(f"   Все {len(chunks)} random-векторов заменены на реальные эмбеддинги.")


if __name__ == "__main__":
    main()
