#!/usr/bin/env python3
"""Ожидание готовности Docker-контейнеров и Python-сервисов."""

import json
import subprocess
import sys
import time
import urllib.request
import urllib.error

COMPOSE_FILE = "service_checker/docker/docker-compose.yml"

# Сервисы, которые должны быть healthy (инфраструктура)
INFRA_SERVICES = ["postgres", "redis", "minio", "tei"]

# Python-сервисы под supervisord (порт, health-путь)
PYTHON_SERVICES = {
    "auth":        (8082, ["/health", "/api/v1/health", "/api/v1/system/health"]),
    "registry":    (8084, ["/api/v1/", "/api/v1/health", "/health"]),
    "converter":   (8086, ["/health", "/api/v1/health"]),
    "parser":      (8087, ["/health", "/api/v1/health"]),
    "orchestrator":(8081, ["/api/v1/system/health", "/health"]),
    "query":       (8083, ["/api/v1/health", "/health"]),
    "rag_builder": (8090, ["/api/v1/rag/", "/api/v1/health", "/health"]),
    "rag_search":  (8091, ["/", "/api/v1/health", "/health"]),
    "gateway":     (8080, ["/api/v1/system/health", "/api/v1/health", "/health"]),
    "ocr":        (8088, ["/api/v1/health", "/health"]),
}

POLL_INTERVAL = 1
MAX_RETRIES = 12  # 12 * 1 = 12 секунд максимум


def log(msg: str):
    print(f"  {msg}")


def wait_for_container_healthy(service: str) -> bool:
    """Ждём, пока контейнер станет healthy через docker compose ps."""
    for _ in range(MAX_RETRIES):
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", COMPOSE_FILE, "ps", "--format", "json", service],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout.strip())
                status = data.get("Status", "")
                state = data.get("State", "")
                if "(healthy)" in status:
                    return True
                if state == "running" and "(healthy)" not in status:
                    pass  # ещё не healthy
        except Exception:
            pass
        time.sleep(POLL_INTERVAL)
    return False


def wait_for_app_container() -> bool:
    """Ждём, пока контейнер app запустится."""
    for _ in range(MAX_RETRIES):
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", COMPOSE_FILE, "ps", "--format", "json", "app"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout.strip())
                state = data.get("State", "")
                if state == "running":
                    return True
        except Exception:
            pass
        time.sleep(POLL_INTERVAL)
    return False


def main():
    print()
    log("Ожидание готовности инфраструктуры (postgres, redis, minio, tei)...")
    ok = sum(1 for svc in INFRA_SERVICES if wait_for_container_healthy(svc))
    log(f"  ✓ {ok}/{len(INFRA_SERVICES)} контейнеров здоровы")

    if not wait_for_app_container():
        log("  ✗ app не запустился")
        return False
    log("  ✓ app запущен")

    log("Ожидание HTTP health'ов Python-сервисов...")
    for _ in range(30):
        alive = 0
        for name, (port, paths) in PYTHON_SERVICES.items():
            for path in paths:
                try:
                    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}")
                    with urllib.request.urlopen(req, timeout=1) as resp:
                        if resp.status < 500:
                            alive += 1
                            break
                except Exception:
                    continue
        if alive >= 3:
            log(f"  ✓ {alive}/10 сервисов отвечают")
            return True
        time.sleep(1)
    log(f"  ⚠ {alive}/10 сервисов ответили, продолжаем...")
    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
