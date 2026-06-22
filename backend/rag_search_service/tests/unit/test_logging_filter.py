"""Unit-тесты для PIIFilter в logging.py."""

from __future__ import annotations

import logging

from app.core.logging import PIIFilter


class TestPIIFilter:
    """Тесты маскирования PII-данных в логах."""

    def test_masks_matching_keys(self):
        filt = PIIFilter(["password", "token"])
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        record.password = "secret123"
        record.token = "abc"
        record.safe_field = "visible"

        result = filt.filter(record)

        assert result is True
        assert record.password == "***"
        assert record.token == "***"
        assert record.safe_field == "visible"

    def test_case_insensitive_matching(self):
        filt = PIIFilter(["password"])
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        record.Password = "secret"
        record.PASSWORD = "secret2"
        setattr(record, "password_field", "secret3")

        filt.filter(record)

        assert record.Password == "***"
        assert record.PASSWORD == "***"

    def test_no_matching_keys_unchanged(self):
        filt = PIIFilter(["password"])
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        record.username = "admin"
        record.query = "test query"

        filt.filter(record)

        assert record.username == "admin"
        assert record.query == "test query"

    def test_empty_pii_list_no_masking(self):
        filt = PIIFilter([])
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        record.password = "secret"

        filt.filter(record)

        assert record.password == "secret"

    def test_masks_pii_in_dict_msg(self):
        filt = PIIFilter(["password"])
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg={"password": "secret123", "user": "admin"},
            args=(),
            exc_info=None,
        )

        filt.filter(record)

        assert record.msg["password"] == "***"
        assert record.msg["user"] == "admin"

    def test_string_msg_not_affected(self):
        filt = PIIFilter(["password"])
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="password is secret",
            args=(),
            exc_info=None,
        )

        filt.filter(record)

        assert record.msg == "password is secret"
