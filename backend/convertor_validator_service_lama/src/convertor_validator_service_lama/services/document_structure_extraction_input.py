from __future__ import annotations

from typing import Any


DEFAULT_MARKDOWN_EXCERPT_CHARS = 12_000
DEFAULT_ITEM_TEXT_CHARS = 700
DEFAULT_MAX_PREVIEW_ITEMS = 300


def build_document_structure_agent_input(
    parse_result_payload: dict[str, Any],
    *,
    max_preview_items: int = DEFAULT_MAX_PREVIEW_ITEMS,
    item_text_chars: int = DEFAULT_ITEM_TEXT_CHARS,
    markdown_excerpt_chars: int = DEFAULT_MARKDOWN_EXCERPT_CHARS,
) -> dict[str, Any]:
    """Build compact, deterministic input for DocumentStructureExtraction agent.

    The function does not call LlamaCloud. It only prepares a prompt-friendly
    preview from an already saved parse result payload.

    It supports both:
    - current payloads with top-level ``items``;
    - older saved payloads where flattened items are available only under
      ``raw_response.items.pages``.
    """

    items = extract_effective_parse_items(parse_result_payload)
    metadata = parse_result_payload.get("metadata") or {}
    job_metadata = parse_result_payload.get("job_metadata") or {}

    page_count = _page_count_from_payload(parse_result_payload)
    markdown = _first_str(
        parse_result_payload.get("markdown"),
        parse_result_payload.get("markdown_full"),
        (parse_result_payload.get("raw_response") or {}).get("markdown_full"),
        (parse_result_payload.get("raw_response") or {}).get("text_full"),
    )

    parse_items_preview = build_parse_items_preview(
        items,
        max_items=max_preview_items,
        item_text_chars=item_text_chars,
    )

    return {
        "job_id": parse_result_payload.get("job_id"),
        "status": parse_result_payload.get("status"),
        "page_count": page_count,
        "metadata_pages_count": _metadata_pages_count(metadata),
        "job_metadata_pdf_pages": job_metadata.get("pdf-pages"),
        "items_count": len(items),
        "items_preview_count": len(parse_items_preview),
        "items_were_flattened_from_raw_response": not bool(parse_result_payload.get("items"))
        and bool(items),
        "parse_items_preview": parse_items_preview,
        "markdown_excerpt": markdown[:markdown_excerpt_chars],
        "markdown_chars": len(markdown),
    }


def extract_effective_parse_items(
    parse_result_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return top-level items or flatten old LlamaParse v2 raw page items."""

    items = parse_result_payload.get("items")
    if isinstance(items, list) and items:
        return [
            item
            for item in items
            if isinstance(item, dict)
        ]

    raw_response = parse_result_payload.get("raw_response") or {}
    raw_items = raw_response.get("items")

    if isinstance(raw_items, list):
        return [
            item
            for item in raw_items
            if isinstance(item, dict)
        ]

    if not isinstance(raw_items, dict):
        return []

    pages = raw_items.get("pages")
    if not isinstance(pages, list):
        return []

    flattened: list[dict[str, Any]] = []

    for page in pages:
        if not isinstance(page, dict):
            continue

        page_number = page.get("page_number")
        page_width = page.get("page_width")
        page_height = page.get("page_height")

        for item in page.get("items") or []:
            if not isinstance(item, dict):
                continue

            row = dict(item)

            if row.get("page_number") is None:
                row["page_number"] = page_number
            if row.get("page_width") is None:
                row["page_width"] = page_width
            if row.get("page_height") is None:
                row["page_height"] = page_height

            flattened.append(row)

    return flattened


def build_parse_items_preview(
    items: list[dict[str, Any]],
    *,
    max_items: int = DEFAULT_MAX_PREVIEW_ITEMS,
    item_text_chars: int = DEFAULT_ITEM_TEXT_CHARS,
) -> list[dict[str, Any]]:
    preview: list[dict[str, Any]] = []

    for item_index, item in enumerate(items[:max_items]):
        source_item_index = _first_int(
            item.get("_source_item_index"),
            item.get("item_index"),
        )
        if source_item_index is None:
            source_item_index = item_index

        text = _extract_item_text(item)
        page_width = _first_number(item.get("page_width"))
        page_height = _first_number(item.get("page_height"))
        bbox = _bbox_from_item(item)
        normalized_bbox = _normalize_bbox(
            bbox,
            page_width=page_width,
            page_height=page_height,
        )

        row: dict[str, Any] = {
            "item_index": source_item_index,
            "type": item.get("type"),
            "page_number": _first_int(item.get("page_number"), item.get("page")),
            "text": _compact_text(text, limit=item_text_chars),
        }

        if bbox is not None:
            row["bbox"] = bbox

        if normalized_bbox is not None:
            row["normalized_bbox"] = normalized_bbox

        if page_width is not None:
            row["page_width"] = page_width

        if page_height is not None:
            row["page_height"] = page_height

        preview.append(row)

    return preview


def _page_count_from_payload(payload: dict[str, Any]) -> int | None:
    metadata = payload.get("metadata") or {}
    job_metadata = payload.get("job_metadata") or {}

    value = _first_int(
        job_metadata.get("pdf-pages"),
        job_metadata.get("page_count"),
        metadata.get("page_count"),
        metadata.get("pages_count"),
        metadata.get("pdf_pages"),
    )
    if value is not None:
        return value

    pages = metadata.get("pages")
    if isinstance(pages, list):
        return len(pages)

    raw_response = payload.get("raw_response") or {}
    raw_metadata = raw_response.get("metadata")
    if isinstance(raw_metadata, dict):
        raw_pages = raw_metadata.get("pages")
        if isinstance(raw_pages, list):
            return len(raw_pages)

    return None


def _metadata_pages_count(metadata: dict[str, Any]) -> int | None:
    pages = metadata.get("pages")
    if isinstance(pages, list):
        return len(pages)

    return None


def _extract_item_text(item: dict[str, Any]) -> str:
    for key in ("md", "markdown", "text", "value", "content"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    data = item.get("data")
    if isinstance(data, dict):
        for key in ("md", "markdown", "text", "value", "content"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return ""


def _bbox_from_item(item: dict[str, Any]) -> list[float] | None:
    value = item.get("bbox")
    if not isinstance(value, list) or len(value) != 4:
        return None

    result: list[float] = []

    for number in value:
        parsed = _first_number(number)
        if parsed is None:
            return None
        result.append(parsed)

    return result


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

    return [
        max(0.0, min(1.0, round(number, 6)))
        for number in normalized
    ]


def _compact_text(text: str, *, limit: int) -> str:
    compact = " ".join(text.replace("\r", "\n").split())

    if len(compact) <= limit:
        return compact

    return compact[: max(0, limit - 1)].rstrip() + "?"


def _first_str(*values: Any) -> str:
    for value in values:
        if isinstance(value, str):
            return value

    return ""


def _first_int(*values: Any) -> int | None:
    for value in values:
        if isinstance(value, bool):
            continue

        if isinstance(value, int):
            return value

        if isinstance(value, float) and value.is_integer():
            return int(value)

        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())

    return None


def _first_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None

    if isinstance(value, int | float):
        return float(value)

    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None

    return None
