#!/usr/bin/env python3
"""
Утилита для запуска mock-gateway PKB Neuroassistant.

Использование:
    python start_service.py           # Запустить gateway (порт из MOCK_PORT)
    python start_service.py list      # Показать справку
"""

import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, ".."))
from mocks.common import MOCK_PORT


def print_help():
    print("Использование: python start_service.py [list]\n")
    print(f"  (без аргументов) → запуск единого gateway (порт {MOCK_PORT})")
    print("  list              → показать эту справку")
    print()


def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() == "list":
        print_help()
        sys.exit(0)

    print(f"[+] Запуск PKB Neuroassistant Mock Gateway на http://127.0.0.1:{MOCK_PORT}")
    print(f"[+] Swagger UI: http://127.0.0.1:{MOCK_PORT}/docs")
    print("[+] Нажмите Ctrl+C для остановки.\n")

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "mocks.gateway:app",
         "--host", "127.0.0.1", "--port", str(MOCK_PORT)],
        cwd=os.path.join(BASE_DIR, ".."),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        for line in proc.stdout:
            print(line, end="")
    except KeyboardInterrupt:
        print("\n[-] Остановка gateway...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("[*] Gateway остановлен.")


if __name__ == "__main__":
    main()
