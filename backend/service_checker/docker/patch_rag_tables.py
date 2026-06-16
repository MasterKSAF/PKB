"""
PKB Neuroassistant — RAG Builder patch: создание таблиц и alembic_version.

Что делает:
1. Создаёт схему rag, если нет
2. Создаёт rag.document_chunks с BIGINT document_id и VECTOR(1536)
3. Если таблица существует с UUID document_id — конвертирует в BIGINT
4. Если embedding имеет неверный размер — пересоздаёт как vector(1536)
5. Проставляет alembic_version = 20260616_0003

Запуск:
  python docker/patch_rag_tables.py
  python -m service_checker docker --action patch-rag    # через checker

Зависимости: psycopg2 или asyncpg (через sqlalchemy)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Добавляем backend/ в sys.path
_backend = Path(__file__).resolve().parent.parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from service_checker.core.utils import log_ok, log_warn, log_err, log_info, log_step


# SQL для расширений БД (устанавливаются после DROP DATABASE / CREATE DATABASE)
# ⚠️ asyncpg не поддерживает множественные команды в одном execute — каждый отдельно
SQL_EXTENSIONS: list[str] = [
    'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"',
    'CREATE EXTENSION IF NOT EXISTS "pgcrypto"',
    'CREATE EXTENSION IF NOT EXISTS "ltree"',
    'CREATE EXTENSION IF NOT EXISTS "pg_trgm"',
    'CREATE EXTENSION IF NOT EXISTS vector',
]
SQL_CREATE_SCHEMA = "CREATE SCHEMA IF NOT EXISTS rag"

SQL_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS rag.document_chunks (
    id BIGSERIAL PRIMARY KEY,
    section_id BIGINT NOT NULL,
    document_id BIGINT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    tsv TSVECTOR,
    strategy VARCHAR(32) NOT NULL,
    page INTEGER,
    bbox JSONB,
    confidence DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""

SQL_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_rag_doc_chunks_doc_id ON rag.document_chunks(document_id)",
    "CREATE INDEX IF NOT EXISTS ix_rag_doc_chunks_tsv ON rag.document_chunks USING gin(tsv)",
    "CREATE INDEX IF NOT EXISTS ix_rag_doc_chunks_embedding_ivfflat ON rag.document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)",
]

SQL_SET_ALEMBIC_VERSION = """
INSERT INTO public.alembic_version (version_num)
VALUES ('20260616_0003')
ON CONFLICT (version_num) DO NOTHING
"""


def get_db_url() -> str:
    """Получить DATABASE_URL из окружения или собрать из переменных."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    host = os.environ.get("DB_HOST", "127.0.0.1")
    port = os.environ.get("DB_PORT", "5432")
    user = os.environ.get("DB_USERNAME", os.environ.get("DB_USER", "pkb"))
    password = os.environ.get("DB_PASSWORD", "pkb")
    db = os.environ.get("DB_DATABASE", os.environ.get("DB_NAME", "pkb_neuro"))
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


