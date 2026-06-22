#!/usr/bin/env python3
"""
Mock Gateway Runner
Запускает единый mock-gateway на порту MOCK_PORT (см. mocks/common.py).
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from mocks.common import MOCK_PORT

if __name__ == "__main__":
    print("=" * 60)
    print("  PKB Neuroassistant — Mock Gateway")
    print(f"  Swagger UI: http://127.0.0.1:{MOCK_PORT}/docs")
    print("=" * 60)
    print()

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "mocks.gateway:app",
         "--host", "127.0.0.1", "--port", str(MOCK_PORT), "--reload"],
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
