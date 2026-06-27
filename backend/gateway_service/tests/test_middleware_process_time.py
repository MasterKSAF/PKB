"""
Tests for ProcessTimeMiddleware.

Проверяет:
  - Ответ содержит X-Process-Time
  - Значение — число с плавающей точкой (float)
  - Время больше 0
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


class TestProcessTime:
    """X-Process-Time заголовок."""

    def test_response_has_process_time(self, client):
        """Ответ содержит X-Process-Time."""
        resp = client.get("/api/v1/system/health")
        assert "X-Process-Time" in resp.headers

    def test_process_time_is_float(self, client):
        """X-Process-Time — число с плавающей точкой."""
        resp = client.get("/api/v1/system/health")
        val = resp.headers["X-Process-Time"]
        try:
            float_val = float(val)
            assert isinstance(float_val, float)
        except ValueError:
            pytest.fail(f"X-Process-Time is not a float: {val!r}")

    def test_process_time_positive(self, client):
        """X-Process-Time > 0."""
        resp = client.get("/api/v1/system/health")
        val = float(resp.headers["X-Process-Time"])
        assert val > 0, f"X-Process-Time should be positive, got {val}"
