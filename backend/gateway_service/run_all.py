"""
Запуск единого mock-сервера Gateway (все сервисы на порту 8081).

Использует mocks/gateway.py как unified entry point.
"""

import subprocess
import sys
import os

if __name__ == "__main__":
    print("Запуск mock Gateway на порту 8081...")
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "mocks.gateway:app",
         "--host", "127.0.0.1", "--port", "8081", "--reload"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
