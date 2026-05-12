#!/usr/bin/env python3
"""
Утилита для запуска mock-сервисов PKB Neuroassistant.

Использование:
    python start_service.py all          # Запустить все сервисы
    python start_service.py auth         # Только Auth Service (порт 8082)
    python start_service.py orchestrator # Только Orchestrator (порт 8081)
    python start_service.py query        # Только Query Service (порт 8083)
    python start_service.py registry     # Только Registry Service (порт 8084)
    python start_service.py list         # Показать доступные сервисы
"""

import os
import subprocess
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SERVICES = {
    "auth": {
        "name": "Auth Service",
        "port": 8082,
        "app": "mocks.auth_service.main:app",
    },
    "orchestrator": {
        "name": "Orchestrator Service",
        "port": 8081,
        "app": "mocks.orchestrator_service.main:app",
    },
    "query": {
        "name": "Query Service",
        "port": 8083,
        "app": "mocks.query_service.main:app",
    },
    "registry": {
        "name": "Registry Service",
        "port": 8084,
        "app": "mocks.registry_service.main:app",
    },
}


def list_services():
    """Вывод списка доступных сервисов."""
    print("Доступные mock-сервисы:\n")
    for key, svc in SERVICES.items():
        print(f"  {key:15s} → {svc['name']} (порт {svc['port']})")
    print()
    print("  all  → запустить все сервисы")
    print("  list → показать эту справку")


def start_service(key: str) -> subprocess.Popen:
    """Запуск одного сервиса."""
    svc = SERVICES[key]
    print(f"[+] Запуск {svc['name']} на порту {svc['port']}...")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            svc["app"],
            "--host",
            "127.0.0.1",
            "--port",
            str(svc["port"]),
        ],
        cwd=os.path.join(BASE_DIR, ".."),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return proc


def main():
    if len(sys.argv) < 2:
        print("Использование: python start_service.py <service_name|all|list>\n")
        list_services()
        sys.exit(1)

    target = sys.argv[1].lower()

    if target == "list":
        list_services()
        sys.exit(0)

    if target == "all":
        processes = {}
        for key in SERVICES:
            proc = start_service(key)
            processes[key] = proc
            time.sleep(1)

        print(f"\n[*] Все {len(processes)} сервиса запущены. PID'ы:")
        for key, proc in processes.items():
            print(f"    {key}: PID {proc.pid}")

        print("\n[*] Нажмите Ctrl+C для остановки всех сервисов.\n")

        try:
            while True:
                for key, proc in list(processes.items()):
                    if proc.poll() is not None:
                        print(
                            f"[!] {SERVICES[key]['name']} завершился (код {proc.returncode})"
                        )
                        del processes[key]
                if not processes:
                    print("[!] Все сервисы завершились.")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[*] Остановка всех сервисов...")
            for key, proc in processes.items():
                print(f"[-] Остановка {SERVICES[key]['name']}...")
                proc.terminate()
            for key, proc in processes.items():
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
            print("[*] Все сервисы остановлены.")
        sys.exit(0)

    if target not in SERVICES:
        print(f"[!] Неизвестный сервис: {target}\n")
        list_services()
        sys.exit(1)

    # Запуск одного сервиса
    proc = start_service(target)
    svc = SERVICES[target]
    print(f"[*] {svc['name']} запущен на http://127.0.0.1:{svc['port']}")
    print("[*] Нажмите Ctrl+C для остановки.\n")

    try:
        proc.wait()
    except KeyboardInterrupt:
        print(f"\n[-] Остановка {svc['name']}...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print(f"[*] {svc['name']} остановлен.")


if __name__ == "__main__":
    main()
