"""
Тесты логирования: JSONLogFormatter, PIIFilter, mask_pii_in_text.

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

from gateway.logging_config import (
    JSONLogFormatter,
    PIIFilter,
    mask_pii_in_text,
    _parse_pii_fields,
    PII_FIELDS,
)


class TestJSONLogFormatter:
    """JSONLogFormatter — форматирование лога в JSON."""

    def test_format_returns_json(self):
        """format() возвращает JSON строку."""
        formatter = JSONLogFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname=__file__,
            lineno=1, msg="test message", args=(), exc_info=None,
        )
        output = formatter.format(record)
        # Должен быть JSON
        parsed = json.loads(output)
        assert "timestamp" in parsed
        assert "level" in parsed
        assert "message" in parsed

    def test_format_contains_required_fields(self):
        """JSON содержит обязательные поля: timestamp, level, service, message."""
        formatter = JSONLogFormatter()
        record = logging.LogRecord(
            name="gateway", level=logging.WARNING, pathname=__file__,
            lineno=1, msg="test warning", args=(), exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["timestamp"] is not None
        assert parsed["level"] == "WARNING"
        assert parsed["service"] == "gateway"
        assert parsed["message"] == "test warning"

    def test_format_with_extra_fields(self):
        """Дополнительные поля (request_id) включаются в JSON."""
        formatter = JSONLogFormatter()
        record = logging.LogRecord(
            name="gateway", level=logging.INFO, pathname=__file__,
            lineno=1, msg="request", args=(), exc_info=None,
        )
        record.request_id = "req-123"
        record.req_method = "GET"
        record.req_path = "/api/v1/health"
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed.get("request_id") == "req-123"
        assert parsed.get("method") == "GET"
        assert parsed.get("path") == "/api/v1/health"


class TestMaskPiiInText:
    """mask_pii_in_text() — маскировка PII-полей."""

    def test_mask_password(self):
        """password маскируется."""
        text = '{"password":"secret123"}'
        masked = mask_pii_in_text(text)
        assert '"password":"***"' in masked
        assert "secret123" not in masked

    def test_mask_access_token(self):
        """access_token маскируется."""
        text = '{"access_token":"eyJhbGciOiJIUzI1NiJ9"}'
        masked = mask_pii_in_text(text)
        assert '"access_token":"***"' in masked

    def test_mask_refresh_token(self):
        """refresh_token маскируется."""
        text = '{"refresh_token":"r-abc123"}'
        masked = mask_pii_in_text(text)
        assert '"refresh_token":"***"' in masked

    def test_multiple_pii_fields(self):
        """Множественные PII-поля маскируются."""
        text = '{"password":"abc","access_token":"def"}'
        masked = mask_pii_in_text(text)
        assert masked.count('"***"') == 2

    def test_non_pii_field_not_masked(self):
        """Не-PII поля не маскируются."""
        text = '{"document_key":"doc-123"}'
        masked = mask_pii_in_text(text)
        assert "doc-123" in masked


class TestPIIFilter:
    """PIIFilter — не блокирует записи."""

    def test_filter_returns_true(self):
        """filter() всегда возвращает True (не блокирует)."""
        pii_filter = PIIFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname=__file__,
            lineno=1, msg="test", args=(), exc_info=None,
        )
        assert pii_filter.filter(record) is True


class TestParsePiiFields:
    """_parse_pii_fields() — парсинг из env."""

    def test_default_fields(self):
        """По умолчанию — password, access_token, refresh_token."""
        fields = _parse_pii_fields(None)
        assert "password" in fields
        assert "access_token" in fields
        assert "refresh_token" in fields

    def test_custom_fields(self):
        """Кастомный набор полей."""
        fields = _parse_pii_fields("password,secret_key,api_key")
        assert "password" in fields
        assert "secret_key" in fields
        assert "api_key" in fields
        assert "access_token" not in fields

    def test_empty_string(self):
        """Пустая строка → default."""
        fields = _parse_pii_fields("")
        assert fields == {"password", "access_token", "refresh_token"}
