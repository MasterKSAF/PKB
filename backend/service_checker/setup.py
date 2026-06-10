#!/usr/bin/env python3
"""
PKB Neuroassistant — Service Checker Setup

One-command setup from scratch:
  1. Install huggingface-hub (if missing)
  2. Download and prepare TEI model
  3. Start Docker Compose (postgres, redis, minio, tei)

Usage:
  python setup.py            # Полный setup
  python setup.py --model    # Только подготовка модели
  python setup.py --up       # Только запуск Docker Compose
  python setup.py --down     # Остановка Docker Compose
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCKER_COMPOSE = ["docker", "compose", "-f", str(ROOT / "docker" / "docker-compose.yml")]


def run(cmd: list[str], cwd: str | None = None, check: bool = True) -> None:
    """Run a command and print its output."""
    print(f"  $ {' '.join(cmd)}")
    try:
        subprocess.run(cmd, cwd=cwd or str(ROOT), check=check)
    except subprocess.CalledProcessError as e:
        print(f"  ✗ FAILED (exit code {e.returncode})")
        sys.exit(e.returncode)


def install_deps() -> None:
    """Ensure huggingface-hub is installed."""
    print("\n[1/3] Installing huggingface-hub...")
    run([sys.executable, "-m", "pip", "install", "huggingface-hub", "-q"])


def prepare_model() -> None:
    """Download and prepare TEI model."""
    print("\n[2/3] Preparing TEI model...")
    run([sys.executable, "docker/prepare_tei_model.py"])


def docker_up() -> None:
    """Start Docker Compose services."""
    print("\n[3/3] Starting Docker Compose...")
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
        docker_up()
    elif args[0] == "--model":
        prepare_model()
    elif args[0] == "--up":
        docker_up()
    elif args[0] == "--down":
        docker_down()
    elif args[0] == "--ps":
        docker_ps()
    else:
        help()
        sys.exit(1)


if __name__ == "__main__":
    main()
