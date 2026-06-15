"""
PKB Neuroassistant — Service Checker Utilities (logging, helpers).
"""

from __future__ import annotations

import sys
import uuid
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


# ──────────────────────────────────────────────────────────────────────
#  ID conversion: int ↔ UUID
# ──────────────────────────────────────────────────────────────────────


def int_to_uuid(n: int, quiet: bool = False) -> str:
    """Convert a BIGINT (int) to a deterministic UUID string.

    В проекте база ID — BIGINT (registry.documents.id и др.),
    но RAG Builder требует UUID для document_id.
    Функция конвертирует int → UUID через 128-битное представление:
      int=1 → "00000000-0000-0000-0000-000000000001"

    Args:
        n: целое число для конвертации
        quiet: если True, не логировать warning (для статических констант)

    Warns: логирует предупреждение о конвертации, кроме quiet=True.
    """
    result = str(uuid.UUID(int=n))
    if not quiet:
        log_warn(f"ID conversion int→UUID: {n} → {result}. "
                 f"Base type is BIGINT, target expects UUID.")
    return result


def uuid_to_int(u: str, quiet: bool = False) -> int:
    """Convert a UUID string back to BIGINT (int).

    Обратное преобразование к int_to_uuid().
    Работает только для UUID, созданных через int_to_uuid()
    (детерминированное 128-битное представление int).

    Args:
        u: UUID строка для конвертации
        quiet: если True, не логировать warning (для статических констант)

    Warns: логирует предупреждение о конвертации, кроме quiet=True.
    """
    result = uuid.UUID(u).int
    if not quiet:
        log_warn(f"ID conversion UUID→int: {u} → {result}. "
                 f"Base type is BIGINT, converting back from UUID.")
    return result