async def patch_rag_tables(db_url: str | None = None) -> bool:
    """Создать таблицы RAG, если их нет. Вернуть True, если были изменения."""
    import asyncio
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    if db_url is None:
        db_url = get_db_url()

    engine = create_async_engine(db_url)
    changed = False

    try:
        async with engine.connect() as conn:
            # 1. Проверяем, существует ли таблица
            exists = await conn.scalar(
                text("SELECT to_regclass('rag.document_chunks')::text")
            )
            if exists:
                log_ok("rag.document_chunks уже существует")
                # Проверяем тип document_id — должен быть BIGINT
                col_type = await conn.scalar(text(
                    "SELECT data_type FROM information_schema.columns "
                    "WHERE table_schema='rag' AND table_name='document_chunks' "
                    "AND column_name='document_id'"
                ))
                if col_type and col_type != 'bigint':
                    log_step(f"Конвертация document_id {col_type} → BIGINT...")
                    # Дропаем FK если есть, затем меняем тип (данные удаляем — они всё равно тестовые)
                    await conn.execute(text(
                        "ALTER TABLE rag.document_chunks "
                        "DROP CONSTRAINT IF EXISTS fk_rag_document_chunks_document_id"
                    ))
                    await conn.execute(text("DELETE FROM rag.document_chunks"))
                    await conn.execute(text(
                        "ALTER TABLE rag.document_chunks "
                        "ALTER COLUMN document_id TYPE BIGINT USING 0"
                    ))
                    log_ok("document_id изменён на BIGINT")
                    changed = True
                # Проверяем размерность вектора
                vec_type = await conn.scalar(text(
                    "SELECT format_type(a.atttypid, a.atttypmod) "
                    "FROM pg_attribute a "
                    "WHERE a.attrelid = 'rag.document_chunks'::regclass "
                    "AND a.attname = 'embedding' AND NOT a.attisdropped"
                ))
                if vec_type and vec_type != 'vector(1536)':
                    log_step(f"Пересоздание embedding {vec_type} → vector(1536)...")
                    await conn.execute(text(
                        "DROP INDEX IF EXISTS rag.ix_rag_doc_chunks_embedding_ivfflat"
                    ))
                    await conn.execute(text(
                        "ALTER TABLE rag.document_chunks DROP COLUMN embedding"
                    ))
                    await conn.execute(text(
                        "ALTER TABLE rag.document_chunks ADD COLUMN embedding vector(1536)"
                    ))
                    await conn.execute(text(
                        "CREATE INDEX IF NOT EXISTS ix_rag_doc_chunks_embedding_ivfflat "
                        "ON rag.document_chunks USING ivfflat (embedding vector_cosine_ops) "
                        "WITH (lists = 100)"
                    ))
                    log_ok("embedding пересоздан как vector(1536)")
                    changed = True
            else:
                log_step("Создание схемы rag...")
                await conn.execute(text(SQL_CREATE_SCHEMA))
                log_step("Установка расширений БД...")
                for ext_sql in SQL_EXTENSIONS:
                    try:
                        await conn.execute(text(ext_sql))
                    except Exception as e:
                        log_warn(f"extension не установился: {e}")
                log_ok("Расширения БД проверены")
                log_step("Создание таблицы rag.document_chunks (BIGINT)...")
                try:
                    await conn.execute(text(SQL_CREATE_TABLE))
                except Exception as e:
                    if "type \"vector\" does not exist" in str(e):
                        log_err("Расширение vector ещё не доступно. Ждём и пробуем ещё раз...")
                        await conn.commit()
                        log_step("Повторная попытка: установка расширений...")
                        for ext_sql in SQL_EXTENSIONS:
                            try:
                                await conn.execute(text(ext_sql))
                            except Exception:
                                pass
                        await conn.execute(text(SQL_CREATE_TABLE))
                    else:
                        raise
                for idx_sql in SQL_CREATE_INDEXES:
                    await conn.execute(text(idx_sql))
                log_ok("Таблица rag.document_chunks создана")
                changed = True

            # 2. Проверяем alembic_version
            av_exists = await conn.scalar(
                text("SELECT to_regclass('public.alembic_version')::text")
            )
            if av_exists:
                ver = await conn.scalar(
                    text("SELECT version_num FROM public.alembic_version LIMIT 1")
                )
                log_info(f"alembic_version: {ver}")
                # Если стоит старая ревизия — обновляем до актуальной
                if ver and ver < '20260616_0003':
                    log_step(f"Обновление alembic_version {ver} → 20260616_0003...")
                    await conn.execute(text(
                        "UPDATE public.alembic_version SET version_num = '20260616_0003'"
                    ))
                    log_ok("alembic_version обновлён до 20260616_0003")
                    changed = True
            else:
                log_step("Создание public.alembic_version...")
                await conn.execute(text(
                    "CREATE TABLE IF NOT EXISTS public.alembic_version ("
                    "version_num VARCHAR(32) NOT NULL, "
                    "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
                ))
                await conn.execute(text(SQL_SET_ALEMBIC_VERSION))
                log_ok("alembic_version = 20260616_0003")
                changed = True

            await conn.commit()
    except Exception as e:
        log_err(f"Ошибка при патче RAG таблиц: {e}")
        return False
    finally:
        await engine.dispose()

    return True


if __name__ == "__main__":
    import asyncio

    log_step("Patching RAG Builder tables...")
    ok = asyncio.run(patch_rag_tables())
    if ok:
        log_ok("RAG таблицы в порядке")
    else:
        log_err("Что-то пошло не так")
        sys.exit(1)
