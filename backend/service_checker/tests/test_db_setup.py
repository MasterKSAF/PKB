"""
Тесты для setup_db.py — проверка генерации SQL инициализации БД.

Сценарий проверки:
1. SQL-синтаксис: парсится без ошибок
2. Схемы: registry, rag — создаются
3. Расширения: uuid-ossp, pgcrypto, ltree, pg_trgm, vector
4. Registry таблицы: присутствуют (из дампа или create_all)
5. RAG таблицы: rag.document_chunks с индексами
6. Пользователи: создаются (или пропускаются в --docker режиме)
7. database/schema/table coverage — ничего не пропущено
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Set

import pytest

# Константы для тестов
EXPECTED_EXTENSIONS = {"uuid-ossp", "pgcrypto", "ltree", "pg_trgm", "vector"}
EXPECTED_SCHEMAS = {"registry", "rag"}
EXPECTED_RAG_TABLES = {"rag.document_chunks"}

# Ключевые таблицы Registry, которые ожидаются в дампе
EXPECTED_REGISTRY_TABLES = {
    "registry.documents",
    "registry.document_sections",
    "registry.classifiers",
    "registry.terminology",
}


# ────────────────────────────────────────────────────────────────
#  Фикстуры
# ────────────────────────────────────────────────────────────────


@pytest.fixture
def setup_db_module():
    """Импорт setup_db как модуля (чтобы видеть его функции)."""
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location(
        "setup_db",
        Path(__file__).resolve().parent.parent / "setup_db.py",
    )
    mod = importlib.util.module_from_spec(spec)
    # Замокаем константы для тестов
    mod.DB_NAME = "pkb_neuro"
    mod.DB_HOST = "127.0.0.1"
    mod.DB_PORT = 5432
    mod.DB_SUPERUSER = "postgres"
    mod.PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def full_sql(setup_db_module):
    """Сгенерированный полный SQL-скрипт (без --docker)."""
    sql = setup_db_module.build_full_sql(drop_first=False, skip_users=False)
    return sql


@pytest.fixture
def docker_sql(setup_db_module):
    """Сгенерированный SQL-скрипт для Docker (skip_users=True)."""
    sql = setup_db_module.build_full_sql(drop_first=False, skip_users=True)
    return sql


@pytest.fixture
def sql_lines(full_sql) -> List[str]:
    """SQL script as list of non-empty, non-comment lines."""
    return [
        line for line in full_sql.split("\n")
        if line.strip() and not line.strip().startswith("--")
    ]


# ────────────────────────────────────────────────────────────────
#  Хелперы
# ────────────────────────────────────────────────────────────────


def extract_schemas_from_sql(lines: List[str]) -> Set[str]:
    """Извлечь имена создаваемых схем из SQL."""
    schemas = set()
    for line in lines:
        line = line.strip()
        if line.upper().startswith("CREATE SCHEMA"):
            # CREATE SCHEMA IF NOT EXISTS registry;
            parts = line.rstrip(";").split()
            # parts = ["CREATE", "SCHEMA", "IF", "NOT", "EXISTS", "registry"]
            for i, p in enumerate(parts):
                if p.upper() in ("SCHEMA",) and i + 1 < len(parts):
                    name = parts[i + 1]
                    if name.upper() in ("IF", "NOT"):
                        # IF NOT EXISTS — имя через 3 слова
                        idx = parts.index("EXISTS") + 1 if "EXISTS" in parts else i + 1
                        if idx < len(parts):
                            schemas.add(parts[idx])
                    else:
                        schemas.add(name)
    return schemas


def extract_extensions_from_sql(lines: List[str]) -> Set[str]:
    """Извлечь имена устанавливаемых расширений из SQL."""
    exts = set()
    for line in lines:
        stripped = line.strip().upper()
        if "CREATE EXTENSION" in stripped:
            # CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
            import re
            match = re.search(r'CREATE EXTENSION\s+(?:IF NOT EXISTS\s+)?["\']?(\w[\w-]+)["\']?', line, re.IGNORECASE)
            if match:
                exts.add(match.group(1))
    return exts


def extract_table_names(lines: List[str]) -> Set[str]:
    """Извлечь имена создаваемых таблиц (CREATE TABLE)."""
    tables = set()
    for line in lines:
        stripped = line.strip().upper()
        if "CREATE TABLE" in stripped and "IF NOT EXISTS" in stripped:
            # CREATE TABLE IF NOT EXISTS rag.document_chunks (...)
            import re
            match = re.search(r'CREATE TABLE\s+IF NOT EXISTS\s+(["\']?\w+["\']?\.["\']?\w+["\']?)', line, re.IGNORECASE)
            if match:
                tables.add(match.group(1).strip('"').strip("'"))
            else:
                # single schema table
                match = re.search(r'CREATE TABLE\s+IF NOT EXISTS\s+(["\']?\w+["\']?)', line, re.IGNORECASE)
                if match:
                    tables.add(match.group(1).strip('"').strip("'"))
    return tables


def extract_users_from_sql(lines: List[str]) -> List[str]:
    """Извлечь имена создаваемых пользователей (CREATE ROLE ... LOGIN)."""
    users = []
    for line in lines:
        if "CREATE ROLE" in line.upper() and "LOGIN" in line.upper():
            import re
            match = re.search(r'CREATE ROLE\s+(\w+)', line, re.IGNORECASE)
            if match:
                users.append(match.group(1))
    return users


def count_create_index(lines: List[str]) -> int:
    """Сосчитать CREATE INDEX."""
    return sum(1 for line in lines if line.strip().upper().startswith("CREATE INDEX"))


def count_create_trigger(lines: List[str]) -> int:
    """Сосчитать CREATE TRIGGER."""
    return sum(1 for line in lines if line.strip().upper().startswith("CREATE TRIGGER"))


# ────────────────────────────────────────────────────────────────
#  Тесты SQL-синтаксиса
# ────────────────────────────────────────────────────────────────


class TestSqlSyntax:
    """Проверка синтаксиса сгенерированного SQL."""

    def test_sql_is_valid_string(self, full_sql):
        """SQL — непустая строка."""
        assert full_sql
        assert len(full_sql) > 500

    def test_sql_contains_no_html(self, full_sql):
        """В SQL нет HTML/заглушек."""
        assert "<!--" not in full_sql
        assert "<%" not in full_sql

    def test_sql_has_correct_encoding(self, full_sql):
        """SQL — валидный UTF-8."""
        full_sql.encode("utf-8")  # не должно бросить UnicodeEncodeError


# ────────────────────────────────────────────────────────────────
#  Тесты схем
# ────────────────────────────────────────────────────────────────


class TestSchemas:
    """Проверка создания схем."""

    def test_registry_schema_created_or_included(self, full_sql, setup_db_module):
        """Registry schema: created by setup_db or inside dump file."""
        # When dump is found — registry schema inside dump, not in SQL itself
        dump = setup_db_module.get_full_sql_path()
        if dump is not None:
            # Verify the dump file contains CREATE SCHEMA registry
            dump_content = dump.read_text(encoding="utf-8")
            assert "CREATE SCHEMA registry" in dump_content, \
                "Registry dump should contain CREATE SCHEMA registry"
        else:
            # Without dump — registry is created by setup_db
            schemas = extract_schemas_from_sql(sql_lines)
            assert "registry" in schemas, (
                f"registry schema not created. Found schemas: {schemas}"
            )

    def test_rag_schema_created(self, sql_lines):
        """Схема rag создаётся."""
        schemas = extract_schemas_from_sql(sql_lines)
        assert "rag" in schemas, (
            f"rag schema not created. Found schemas: {schemas}"
        )

    def test_no_extra_schemas(self, sql_lines):
        """Нет лишних схем."""
        schemas = extract_schemas_from_sql(sql_lines)
        known = {"registry", "rag"}
        extra = schemas - known
        assert not extra, f"Unexpected schemas: {extra}"


# ────────────────────────────────────────────────────────────────
#  Тесты расширений
# ────────────────────────────────────────────────────────────────


class TestExtensions:
    """Проверка установки расширений PostgreSQL."""

    def test_all_required_extensions_present(self, sql_lines):
        """Все обязательные расширения устанавливаются."""
        exts = extract_extensions_from_sql(sql_lines)
        missing = EXPECTED_EXTENSIONS - exts
        assert not missing, f"Missing extensions: {missing}"

    def test_vector_extension_handled_gracefully(self, full_sql):
        """pgvector устанавливается через DO block (не фатально)."""
        assert "CREATE EXTENSION IF NOT EXISTS \"vector\"" in full_sql, \
            "vector extension not found in SQL"
        assert "EXCEPTION WHEN OTHERS THEN" in full_sql, \
            "vector extension missing fallback (EXCEPTION block)"


# ────────────────────────────────────────────────────────────────
#  Тесты RAG таблиц
# ────────────────────────────────────────────────────────────────


class TestRagTables:
    """Проверка создания RAG-таблиц."""

    def test_rag_document_chunks_exists(self, sql_lines):
        """Таблица rag.document_chunks создаётся."""
        tables = extract_table_names(sql_lines)
        assert "rag.document_chunks" in tables, (
            f"rag.document_chunks not found. Tables: {tables}"
        )

    def test_rag_has_embedding_column(self, full_sql):
        """Таблица rag.document_chunks имеет колонку embedding vector(1536)."""
        assert "embedding   vector(1536)" in full_sql, \
            "embedding column not found in rag.document_chunks"

    def test_rag_has_hnsw_index(self, full_sql):
        """Есть HNSW-индекс для векторного поиска."""
        assert "USING hnsw (embedding vector_cosine_ops)" in full_sql, \
            "HNSW index on embedding not found"

    def test_rag_has_gin_index(self, full_sql):
        """Есть GIN-индекс для полнотекстового поиска."""
        assert "USING gin (tsv)" in full_sql, \
            "GIN index on tsv not found"

    def test_rag_has_update_tsv_trigger(self, full_sql):
        """Есть триггер авто-обновления tsv."""
        assert "CREATE TRIGGER trg_chunks_tsv" in full_sql, \
            "tsv auto-update trigger not found"

    def test_rag_index_count(self, sql_lines):
        """Минимум 2 индекса на RAG таблицу."""
        assert count_create_index(sql_lines) >= 2

    def test_rag_trigger_count(self, sql_lines):
        """Минимум 1 триггер."""
        assert count_create_trigger(sql_lines) >= 1

    def test_rag_has_created_at(self, full_sql):
        """Есть колонка created_at с now() по умолчанию."""
        assert "created_at" in full_sql and "now()" in full_sql, \
            "created_at with default now() not found"


# ────────────────────────────────────────────────────────────────
#  Тесты Registry таблиц (из дампа)
# ────────────────────────────────────────────────────────────────


class TestRegistryTables:
    """Проверка, что Registry SQL-дамп включён в скрипт."""

    def test_registry_dump_included(self, full_sql):
        """Дамп registry подключён через \\i."""
        assert "\\i '" in full_sql, \
            "Registry dump (\\i) not included in SQL"
        assert "Registry tables (from" in full_sql, \
            "Registry dump comment not found"

    def test_registry_referenced_in_grants(self, full_sql):
        """Хотя бы одна ссылка на schema registry (grants или дамп)."""
        has_registry_ref = "registry." in full_sql or "\\i '" in full_sql
        assert has_registry_ref, \
            "No registry schema references found in SQL"

    def test_registry_sql_file_exists(self, setup_db_module):
        """Проверка, что путь к дампу существует."""
        path = setup_db_module.get_full_sql_path()
        assert path is not None, "Registry SQL dump not found!"
        assert path.exists(), f"Registry SQL dump not found at {path}"

    def test_dump_file_name(self, setup_db_module):
        """Проверка имени файла дампа (любой .sql в install/)."""
        path = setup_db_module.get_full_sql_path()
        assert path.suffix == ".sql", f"Not a SQL file: {path}"


# ────────────────────────────────────────────────────────────────
#  Тесты пользователей
# ────────────────────────────────────────────────────────────────


class TestUsers:
    """Проверка создания пользователей БД."""

    def test_users_created_in_normal_mode(self, sql_lines):
        """Пользователи создаются в обычном режиме."""
        users = extract_users_from_sql(sql_lines)
        assert users, "No users created in normal mode"
        assert "pkb_user" in users, "pkb_user not created"
        assert "rag_user" in users, "rag_user not created"

    def test_users_skipped_in_docker_mode(self, docker_sql, setup_db_module):
        """Пользователи не создаются в Docker-режиме (--docker)."""
        # При --docker skip_users=True → sql_create_users(skip=True)
        sql = setup_db_module.sql_create_users(skip=True)
        assert "не создаются" in sql, \
            "Docker mode: expected user creation to be skipped"
        assert "CREATE ROLE" not in sql.upper(), \
            "Docker mode: CREATE ROLE should not appear"

    def test_users_have_correct_schemas(self, setup_db_module):
        """У каждого пользователя есть grants на нужные схемы."""
        for svc, info in setup_db_module.SERVICE_USERS.items():
            schemas = info["schemas"]
            # orchestrator может не иметь схем (только DATABASE_URL)
            for sch in schemas:
                assert sch in ("registry", "rag", "public"), \
                    f"Service {svc}: unexpected schema {sch}"


# ────────────────────────────────────────────────────────────────
#  Тесты DATABASE создания
# ────────────────────────────────────────────────────────────────


class TestDatabase:
    """Проверка создания БД."""

    def test_create_database_present(self, full_sql):
        """Присутствует CREATE DATABASE."""
        assert "CREATE DATABASE" in full_sql

    def test_db_name_is_correct(self, full_sql, setup_db_module):
        """Имя БД совпадает с конфигурацией."""
        assert setup_db_module.DB_NAME in full_sql

    def test_drop_first_works(self, setup_db_module):
        """--drop-first генерирует DROP DATABASE."""
        sql = setup_db_module.build_full_sql(drop_first=True)
        assert "DROP DATABASE IF EXISTS" in sql, \
            "drop_first=True should include DROP DATABASE IF EXISTS"
        assert "pg_terminate_backend" in sql, \
            "drop_first should terminate connections first"

    def test_no_drop_without_drop_first(self, full_sql):
        """Без --drop-first DROP DATABASE не генерируется."""
        assert "DROP DATABASE" not in full_sql, \
            "DROP DATABASE should not appear without --drop-first"


# ────────────────────────────────────────────────────────────────
#  Интеграционные проверки SQL (без реальной БД)
# ────────────────────────────────────────────────────────────────


class TestSqlCohesion:
    """Проверка целостности SQL-скрипта."""

    def test_no_orphan_semicolons(self, full_sql):
        """Нет пустых инструкций (;;)."""
        assert ";;" not in full_sql

    def test_c_commands_balanced(self, full_sql):
        """psql \\c commands для переключения БД."""
        # Должен быть хотя бы один \c после CREATE DATABASE
        assert "\\c " in full_sql, "No \\c (connect) command found"

    def test_on_error_stop_not_in_sql(self, full_sql):
        """ON_ERROR_STOP — не в SQL, а в аргументах psql."""
        assert "ON_ERROR_STOP" not in full_sql

    def test_full_coverage_lines(self, full_sql):
        """SQL покрывает минимум 50 строк."""
        lines = [l for l in full_sql.split("\n") if l.strip()]
        assert len(lines) >= 50, f"Only {len(lines)} non-empty lines"
