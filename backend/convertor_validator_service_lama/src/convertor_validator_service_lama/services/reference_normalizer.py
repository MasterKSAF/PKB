from __future__ import annotations

import re


_GOST_RANGE_RE = re.compile(
    r"(?P<prefix>\b(?:\u0413\u041e\u0421\u0422|GOST))\s*"
    r"(?P<start_number>\d{1,6})\s*[-\u2013\u2014]\s*(?P<start_year>\d{2,4})\s*"
    r"[-\u2013\u2014]\s*"
    r"(?:(?:\u0413\u041e\u0421\u0422|GOST)\s*)?"
    r"(?P<end_number>\d{1,6})\s*[-\u2013\u2014]\s*(?P<end_year>\d{2,4})",
    re.IGNORECASE,
)

_GOST_SINGLE_RE = re.compile(
    r"(?P<prefix>\b(?:\u0413\u041e\u0421\u0422|GOST))\s*"
    r"(?P<number>\d{1,6})\s*[-\u2013\u2014]\s*(?P<year>\d{2,4})",
    re.IGNORECASE,
)

_MAX_RANGE_WIDTH = 100


def expand_gost_document_codes(text: str | None) -> list[str]:
    if not text:
        return []

    result: list[str] = []
    covered_spans: list[tuple[int, int]] = []

    for match in _GOST_RANGE_RE.finditer(text):
        covered_spans.append(match.span())

        prefix = _canonical_prefix(match.group("prefix"))
        start_number = int(match.group("start_number"))
        end_number = int(match.group("end_number"))
        start_year = match.group("start_year")
        end_year = match.group("end_year")

        if start_year != end_year:
            result.extend(
                [
                    _format_gost_code(prefix, start_number, start_year),
                    _format_gost_code(prefix, end_number, end_year),
                ]
            )
            continue

        if end_number < start_number or end_number - start_number > _MAX_RANGE_WIDTH:
            result.extend(
                [
                    _format_gost_code(prefix, start_number, start_year),
                    _format_gost_code(prefix, end_number, end_year),
                ]
            )
            continue

        for number in range(start_number, end_number + 1):
            result.append(_format_gost_code(prefix, number, start_year))

    for match in _GOST_SINGLE_RE.finditer(text):
        if _is_inside_any_span(match.start(), covered_spans):
            continue

        result.append(
            _format_gost_code(
                _canonical_prefix(match.group("prefix")),
                int(match.group("number")),
                match.group("year"),
            )
        )

    return _deduplicate_preserving_order(result)



def expand_gost_document_codes_from_values(*values: str | None) -> list[str]:
    result: list[str] = []

    for value in values:
        result.extend(expand_gost_document_codes(value))

    return _deduplicate_preserving_order(result)


def _canonical_prefix(prefix: str) -> str:
    if prefix.upper() == "GOST":
        return "GOST"

    return "\u0413\u041e\u0421\u0422"


def _format_gost_code(prefix: str, number: int, year: str) -> str:
    return f"{prefix} {number}-{year}"


def _is_inside_any_span(position: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= position < end for start, end in spans)


def _deduplicate_preserving_order(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        if value in seen:
            continue

        result.append(value)
        seen.add(value)

    return result


def document_codes_equal(left: str | None, right: str | None) -> bool:
    left_identity = normalize_document_code_identity(left)
    right_identity = normalize_document_code_identity(right)

    return (
        left_identity is not None
        and right_identity is not None
        and left_identity == right_identity
    )


def normalize_document_code_identity(value: str | None) -> str | None:
    if not value:
        return None

    result = value.strip().upper()
    if not result:
        return None

    result = result.replace("\u0413\u041e\u0421\u0422", "GOST")
    result = result.replace("\u2013", "-").replace("\u2014", "-")
    result = re.sub(r"\s+", " ", result)
    result = re.sub(r"\s*-\s*", "-", result)
    return result
