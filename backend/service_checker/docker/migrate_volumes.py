#!/usr/bin/env python3
"""
PKB Neuroassistant — Migration helper for Docker volumes.

Переносит данные из старых volumes (docker_*) в новые (pkb_*)
после смены project name с 'docker' на 'pkb'.

Запуск: python docker/migrate_volumes.py
"""

import subprocess
import sys

_OLD_VOLUMES = {
    "docker_pg_data": "pkb_pg_data",
    "docker_minio_data": "pkb_minio_data",
    "docker_app_logs": "pkb_app_logs",
    "docker_tei_cache": "pkb_tei_cache",
}


def migrate() -> None:
    for old_name, new_name in _OLD_VOLUMES.items():
        inspect = subprocess.run(
            ["docker", "volume", "inspect", old_name],
            capture_output=True, text=True, timeout=10,
        )
        if inspect.returncode != 0:
            continue

        new_inspect = subprocess.run(
            ["docker", "volume", "inspect", new_name],
            capture_output=True, text=True, timeout=10,
        )
        if new_inspect.returncode != 0:
            subprocess.run(
                ["docker", "volume", "create", new_name],
                capture_output=True, timeout=10,
            )
            print(f"  Created: {new_name}")

        print(f"  Copying {old_name} -> {new_name}...")
        copy = subprocess.run(
            ["docker", "run", "--rm",
             "-v", f"{old_name}:/from",
             "-v", f"{new_name}:/to",
             "alpine", "cp", "-a", "/from/.", "/to/"],
            capture_output=True, text=True, timeout=120,
        )
        if copy.returncode != 0:
            print(f"  WARNING: copy failed: {copy.stderr.strip()}", file=sys.stderr)
            continue

        # Remove containers that still reference the old volume
        containers = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"volume={old_name}",
             "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=10,
        )
        for cname in containers.stdout.strip().split("\n"):
            cname = cname.strip()
            if not cname:
                continue
            subprocess.run(["docker", "rm", "-f", cname], capture_output=True, timeout=10)

        rm = subprocess.run(
            ["docker", "volume", "rm", old_name],
            capture_output=True, text=True, timeout=10,
        )
        if rm.returncode == 0:
            print(f"  Done: {old_name} migrated to {new_name}")
        else:
            print(f"  WARNING: could not remove {old_name}: {rm.stderr.strip()}", file=sys.stderr)


if __name__ == "__main__":
    migrate()
