#!/usr/bin/env python3
"""
Скрипт для генерации реальных эмбеддингов в seed_data.sql.

Заменяет random()-векторы на настоящие эмбеддинги от intfloat/multilingual-e5-large.
Использует ту же модель, что и микросервис (через sentence-transformers).

Запуск:
    cd rag_search
    python scripts/generate_seed_embeddings.py

Результат: обновлённый migrations/seed_data.sql с реальными эмбеддингами.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path, чтобы можно было импортировать настройки
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ──────────────────────────────────────────────────────────────────────
# Конфигурация
# ──────────────────────────────────────────────────────────────────────
SEED_FILE = PROJECT_ROOT / "migrations" / "seed_data.sql"
MODEL_NAME = "intfloat/multilingual-e5-large"
EMBEDDING_DIM = 1024

# E5 требует префикса "passage: " для документов
E5_PREFIX = "passage: "


def extract_chunk_contents(sql: str) -> list[dict]:
    """
    Извлечь содержимое чанков из INSERT-ов seed_data.sql.

    Парсит блоки VALUES после INSERT INTO rag.document_chunks.
    Возвращает список словарей с id, content и позицией в файле.
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

    # Каждый чанк — это строка в скобках, начинающаяся с UUID
    # Разделяем на отдельные VALUES-строки
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

        # Извлекаем UUID чанка (первый аргумент)
        id_match = re.search(r"'([0-9a-f-]{36})'", block)
        if not id_match:
            continue
        chunk_id = id_match.group(1)

        # Извлекаем content (четвёртый текстовый аргумент)
        # Ищем content между кавычками — это 4-е строковое поле
        # Проще: ищем строку после section_id (который может быть NULL или UUID)
        content_match = re.search(
            r"'(Для ледового класса[^']*|Ледовые усиления[^']*|Метрическая резьба[^']*|Ледовые классы[^']*)'",
            block,
        )
        if not content_match:
            print(f"WARNING: Не удалось извлечь content для чанка {chunk_id}")
            continue

        content = content_match.group(1)

        # Находим позицию random()-выражения для замены
        random_expr_match = re.search(
            r"\(SELECT ARRAY_AGG\(random\(\)::float - 0\.5 ORDER BY g\) FROM generate_series\(1, 1024\) g\)::vector\(1024\)",
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


def generate_embedding(text: str) -> list[float]:
    """
    Сгенерировать эмбеддинг через sentence-transformers.

    Для E5 используем префикс "passage: ".
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("ERROR: sentence-transformers не установлен. Установите: pip install sentence-transformers")
        sys.exit(1)

    print(f"  Загрузка модели {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    dim = model.get_sentence_embedding_dimension()
    print(f"  Модель загружена, размерность: {dim}")

    if dim != EMBEDDING_DIM:
        print(f"WARNING: Размерность модели ({dim}) не совпадает с ожидаемой ({EMBEDDING_DIM})")

    prefixed = f"{E5_PREFIX}{text}"
    print(f"  Генерация эмбеддинга для: {text[:60]}...")
    embedding = model.encode(prefixed)
    return embedding.tolist()


def format_vector(embedding: list[float]) -> str:
    """Форматировать вектор как PostgreSQL-литерал (pgvector)."""
    # pgvector использует квадратные скобки: '[0.001,-0.002,...]'::vector(1024)
    values = ",".join(f"{v:.6f}" for v in embedding)
    return f"'[{values}]'::vector({EMBEDDING_DIM})"


def main():
    print("=" * 60)
    print("Генерация реальных эмбеддингов для seed_data.sql")
    print("=" * 60)

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
    print("\nГенерация эмбеддингов...")
    for i, ch in enumerate(chunks):
        print(f"\n[{i + 1}/{len(chunks)}] Чанк {ch['id'][:8]}...")
        embedding = generate_embedding(ch["content"])
        vector_str = format_vector(embedding)
        ch["vector_str"] = vector_str

    # Заменяем random-выражения на реальные векторы
    print("\nОбновление seed_data.sql...")

    # Работаем с каждым блоком отдельно
    # Проще: заменяем в исходном SQL каждое random-выражение
    # Для этого находим их позиции в общем файле

    # Находим все random-выражения в файле
    all_random_exprs = list(
        re.finditer(
            r"\(SELECT ARRAY_AGG\(random\(\)::float - 0\.5 ORDER BY g\) FROM generate_series\(1, 1024\) g\)::vector\(1024\)",
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
