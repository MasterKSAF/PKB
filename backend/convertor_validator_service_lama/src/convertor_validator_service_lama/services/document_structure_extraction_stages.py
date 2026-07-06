from __future__ import annotations

from collections import Counter
from typing import Any

from convertor_validator_service_lama.services.document_structure_extraction_input import (
    build_document_structure_agent_input,
    build_parse_items_preview,
    extract_effective_parse_items,
)


DEFAULT_OVERVIEW_MAX_ITEMS = 180
DEFAULT_SCOPE_MAX_ITEMS = 350
DEFAULT_SCOPE_MAX_WINDOW_ITEMS = 300
DEFAULT_SCOPE_OVERLAP_ITEMS = 20
DEFAULT_STAGE_ITEM_TEXT_CHARS = 700
DEFAULT_STAGE_MARKDOWN_EXCERPT_CHARS = 12_000

STRUCTURAL_ITEM_TYPES = {
    "heading",
    "header",
    "footer",
    "table",
}

# Written with unicode escapes to avoid Windows PowerShell 5.1 mojibake in source edits.
STRUCTURAL_TEXT_MARKERS = (
    "\u0421\u041e\u0414\u0415\u0420\u0416\u0410\u041d\u0418\u0415",  # ??????????
    "\u041e\u0413\u041b\u0410\u0412\u041b\u0415\u041d\u0418\u0415",  # ??????????
    "\u0427\u0410\u0421\u0422\u042c",  # ?????
    "\u0420\u0410\u0417\u0414\u0415\u041b",  # ??????
    "\u041f\u0420\u0418\u041b\u041e\u0416\u0415\u041d\u0418\u0415",  # ??????????
    "\u041f\u0420\u0410\u0412\u0418\u041b\u0410",  # ???????
)


def build_document_structure_stage_plan(
    parse_result_payload: dict[str, Any],
    *,
    numbering_scopes: list[dict[str, Any]] | None = None,
    overview_max_items: int = DEFAULT_OVERVIEW_MAX_ITEMS,
    scope_max_items: int = DEFAULT_SCOPE_MAX_ITEMS,
    scope_max_window_items: int = DEFAULT_SCOPE_MAX_WINDOW_ITEMS,
    scope_overlap_items: int = DEFAULT_SCOPE_OVERLAP_ITEMS,
    item_text_chars: int = DEFAULT_STAGE_ITEM_TEXT_CHARS,
    markdown_excerpt_chars: int = DEFAULT_STAGE_MARKDOWN_EXCERPT_CHARS,
) -> dict[str, Any]:
    """Build staged extraction plan without calling an LLM.

    Stage 1 is always an overview pass. Scope/window passes are created only
    when numbering scopes are already known, for example after an overview-agent
    response or from deterministic diagnostics.
    """

    base_input = build_document_structure_agent_input(
        parse_result_payload,
        max_preview_items=0,
        item_text_chars=item_text_chars,
        markdown_excerpt_chars=0,
    )

    overview_input = build_document_structure_overview_agent_input(
        parse_result_payload,
        max_preview_items=overview_max_items,
        item_text_chars=item_text_chars,
        markdown_excerpt_chars=markdown_excerpt_chars,
    )

    scope_inputs = build_scope_extraction_agent_inputs(
        parse_result_payload,
        numbering_scopes=numbering_scopes or [],
        max_preview_items=scope_max_items,
        max_scope_items_per_window=scope_max_window_items,
        overlap_items=scope_overlap_items,
        item_text_chars=item_text_chars,
        markdown_excerpt_chars=markdown_excerpt_chars,
    )

    return {
        "job_id": base_input["job_id"],
        "status": base_input["status"],
        "page_count": base_input["page_count"],
        "items_count": base_input["items_count"],
        "stages_count": 1 + len(scope_inputs),
        "requires_overview_agent_output": not bool(numbering_scopes),
        "overview_input": overview_input,
        "scope_inputs": scope_inputs,
    }


