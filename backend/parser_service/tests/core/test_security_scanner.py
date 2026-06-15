import pytest
from app.core.security_scanner import SecurityScanner

def test_dangerous_keys_detection():
    data = b"/JS 1 0 R"
    is_safe, msg = SecurityScanner.scan_pdf(data, "test.pdf", "", 10000, False, False)
    assert not is_safe
    assert "JS" in msg

def test_jbig2_not_rejected_by_default():
    data = b"/JBIG2Decode"
    is_safe, msg = SecurityScanner.scan_pdf(data, "test.pdf", "", 10000, False, False)
    assert is_safe is True
    assert msg is None

def test_jbig2_rejected_when_flag_true():
    data = b"/JBIG2Decode"
    is_safe, msg = SecurityScanner.scan_pdf(data, "test.pdf", "", 10000, True, False)
    assert not is_safe
    assert "JBIG2Decode" in msg

def test_unicode_filename():
    dangerous = "file\u202E.pdf"
    is_safe, msg = SecurityScanner.scan_pdf(b"", dangerous, "", 10000, False, False)
    assert not is_safe
    assert "Unicode" in msg

def test_large_file_only_logs():
    data = b"x" * (20 * 1024 * 1024)  # 20 MB > max_font_stream (10 MB)
    is_safe, msg = SecurityScanner.scan_pdf(data, "big.pdf", "", 10_000_000, False, False)
    assert is_safe is True
    assert msg is None