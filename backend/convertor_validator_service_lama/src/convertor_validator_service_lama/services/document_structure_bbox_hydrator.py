from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
import re
from typing import Any

from convertor_validator_service_lama.models.document_structure_extraction import (
    DocumentStructureExtraction,
    ParseItemSpan,
)


_SPACE_RE = re.compile(r"\s+")
_WORD_RE = re.compile(r"\w+", re.UNICODE)
_CLAUSE_RE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)*)\s*[.)]?")


@dataclass
class DocumentStructureBboxHydrationResult:
    extraction: DocumentStructureExtraction
    diagnostics: dict[str, Any] = field(default_factory=dict)


def hydrate_document_structure_extraction_source_spans_from_parse_items(
    extraction: DocumentStructureExtraction,
    parse_items: list[dict[str, Any]],
) -> DocumentStructureBboxHydrationResult:
    """Fill missing source-span bboxes from deterministic LlamaParse items.

    LlamaExtract decides document structure. LlamaParse remains the source of
    truth for geometry. We first try LlamaExtract source_span.item_index. If a
    section still has no usable bbox, we recover by locating the parse item that
    starts with the section clause number.
    """

    hydrated = extraction.model_copy(deep=True)
    indexed_items = _index_parse_items(parse_items)

    diagnostics = {
        "source": "llama_parse_effective_items",
        "parse_items_count": len(parse_items),
        "indexed_parse_items_count": len(indexed_items.by_index),
        "spans_seen": 0,
        "spans_hydrated": 0,
        "spans_already_had_bbox": 0,
        "spans_missing_item_index": 0,
        "spans_missing_parse_item": 0,
        "spans_page_mismatch": 0,
        "spans_text_mismatch": 0,
        "spans_clause_mismatch": 0,
        "spans_missing_parse_bbox": 0,
        "spans_hydrated_from_nested_list_item": 0,
        "sections_seen": 0,
        "sections_with_bbox_after_direct_hydration": 0,
        "sections_hydrated_by_clause_fallback": 0,
        "sections_preferred_clause_fallback": 0,
        "sections_missing_clause_fallback": 0,
        "spans_replaced_by_clause_fallback": 0,
        "spans_added_by_clause_fallback": 0,
    }

    for classification in hydrated.item_classifications:
        if classification.source_span is not None:
            _hydrate_span(
                classification.source_span,
                indexed_items=indexed_items,
                diagnostics=diagnostics,
            )

    for section in hydrated.sections:
        diagnostics["sections_seen"] += 1

        for span in section.source_spans:
            _hydrate_span(
                span,
                indexed_items=indexed_items,
                diagnostics=diagnostics,
                expected_clause=section.clause,
            )

        direct_has_bbox = _section_has_hydrated_bbox(section.source_spans)

        if direct_has_bbox:
            diagnostics["sections_with_bbox_after_direct_hydration"] += 1

            if _section_has_clause_primary_bbox(
                section.source_spans,
                section.clause,
            ):
                continue

        fallback_span = _build_clause_fallback_span(
            section.clause,
            indexed_items=indexed_items,
        )

        if fallback_span is not None:
            _hydrate_span(
                fallback_span,
                indexed_items=indexed_items,
                diagnostics=diagnostics,
                expected_clause=section.clause,
            )

        fallback_has_bbox = (
            fallback_span is not None
            and (
                fallback_span.bbox is not None
                or fallback_span.normalized_bbox is not None
            )
        )

        if direct_has_bbox:
            if fallback_has_bbox:
                _make_clause_span_primary(
                    section.source_spans,
                    fallback_span,
                )
                diagnostics["sections_preferred_clause_fallback"] += 1

            continue

        if not fallback_has_bbox:
            diagnostics["sections_missing_clause_fallback"] += 1
            continue

        if section.source_spans:
            section.source_spans = [fallback_span]
            diagnostics["spans_replaced_by_clause_fallback"] += 1
        else:
            section.source_spans.append(fallback_span)
            diagnostics["spans_added_by_clause_fallback"] += 1

        diagnostics["sections_hydrated_by_clause_fallback"] += 1

    return DocumentStructureBboxHydrationResult(
        extraction=hydrated,
        diagnostics=diagnostics,
    )


@dataclass(frozen=True)
class _IndexedParseItems:
    by_index: dict[int, dict[str, Any]]
    positions_by_item_id: dict[int, int]
    parse_items: list[dict[str, Any]]