def build_document_structure_overview_agent_input(
    parse_result_payload: dict[str, Any],
    *,
    max_preview_items: int = DEFAULT_OVERVIEW_MAX_ITEMS,
    item_text_chars: int = DEFAULT_STAGE_ITEM_TEXT_CHARS,
    markdown_excerpt_chars: int = DEFAULT_STAGE_MARKDOWN_EXCERPT_CHARS,
) -> dict[str, Any]:
    """Build compact input for the overview/routing pass.

    This pass should identify document_profile and numbering_scopes. It should
    not extract every section from a large document.
    """

    items = extract_effective_parse_items(parse_result_payload)
    base_input = build_document_structure_agent_input(
        parse_result_payload,
        max_preview_items=0,
        item_text_chars=item_text_chars,
        markdown_excerpt_chars=markdown_excerpt_chars,
    )

    overview_items = select_overview_items(
        items,
        max_items=max_preview_items,
    )
    parse_items_preview = build_parse_items_preview(
        overview_items,
        max_items=max_preview_items,
        item_text_chars=item_text_chars,
    )

    return {
        "stage_id": "overview",
        "stage_type": "overview",
        "job_id": base_input["job_id"],
        "status": base_input["status"],
        "page_count": base_input["page_count"],
        "items_count": len(items),
        "items_preview_count": len(parse_items_preview),
        "page_overview": build_page_overview(items),
        "parse_items_preview": parse_items_preview,
        "markdown_excerpt": base_input["markdown_excerpt"],
        "markdown_chars": base_input["markdown_chars"],
        "goal": (
            "Determine document_profile and numbering_scopes. "
            "Do not extract all sections in this pass."
        ),
    }


def build_scope_extraction_agent_inputs(
    parse_result_payload: dict[str, Any],
    *,
    numbering_scopes: list[dict[str, Any]],
    max_preview_items: int = DEFAULT_SCOPE_MAX_ITEMS,
    max_scope_items_per_window: int = DEFAULT_SCOPE_MAX_WINDOW_ITEMS,
    overlap_items: int = DEFAULT_SCOPE_OVERLAP_ITEMS,
    item_text_chars: int = DEFAULT_STAGE_ITEM_TEXT_CHARS,
    markdown_excerpt_chars: int = DEFAULT_STAGE_MARKDOWN_EXCERPT_CHARS,
) -> list[dict[str, Any]]:
    """Build extraction inputs for numbering scopes and their item windows."""

    items = extract_effective_parse_items(parse_result_payload)
    result: list[dict[str, Any]] = []

    for ordinal, scope in enumerate(numbering_scopes):
        namespace_id = _safe_namespace_id(
            scope.get("namespace_id"),
            fallback=f"scope_{ordinal + 1}",
        )
        page_start = _first_int(scope.get("page_start"))
        page_end = _first_int(scope.get("page_end"))

        scope_items = filter_items_by_page_range(
            items,
            page_start=page_start,
            page_end=page_end,
        )
        scope_windows = split_scope_items_into_windows(
            scope_items,
            max_items_per_window=max_scope_items_per_window,
            overlap_items=overlap_items,
        )

        windows_count = len(scope_windows)

        for window_index, window_items in enumerate(scope_windows):
            window_page_start, window_page_end = _page_range_for_items(window_items)
            source_item_index_start, source_item_index_end = _source_index_range_for_items(
                window_items
            )

            if windows_count == 1:
                stage_page_start = page_start or window_page_start
                stage_page_end = page_end or window_page_end
            else:
                stage_page_start = window_page_start or page_start
                stage_page_end = window_page_end or page_end

            parse_items_preview = build_parse_items_preview(
                window_items,
                max_items=max_preview_items,
                item_text_chars=item_text_chars,
            )
            markdown_excerpt = build_markdown_excerpt_from_preview(
                parse_items_preview,
                limit=markdown_excerpt_chars,
            )

            result.append(
                {
                    "stage_id": _stage_id_for_scope(
                        namespace_id=namespace_id,
                        page_start=stage_page_start,
                        page_end=stage_page_end,
                        window_index=window_index,
                        windows_count=windows_count,
                    ),
                    "stage_type": "scope_extraction",
                    "namespace_id": namespace_id,
                    "scope_title": str(scope.get("title") or namespace_id),
                    "scope_type": scope.get("scope_type"),
                    "page_start": stage_page_start,
                    "page_end": stage_page_end,
                    "window_index": window_index,
                    "windows_count": windows_count,
                    "scope_items_count": len(scope_items),
                    "source_item_index_start": source_item_index_start,
                    "source_item_index_end": source_item_index_end,
                    "items_count": len(window_items),
                    "items_preview_count": len(parse_items_preview),
                    "parse_items_preview": parse_items_preview,
                    "markdown_excerpt": markdown_excerpt,
                    "goal": (
                        "Extract sections, item classifications and source_spans "
                        "inside this numbering scope window only."
                    ),
                }
            )

    return result


