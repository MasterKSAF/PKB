"""
PKB Neuroassistant — Service Checker Utilities (logging, helpers).
"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Optional, Union


def find_available_python() -> str:
    """Найти доступный python с установленными зависимостями."""
    return sys.executable


def log(msg: str, emoji: str = "•"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  {emoji} [{ts}] {msg}")


def log_ok(msg: str):
    log(msg, "✓")


def log_warn(msg: str):
    log(msg, "⚠")


def log_err(msg: str):
    log(msg, "✗")


def log_info(msg: str):
    log(msg, "ℹ")


def log_step(msg: str):
    log(msg, "→")


def log_header(title: str):
    width = 70
    print(f"\n  {'═' * width}")
    print(f"  ┃  {title}")
    print(f"  {'═' * width}\n")


