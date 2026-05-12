#!/usr/bin/env python3
"""
Mock Services Runner
Запускает все mock-сервисы для тестирования фронтенда.
Каждый сервис запускается в отдельном процессе на своём порту.
"""

import os
import signal
import subprocess
import sys
import time

SERVICES = [
    ("Auth Service", 8082, "auth_service.main:app"),
    ("Orchestrator Service", 8081, "orchestrator_service.main:app"),
    ("Query Service", 8083, "query_service.main:app"),
    ("Registry Service", 8084, "registry_service.main:app"),
]

processes = []


def start_services():
    """Запускает все mock-сервисы."""
    base_dir = os.path.dirname(os.path.abspath(__file__))

    for name, port, app_path in SERVICES:
        print(f"[+] Starting {name} on port {port}...")
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                app_path,
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--reload",
            ],
            cwd=base_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        processes.append((name, proc))

    print(f"\n[*] All {len(SERVICES)} services started. Press Ctrl+C to stop all.\n")

    try:
        # Мониторим процессы
        while True:
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"[!] {name} exited with code {proc.returncode}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Shutting down all services...")
        stop_services()


def stop_services():
    """Останавливает все запущенные сервисы."""
    for name, proc in processes:
        print(f"[-] Stopping {name}...")
        if sys.platform == "win32":
            proc.terminate()
        else:
            proc.send_signal(signal.SIGTERM)

    for name, proc in processes:
        proc.wait(timeout=5)

    print("[*] All services stopped.")


if __name__ == "__main__":
    print("=" * 60)
    print("  PKB Neuroassistant — Mock Services")
    print("=" * 60)
    print()
    start_services()