def split_scope_items_into_windows(
    items: list[dict[str, Any]],
    *,
    max_items_per_window: int = DEFAULT_SCOPE_MAX_WINDOW_ITEMS,
    overlap_items: int = DEFAULT_SCOPE_OVERLAP_ITEMS,
) -> list[list[dict[str, Any]]]:
    """Split scope items into overlapping windows.

    Overlap protects clauses and tables that cross a window boundary.
    """

    if not items:
        return []

    if max_items_per_window <= 0:
        return [items]

    if len(items) <= max_items_per_window:
        return [items]

    safe_overlap = max(0, min(overlap_items, max_items_per_window - 1))
    step = max(1, max_items_per_window - safe_overlap)

    windows: list[list[dict[str, Any]]] = []
    start = 0

    while start < len(items):
        end = min(len(items), start + max_items_per_window)
        windows.append(items[start:end])

        if end >= len(items):
            break

        start += step

    return windows


def select_overview_items(
    items: list[dict[str, Any]],
    *,
    max_items: int = DEFAULT_OVERVIEW_MAX_ITEMS,
) -> list[dict[str, Any]]:
    """Select structural items distributed through the document."""

    selected_indexes: set[int] = set()

    for index in range(min(12, len(items))):
        selected_indexes.add(index)

    for index in range(max(0, len(items) - 5), len(items)):
        selected_indexes.add(index)

    first_items_by_page: dict[int, int] = {}

    for index, item in enumerate(items):
        page = _first_int(item.get("page_number"), item.get("page"))
        if page is not None and page not in first_items_by_page:
            first_items_by_page[page] = index

        item_type = str(item.get("type") or "").lower()
        text = _extract_item_text(item)
        text_upper = text.upper()

        if item_type in STRUCTURAL_ITEM_TYPES:
            selected_indexes.add(index)
            continue

        if text.startswith("#"):
            selected_indexes.add(index)
            continue

        if any(marker in text_upper for marker in STRUCTURAL_TEXT_MARKERS):
            selected_indexes.add(index)

    selected_indexes.update(first_items_by_page.values())

    indexes = _downsample_sorted_indexes(
        sorted(selected_indexes),
        max_items=max_items,
    )

    return [
        _copy_with_source_item_index(items[index], index)
        for index in indexes
    ]