def _hydrate_span(
    span: ParseItemSpan,
    *,
    indexed_items: _IndexedParseItems,
    diagnostics: dict[str, Any],
    expected_clause: str | None = None,
) -> None:
    diagnostics["spans_seen"] += 1

    if span.bbox is not None and span.normalized_bbox is not None:
        diagnostics["spans_already_had_bbox"] += 1
        return

    if span.item_index is None:
        diagnostics["spans_missing_item_index"] += 1
        return

    parse_item = indexed_items.by_index.get(span.item_index)

    if parse_item is None:
        diagnostics["spans_missing_parse_item"] += 1
        return

    parse_page = _file_page_number_from_item(parse_item)

    if span.page is not None and parse_page is not None and span.page != parse_page:
        diagnostics["spans_page_mismatch"] += 1
        return

    if not _text_preview_matches_parse_item(span.text_preview, parse_item):
        diagnostics["spans_text_mismatch"] += 1
        return

    if not _span_clause_matches_expected_clause(
        span.text_preview,
        expected_clause,
    ):
        diagnostics["spans_clause_mismatch"] += 1
        return

    nested_clause_item = _nested_list_item_for_clause(
        parse_item,
        expected_clause,
    )

    if nested_clause_item is not None:
        bbox = _bbox_from_parse_item(nested_clause_item)
        normalized_bbox = _normalized_bbox_from_parse_item(nested_clause_item)
        diagnostics["spans_hydrated_from_nested_list_item"] += 1
    else:
        bbox = _bbox_from_parse_item(parse_item)
        normalized_bbox = _normalized_bbox_from_parse_item(parse_item)

    if normalized_bbox is None:
        page_width = _first_number(
            nested_clause_item.get("page_width") if nested_clause_item else None,
            parse_item.get("page_width"),
        )
        page_height = _first_number(
            nested_clause_item.get("page_height") if nested_clause_item else None,
            parse_item.get("page_height"),
        )
        normalized_bbox = _normalize_bbox(
            bbox,
            page_width=page_width,
            page_height=page_height,
        )

    if bbox is None and normalized_bbox is None:
        diagnostics["spans_missing_parse_bbox"] += 1
        return

    if span.page is None and parse_page is not None:
        span.page = parse_page

    if span.file_page_number is None and parse_page is not None:
        span.file_page_number = parse_page

    if span.file_page_index is None:
        span.file_page_index = _file_page_index_from_item(parse_item)

    if span.printed_page_label is None:
        span.printed_page_label = _printed_page_label_from_item(parse_item)

    if span.bbox is None and bbox is not None:
        span.bbox = bbox

    if span.normalized_bbox is None and normalized_bbox is not None:
        span.normalized_bbox = normalized_bbox

    diagnostics["spans_hydrated"] += 1


def _index_parse_items(parse_items: list[dict[str, Any]]) -> _IndexedParseItems:
    by_index: dict[int, dict[str, Any]] = {}
    positions_by_item_id: dict[int, int] = {}
    clean_items: list[dict[str, Any]] = []

    for position, item in enumerate(parse_items):
        if not isinstance(item, dict):
            continue

        clean_items.append(item)

        candidate_index = _first_int(
            item.get("_source_item_index"),
            item.get("item_index"),
        )

        if candidate_index is not None:
            by_index.setdefault(candidate_index, item)
            positions_by_item_id[id(item)] = candidate_index

        by_index.setdefault(position, item)
        positions_by_item_id.setdefault(id(item), position)

    return _IndexedParseItems(
        by_index=by_index,
        positions_by_item_id=positions_by_item_id,
        parse_items=clean_items,
    )


def _section_has_hydrated_bbox(source_spans: list[ParseItemSpan]) -> bool:
    return any(
        span.bbox is not None or span.normalized_bbox is not None
        for span in source_spans
    )


def _section_has_clause_primary_bbox(
    source_spans: list[ParseItemSpan],
    clause: str | None,
) -> bool:
    for span in source_spans:
        if span.bbox is None and span.normalized_bbox is None:
            continue

        if _span_text_starts_with_clause(span.text_preview, clause):
            return True

    return False


def _make_clause_span_primary(
    source_spans: list[ParseItemSpan],
    fallback_span: ParseItemSpan,
) -> None:
    retained_spans: list[ParseItemSpan] = []

    for span in source_spans:
        if span.item_index == fallback_span.item_index:
            continue

        if span.bbox is None and span.normalized_bbox is None:
            continue

        retained_spans.append(span)

    source_spans[:] = [fallback_span, *retained_spans]


def _span_text_starts_with_clause(
    text_preview: str | None,
    clause: str | None,
) -> bool:
    normalized_clause = _normalize_clause(clause or "")

    if not normalized_clause:
        return False

    if not text_preview or not text_preview.strip():
        return False

    return _leading_clause(_normalize_text(text_preview)) == normalized_clause


