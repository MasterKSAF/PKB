#!/usr/bin/env python3
"""
PKB Neuroassistant — Service Checker Setup

One-command setup from scratch:
  1. Install huggingface-hub (if missing)
  2. Download and prepare TEI model
  3. Build base image (if missing or --build forced)
  4. Start Docker Compose (postgres, redis, minio, tei, app)

Usage:
  python setup.py                  # Полный setup
  python setup.py --build          # Принудительная пересборка образа
  python setup.py --model          # Только подготовка модели
  python setup.py --up             # Только запуск Docker Compose
  python setup.py --down           # Остановка Docker Compose
  python setup.py --ps             # Статус контейнеров
  python setup.py --prepare        # Полный цикл как в prepare.bat (build + down -v + up)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCKER_DIR = ROOT / "docker"
DOCKER_COMPOSE = ["docker", "compose", "-f", str(DOCKER_DIR / "docker-compose.yml")]
BASE_IMAGE = "ghcr.io/pkb/neuro-base:latest"


def run(cmd: list[str], cwd: str | None = None, check: bool = True) -> None:
    """Run a command and print its output."""
    print(f"  $ {' '.join(cmd)}")
    try:
        subprocess.run(cmd, cwd=cwd or str(ROOT), check=check)
    except subprocess.CalledProcessError as e:
        print(f"  ✗ FAILED (exit code {e.returncode})")
        sys.exit(e.returncode)


def image_exists() -> bool:
    """Check if base image exists locally."""
    result = subprocess.run(
        ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
        capture_output=True, text=True, timeout=30,
    )
    return BASE_IMAGE in result.stdout


def build_image() -> None:
    """Build base image from Dockerfile.base."""
    print(f"\n[{'2' if not image_exists() else '3'}/4] Building base image...")
    run([
        "docker", "build",
        "-f", str(DOCKER_DIR / "Dockerfile.base"),
        "-t", BASE_IMAGE,
        str(DOCKER_DIR),
    ])


def install_deps() -> None:
    """Ensure huggingface-hub is installed."""
    print("\n[1/4] Installing huggingface-hub...")
    run([sys.executable, "-m", "pip", "install", "huggingface-hub", "-q"])


def prepare_model() -> None:
    """Download and prepare TEI model."""
    print("\n[2/4] Preparing TEI model...")
    run([sys.executable, "docker/prepare_tei_model.py"])


def migrate_volumes() -> None:
    """Migrate old docker_* volumes to new pkb_* ones."""
    print("\n[3.5/4] Migrating old volumes (docker_* → pkb_*)...")
    migrate_script = ROOT / "docker" / "migrate_volumes.py"
    if migrate_script.exists():
        run([sys.executable, str(migrate_script)])
    else:
        try:
            from service_checker.core.docker import _migrate_volumes
            _migrate_volumes()
        except ImportError:
            print("  ⚠️  Cannot migrate volumes — script not found")
        except Exception as e:
            print(f"  ⚠️  Migration failed: {e}")


def docker_up() -> None:
    """Start Docker Compose services."""
    print("\n[4/4] Starting Docker Compose...")
    run([*DOCKER_COMPOSE, "up", "-d"])
    print("\n✓ Setup complete! Containers are starting.")
    print("  Run 'docker compose -f docker/docker-compose.yml logs -f' to see logs.")


def docker_down() -> None:
    """Stop Docker Compose services."""
    print("\nStopping Docker Compose...")
    run([*DOCKER_COMPOSE, "down"])
    print("✓ Docker Compose stopped.")


def docker_ps() -> None:
    """Show container status."""
    run([*DOCKER_COMPOSE, "ps"])


def help() -> None:
    print(__doc__.strip())


def main() -> None:
    args = sys.argv[1:]

    if not args:
        # Полный setup
        install_deps()
        prepare_model()
        if not image_exists():
            build_image()
        migrate_volumes()
        docker_up()
    elif args[0] == "--build":
        build_image()
    elif args[0] == "--model":
        prepare_model()
    elif args[0] == "--up":
        migrate_volumes()
        docker_up()
    elif args[0] == "--down":
        docker_down()
    elif args[0] == "--ps":
        docker_ps()
    elif args[0] == "--prepare":
        # Полный цикл как в prepare.bat: build + down + чистка volumes + up
        build_image()
        run([*DOCKER_COMPOSE, "down"])
        # Явно удаляем только известные volumes
        for vol_name in ["pkb_pg_data", "pkb_minio_data", "pkb_app_logs"]:
            subprocess.run(["docker", "volume", "rm", "-f", vol_name], capture_output=True, timeout=10)
        migrate_volumes()
        docker_up()
    else:
        help()
        sys.exit(1)


if __name__ == "__main__":
    main()
