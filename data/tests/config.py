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


def cleanup_enabled() -> bool:
    """Проверка флага очистки тестовых данных.

    Приоритет:
      1. TEST_CLEANUP=true/false — явный флаг
      2. TEST_SKIP_REBUILD=true (обратная совместимость) — false (не чистить)
      3. По умолчанию — true (чистить)

    Returns:
        bool: True если очистка разрешена.
    """
    cleanup = os.environ.get("TEST_CLEANUP")
    if cleanup:
        return cleanup.lower() in ("1", "true", "yes")
    # Обратная совместимость: TEST_SKIP_REBUILD=true отключает очистку
    skip = os.environ.get("TEST_SKIP_REBUILD", "").lower() in ("1", "true", "yes")
    return not skip


def ensure_services(service_set: str = "all"):
    """Проверить доступность сервисов и очистить тестовые данные (опционально).

    Не трогает контейнеры — код подхватывается через volume-монтирование.
    Если нужно пересоздать контейнеры (например, после изменений в compose):
      docker compose up -d --force-recreate <service>

    Очистка данных управляется:
      - TEST_CLEANUP=true  (по умолч.) — очищает БД и Minio
      - TEST_CLEANUP=false — не очищает (для проверки на существующих данных)
      - TEST_SKIP_REBUILD=true (обратная совместимость) — то же что TEST_CLEANUP=false

    Пропускается полностью если:
      - TEST_API_URL указывает на внешний сервер (не localhost)
    """
    import sys

    if not is_local():
        return

    if not cleanup_enabled():
        print("  [SKIP] DATA CLEANUP (TEST_CLEANUP=false)")
        sys.stdout.flush()
        return

    print(f"\n  >>> CLEANUP TEST DATA")
    sys.stdout.flush()

    _clean_database()
    _clean_minio()

    print(f"  [OK] Test data cleaned")
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