def _build_clause_fallback_span(
    clause: str | None,
    *,
    indexed_items: _IndexedParseItems,
) -> ParseItemSpan | None:
    parse_item = _find_parse_item_by_leading_clause(
        clause,
        indexed_items.parse_items,
    )

    if parse_item is None:
        return None

    item_index = indexed_items.positions_by_item_id.get(id(parse_item))

    if item_index is None:
        return None

    text = _extract_item_text(parse_item)

    file_page_number = _file_page_number_from_item(parse_item)

    return ParseItemSpan(
        page=file_page_number,
        file_page_number=file_page_number,
        file_page_index=_file_page_index_from_item(parse_item),
        printed_page_label=_printed_page_label_from_item(parse_item),
        item_index=item_index,
        text_preview=_compact_text(text, limit=500),
    )


def _find_parse_item_by_leading_clause(
    clause: str | None,
    parse_items: list[dict[str, Any]],
) -> dict[str, Any] | None:
    normalized_clause = _normalize_clause(clause or "")

    if not normalized_clause:
        return None

    for item in parse_items:
        text = _extract_item_text(item)
        leading_clause = _leading_clause(_normalize_text(text))

        if leading_clause != normalized_clause:
            continue

        if _bbox_from_parse_item(item) is not None:
            return item

        if _normalized_bbox_from_parse_item(item) is not None:
            return item

    return None


def _nested_list_item_for_clause(
    parse_item: dict[str, Any],
    expected_clause: str | None,
) -> dict[str, Any] | None:
    normalized_clause = _normalize_clause(expected_clause or "")

    if not normalized_clause:
        return None

    nested_items = parse_item.get("items")

    if not isinstance(nested_items, list) or not nested_items:
        return None

    clause_segments = _clause_text_segments(_extract_item_text(parse_item))

    if len(clause_segments) != len(nested_items):
        return None

    for index, segment in enumerate(clause_segments):
        if segment.clause != normalized_clause:
            continue

        nested_item = nested_items[index]

        if not isinstance(nested_item, dict):
            return None

        if _bbox_from_parse_item(nested_item) is None:
            return None

        return _inherit_page_geometry(
            nested_item,
            parse_item,
        )

    return None


@dataclass(frozen=True)
class _ClauseTextSegment:
    clause: str
    text: str
    start: int
    end: int


def _clause_text_segments(text: str) -> list[_ClauseTextSegment]:
    if not text or not text.strip():
        return []

    matches = list(
        re.finditer(
            r"(?m)(?:^|\n)\s*([0-9]+(?:\.[0-9]+)*)\s*[.)]\s+",
            text,
        )
    )

    if not matches:
        return []

    segments: list[_ClauseTextSegment] = []

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        segment_text = text[start:end].strip()

        if not segment_text:
            continue

        segments.append(
            _ClauseTextSegment(
                clause=_normalize_clause(match.group(1)),
                text=segment_text,
                start=start,
                end=end,
            )
        )

    return segments


def _inherit_page_geometry(
    nested_item: dict[str, Any],
    parent_item: dict[str, Any],
) -> dict[str, Any]:
    result = dict(nested_item)

    for key in (
        "file_page_number",
        "file_page_index",
        "printed_page_label",
        "page_label",
        "page_number",
        "page",
        "page_width",
        "page_height",
    ):
        if result.get(key) is None and parent_item.get(key) is not None:
            result[key] = parent_item[key]

    return result


def _file_page_number_from_item(item: dict[str, Any]) -> int | None:
    return _first_int(
        item.get("file_page_number"),
        item.get("page_number"),
        item.get("page"),
    )


def _file_page_index_from_item(item: dict[str, Any]) -> int | None:
    explicit_index = _first_int(
        item.get("file_page_index"),
        item.get("page_index"),
    )

    if explicit_index is not None:
        return explicit_index

    file_page_number = _file_page_number_from_item(item)

    if file_page_number is None:
        return None

    return file_page_number - 1


def _printed_page_label_from_item(item: dict[str, Any]) -> str | None:
    return _first_str(
        item.get("printed_page_label"),
        item.get("page_label"),
        item.get("printed_page"),
        item.get("page_display"),
    )


def _bbox_from_parse_item(item: dict[str, Any]) -> list[float] | None:
    return _bbox(item.get("bbox"))


def _normalized_bbox_from_parse_item(item: dict[str, Any]) -> list[float] | None:
    return _bbox(item.get("normalized_bbox"))


def _bbox(value: Any) -> list[float] | None:
    if isinstance(value, dict):
        return _bbox_from_dict(value)

    if not isinstance(value, list):
        return None

    direct = _bbox_from_number_list(value)

    if direct is not None:
        return direct

    box_dicts = [
        item for item in value
        if isinstance(item, dict)
    ]

    if not box_dicts:
        return None

    return _union_bbox_dicts(box_dicts)


def _bbox_from_number_list(value: list[Any]) -> list[float] | None:
    if len(value) != 4:
        return None

    result: list[float] = []

    for item in value:
        number = _first_number(item)

        if number is None:
            return None

        result.append(number)

    return result


