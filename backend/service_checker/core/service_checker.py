#!/usr/bin/env python3
"""
PKB Neuroassistant — Service Checker & Report Generator

Entry point for the service_checker tool.
All logic is in the `core/` package modules.

⚠️  ВАЖНО: service_checker НЕ вмешивается в работу других сервисов.
Его единственная задача — проверить их состояние (health check),
выполнить тестовые API-вызовы (эмуляция) и сформировать отчёт.
Любые изменения конфигурации, данных или кода сервисов ЗАПРЕЩЕНЫ.

Использование:
  python service_checker/service_checker.py --help
  python service_checker/service_checker.py docker --action full-report
  python -m service_checker docker --action full-report
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Добавляем backend/ в sys.path (нужно для импорта service_checker как пакета)
_backend = Path(__file__).resolve().parent.parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from service_checker.core.cli import main

if __name__ == "__main__":
    asyncio.run(main())
