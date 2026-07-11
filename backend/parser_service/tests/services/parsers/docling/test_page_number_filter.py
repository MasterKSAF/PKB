"""
Tests for page number filtering.

Two-stage defense:
1. enrich_docling_document (PyMuPDF) — не даёт номерам попасть в DoclingDocument
2. html_to_document_json (финальный) — отлавливает то, что уже было в Docling
"""
import re
import sys
from pathlib import Path

_docling_dir = Path(__file__).parent.parent.parent.parent / "app" / "services" / "parsers" / "docling"
sys.path.insert(0, str(_docling_dir))

from html_to_json import html_to_document_json


def _page(*blocks: str) -> str:
    return "<html><body><div class=\"page\">" + "".join(blocks) + "</div></body></html>"


def _block(text: str, tag: str = "p") -> str:
    return f"<{tag}>{text}</{tag}>"


# --- enrich regex (такой же как в docling_mapper.py) ---
ENRICH_RE = re.compile(r'^[\d\s\-—\/]+$')

def test_enrich_filter_standalone_number():
    assert ENRICH_RE.match('105')
def test_enrich_filter_em_dash_wrapped():
    assert ENRICH_RE.match('\u2014 5 \u2014')
def test_enrich_filter_slash_range():
    assert ENRICH_RE.match('5 / 15')
def test_enrich_filter_multi_digit():
    assert ENRICH_RE.match('15 / 15')
def test_enrich_filter_section_number_survives():
    assert not ENRICH_RE.match('1.2')
def test_enrich_filter_classification_code_survives():
    assert not ENRICH_RE.match('2123.234234.1')
def test_enrich_filter_text_survives():
    assert not ENRICH_RE.match('1.2 ОПРЕДЕЛЕНИЯ И ПОЯСНЕНИЯ')


# --- html_to_json final filter ---
# Имитируем то, что может выдать Docling: page number как параграф

def test_final_filter_removes_bare_number():
    result = html_to_document_json([(1, _page(_block("3")))], "test.pdf")
    assert len(result["content"]["document"]["block"]) == 0, "3 should be filtered"


def test_final_filter_removes_em_dash_number():
    result = html_to_document_json([(1, _page(_block("\u2014 5 \u2014")))], "test.pdf")
    assert len(result["content"]["document"]["block"]) == 0


def test_final_filter_removes_slash_range():
    result = html_to_document_json([(1, _page(_block("5 / 15")))], "test.pdf")
    assert len(result["content"]["document"]["block"]) == 0


def test_final_filter_keeps_section_number():
    result = html_to_document_json([(1, _page(_block("1.2", "h1")))], "test.pdf")
    assert len(result["content"]["document"]["block"]) == 1
    assert result["content"]["document"]["block"][0]["content"] == "1.2"


def test_final_filter_keeps_classification_code():
    result = html_to_document_json([(1, _page(_block("2123.234234.1")))], "test.pdf")
    assert len(result["content"]["document"]["block"]) == 1


def test_final_filter_keeps_text():
    result = html_to_document_json([(1, _page(_block("\u041f\u0415\u0420\u0415\u0427\u0415\u041d\u042c \u0418\u0417\u041c\u0415\u041d\u0415\u041d\u0418\u0419 1", "h1")))], "test.pdf")
    assert len(result["content"]["document"]["block"]) == 1


def test_scenario_realistic():
    """Точное воспроизведение проблемы: page number 5 между двумя заголовками."""
    html = _page(
        _block("\u041f\u0415\u0420\u0415\u0427\u0415\u041d\u042c \u0418\u0417\u041c\u0415\u041d\u0415\u041d\u0418\u0419 1", "h1"),
        _block("5"),
        _block("1.2 \u041e\u041f\u0420\u0415\u0414\u0415\u041b\u0415\u041d\u0418\u042f", "h1"),
    )
    result = html_to_document_json([(1, html)], "test.pdf")
    blocks = result["content"]["document"]["block"]
    assert len(blocks) == 2, f"Expected 2 blocks, got {len(blocks)}: {[b['content'] for b in blocks]}"
    assert "\u041f\u0415\u0420\u0415\u0427\u0415\u041d\u042c" in blocks[0]["content"]
    assert "\u041e\u041f\u0420\u0415\u0414\u0415\u041b\u0415\u041d\u0418\u042f" in blocks[1]["content"]


def test_scenario_two_pages():
    """Page number 3 на стр.1 и page number 5 на стр.2 — оба должны быть отфильтрованы."""
    html = _page(_block("3"))
    html2 = _page(
        _block("\u041f\u0415\u0420\u0415\u0427\u0415\u041d\u042c \u0418\u0417\u041c\u0415\u041d\u0415\u041d\u0418\u0419 1", "h1"),
        _block("5"),
        _block("1.2 \u041e\u041f\u0420\u0415\u0414\u0415\u041b\u0415\u041d\u0418\u042f", "h1"),
    )
    result = html_to_document_json([(1, html), (2, html2)], "test.pdf")
    blocks = result["content"]["document"]["block"]
    assert len(blocks) == 2, f"Expected 2 blocks, got {len(blocks)}: {[b['content'] for b in blocks]}"


if __name__ == "__main__":
    tests = [
        test_enrich_filter_standalone_number,
        test_enrich_filter_em_dash_wrapped,
        test_enrich_filter_slash_range,
        test_enrich_filter_multi_digit,
        test_enrich_filter_section_number_survives,
        test_enrich_filter_classification_code_survives,
        test_enrich_filter_text_survives,
        test_final_filter_removes_bare_number,
        test_final_filter_removes_em_dash_number,
        test_final_filter_removes_slash_range,
        test_final_filter_keeps_section_number,
        test_final_filter_keeps_classification_code,
        test_final_filter_keeps_text,
        test_scenario_realistic,
        test_scenario_two_pages,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{passed}/{len(tests)} passed")
