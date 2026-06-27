"""
Тесты JSONLogFormatter, PII-маскировка, _parse_pii_fields.

Unit-тесты, не требуют Docker.
"""

from __future__ import annotations

import json
import logging
import os
import sys

import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)

from gateway.logging_config import JSONLogFormatter, _parse_pii_fields


class TestJSONLogFormatter:
    """JSONLogFormatter — структура и поля JSON."""

    def test_format_returns_json_string(self):
        """format() возвращает JSON-строку."""
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname=__file__, lineno=42, msg="hello", args=(),
            exc_info=None,
        )
        formatter = JSONLogFormatter()
        result = formatter.format(record)
        data = json.loads(result)
        assert "message" in data
        assert data["message"] == "hello"

    def test_format_includes_required_fields(self):
        """JSON лог содержит обязательные поля: level, timestamp, module."""
        record = logging.LogRecord(
            name="test.logger", level=logging.WARNING,
            pathname=__file__, lineno=10, msg="test", args=(),
            exc_info=None,
        )
        formatter = JSONLogFormatter()
        result = formatter.format(record)
        data = json.loads(result)
        assert "level" in data
        assert "timestamp" in data
        assert "module" in data
        assert "logger" in data
        assert "message" in data
        assert data["level"] == "WARNING"

    def test_format_includes_exception(self):
        """При exc_info — поле exception в JSON."""
        try:
            raise ValueError("test error")
        except ValueError:
            record = logging.LogRecord(
                name="test", level=logging.ERROR,
                pathname=__file__, lineno=20, msg="error", args=(),
                exc_info=True,
            )
        formatter = JSONLogFormatter()
        result = formatter.format(record)
        data = json.loads(result)
        assert "exception" in data
        assert "test error" in data["exception"]

    def test_format_masks_password_in_message(self):
        """PII-поля (password) маскируются в message."""
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname=__file__, lineno=30,
            msg='password=secret123', args=(),
            exc_info=None,
        )
        formatter = JSONLogFormatter()
        result = formatter.format(record)
        data = json.loads(result)
        assert "***" in data["message"]
        assert "secret123" not in data["message"]


class TestParsePiiFields:
    """_parse_pii_fields — разметка PII в лог-записях."""

    def test_parse_pii_fields_detects_password(self):
        """Парсинг обнаруживает password в строке."""
        fields = _parse_pii_fields("password=secret")
        assert "password" in fields

    def test_parse_pii_fields_detects_token(self):
        """Парсинг обнаруживает access_token в строке."""
        fields = _parse_pii_fields("access_token=eyJhbGci")
        assert "access_token" in fields

    def test_parse_pii_fields_no_pii(self):
        """Без PII — пустой список."""
        fields = _parse_pii_fields("normal log message")
        assert not fields
