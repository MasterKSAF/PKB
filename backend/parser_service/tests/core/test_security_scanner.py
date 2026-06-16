import pytest
import app.core.security_scanner as security_scanner

# Сохраняем исходные значения глобальных переключателей (на случай, если они изменены)
_orig_unicode = security_scanner.BLOCK_ON_UNICODE_CHECK
_orig_jbig2 = security_scanner.BLOCK_ON_JBIG2_CHECK
_orig_dangerous = security_scanner.BLOCK_ON_DANGEROUS_KEYS
_orig_yara = security_scanner.BLOCK_ON_YARA


def test_dangerous_keys_detection():
    # Включаем блокировку на опасные ключи
    security_scanner.BLOCK_ON_DANGEROUS_KEYS = True
    try:
        data = b"/JS 1 0 R"
        is_safe, msg = security_scanner.SecurityScanner.scan_pdf(data, "test.pdf", "", 10000, False, False)
        assert not is_safe
        assert "JS" in msg
    finally:
        security_scanner.BLOCK_ON_DANGEROUS_KEYS = _orig_dangerous


def test_jbig2_not_rejected_by_default():
    # При выключенной блокировке и reject_jbig2=False — файл безопасен
    data = b"/JBIG2Decode"
    is_safe, msg = security_scanner.SecurityScanner.scan_pdf(data, "test.pdf", "", 10000, False, False)
    assert is_safe is True
    assert msg is None


def test_jbig2_rejected_when_flag_true():
    # Включаем блокировку JBIG2 и передаём reject_jbig2=True
    security_scanner.BLOCK_ON_JBIG2_CHECK = True
    try:
        data = b"/JBIG2Decode"
        is_safe, msg = security_scanner.SecurityScanner.scan_pdf(data, "test.pdf", "", 10000, True, False)
        assert not is_safe
        assert "JBIG2Decode" in msg
    finally:
        security_scanner.BLOCK_ON_JBIG2_CHECK = _orig_jbig2


def test_unicode_filename():
    # Включаем блокировку на Unicode-маскировку
    security_scanner.BLOCK_ON_UNICODE_CHECK = True
    try:
        dangerous = "file\u202E.pdf"
        is_safe, msg = security_scanner.SecurityScanner.scan_pdf(b"", dangerous, "", 10000, False, False)
        assert not is_safe
        assert "Unicode" in msg
    finally:
        security_scanner.BLOCK_ON_UNICODE_CHECK = _orig_unicode


def test_large_file_only_logs():
    # Большой файл никогда не блокируется (только лог)
    data = b"x" * (20 * 1024 * 1024)  # 20 MB > max_font_stream (10 MB)
    is_safe, msg = security_scanner.SecurityScanner.scan_pdf(data, "big.pdf", "", 10_000_000, False, False)
    assert is_safe is True
    assert msg is None