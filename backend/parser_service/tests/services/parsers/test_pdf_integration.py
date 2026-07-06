import re
import sys
from pathlib import Path

import fitz
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "app" / "services" / "parsers" / "docling"))
from text_cleaner import process_extracted_text

PDF_DIR = Path(__file__).resolve().parent.parent.parent.parent / "pdf"


def _extract_text(pdf_name: str) -> str:
    path = PDF_DIR / pdf_name
    if not path.exists():
        pytest.skip(f"PDF not found: {path}")
    doc = fitz.open(str(path))
    lines = []
    for pno in range(doc.page_count):
        lines.append(doc[pno].get_text("text", sort=True))
    doc.close()
    return "\n".join(lines)


class TestPdf013GrainCarriage:
    """2-020101-013 — Правила перевозки зерна (39 pages)."""

    @pytest.fixture(scope="class")
    def raw_text(self):
        return _extract_text("2-020101-013.pdf")

    @pytest.fixture(scope="class")
    def cleaned_text(self, raw_text):
        return process_extracted_text(raw_text)

    def test_preserves_document_number(self, cleaned_text):
        assert "2-020101-013" in cleaned_text

    def test_preserves_title(self, cleaned_text):
        assert "ПРАВИЛА ПЕРЕВОЗКИ ЗЕРНА" in cleaned_text

    def test_preserves_russian_body(self, cleaned_text):
        assert "Правил перевозки зерна" in cleaned_text
        assert "морского регистра судоходства" in cleaned_text

    def test_filters_single_digit_page_numbers(self, raw_text, cleaned_text):
        has_single_digit = any(re.fullmatch(r"\d+", l.strip()) for l in raw_text.split("\n") if l.strip())
        assert has_single_digit
        assert not any(re.fullmatch(r"\d+", l.strip()) for l in cleaned_text.split("\n") if l.strip())

    def test_kept_vs_filtered_ratio(self, raw_text, cleaned_text):
        raw_count = len([l for l in raw_text.split("\n") if l.strip()])
        cleaned_count = len([l for l in cleaned_text.split("\n") if l.strip()])
        assert cleaned_count >= raw_count * 0.5
        assert cleaned_count >= raw_count * 0.80

    def test_column_sort_enabled(self):
        doc = fitz.open(str(PDF_DIR / "2-020101-013.pdf"))
        page = doc[0]
        blocks = page.get_text("dict", sort=True)["blocks"]
        doc.close()
        assert len(blocks) > 0


class TestPdf174Refrigerating:
    """2-020101-174-12 — Холодильные установки (Часть XII) (41 page)."""

    @pytest.fixture(scope="class")
    def raw_text(self):
        return _extract_text("2-020101-174-12.pdf")

    @pytest.fixture(scope="class")
    def cleaned_text(self, raw_text):
        return process_extracted_text(raw_text)

    def test_preserves_document_number(self, cleaned_text):
        assert "2-020101-174" in cleaned_text

    def test_preserves_section_title(self, cleaned_text):
        assert "ХОЛОДИЛЬНЫЕ УСТАНОВКИ" in cleaned_text

    def test_preserves_classification_rules(self, cleaned_text):
        assert "КЛАССИФИКАЦИИ И ПОСТРОЙКИ" in cleaned_text

    def test_filters_single_digit_page_numbers(self, raw_text, cleaned_text):
        has_single_digit = any(re.fullmatch(r"\d+", l.strip()) for l in raw_text.split("\n") if l.strip())
        assert has_single_digit
        assert not any(re.fullmatch(r"\d+", l.strip()) for l in cleaned_text.split("\n") if l.strip())

    def test_kept_vs_filtered_ratio(self, raw_text, cleaned_text):
        raw_count = len([l for l in raw_text.split("\n") if l.strip()])
        cleaned_count = len([l for l in cleaned_text.split("\n") if l.strip()])
        assert cleaned_count >= raw_count * 0.5
        assert cleaned_count >= raw_count * 0.85
