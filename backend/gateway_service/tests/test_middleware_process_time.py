"""
Тесты ProcessTimeMiddleware — X-Process-Time header.

Unit-тесты, не требуют Docker.
"""

from __future__ import annotations

import os
import sys

import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)


class TestProcessTime:
    """X-Process-Time заголовок."""

    def test_process_time_header_present(self, client):
        """Ответ содержит X-Process-Time."""
        resp = client.get("/api/v1/health")
        assert "X-Process-Time" in resp.headers

    def test_process_time_is_float(self, client):
        """X-Process-Time — число с плавающей точкой."""
        resp = client.get("/api/v1/health")
        val = float(resp.headers["X-Process-Time"])
        assert val > 0
