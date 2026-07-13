"""
Tests for formula block extraction and regex fallback.

Two paths to formula blocks:
1. Direct: Docling returns <figure class="formula"> — parser emits type: "formula"
2. Regex fallback: paragraphs with $..$, $$..$$, \\(..\\) retyped to formula
"""
import sys
from pathlib import Path

_docling_dir = Path(__file__).parent.parent.parent.parent.parent / "app" / "services" / "parsers" / "docling"
sys.path.insert(0, str(_docling_dir))

from html_to_json import html_to_document_json


def _page(*blocks: str) -> str:
    return "<html><body><div class=\"page\">" + "".join(blocks) + "</div></body></html>"


def p(text: str) -> str:
    return f"<p>{text}</p>"


def h1(text: str) -> str:
    return f"<h1>{text}</h1>"


def formula_figure(latex: str, caption: str = "") -> str:
    cap = f"<figcaption>{caption}</figcaption>" if caption else ""
    return f'<figure class="formula"><span>{latex}</span>{cap}</figure>'


# --- Direct: <figure class="formula"> from Docling ---

def test_direct_formula_figure():
    html = _page(formula_figure("E = mc^2"))
    result = html_to_document_json([(1, html)], "test.pdf")
    blocks = result["content"]["document"]["block"]
    assert len(blocks) == 1
    assert blocks[0]["type"] == "formula"
    assert "E = mc^2" in blocks[0]["content"]


def test_direct_formula_with_caption():
    html = _page(formula_figure("\\frac{a}{b}", caption="Equation 1"))
    result = html_to_document_json([(1, html)], "test.pdf")
    blocks = result["content"]["document"]["block"]
    assert len(blocks) == 1
    assert blocks[0]["type"] == "formula"
    # Content — LaTeX (изнутри <figure>), не caption
    assert "frac" in blocks[0]["content"]


def test_direct_formula_among_other_blocks():
    html = _page(
        h1("Section 1"),
        p("Some text"),
        formula_figure("F = ma"),
        p("More text"),
    )
    result = html_to_document_json([(1, html)], "test.pdf")
    blocks = result["content"]["document"]["block"]
    formula = [b for b in blocks if b["type"] == "formula"]
    assert len(formula) == 1
    assert "F = ma" in formula[0]["content"]


# --- Regex fallback: LaTeX in paragraphs ---

def test_regex_fallback_dollar_inline():
    html = _page(p("Formula $a^2 + b^2 = c^2$ inline"))
    result = html_to_document_json([(1, html)], "test.pdf")
    blocks = result["content"]["document"]["block"]
    assert len(blocks) == 1
    assert blocks[0]["type"] == "formula"


def test_regex_fallback_dollar_display():
    html = _page(p("$$\\int_{0}^{\\infty} e^{-x} dx$$"))
    result = html_to_document_json([(1, html)], "test.pdf")
    blocks = result["content"]["document"]["block"]
    assert len(blocks) == 1
    assert blocks[0]["type"] == "formula"


def test_regex_fallback_paren_inline():
    html = _page(p("Formula \\(E = h\\nu\\) inline"))
    result = html_to_document_json([(1, html)], "test.pdf")
    blocks = result["content"]["document"]["block"]
    assert len(blocks) == 1
    assert blocks[0]["type"] == "formula"


def test_regex_fallback_bracket_display():
    html = _page(p("\\[\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}\\]"))
    result = html_to_document_json([(1, html)], "test.pdf")
    blocks = result["content"]["document"]["block"]
    assert len(blocks) == 1
    assert blocks[0]["type"] == "formula"


def test_regex_fallback_does_not_affect_regular_text():
    html = _page(p("This is normal text without formulas."))
    result = html_to_document_json([(1, html)], "test.pdf")
    blocks = result["content"]["document"]["block"]
    assert len(blocks) == 1
    assert blocks[0]["type"] == "paragraph"


def test_regex_fallback_does_not_affect_heading():
    html = _page(h1("Section 1 with $x$"))
    result = html_to_document_json([(1, html)], "test.pdf")
    blocks = result["content"]["document"]["block"]
    assert len(blocks) == 1
    assert blocks[0]["type"] == "heading"
    assert blocks[0]["heading level"] == 1


# --- Mixed: direct formula + regex fallback ---

def test_mixed_direct_and_regex():
    html = _page(
        formula_figure("\\alpha + \\beta = \\gamma"),
        p("Some explanation"),
        p("With inline $x$ formula"),
    )
    result = html_to_document_json([(1, html)], "test.pdf")
    blocks = result["content"]["document"]["block"]
    formula_blocks = [b for b in blocks if b["type"] == "formula"]
    assert len(formula_blocks) == 2
    para_blocks = [b for b in blocks if b["type"] == "paragraph"]
    assert len(para_blocks) == 1


if __name__ == "__main__":
    tests = [
        test_direct_formula_figure,
        test_direct_formula_with_caption,
        test_direct_formula_among_other_blocks,
        test_regex_fallback_dollar_inline,
        test_regex_fallback_dollar_display,
        test_regex_fallback_paren_inline,
        test_regex_fallback_bracket_display,
        test_regex_fallback_does_not_affect_regular_text,
        test_regex_fallback_does_not_affect_heading,
        test_mixed_direct_and_regex,
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
