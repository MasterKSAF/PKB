#!/usr/bin/env python3
"""
Mock Gateway Runner
Запускает единый mock-gateway на порту 8081.
"""

import subprocess
import sys

if __name__ == "__main__":
    print("=" * 60)
    print("  PKB Neuroassistant — Mock Gateway")
    print("  Swagger UI: http://127.0.0.1:8081/docs")
    print("=" * 60)
    print()

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "mocks.gateway:app",
         "--host", "127.0.0.1", "--port", "8081", "--reload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        for line in proc.stdout:
            print(line, end="")
    except KeyboardInterrupt:
        print("\n[*] Shutting down gateway...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("[*] Gateway stopped.")
