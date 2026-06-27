"""
Tests for logging — JSONLogFormatter, PII masking (P11-1, P11-2, P11-3).

Сценарии:
  - JSONLogFormatter.format(): JSON строка с полями timestamp, level, service, message
  - PII-маскировка: "password":"secret" → "password":"***"
  - PII-маскировка: "access_token":"eyJ..." → "access_token":"***"
  - mask_pii_in_text(): единичное и множественное вхождение
  - PIIFilter.filter(): не блокирует записи
  - setup_logging(): уровень из GATEWAY_LOG_LEVEL
  - _parse_pii_fields(): парсинг из env, значения по умолчанию
  - LOG_PII_FIELDS: кастомный набор полей для маскировки
"""

import sys
import os
import json
import logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from gateway.logging_config import (
    JSONLogFormatter,
    PIIFilter,
    mask_pii_in_text,
    _parse_pii_fields,
    DEFAULT_PII_FIELDS,
    PII_FIELDS,
    setup_logging,
)


class TestJSONLogFormatter:
    """JSONLogFormatter — формат JSON-логов."""

    def test_format_returns_json(self):
        """format() возвращает JSON-строку."""
        formatter = JSONLogFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname=__file__, lineno=42,
            msg="test message", args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert isinstance(data, dict)

    def test_format_contains_required_fields(self):
        """JSON содержит timestamp, level, service, message."""
        formatter = JSONLogFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname=__file__, lineno=42,
            msg="hello world", args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert "timestamp" in data
        assert data["level"] == "INFO"
        assert data["service"] == "gateway"
        assert data["message"] == "hello world"

    def test_format_with_extra_fields(self):
        """Дополнительные поля (trace_id, request_id) сериализуются."""
        formatter = JSONLogFormatter()
        record = logging.LogRecord(
            name="test", level=logging.WARNING,
            pathname=__file__, lineno=42,
            msg="request processed", args=(),
            exc_info=None,
        )
        record.trace_id = "trace-123"
        record.request_id = "req-456"
        record.user_id = 42
        record.req_path = "/api/v1/health"
        record.req_method = "GET"
        record.req_status = 200
        record.latency_ms = 15.3

        output = formatter.format(record)
        data = json.loads(output)
        assert data["trace_id"] == "trace-123"
        assert data["request_id"] == "req-456"
        assert data["user_id"] == 42
        assert data["path"] == "/api/v1/health"
        assert data["method"] == "GET"
        assert data["status"] == 200

    def test_none_fields_omitted(self):
        """Поля с None не включаются в JSON."""
        formatter = JSONLogFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname=__file__, lineno=42,
            msg="no extras", args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        # Основные поля есть
        assert "timestamp" in data
        assert "level" in data
        assert "service" in data
        assert "message" in data
        # None-поля отсутствуют
        assert "trace_id" not in data
        assert "request_id" not in data


class TestPIIMasking:
    """PII-маскировка в логах."""

    def test_mask_password(self):
        """password маскируется."""
        text = '"password":"my_secret_pass"'
        masked = mask_pii_in_text(text)
        assert "my_secret_pass" not in masked
        assert '"password":"***"' in masked

    def test_mask_access_token(self):
        """access_token маскируется."""
        text = '"access_token":"eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"'
        masked = mask_pii_in_text(text)
        assert "eyJhbGci" not in masked
        assert "***" in masked

    def test_mask_refresh_token(self):
        """refresh_token маскируется."""
        text = '"refresh_token":"rftok_abc123"'
        masked = mask_pii_in_text(text)
        assert "rftok_abc123" not in masked
        assert "***" in masked

    def test_multiple_pii_fields_in_one_text(self):
        """Несколько PII-полей в одном тексте маскируются все."""
        text = '"password":"pass1","access_token":"tok1","refresh_token":"rtok1"'
        masked = mask_pii_in_text(text)
        # Ни одно значение не должно быть видно
        assert "pass1" not in masked
        assert "tok1" not in masked
        assert "rtok1" not in masked
        # Счётчик вхождений ***
        assert masked.count("***") == 3

    def test_no_pii_unchanged(self):
        """Текст без PII не изменяется."""
        text = '"status":"ok","message":"hello"'
        masked = mask_pii_in_text(text)
        assert masked == text

    def test_mask_case_insensitive(self):
        """PII-поля маскируются регистронезависимо."""
        text = '"Password":"secret","ACCESS_TOKEN":"eyJ"'
        masked = mask_pii_in_text(text)
        assert "secret" not in masked
        assert "eyJ" not in masked


class TestPIIFilter:
    """PIIFilter не блокирует записи."""

    def test_filter_always_returns_true(self):
        """PIIFilter.filter() всегда возвращает True (не блокирует)."""
        filtr = PIIFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname=__file__, lineno=42,
            msg="test message", args=(),
            exc_info=None,
        )
        assert filtr.filter(record) is True


class TestParsePIIFields:
    """_parse_pii_fields — парсинг из переменной окружения."""

    def test_default_fields(self):
        """Без env возвращает DEFAULT_PII_FIELDS."""
        fields = _parse_pii_fields(None)
        assert fields == DEFAULT_PII_FIELDS

    def test_empty_env(self):
        """Пустая строка env → DEFAULT_PII_FIELDS."""
        fields = _parse_pii_fields("")
        assert fields == DEFAULT_PII_FIELDS

    def test_custom_fields(self):
        """Перечисление полей через запятую."""
        fields = _parse_pii_fields("password,secret,api_key")
        assert fields == {"password", "secret", "api_key"}

    def test_whitespace_trimmed(self):
        """Пробелы вокруг значений обрезаются."""
        fields = _parse_pii_fields(" password , access_token ")
        assert "password" in fields
        assert "access_token" in fields

    def test_lowercase_normalized(self):
        """Значения приводятся к нижнему регистру."""
        fields = _parse_pii_fields("PASSWORD,Access_Token")
        assert "password" in fields
        assert "access_token" in fields


class TestDefaultPIIFields:
    """DEFAULT_PII_FIELDS содержит ожидаемые поля."""

    def test_default_fields_set(self):
        """По умолчанию: password, access_token, refresh_token."""
        assert "password" in DEFAULT_PII_FIELDS
        assert "access_token" in DEFAULT_PII_FIELDS
        assert "refresh_token" in DEFAULT_PII_FIELDS
        assert len(DEFAULT_PII_FIELDS) == 3


class TestSetupLogging:
    """setup_logging() — настройка корневого логгера."""

    def test_setup_logging_uses_env_level(self, monkeypatch):
        """Уровень логирования из GATEWAY_LOG_LEVEL."""
        monkeypatch.setenv("GATEWAY_LOG_LEVEL", "DEBUG")
        setup_logging()
        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_setup_logging_default_level(self):
        """Без env уровень по умолчанию INFO."""
        # Удаляем переменную, если установлена
        if "GATEWAY_LOG_LEVEL" in os.environ:
            del os.environ["GATEWAY_LOG_LEVEL"]
        setup_logging()
        root = logging.getLogger()
        assert root.level == logging.INFO
