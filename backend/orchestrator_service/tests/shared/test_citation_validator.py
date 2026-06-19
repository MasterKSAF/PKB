"""
Tests for citation format validation (P3S-4).

Covers:
  1. Valid [source:N] format
  2. Invalid formats detected
  3. Auto-fix of common issues
  4. Retry + fallback behaviour
"""

import pytest

from app.shared.citation_validator import (
    validate_citation_format,
    extract_source_indices,
    fix_citation_format,
    validate_with_retry,
)


class TestValidateCitationFormat:
    """Tests for validate_citation_format()."""

    def test_no_citations(self):
        """Text without citations is valid."""
        assert validate_citation_format("Просто текст без ссылок") is True

    def test_empty_text(self):
        """Empty text is valid."""
        assert validate_citation_format("") is True
        assert validate_citation_format(None) is True

    def test_valid_single_citation(self):
        """[source:1] is valid."""
        assert validate_citation_format("Согласно [source:1]") is True

    def test_valid_multiple_citations(self):
        """Multiple [source:N] are valid."""
        assert validate_citation_format(
            "По [source:1] и [source:2] и [source:10]"
        ) is True

    def test_valid_range_citation(self):
        """[source:1-3] range is valid."""
        assert validate_citation_format("Согласно [source:1-3]") is True

    def test_invalid_space_after_colon(self):
        """[source: 1] with space is invalid."""
        assert validate_citation_format("[source: 1]") is False

    def test_invalid_lowercase_source(self):
        """[Source:1] wrong case is invalid."""
        assert validate_citation_format("[Source:1]") is False

    def test_invalid_comma_list(self):
        """[source:1,2] comma list is invalid."""
        assert validate_citation_format("[source:1,2]") is False

    def test_invalid_zero_index(self):
        """[source:0] index 0 is invalid."""
        assert validate_citation_format("[source:0]") is False


class TestExtractSourceIndices:
    """Tests for extract_source_indices()."""

    def test_single(self):
        assert extract_source_indices("[source:5]") == [5]

    def test_multiple(self):
        assert extract_source_indices("[source:1] и [source:3]") == [1, 3]

    def test_range(self):
        assert extract_source_indices("[source:1-3]") == [1, 2, 3]

    def test_no_citations(self):
        assert extract_source_indices("просто текст") == []

    def test_sorted_unique(self):
        assert extract_source_indices("[source:3] [source:1] [source:3]") == [1, 3]


class TestFixCitationFormat:
    """Tests for fix_citation_format()."""

    def test_fix_space_after_colon(self):
        """[source: 1] → [source:1]"""
        assert fix_citation_format("[source: 1]") == "[source:1]"

    def test_fix_wrong_case(self):
        """[Source:1] → [source:1]"""
        assert fix_citation_format("[Source:1]") == "[source:1]"
        assert fix_citation_format("[SOURCE:2]") == "[source:2]"

    def test_fix_space_instead_comma(self):
        """[source:1 2] → [source:1], [source:2]"""
        result = fix_citation_format("[source:1 2]")
        assert "[source:1]" in result
        assert "[source:2]" in result

    def test_no_change_for_valid(self):
        """Valid format is unchanged."""
        assert fix_citation_format("[source:42]") == "[source:42]"

    def test_empty(self):
        assert fix_citation_format("") == ""


class TestValidateWithRetry:
    """Tests for validate_with_retry()."""

    def test_valid_passes_immediately(self):
        is_valid, text, was_fixed = validate_with_retry("[source:1]")
        assert is_valid is True
        assert was_fixed is False

    def test_fix_on_second_attempt(self):
        """Space after colon is fixed on first retry."""
        is_valid, text, was_fixed = validate_with_retry("[source: 1]")
        assert is_valid is True
        assert was_fixed is True
        assert text == "[source:1]"

    def test_fix_wrong_case(self):
        is_valid, text, was_fixed = validate_with_retry("[Source:42]")
        assert is_valid is True
        assert was_fixed is True
        assert text == "[source:42]"

    def test_fallback_strips_invalid(self):
        """Unfixable citations are stripped."""
        is_valid, text, was_fixed = validate_with_retry(
            "текст [source:1,2] ещё текст"
        )
        assert is_valid is False
        assert was_fixed is True
        assert "текст" in text
        assert "[source:1,2]" not in text

    def test_empty_text(self):
        is_valid, text, was_fixed = validate_with_retry("")
        assert is_valid is True
        assert was_fixed is False

    def test_custom_max_retries(self):
        """Zero retries means no fix attempts."""
        is_valid, text, was_fixed = validate_with_retry("[source: 1]", max_retries=0)
        assert is_valid is False
        assert was_fixed is True  # fallback stripped