def build_page_overview(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pages: dict[int, dict[str, Any]] = {}

    for index, item in enumerate(items):
        page = _first_int(item.get("page_number"), item.get("page"))
        if page is None:
            continue

        page_row = pages.setdefault(
            page,
            {
                "page_number": page,
                "items_count": 0,
                "item_index_start": index,
                "item_index_end": index,
                "types": Counter(),
                "headings": [],
            },
        )

        page_row["items_count"] += 1
        page_row["item_index_end"] = index
        page_row["types"][str(item.get("type") or "unknown")] += 1

        text = _extract_item_text(item)
        item_type = str(item.get("type") or "").lower()

        if (
            item_type == "heading"
            or text.startswith("#")
            or any(marker in text.upper() for marker in STRUCTURAL_TEXT_MARKERS)
        ):
            if len(page_row["headings"]) < 8:
                page_row["headings"].append(
                    {
                        "item_index": index,
                        "type": item.get("type"),
                        "text": _compact_text(text, limit=300),
                    }
                )

    result = []

    for page_number in sorted(pages):
        row = pages[page_number]
        result.append(
            {
                "page_number": row["page_number"],
                "items_count": row["items_count"],
                "item_index_start": row["item_index_start"],
                "item_index_end": row["item_index_end"],
                "types": dict(sorted(row["types"].items())),
                "headings": row["headings"],
            }
        )

    return result


def filter_items_by_page_range(
    items: list[dict[str, Any]],
    *,
    page_start: int | None,
    page_end: int | None,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for index, item in enumerate(items):
        page = _first_int(item.get("page_number"), item.get("page"))

        if page is None:
            continue

        if page_start is not None and page < page_start:
            continue

        if page_end is not None and page > page_end:
            continue

        result.append(_copy_with_source_item_index(item, index))

    return result


def build_markdown_excerpt_from_preview(
    parse_items_preview: list[dict[str, Any]],
    *,
    limit: int = DEFAULT_STAGE_MARKDOWN_EXCERPT_CHARS,
) -> str:
    blocks = []

    for item in parse_items_preview:
        text = str(item.get("text") or "")
        if not text:
            continue

        blocks.append(
            (
                f'[item_index={item.get("item_index")} '
                f'page={item.get("page_number")} '
                f'type={item.get("type")}]\n'
                f"{text}"
            )
        )

    markdown = "\n\n".join(blocks)

    if len(markdown) <= limit:
        return markdown

    return markdown[: max(0, limit - 1)].rstrip() + "?"


def _copy_with_source_item_index(
    item: dict[str, Any],
    source_item_index: int,
) -> dict[str, Any]:
    row = dict(item)
    row["_source_item_index"] = source_item_index
    return row


def _downsample_sorted_indexes(
    indexes: list[int],
    *,
    max_items: int,
) -> list[int]:
    if max_items <= 0:
        return []

    if len(indexes) <= max_items:
        return indexes

    if max_items == 1:
        return [indexes[0]]

    last_position = len(indexes) - 1
    sampled = {
        indexes[round(position * last_position / (max_items - 1))]
        for position in range(max_items)
    }

    sampled.add(indexes[0])
    sampled.add(indexes[-1])

    return sorted(sampled)


def _stage_id_for_scope(
    *,
    namespace_id: str,
    page_start: int | None,
    page_end: int | None,
    window_index: int = 0,
    windows_count: int = 1,
) -> str:
    page_part = f"p{page_start or 'start'}_{page_end or 'end'}"

    if windows_count > 1:
        return f"scope_{namespace_id}_{page_part}_w{window_index + 1:02d}"

    return f"scope_{namespace_id}_{page_part}"


def _page_range_for_items(items: list[dict[str, Any]]) -> tuple[int | None, int | None]:
    pages = [
        page
        for item in items
        if (page := _first_int(item.get("page_number"), item.get("page"))) is not None
    ]

    if not pages:
        return None, None

    return min(pages), max(pages)


def _source_index_range_for_items(
    items: list[dict[str, Any]],
) -> tuple[int | None, int | None]:
    indexes = [
        index
        for item in items
        if (index := _first_int(item.get("_source_item_index"))) is not None
    ]

    if not indexes:
        return None, None

    return min(indexes), max(indexes)


def _safe_namespace_id(value: Any, *, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()

    return fallback


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


def _compact_text(text: str, *, limit: int) -> str:
    compact = " ".join(text.replace("\r", "\n").split())

    if len(compact) <= limit:
        return compact

    return compact[: max(0, limit - 1)].rstrip() + "?"


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
