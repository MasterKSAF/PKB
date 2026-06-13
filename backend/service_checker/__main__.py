"""
PKB Neuroassistant — Service Checker CLI Entry Point.

Запуск: python -m service_checker
         python service_checker/__main__.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Добавляем backend/ в sys.path для импорта service_checker как пакета
_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from service_checker.core.cli import main

if __name__ == "__main__":
    asyncio.run(main())
