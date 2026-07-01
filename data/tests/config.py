"""Test configuration — shared across all server tests.

Usage:
    # Default — local server
    python data/tests/test_e2e.py

    # External server
    set TEST_API_URL=http://195.70.195.203/api/v1 && python data/tests/test_e2e.py
"""
import os
from typing import Optional


def get_api_url() -> str:
    """Get the API base URL.

    Default: http://localhost:8080/api/v1
    Override with TEST_API_URL env var (e.g. http://195.70.195.203/api/v1).
    """
    return os.environ.get("TEST_API_URL", "http://localhost:8080/api/v1")


def is_local() -> bool:
    """Check if target server is local (localhost/127.0.0.1)."""
    url = get_api_url()
    return "localhost" in url or "127.0.0.1" in url


def get_direct_rag_url() -> Optional[str]:
    """Get direct rag-search URL (internal service, accessible only locally)."""
    if is_local():
        return "http://localhost:8091/api/v1/rag/search"
    return None


# ─── Какие сервисы собираются локально (не системные) ───────────────────
_APP_SERVICES_MINIMAL = ["gateway", "auth", "registry", "orchestrator", "celery-worker"]
_APP_SERVICES_ALL = [
    "auth", "registry", "parser", "converter-validator",
    "rag-builder", "rag-search", "query",
    "orchestrator", "celery-worker", "gateway", "frontend",
]
# Системные сервисы НЕ перезапускаем: postgres, redis, minio, infinity, db-init, minio-init


def _subp(cmd, cwd, timeout=120):
    """Run subprocess, return (returncode, stdout_str, stderr_str)."""
    import subprocess
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=timeout)
        return r.returncode, r.stdout.decode(errors="replace"), r.stderr.decode(errors="replace")
    except subprocess.TimeoutExpired:
        return -1, "", f"TIMEOUT {timeout}s"
    except FileNotFoundError:
        return -2, "", "docker command not found"


def ensure_services(service_set: str = "all"):
    """Перезапустить рабочие сервисы корневого docker-compose, очистить данные.

    - Системные сервисы (postgres, redis, minio, infinity) НЕ трогает.
    - Init-задания (db-init, minio-init) НЕ перезапускает.
    - Базу данных и Minio ОЧИЩАЕТ от тестовых данных.
    - Образы НЕ пересобирает (использует существующие).

    Вызывается автоматически из тестов для локального запуска.
    Пропускается если:
      - TEST_API_URL указывает на внешний сервер (не localhost)
      - TEST_SKIP_REBUILD=true (для быстрых итераций без изменений кода)

    Args:
        service_set: "minimal" (gateway+auth+registry) или "all" (все сервисы).
    """
    import sys

    if not is_local():
        return
    if os.environ.get("TEST_SKIP_REBUILD", "").lower() in ("1", "true", "yes"):
        print("  [SKIP] SERVICE RESTART (TEST_SKIP_REBUILD=true)")
        return

    compose_file = os.environ.get("TEST_COMPOSE_FILE", "docker-compose.yml")
    project_dir = os.environ.get("TEST_PROJECT_DIR", os.path.join(os.path.dirname(__file__), "..", ".."))
    project_dir = os.path.abspath(project_dir)

    if service_set == "minimal":
        services = _APP_SERVICES_MINIMAL[:]
    else:
        services = _APP_SERVICES_ALL[:]

    svc_str = " ".join(services)
    print(f"\n  >>> BUILD & UP: {svc_str}")
    sys.stdout.flush()

    # ─── Step 1: Rebuild images ──────────────────────────────────────────
    code, out, err = _subp(
        ["docker", "compose", "-f", compose_file, "build"] + services,
        project_dir, timeout=300,
    )

    # ─── Step 2: Clean DB data ───────────────────────────────────────────
    _clean_database()

    # ─── Step 3: Clean Minio data ────────────────────────────────────────
    _clean_minio()

    print(f"  [OK] Test environment ready")
    sys.stdout.flush()


def _clean_database():
    """Очистить тестовые данные из PostgreSQL (registry + pipeline схемы)."""
    import subprocess
    import sys

    sql = """
    TRUNCATE TABLE registry.drafts CASCADE;
    TRUNCATE TABLE registry.documents CASCADE;
    TRUNCATE TABLE pipeline.tasks CASCADE;
    """
    cmd = [
        "docker", "exec", "-i", "pkb-postgres",
        "psql", "-U", "pkb", "-d", "pkb_neuro", "-c", sql,
    ]
    code, out, err = _subp(cmd, ".", timeout=30)
    if code == 0:
        print(f"  [OK] Database cleaned")
    else:
        # Если таблиц нет — не ошибка, могли не создаться
        if "does not exist" not in err:
            print(f"  [WARN] DB clean issue: {err[:200]}")
    sys.stdout.flush()


def _clean_minio():
    """Очистить test data из Minio bucket 'documents'."""
    import sys

    # Удаление через Minio Client внутри контейнера
    cmds = [
        ["docker", "exec", "pkb-minio", "sh", "-c", "rm -rf /data/documents/* 2>/dev/null; exit 0"],
        ["docker", "exec", "pkb-minio", "sh", "-c", "rm -rf /data/images/* 2>/dev/null; exit 0"],
    ]
    for cmd in cmds:
        code, _, _ = _subp(cmd, ".", timeout=15)
    print(f"  [OK] Minio cleaned")
    sys.stdout.flush()
