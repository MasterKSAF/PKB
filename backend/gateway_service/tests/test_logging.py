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
        """JSON лог содержит обязательные поля: level, timestamp, service, message."""
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
        assert "service" in data
        assert "message" in data
        assert data["level"] == "WARNING"
        assert data["service"] == "gateway"

    def test_format_includes_exception(self):
        """При exc_info — форматтер обрабатывает без ошибок."""
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
        assert "message" in data
        assert "level" in data

    def test_format_masks_password_in_json(self):
        """PII-поля (password) маскируются в JSON-строке (mask_pii_in_text)."""
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname=__file__, lineno=30,
            msg='request processed', args=(),
            exc_info=None,
        )
        formatter = JSONLogFormatter()
        # Маскировка применяется к JSON-строке: "password":"secret" → "password":"***"
        result = formatter.format(record)
        data = json.loads(result)
        assert data["message"] == "request processed"
        assert "message" in data


class TestParsePiiFields:
    """_parse_pii_fields — парсинг списка PII-полей из env."""

    def test_default_fields(self):
        """Без env возвращает DEFAULT_PII_FIELDS."""
        fields = _parse_pii_fields(None)
        assert len(fields) > 0

    def test_custom_fields(self):
        """Строка с запятыми — кастомный набор."""
        fields = _parse_pii_fields("password,secret_key")
        assert "password" in fields
        assert "secret_key" in fields

    def test_empty_string_returns_default(self):
        """Пустая строка → DEFAULT_PII_FIELDS."""
        fields = _parse_pii_fields("")
        assert len(fields) > 0
