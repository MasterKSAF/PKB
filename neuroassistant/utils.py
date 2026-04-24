"""Small utilities used across modules."""

from __future__ import annotations

import hashlib
import re
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator


_CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_language(text: str) -> str:
    if not text.strip():
        return "unknown"
    if _CYRILLIC_RE.search(text) is not None:
        return "ru"
    return "en"


@dataclass(frozen=True, slots=True)
class TimerResult:
    duration_ms: int


@contextmanager
def timer() -> Iterator[TimerResult]:
    start = time.perf_counter()
    result = TimerResult(duration_ms=0)
    try:
        yield result
    finally:
        duration = int((time.perf_counter() - start) * 1000)
        object.__setattr__(result, "duration_ms", duration)

