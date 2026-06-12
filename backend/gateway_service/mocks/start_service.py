#!/usr/bin/env python3
"""
Утилита для запуска mock-gateway PKB Neuroassistant.

Использование:
    python start_service.py           # Запустить gateway (порт 8081)
    python start_service.py list      # Показать справку
"""

import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def print_help():
    print("Использование: python start_service.py [list]\n")
    print("  (без аргументов) → запуск единого gateway (порт 8081)")
    print("  list              → показать эту справку")
    print()


def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() == "list":
        print_help()
        sys.exit(0)

    print("[+] Запуск PKB Neuroassistant Mock Gateway на http://127.0.0.1:8081")
    print("[+] Swagger UI: http://127.0.0.1:8081/docs")
    print("[+] Нажмите Ctrl+C для остановки.\n")

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "mocks.gateway:app",
         "--host", "127.0.0.1", "--port", "8081"],
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
