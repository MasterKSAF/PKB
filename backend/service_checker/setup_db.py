#!/usr/bin/env python3
"""
PKB Neuroassistant — Database Setup Script

Создаёт единую БД, схемы, расширения, таблицы и seed-данные
для всех сервисов backend (Registry, Integration, RAG Builder, RAG Search).

Использование:
  python backend/service_checker/setup_db.py                          # интерактивный ввод пароля
  python backend/service_checker/setup_db.py --password postgres      # пароль в аргументе
  python backend/service_checker/setup_db.py --dry-run               # только показать SQL
  python backend/service_checker/setup_db.py --drop-first            # пересоздать БД с нуля
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ──────────────────────────────────────────────────────────────────────
#  Config
# ──────────────────────────────────────────────────────────────────────

DB_NAME = "pkb_neuroassistant"
DB_HOST = "127.0.0.1"
DB_PORT = 5432
DB_SUPERUSER = "postgres"

# Пользователи сервисов (каждый сервис может иметь своего)
SERVICE_USERS = {
    "registry": {"user": "pkb_user", "pass": "pkb_pass", "schemas": ["registry", "public"]},
    "integration": {"user": "pkb_user", "pass": "pkb_pass", "schemas": ["public"]},
    "rag_builder": {"user": "rag_user", "pass": "rag_pass", "schemas": ["rag"]},
    "rag_search": {"user": "rag_user", "pass": "rag_pass", "schemas": ["registry", "rag"]},
    "orchestrator": {"user": "pkb_user", "pass": "pkb_pass", "schemas": []},
}


def get_full_sql_path() -> Optional[Path]:
    """Путь к SQL-файлу registry схемы."""
    p = PROJECT_ROOT / "backend" / "registry_service" / "install" / "0. full_schema.sql"
    return p if p.exists() else None


# ──────────────────────────────────────────────────────────────────────
#  SQL Generators
# ──────────────────────────────────────────────────────────────────────


def sql_create_database(drop_first: bool = False) -> str:
    sql = ""
    if drop_first:
        sql += f"-- Отключаем всех и удаляем БД\n"
        sql += f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        sql += f"WHERE datname = '{DB_NAME}' AND pid <> pg_backend_pid();\n"
        sql += f"DROP DATABASE IF EXISTS {DB_NAME};\n\n"
    sql += f"CREATE DATABASE {DB_NAME}\n"
    sql += f"  WITH ENCODING 'UTF8'\n"
    sql += f"       LC_COLLATE = 'ru_RU.UTF-8'\n"
    sql += f"       LC_CTYPE  = 'ru_RU.UTF-8'\n"
    sql += f"       TEMPLATE template0;\n"
    return sql


def sql_setup_extensions_and_schemas() -> str:
    return textwrap.dedent(f"""\
    \\c {DB_NAME}

    -- Расширения (основные — всегда доступны)
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    CREATE EXTENSION IF NOT EXISTS "ltree";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";

    -- pgvector — может быть не установлен в ОС; пробуем, но не фатально
    DO $$ BEGIN
        CREATE EXTENSION IF NOT EXISTS "vector";
    EXCEPTION WHEN OTHERS THEN
        RAISE WARNING 'pgvector extension not available — RAG services will not work';
    END $$;

    -- Схемы
    CREATE SCHEMA IF NOT EXISTS registry;
    CREATE SCHEMA IF NOT EXISTS rag;

    -- Права
    GRANT ALL ON SCHEMA registry TO PUBLIC;
    GRANT ALL ON SCHEMA rag TO PUBLIC;
    GRANT ALL ON SCHEMA public TO PUBLIC;
    """)


def sql_create_users() -> str:
    lines: List[str] = []
    for svc, info in SERVICE_USERS.items():
        user = info["user"]
        pwd = info["pass"]
        schemas = info["schemas"]
        lines.append(f"")
        lines.append(f"-- Пользователь для {svc}")
        lines.append(f"DO $$")
        lines.append(f"BEGIN")
        lines.append(f"  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '{user}') THEN")
        lines.append(f"    CREATE ROLE {user} LOGIN PASSWORD '{pwd}';")
        lines.append(f"  END IF;")
        lines.append(f"END $$;")
        for sch in schemas:
            lines.append(f"GRANT USAGE ON SCHEMA {sch} TO {user};")
            lines.append(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA {sch} TO {user};")
            lines.append(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA {sch} TO {user};")
            lines.append(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {sch} GRANT ALL ON TABLES TO {user};")
            lines.append(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {sch} GRANT ALL ON SEQUENCES TO {user};")
    return "\n".join(lines)


def sql_create_rag_tables() -> str:
    """Таблица rag.document_chunks для RAG Builder (port 8090) и RAG Search (port 8091)."""
    return textwrap.dedent(f"""\
    -- RAG: создаём только если расширение vector доступно
    DO $$
    DECLARE
        has_vector bool;
    BEGIN
        SELECT count(*) > 0 INTO has_vector
        FROM pg_extension WHERE extname = 'vector';

        IF has_vector THEN
            CREATE TABLE IF NOT EXISTS rag.document_chunks (
                id          SERIAL PRIMARY KEY,
                section_id  INTEGER NOT NULL,
                document_id UUID NOT NULL,
                chunk_index INTEGER NOT NULL,
                content     TEXT NOT NULL,
                embedding   vector(1536),
                strategy    VARCHAR(32) NOT NULL,
                page        INTEGER,
                bbox        JSONB,
                confidence  FLOAT,
                created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
            );

            CREATE INDEX IF NOT EXISTS ix_rag_chunks_doc_id
                ON rag.document_chunks (document_id);

            -- HNSW-индекс для векторного поиска
            CREATE INDEX IF NOT EXISTS idx_chunks_embedding
                ON rag.document_chunks
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64);

            -- GIN-индекс для полнотекстового поиска
            ALTER TABLE rag.document_chunks ADD COLUMN IF NOT EXISTS tsv tsvector;
            CREATE INDEX IF NOT EXISTS idx_chunks_tsv
                ON rag.document_chunks USING gin (tsv);

            -- Триггер авто-обновления tsv (русская конфигурация)
            CREATE OR REPLACE FUNCTION rag.update_tsv() RETURNS trigger AS $func$
            BEGIN
                NEW.tsv := to_tsvector('russian', COALESCE(NEW.content, ''));
                RETURN NEW;
            END;
            $func$ LANGUAGE plpgsql;

            DROP TRIGGER IF EXISTS trg_chunks_tsv ON rag.document_chunks;
            CREATE TRIGGER trg_chunks_tsv
                BEFORE INSERT OR UPDATE OF content ON rag.document_chunks
                FOR EACH ROW EXECUTE FUNCTION rag.update_tsv();

            RAISE NOTICE 'RAG table created successfully';
        ELSE
            RAISE WARNING 'vector extension not found — skipping RAG tables';
        END IF;
    END $$;
    """)


# ──────────────────────────────────────────────────────────────────────
#  Full setup script
# ──────────────────────────────────────────────────────────────────────


def build_full_sql(drop_first: bool = False) -> str:
    """Собирает полный SQL-скрипт инициализации БД."""
    parts: List[str] = [
        "-- ============================================================",
        "-- PKB Neuroassistant — Full Database Setup",
        "-- ============================================================",
        "",
        sql_create_database(drop_first),
        sql_setup_extensions_and_schemas(),
    ]

    # Registry schema
    full_schema = get_full_sql_path()
    if full_schema:
        parts.append(f"-- Registry tables (from {full_schema.name})")
        # psql на Windows требует forward slashes
        path_str = str(full_schema.as_posix())
        parts.append(f"\\i '{path_str}'")
    else:
        parts.append("-- WARNING: registry schema SQL not found, skipping")
        parts.append("-- Expected at: backend/registry_service/install/0. full_schema.sql")

    # RAG tables
    parts.append(sql_create_rag_tables())

    # Users
    parts.append(sql_create_users())

    parts.append("")
    parts.append("-- ============================================================")
    parts.append("-- Setup complete!")
    parts.append("-- ============================================================")

    return "\n\n".join(parts)


# ──────────────────────────────────────────────────────────────────────
#  .env generators
# ──────────────────────────────────────────────────────────────────────


def generate_env_files():
    """Создаёт .env файлы для каждого сервиса (если их нет)."""
    env_files: dict[str, dict[str, str]] = {
        # Registry Service
        PROJECT_ROOT / "backend" / "registry_service" / ".env": {
            "DB_USERNAME": "pkb_user",
            "DB_PASSWORD": "pkb_pass",
            "DB_DATABASE": DB_NAME,
            "DB_HOST": DB_HOST,
            "DB_PORT": str(DB_PORT),
        },
        # Integration Service
        PROJECT_ROOT / "backend" / "integration_service" / ".env": {
            "DB_USERNAME": "pkb_user",
            "DB_PASSWORD": "pkb_pass",
            "DB_DATABASE": DB_NAME,
            "DB_HOST": DB_HOST,
            "DB_PORT": str(DB_PORT),
        },
        # RAG Builder Service
        PROJECT_ROOT / "backend" / "rag_builder" / ".env": {
            "DB_HOST": DB_HOST,
            "DB_PORT": str(DB_PORT),
            "DB_NAME": DB_NAME,
            "DB_USER": "rag_user",
            "DB_PASSWORD": "rag_pass",
            "EMBEDDING_PROVIDER": "mock",
            "JWT_SECRET": "dev-secret-key-change-in-production",
        },
        # RAG Search Service
        PROJECT_ROOT / "backend" / "rag_search_service" / ".env": {
            "POSTGRES_USER": "rag_user",
            "POSTGRES_PASSWORD": "rag_pass",
            "POSTGRES_DB": DB_NAME,
            "POSTGRES_HOST": DB_HOST,
            "POSTGRES_PORT": str(DB_PORT),
            "SERVICE_PORT": "8091",
            "EMBEDDING_API_KEY": "",
        },
        # Orchestrator Service
        PROJECT_ROOT / "backend" / "orchestrator_service" / ".env": {
            "DATABASE_URL": f"postgresql+asyncpg://pkb_user:pkb_pass@{DB_HOST}:{DB_PORT}/{DB_NAME}",
            "REDIS_URL": "redis://localhost:6379/0",
            "AUTH_SERVICE_URL": "http://127.0.0.1:8082",
            "AUTH_SERVICE_MOCK": "True",
            "REGISTRY_SERVICE_URL": "http://127.0.0.1:8084",
            "REGISTRY_SERVICE_MOCK": "True",
            "HOST": "0.0.0.0",
            "PORT": "8000",
            "DEBUG": "True",
        },
    }

    created = 0
    skipped = 0
    for path, params in env_files.items():
        if path.exists():
            skipped += 1
            continue
        lines = []
        for key, value in params.items():
            lines.append(f"{key}={value}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        created += 1
        print(f"  ✓ {path.relative_to(PROJECT_ROOT)}")

    return created, skipped


# ──────────────────────────────────────────────────────────────────────
#  Execution
# ──────────────────────────────────────────────────────────────────────


def find_psql() -> Optional[str]:
    """Ищет psql в PATH и в стандартных местах Windows."""
    # Сначала ищем в PATH
    try:
        result = subprocess.run(["psql", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            return "psql"
    except FileNotFoundError:
        pass

    # Типичные пути на Windows
    candidates = [
        "C:/Program Files/PostgreSQL/15/bin/psql.exe",
        "C:/Program Files/PostgreSQL/16/bin/psql.exe",
        "C:/Program Files/PostgreSQL/17/bin/psql.exe",
        "C:/Program Files (x86)/PostgreSQL/15/bin/psql.exe",
        "C:/Program Files (x86)/PostgreSQL/16/bin/psql.exe",
        "C:/Program Files (x86)/PostgreSQL/17/bin/psql.exe",
    ]
    for p in candidates:
        if Path(p).exists():
            return str(Path(p).resolve())

    return None


def run_psql(sql: str, password: str, dry_run: bool = False) -> bool:
    """Запустить SQL через psql."""
    if dry_run:
        print("\n─── DRY RUN — SQL будет выполнен: ───")
        print(sql[:2000])
        if len(sql) > 2000:
            print(f"... ({len(sql) - 2000} more bytes)")
        print("─────────────────────────────────────\n")
        return True

    psql_path = find_psql()
    if not psql_path:
        print("  ✗ psql не найден. Установите PostgreSQL Client или добавьте в PATH.")
        print("    Попробуйте: set PATH=%PATH%;C:\\Program Files\\PostgreSQL\\15\\bin")
        return False

    # Пишем SQL во временный файл с BOM для Windows
    import tempfile
    tmp = Path(tempfile.gettempdir()) / f"pkb_setup_{os.getpid()}.sql"
    try:
        # UTF-8 with BOM для корректного чтения psql на Windows
        tmp.write_bytes(b"\xef\xbb\xbf" + sql.encode("utf-8"))

        env = os.environ.copy()
        env["PGPASSWORD"] = password
        # Принудительно UTF-8 для вывода
        env["PGCLIENTENCODING"] = "UTF8"

        cmd = [
            str(psql_path),
            "-h", DB_HOST,
            "-p", str(DB_PORT),
            "-U", DB_SUPERUSER,
            "-d", "postgres",
            "-f", str(tmp),
            "-v", "ON_ERROR_STOP=1",
        ]

        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=False,  # bytes, чтобы избежать cp1251 ошибок
        )

        # Декодируем вывод в UTF-8, игнорируя ошибки
        stdout = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
        stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""

        if result.returncode != 0:
            print(f"  ✗ Ошибка psql (код {result.returncode})")
            if stderr.strip():
                for line in stderr.split("\n")[-10:]:
                    if line.strip():
                        print(f"  {line.strip()}")
            elif stdout.strip():
                for line in stdout.split("\n")[-5:]:
                    if line.strip():
                        print(f"  {line.strip()}")
            return False

        print(f"  ✓ psql выполнен успешно")
        for line in stdout.split("\n"):
            if any(kw in line for kw in ["CREATE", "GRANT", "INSERT", "ERROR"]):
                print(f"    {line.strip()}")
        return True

    finally:
        if tmp.exists():
            tmp.unlink()


def main():
    parser = argparse.ArgumentParser(
        description="PKB Neuroassistant — Database Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--password", default="", help="Пароль postgres")
    parser.add_argument("--dry-run", action="store_true", help="Только показать SQL")
    parser.add_argument("--drop-first", action="store_true", help="Пересоздать БД с нуля")
    parser.add_argument("--only-env", action="store_true", help="Только создать .env файлы")
    args = parser.parse_args()

    password = args.password
    if not password and not args.dry_run and not args.only_env:
        import getpass
        password = getpass.getpass(f"  Пароль для postgres@{DB_HOST}:{DB_PORT}: ")

    if args.only_env:
        print("\n  Создание .env файлов...")
        c, s = generate_env_files()
        print(f"  Создано: {c}, пропущено (уже есть): {s}\n")
        return

    print(f"\n  ┌──────────────────────────────────────────────────────────┐")
    print(f"  │  PKB Neuroassistant — Database Setup                     │")
    print(f"  │  Хост: {DB_HOST}:{DB_PORT}                                │")
    print(f"  │  База: {DB_NAME}                                          │")
    print(f"  │  Пользователь: {DB_SUPERUSER}                             │")
    if args.drop_first:
        print(f"  │  ⚠ Режим: пересоздать БД с нуля                        │")
    print(f"  └──────────────────────────────────────────────────────────┘\n")

    # Проверка
    full_schema = get_full_sql_path()
    if not full_schema:
        print("  ⚠ Внимание: не найден registry schema SQL-файл")
        print(f"    Ожидается: backend/registry_service/install/0. full_schema.sql")
        print(f"    Registry таблицы не будут созданы!\n")

    # Генерация SQL
    sql = build_full_sql(drop_first=args.drop_first)

    # Выполнение
    if not run_psql(sql, password, dry_run=args.dry_run):
        sys.exit(1)

    # .env
    print("\n  Создание .env файлов...")
    c, s = generate_env_files()
    print(f"  Создано: {c}, пропущено (уже есть): {s}")

    # Проверка
    if not args.dry_run:
        print("\n  Проверка...")
        try:
            env = os.environ.copy()
            env["PGPASSWORD"] = password
            check = subprocess.run(
                ["psql", "-h", DB_HOST, "-p", str(DB_PORT), "-U", DB_SUPERUSER,
                 "-d", DB_NAME, "-c", "SELECT schemaname, tablename FROM pg_tables WHERE schemaname IN ('registry','rag') ORDER BY schemaname, tablename;"],
                env=env, capture_output=True, text=True,
            )
            if check.returncode == 0:
                print(check.stdout)
            else:
                print(f"  Ошибка проверки: {check.stderr[:300]}")
        except FileNotFoundError:
            pass  # psql not available for check

    print("""\n  Готово! Теперь можно запускать сервисы:\n
    python backend/service_checker/service_checker.py all --with-real
  """)


if __name__ == "__main__":
    main()
