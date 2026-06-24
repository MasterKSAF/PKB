"""
Тесты для модуля безопасности PDF (security_scanner.py).
"""
import pytest
from app.core.security_scanner import SecurityScanner


def test_dangerous_keys_detection():
    """Обнаружение опасных ключей с блокировкой."""
    data = b"/JS 1 0 R"
    is_safe, msg = SecurityScanner.scan_pdf(
        data, "test.pdf",
        yara_rules_path="",
        max_font_stream=10000,
        reject_jbig2=False,
        enable_yara=False,
        block_on_unicode=False,
        block_on_jbig2=False,
        block_on_dangerous_keys=True,
        block_on_yara=False
    )
    assert not is_safe
    assert "JS" in msg


def test_jbig2_not_rejected_by_default():
    """JBIG2 не блокируется по умолчанию."""
    data = b"/JBIG2Decode"
    is_safe, msg = SecurityScanner.scan_pdf(
        data, "test.pdf",
        yara_rules_path="",
        max_font_stream=10000,
        reject_jbig2=False,
        enable_yara=False,
        block_on_unicode=False,
        block_on_jbig2=False,
        block_on_dangerous_keys=False,
        block_on_yara=False
    )
    assert is_safe is True
    assert msg is None


def test_jbig2_rejected_when_flag_true():
    """JBIG2 блокируется при включённом флаге."""
    data = b"/JBIG2Decode"
    is_safe, msg = SecurityScanner.scan_pdf(
        data, "test.pdf",
        yara_rules_path="",
        max_font_stream=10000,
        reject_jbig2=True,
        enable_yara=False,
        block_on_unicode=False,
        block_on_jbig2=True,
        block_on_dangerous_keys=False,
        block_on_yara=False
    )
    assert not is_safe
    assert "JBIG2Decode" in msg


def test_unicode_filename():
    """Обнаружение Unicode-маскировки."""
    dangerous = "file\u202E.pdf"
    is_safe, msg = SecurityScanner.scan_pdf(
        b"", dangerous,
        yara_rules_path="",
        max_font_stream=10000,
        reject_jbig2=False,
        enable_yara=False,
        block_on_unicode=True,
        block_on_jbig2=False,
        block_on_dangerous_keys=False,
        block_on_yara=False
    )
    assert not is_safe
    assert "Unicode" in msg


def test_large_file_only_logs():
    """Большой файл только логируется, но не блокируется."""
    data = b"x" * (20 * 1024 * 1024)  # 20 MB > max_font_stream (10 MB)
    is_safe, msg = SecurityScanner.scan_pdf(
        data, "big.pdf",
        yara_rules_path="",
        max_font_stream=10_000_000,
        reject_jbig2=False,
        enable_yara=False,
        block_on_unicode=False,
        block_on_jbig2=False,
        block_on_dangerous_keys=False,
        block_on_yara=False
    )
    assert is_safe is True
    assert msg is None