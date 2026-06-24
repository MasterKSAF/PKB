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

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# ──────────────────────────────────────────────────────────────────────
#  Config (from env with fallback to hardcoded defaults)
# ──────────────────────────────────────────────────────────────────────

DB_NAME = os.getenv("DB_DATABASE", "pkb_neuro")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "15432"))
DB_SUPERUSER = os.getenv("DB_SUPERUSER", "postgres")

# Пользователи сервисов (каждый сервис может иметь своего)
SERVICE_USERS = {
    "registry": {"user": "pkb_user", "pass": "pkb_pass", "schemas": ["registry", "public"]},
    "integration": {"user": "pkb_user", "pass": "pkb_pass", "schemas": ["public"]},
    "rag_builder": {"user": "rag_user", "pass": "rag_pass", "schemas": ["rag"]},
    "rag_search": {"user": "rag_user", "pass": "rag_pass", "schemas": ["registry", "rag"]},
    "orchestrator": {"user": "pkb_user", "pass": "pkb_pass", "schemas": []},
}





# ──────────────────────────────────────────────────────────────────────
#  SQL Generators
# ──────────────────────────────────────────────────────────────────────


def sql_create_database(drop_first: bool = False) -> str:
    """Создание БД — только если drop_first.
    
    В Docker БД уже создаётся через POSTGRES_DB в docker-compose.
    """
    sql = ""
    if drop_first:
        sql += f"-- Отключаем всех и удаляем БД\n"
        sql += f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        sql += f"WHERE datname = '{DB_NAME}' AND pid <> pg_backend_pid();\n"
        sql += f"DROP DATABASE IF EXISTS {DB_NAME};\n"
        sql += f"CREATE DATABASE {DB_NAME} ENCODING 'UTF8' LC_COLLATE 'en_US.UTF-8' LC_CTYPE 'en_US.UTF-8' TEMPLATE template0;\n"
    return sql


def sql_setup_extensions_and_schemas() -> str:
    """
    SQL для расширений.

    Создаёт только расширения PostgreSQL.
    Схемы и таблицы сервисов — зона ответственности самих сервисов.
    """

    return textwrap.dedent(f"""\
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

    -- Права на public
    GRANT ALL ON SCHEMA public TO PUBLIC;
    """)


def sql_create_users(skip: bool = False) -> str:
    if skip:
        return """-- Пользователи не создаются: в Docker используем 'pkb' (owner БД)"""

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


# sql_create_rag_tables removed — checker не создаёт таблицы сервисов.
# RAG Builder должен сам создавать rag.document_chunks через create_all() при старте.


# ──────────────────────────────────────────────────────────────────────
#  Full setup script
# ──────────────────────────────────────────────────────────────────────


def build_full_sql(drop_first: bool = False, skip_users: bool = False) -> str:
    """Собирает SQL-скрипт инициализации БД.

    Создаёт только базу данных, расширения PostgreSQL и настройки прав.
    Схемы и таблицы сервисов — зона ответственности самих сервисов.
    """

    parts: List[str] = [
        "-- ============================================================",
        "-- PKB Neuroassistant — Database Setup (service_checker)",
        "-- ============================================================",
        "-- Внимание: checker создаёт ТОЛЬКО расширения.",
        "-- Схемы и таблицы сервисов (registry, rag, auth, ...)",
        "-- создаются самими сервисами через create_all() при старте.",
        "",
        sql_setup_extensions_and_schemas(),
    ]

    # CREATE DATABASE только при drop_first (пересоздание)
    if drop_first:
        parts.insert(1, sql_create_database(drop_first))

    # Users (в Docker не создаём — используем 'pkb' owner'а БД)
    parts.append(sql_create_users(skip=skip_users))

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
    env_files: dict[str, dict[str, str]] = {}

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
        print("    Попробуйте: set PATH=%PATH%;C:\Program Files\PostgreSQL\15\bin")
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

        # В Docker-режиме подключаемся напрямую к целевой БД (она уже создана через POSTGRES_DB)
        # В обычном режиме — к postgres (БД может ещё не существовать)
        target_db = DB_NAME if os.environ.get("DOCKER_MODE") else "postgres"
        cmd = [
            str(psql_path),
            "-h", DB_HOST,
            "-p", str(DB_PORT),
            "-U", DB_SUPERUSER,
            "-d", target_db,
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
    parser.add_argument("--password", default="", help="Пароль postgres (по умолчанию: из PGPASSWORD env или 'pkb' в Docker)")
    parser.add_argument("--dry-run", action="store_true", help="Только показать SQL")
    parser.add_argument("--drop-first", action="store_true", help="Пересоздать БД с нуля")
    parser.add_argument("--only-env", action="store_true", help="Только создать .env файлы")
    parser.add_argument("--docker", action="store_true", help="Режим Docker: без создания пользователей, пароль 'pkb'")
    args = parser.parse_args()

    password = args.password
    if args.docker:
        # Docker-режим: пароль pkb, не создаём пользователей
        password = "pkb"
        skip_users = True
        os.environ["DOCKER_MODE"] = "1"
        print("  🐳 Docker-режим: ")
        print(f"    пароль: '{password}', пользователи БД: 'pkb' (owner)")
    elif not password and not args.dry_run and not args.only_env:
        password = os.environ.get("PGPASSWORD", "")
        if not password:
            if DB_HOST == "postgres" or DB_HOST == "127.0.0.1":
                password = "pkb"
                print(f"  Использую пароль по умолчанию: '{password}'")
            else:
                import getpass
                password = getpass.getpass(f"  Пароль для postgres@{DB_HOST}:{DB_PORT}: ")
        skip_users = False
    else:
        skip_users = False

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
    if skip_users:
        print(f"  │  👤 Без создания пользователей (Docker)                 │")
    print(f"  └──────────────────────────────────────────────────────────┘\n")

    # Информация (больше не ищем дамп — схемы создают сервисы)
    print("  ℹ Схемы и таблицы сервисов (registry, rag, auth, ...)")
    print("    создаются самими сервисами через create_all() при старте.")

    # Генерация SQL (только БД + расширения, без схем и таблиц сервисов)
    sql = build_full_sql(drop_first=args.drop_first, skip_users=skip_users)

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