def _bbox_from_dict(value: dict[str, Any]) -> list[float] | None:
    x = _first_number(value.get("x"))
    y = _first_number(value.get("y"))
    width = _first_number(value.get("w"), value.get("width"))
    height = _first_number(value.get("h"), value.get("height"))

    if x is None or y is None or width is None or height is None:
        return None

    return [x, y, width, height]


def _union_bbox_dicts(values: list[dict[str, Any]]) -> list[float] | None:
    parsed_boxes = [
        box for value in values
        if (box := _bbox_from_dict(value)) is not None
    ]

    if not parsed_boxes:
        return None

    min_x = min(box[0] for box in parsed_boxes)
    min_y = min(box[1] for box in parsed_boxes)
    max_x = max(box[0] + box[2] for box in parsed_boxes)
    max_y = max(box[1] + box[3] for box in parsed_boxes)

    return [
        min_x,
        min_y,
        max_x - min_x,
        max_y - min_y,
    ]


def _normalize_bbox(
    bbox: list[float] | None,
    *,
    page_width: float | None,
    page_height: float | None,
) -> list[float] | None:
    if bbox is None or page_width is None or page_height is None:
        return None

    if page_width <= 0 or page_height <= 0:
        return None

    x, y, width, height = bbox

    normalized = [
        x / page_width,
        y / page_height,
        width / page_width,
        height / page_height,
    ]

    if any(number < 0 or number > 1 for number in normalized):
        return None

    return [
        round(number, 6)
        for number in normalized
    ]


def _span_clause_matches_expected_clause(
    text_preview: str | None,
    expected_clause: str | None,
) -> bool:
    if not expected_clause or not expected_clause.strip():
        return True

    if not text_preview or not text_preview.strip():
        return True

    normalized_preview = _normalize_text(text_preview)
    normalized_clause = _normalize_clause(expected_clause)

    if not normalized_clause:
        return True

    preview_clause = _leading_clause(normalized_preview)

    if preview_clause is None:
        return True

    return preview_clause == normalized_clause


def _leading_clause(value: str) -> str | None:
    match = _CLAUSE_RE.match(value)

    if match is None:
        return None

    return _normalize_clause(match.group(1))


def _normalize_clause(value: str) -> str:
    value = value.strip()
    value = value.rstrip(".")
    value = value.replace(" ", "")
    return value


def _text_preview_matches_parse_item(
    text_preview: str | None,
    parse_item: dict[str, Any],
) -> bool:
    if not text_preview or not text_preview.strip():
        return True

    item_text = _extract_item_text(parse_item)

    if not item_text:
        return True

    preview = _normalize_text(text_preview)
    text = _normalize_text(item_text)

    if not preview or not text:
        return True

    if preview in text or text in preview:
        return True

    preview_prefix = preview[:80].rstrip(" .")

    if len(preview_prefix) >= 20 and preview_prefix in text:
        return True

    preview_words = set(_WORD_RE.findall(preview))
    text_words = set(_WORD_RE.findall(text))

    meaningful_preview_words = {
        word for word in preview_words
        if len(word) >= 3
    }

    if meaningful_preview_words:
        overlap = meaningful_preview_words & text_words
        required = min(3, len(meaningful_preview_words))

        if len(overlap) >= required:
            return True

    ratio = SequenceMatcher(None, preview[:120], text[:240]).ratio()
    return ratio >= 0.45


def _extract_item_text(item: dict[str, Any]) -> str:
    for key in ("md", "markdown", "text", "value", "content"):
        value = item.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    return ""


def _compact_text(value: str, *, limit: int) -> str | None:
    value = _SPACE_RE.sub(" ", value).strip()

    if not value:
        return None

    if len(value) <= limit:
        return value

    return value[: limit - 1].rstrip() + "?"


def _normalize_text(value: str) -> str:
    value = value.replace("?", "?").replace("?", "?")
    value = value.replace("?", "...")
    value = value.lower()
    value = _SPACE_RE.sub(" ", value)
    return value.strip()




def _first_str(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()

        if isinstance(value, int):
            return str(value)

    return None

def _first_int(*values: Any) -> int | None:
    for value in values:
        if isinstance(value, bool):
            continue

        if isinstance(value, int):
            return value

        if isinstance(value, float) and value.is_integer():
            return int(value)

        if isinstance(value, str):
            stripped = value.strip()

            if stripped.isdigit():
                return int(stripped)

    return None


def _first_number(*values: Any) -> float | None:
    for value in values:
        if isinstance(value, bool):
            continue

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            stripped = value.strip().replace(",", ".")

            try:
                return float(stripped)
            except ValueError:
                continue

    return None
