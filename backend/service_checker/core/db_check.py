"""
PKB Neuroassistant — Database Health Check.

⚠️ ВНИМАНИЕ: Read-only модуль.
Этот модуль ТОЛЬКО проверяет состояние БД через SELECT-запросы.
НИКАКИХ изменений БД (CREATE, ALTER, INSERT, DROP) он не производит.
Создание таблиц — зона ответственности самих сервисов (create_all в startup).

Проверяет:
- База данных pkb_neuro существует
- Расширения (uuid-ossp, pgcrypto, ltree, pg_trgm, vector) установлены
- Схемы (public, registry, rag) созданы
- Таблицы Registry и RAG существуют
- RAG индексы (HNSW, GIN) и триггер tsv созданы
- Какой сервис создаёт таблицы при старте (create_all)

Запуск:
    python service_checker.py docker --action db-check
    python service_checker.py docker --action full-report  # включено в отчёт
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple

# ────────────────────────────────────────────────────────────────
#  Константы
# ────────────────────────────────────────────────────────────────

DB_NAME = "pkb_neuro"
DB_USER = "pkb"
POSTGRES_CONTAINER = "pkb-postgres"

EXPECTED_EXTENSIONS: Set[str] = {
    "uuid-ossp",
    "pgcrypto",
    "ltree",
    "pg_trgm",
    "vector",
}

EXPECTED_SCHEMAS: Set[str] = {
    "public",
    "registry",
    "rag",
    "pipeline",  # DB-23: schema для pipeline.tasks / pipeline.task_steps
    "auth",      # DB-29: schema для auth.users
}

EXPECTED_REGISTRY_TABLES: Set[str] = {
    "registry.documents",
    "registry.document_sections",
    "registry.classifiers",
    "registry.terminology",
    "registry.document_history",
    "registry.document_references",
    "registry.document_versions",
    "registry.rs_enums",
    "registry.drafts",                # DB-19: черновики в Registry
    "registry.classifier_registry",   # DB-20: классификаторы (mks|oks|okstu|udk)
    "registry.categories",            # DB-21: категории
    "registry.document_categories",   # DB-21: M:N документы-категории
}

EXPECTED_PIPELINE_TABLES: Set[str] = {
    "pipeline.tasks",
    "pipeline.task_steps",
    "pipeline.draft_notifications",  # OR-6: уведомления pipeline
}

EXPECTED_RAG_TABLES: Set[str] = {
    "rag.document_chunks",
}

# Таблицы схемы auth (DB-29)
EXPECTED_AUTH_TABLES: Set[str] = {
    "auth.users",
}

# Ожидаемые UNIQUE-индексы (DB-4, P1F-1)
EXPECTED_UNIQUE_INDEXES: Dict[str, str] = {
    "registry.documents_doc_code_era_key":
        "CREATE UNIQUE INDEX ON registry.documents (doc_code, era)",
    "registry.documents_title_hash_sha256_key":
        "CREATE UNIQUE INDEX ON registry.documents (title_hash_sha256)",
    "registry.document_versions_doc_id_path_key":
        "CREATE UNIQUE INDEX ON registry.document_versions (document_id, path)",
    "registry.document_versions_doc_id_version_key":
        "CREATE UNIQUE INDEX ON registry.document_versions (document_id, version_number)",
    "registry.documents_title_key_key":
        "CREATE UNIQUE INDEX ON registry.documents (title_key)",  # DB-29
}

# ВНИМАНИЕ: rag.document_chunks_section_chunk_key был намеренно удалён
# из RAG Builder (миграция 20260623_0001) — UNIQUE(section_id, chunk_index)
# ломал индексацию нескольких документов. Не добавлять обратно.

# Список сервисов — кто должен создавать таблицы при старте
SERVICE_STARTUP_CHECKS: Dict[str, dict] = {
    "auth_service": {
        "path": "auth_service/app/main.py",
        "schema": "public",
        "reason": "Auth: users, roles, audit_log",
        "markers": [".create_all", "init_db"],
    },
    "query_service": {
        "path": "query_service/app/main.py",
        "schema": "public",
        "reason": "Query: sessions, messages",
        "markers": [".create_all", "init_db"],
    },
    "orchestrator_service": {
        "path": "orchestrator_service/app/main.py",
        "schema": "public",
        "reason": "Orchestrator: pipeline, steps",
        "markers": [".create_all"],
    },
    "integration_service": {
        "path": "integration_service/api/v1/models.py",
        "schema": "public",
        "reason": "Integration: documents, tasks",
        "markers": [".create_all"],
    },
    "registry_service": {
        "path": "registry_service/main.py",
        "schema": "registry",
        "reason": "Registry: ~18 таблиц (documents, classifiers, terminology)",
        "markers": [".create_all"],
    },
    "rag_builder_service": {
        "path": "rag_builder_service/src/rag_builder/api/app.py",
        "schema": "rag",
        "reason": "RAG Builder: document_chunks (HNSW/GIN индексы)",
        "markers": [".create_all", "validate_startup_migrations", "upgrade_to_head"],
    },
    "rag_search_service": {
        "path": "rag_search_service/app/main.py",
        "schema": "rag",
        "reason": "RAG Search: consumer, читает document_chunks",
        "markers": [],  # consumer — НЕ должен создавать
        "must_not_have_create_all": True,
    },
}

# ────────────────────────────────────────────────────────────────
#  Data model
# ────────────────────────────────────────────────────────────────


@dataclass
class DbCheckResult:
    """Результат проверки состояния БД."""

    db_exists: bool = False
    db_accessible: bool = False

    extensions_installed: Set[str] = field(default_factory=set)
    extensions_missing: Set[str] = field(default_factory=set)

    schemas_found: Set[str] = field(default_factory=set)
    schemas_missing: Set[str] = field(default_factory=set)

    registry_tables: List[str] = field(default_factory=list)
    registry_missing: Set[str] = field(default_factory=set)

    pipeline_tables: List[str] = field(default_factory=list)
    pipeline_missing: Set[str] = field(default_factory=set)

    rag_tables: List[str] = field(default_factory=list)
    rag_has_embedding: bool = False
    rag_has_hnsw: bool = False
    rag_has_gin: bool = False
    rag_has_created_at: bool = False

    auth_tables: List[str] = field(default_factory=list)
    auth_missing: Set[str] = field(default_factory=set)

    # UNIQUE-индексы (DB-4, P1F-1)
    unique_indexes_found: Set[str] = field(default_factory=set)
    unique_indexes_missing: Set[str] = field(default_factory=set)

    can_select_registry: bool = False
    error: str | None = None

    # Статическая проверка: какой сервис создаёт таблицы при старте
    services_create_all: Dict[str, bool] = field(default_factory=dict)

    @property
    def extensions_ok(self) -> bool:
        return len(self.extensions_missing) == 0

    @property
    def schemas_ok(self) -> bool:
        return len(self.schemas_missing) == 0

    @property
    def registry_ok(self) -> bool:
        return len(self.registry_missing) == 0

    @property
    def rag_ok(self) -> bool:
        return (self.rag_has_embedding and
                self.rag_has_hnsw and
                self.rag_has_gin)

    @property
    def pipeline_ok(self) -> bool:
        return len(self.pipeline_missing) == 0

    @property
    def auth_ok(self) -> bool:
        return len(self.auth_missing) == 0

    @property
    def unique_indexes_ok(self) -> bool:
        return len(self.unique_indexes_missing) == 0

    @property
    def healthy(self) -> bool:
        """БД полностью инициализирована."""
        return (self.db_exists and self.db_accessible
                and self.extensions_ok
                and self.schemas_ok
                and self.registry_ok
                and self.pipeline_ok
                and self.auth_ok
                and self.unique_indexes_ok
                and self.rag_ok)

    @property
    def summary_icon(self) -> str:
        return "✅" if self.healthy else "❌"


# ────────────────────────────────────────────────────────────────
#  Docker helpers
# ────────────────────────────────────────────────────────────────


def _docker_exec(sql: str, db: str = DB_NAME) -> Tuple[int, str, str]:
    """Выполнить SQL через docker exec в контейнере PostgreSQL."""
    result = subprocess.run(
        [
            "docker", "exec", "-i", POSTGRES_CONTAINER,
            "psql", "-U", DB_USER, "-d", db,
            "-t",       # tuples only (no headers)
            "-A",       # unaligned output
            "-c", sql,
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _query_single_column(sql: str, db: str = DB_NAME) -> List[str]:
    """Выполнить SQL и вернуть список значений первой колонки."""
    rc, stdout, stderr = _docker_exec(sql, db)
    if rc != 0:
        return []
    return [line.strip() for line in stdout.split("\n") if line.strip()]


def check_docker_available() -> bool:
    """Проверить, доступен ли Docker и запущен ли PostgreSQL."""
    try:
        rc, stdout, _ = _docker_exec("SELECT 1")
        return rc == 0 and "1" in stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


# ────────────────────────────────────────────────────────────────
#  Main check
# ────────────────────────────────────────────────────────────────


def run_db_check() -> DbCheckResult:
    """Выполнить полную проверку состояния БД в Docker."""
    result = DbCheckResult()

    if not check_docker_available():
        result.error = "PostgreSQL в Docker недоступен"
        return result

    # ── 1. База данных ──────────────────────────────────────────
    dbs = _query_single_column(
        "SELECT datname FROM pg_database WHERE datname = 'pkb_neuro'",
        db="postgres",
    )
    result.db_exists = "pkb_neuro" in dbs

    rc, stdout, _ = _docker_exec("SELECT current_database()")
    result.db_accessible = rc == 0 and DB_NAME in stdout

    # ── 2. Расширения ───────────────────────────────────────────
    installed = set(_query_single_column(
        "SELECT extname FROM pg_extension ORDER BY extname"
    ))
    result.extensions_installed = installed
    result.extensions_missing = EXPECTED_EXTENSIONS - installed

    # ── 3. Схемы ────────────────────────────────────────────────
    schemas = set(_query_single_column(
        "SELECT nspname FROM pg_namespace "
        "WHERE nspname NOT LIKE 'pg_%' AND nspname != 'information_schema' "
        "ORDER BY nspname"
    ))
    result.schemas_found = schemas
    result.schemas_missing = EXPECTED_SCHEMAS - schemas

    # ── 4. Registry таблицы ─────────────────────────────────────
    tables = _query_single_column(
        "SELECT schemaname || '.' || tablename "
        "FROM pg_tables WHERE schemaname = 'registry' "
        "ORDER BY tablename"
    )
    result.registry_tables = tables
    result.registry_missing = EXPECTED_REGISTRY_TABLES - set(tables)

    # ── 5. RAG таблицы (миграции могут не успеть накатиться) ──
    result.rag_tables = sorted(set(_query_single_column(
        "SELECT schemaname || '.' || tablename "
        "FROM pg_tables WHERE schemaname = 'rag'"
    )))
    if result.rag_tables:
        result.rag_has_embedding = bool(_query_single_column(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'rag' AND table_name = 'document_chunks' "
            "AND column_name = 'embedding'"
        ))
        rag_indexes = set(_query_single_column(
            "SELECT indexname FROM pg_indexes "
            "WHERE schemaname = 'rag' AND tablename = 'document_chunks'"
        ))
        result.rag_has_hnsw = "ix_rag_doc_chunks_embedding_hnsw" in rag_indexes
        result.rag_has_gin = "ix_rag_doc_chunks_tsv" in rag_indexes
        result.rag_has_created_at = bool(_query_single_column(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'rag' AND table_name = 'document_chunks' "
            "AND column_name = 'created_at'"
        ))

    # ── 6. Проверка прав (SELECT) ───────────────────────────────
    if tables:
        table_name = tables[0]
        rc, _, _ = _docker_exec(f"SELECT count(*) FROM {table_name}")
        result.can_select_registry = rc == 0

    # ── 6. Pipeline таблицы (DB-23/24) ───────────────────────────
    pipeline_tables = _query_single_column(
        "SELECT schemaname || '.' || tablename "
        "FROM pg_tables WHERE schemaname = 'pipeline' "
        "ORDER BY tablename"
    )
    result.pipeline_tables = pipeline_tables
    result.pipeline_missing = EXPECTED_PIPELINE_TABLES - set(pipeline_tables)

    # ── 7. Auth таблицы (DB-29) — в схеме auth ────────────────
    auth_tables = _query_single_column(
        "SELECT schemaname || '.' || tablename "
        "FROM pg_tables WHERE schemaname = 'auth' "
        "ORDER BY tablename"
    )
    result.auth_tables = auth_tables
    result.auth_missing = EXPECTED_AUTH_TABLES - set(auth_tables)

    # ── 8. UNIQUE-индексы (DB-4, P1F-1) ────────────────────────
    all_indexes = _query_single_column(
        "SELECT indexname FROM pg_indexes "
        "WHERE schemaname IN ('registry', 'rag') "
        "AND indexdef LIKE '%UNIQUE INDEX%' "
        "ORDER BY indexname"
    )
    result.unique_indexes_found = set(all_indexes)
    # Проверка по ключевым словам в имени индекса
    result.unique_indexes_missing = set()
    for expected_name in EXPECTED_UNIQUE_INDEXES:
        parts = expected_name.replace("registry.", "").replace("rag.", "").split("_")
        # Берём первые 3-4 значимых слова (таблица + ключевые колонки)
        significant = [p for p in parts if p not in ("key", "idx", "ix")][:4]
        found = False
        for idx_name in all_indexes:
            if all(p in idx_name.lower() for p in significant):
                found = True
                break
        if not found:
            result.unique_indexes_missing.add(expected_name)

    # ── 9. Статический анализ: create_all в сервисах ────────────
    result.services_create_all = check_services_startup_create_all()

    return result


# ────────────────────────────────────────────────────────────────
#  Service startup static check
# ────────────────────────────────────────────────────────────────


def _find_project_root() -> Path:
    """Корень проекта (backend/)."""
    # Проверяем несколько вариантов (локально / внутри Docker)
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent / "backend",
        Path("/app/backend"),
    ]
    for c in candidates:
        if (c / "service_checker").is_dir():
            return c
    return Path(__file__).resolve().parent.parent.parent.parent / "backend"


def check_services_startup_create_all() -> Dict[str, bool]:
    """
    Статический анализ: какие сервисы вызывают create_all() при старте.

    Читает файлы сервисов и ищет маркеры (.create_all, init_db).
    Не требует Docker — работает на файлах проекта.

    Returns:
        {service_key: has_create_all}
    """
    project_root = _find_project_root()
    result: Dict[str, bool] = {}

    for svc_key, info in SERVICE_STARTUP_CHECKS.items():
        markers = info["markers"]
        must_not = info.get("must_not_have_create_all", False)

        file_path = project_root / info["path"]
        if not file_path.exists():
            result[svc_key] = False
            continue

        content = file_path.read_text(encoding="utf-8", errors="ignore")

        if must_not:
            # Consumer — НЕ должен иметь create_all
            result[svc_key] = "create_all" not in content
        else:
            # Должен иметь хотя бы один из маркеров
            result[svc_key] = any(m in content for m in markers)

    return result


# ────────────────────────────────────────────────────────────────
#  Report formatting
# ────────────────────────────────────────────────────────────────


def format_db_report(result: DbCheckResult) -> str:
    """Сформировать Markdown-отчёт о состоянии БД."""
    if result.error:
        return (f"### 🗄️ БД PostgreSQL\n\n"
                f"❌ **PostgreSQL недоступен:** {result.error}\n"
                f"Проверьте: запущен ли контейнер `{POSTGRES_CONTAINER}`\n")

    lines: List[str] = []
    w = lines.append

    w("### 🗄️ БД PostgreSQL\n")
    w("")
    w(f"Общий статус: **{result.summary_icon}**\n")

    w("| Проверка | Статус | Детали |")
    w("|----------|:------:|--------|")

    # База данных
    db_icon = "✅" if result.db_exists else "❌"
    w(f"| База данных `{DB_NAME}` | {db_icon} | {'существует' if result.db_exists else 'НЕ создана'} |")

    # Расширения
    if result.extensions_ok:
        ext_list = ", ".join(sorted(result.extensions_installed))
        w(f"| Расширения | ✅ | {ext_list} |")
    else:
        missing = ", ".join(sorted(result.extensions_missing))
        installed = ", ".join(sorted(result.extensions_installed)) or "—"
        w(f"| Расширения | ❌ | отсутствуют: {missing} |")
        w(f"| | | установлены: {installed} |")

    # Схемы
    if result.schemas_ok:
        sch_list = ", ".join(sorted(result.schemas_found))
        w(f"| Схемы | ✅ | {sch_list} |")
    else:
        missing = ", ".join(sorted(result.schemas_missing))
        w(f"| Схемы | ❌ | отсутствуют: {missing} |")

    # Registry таблицы
    if result.registry_ok:
        w(f"| Registry таблицы | ✅ | {len(result.registry_tables)} таблиц |")
    else:
        missing = ", ".join(sorted(result.registry_missing))
        found_count = len(result.registry_tables)
        w(f"| Registry таблицы | ❌ | отсутствуют: {missing} |")
        w(f"| | | создано: {found_count} из {len(EXPECTED_REGISTRY_TABLES)} ожидаемых |")

    # Pipeline таблицы (DB-23/24)
    if result.pipeline_ok:
        w(f"| Pipeline таблицы | ✅ | {len(result.pipeline_tables)} таблиц |")
    else:
        missing_p = ", ".join(sorted(result.pipeline_missing))
        w(f"| Pipeline таблицы | ❌ | отсутствуют: {missing_p} |")

    # Auth таблицы (DB-29)
    if result.auth_ok:
        w(f"| Auth таблицы | ✅ | {len(result.auth_tables)} таблиц |")
    else:
        missing_a = ", ".join(sorted(result.auth_missing))
        w(f"| Auth таблицы | ❌ | отсутствуют: {missing_a} |")

    # UNIQUE-индексы (DB-4, P1F-1)
    if result.unique_indexes_ok:
        w(f"| UNIQUE-индексы | ✅ | {len(result.unique_indexes_found)} найдено |")
    else:
        missing_u = ", ".join(sorted(result.unique_indexes_missing))
        w(f"| UNIQUE-индексы | ❌ | отсутствуют: {missing_u} |")

    # RAG
    rag_checks = [
        ("Таблица `document_chunks`", bool(result.rag_tables)),
        ("Колонка `embedding` (vector)", result.rag_has_embedding),
        ("HNSW индекс `ix_rag_doc_chunks_embedding_hnsw`", result.rag_has_hnsw),
        ("GIN индекс `ix_rag_doc_chunks_tsv`", result.rag_has_gin),
        ("Колонка `created_at`", result.rag_has_created_at),
    ]
    for label, ok in rag_checks:
        icon = "✅" if ok else "❌"
        w(f"| RAG: {label} | {icon} |")

    # Права доступа
    if result.registry_tables:
        sel_icon = "✅" if result.can_select_registry else "❌"
        w(f"| SELECT из Registry | {sel_icon} | {'доступно' if result.can_select_registry else 'ОШИБКА'} |")

    # Сервисы и create_all — статический анализ
    if result.services_create_all:
        w("")
        w("### 🔍 Статический анализ: сервисы и create_all()\n")
        w("| Сервис | Схема | Статус | create_all |")
        w("|--------|:-----:|:------:|:----------:|")
        for svc_key, info in SERVICE_STARTUP_CHECKS.items():
            has_it = result.services_create_all.get(svc_key, False)
            icon = "✅" if has_it else "❌"
            must_not = info.get("must_not_have_create_all", False)
            if must_not:
                # Consumer — инвертируем: True значит create_all НЕТ
                detail = "consumer, без create_all" if has_it else "❗ есть create_all"
            else:
                detail = info.get("reason", "")
            w(f"| `{svc_key}` | {info['schema']} | {icon} | {detail} |")

    w("")
    return "\n".join(lines)
