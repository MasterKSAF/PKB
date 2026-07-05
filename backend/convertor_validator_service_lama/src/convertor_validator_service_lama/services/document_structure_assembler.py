from __future__ import annotations

import re
from collections import Counter
from typing import Any


_HEADING_MD_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<title>.+)")
_NUMBERED_HEADING_RE = re.compile(r"^(?P<number>\d+(?:\.\d+)*\.?)\s+(?P<title>.+)")
_SPACE_RE = re.compile(r"\s+")

# Russian strings are stored as unicode escapes to avoid PowerShell 5.1 mojibake.
_RU_TOC = "\u0441\u043e\u0434\u0435\u0440\u0436\u0430\u043d\u0438\u0435"
_RU_INTRODUCTION = "\u0432\u0432\u0435\u0434\u0435\u043d\u0438\u0435"
_RU_PART_I = "\u0447\u0430\u0441\u0442\u044c i"
_RU_CLASSIFICATION = "\u043a\u043b\u0430\u0441\u0441\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f"
_RU_APPENDICES_PART_I = "\u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f \u043a \u0447\u0430\u0441\u0442\u0438 i"
_RU_PTNE_FULL = "\u043f\u0440\u0430\u0432\u0438\u043b\u0430 \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u043e\u0433\u043e \u043d\u0430\u0434\u0437\u043e\u0440\u0430 \u0437\u0430 \u0441\u0443\u0434\u0430\u043c\u0438 \u0432 \u044d\u043a\u0441\u043f\u043b\u0443\u0430\u0442\u0430\u0446\u0438\u0438"
_RU_PTNE_SHORT = "\u043f\u0442\u043d\u044d"
_RU_PTNP_FULL = "\u043f\u0440\u0430\u0432\u0438\u043b\u0430 \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u043e\u0433\u043e \u043d\u0430\u0434\u0437\u043e\u0440\u0430 \u0437\u0430 \u043f\u043e\u0441\u0442\u0440\u043e\u0439\u043a\u043e\u0439 \u0441\u0443\u0434\u043e\u0432"
_RU_PTNP_SHORT = "\u043f\u0442\u043d\u043f"
_RU_FRONT_MATTER_TITLE = "\u0422\u0438\u0442\u0443\u043b\u044c\u043d\u044b\u0439 \u0431\u043b\u043e\u043a"


def assemble_document_structure_from_parse_items(
    items: list[dict[str, Any]],
    *,
    page_count: int | None = None,
) -> dict[str, Any]:
    """Build a rich citeable document structure from flattened LlamaParse items."""

    headings = extract_headings(items)
    headings = build_number_aware_heading_tree(headings)
    namespaces = build_namespaces(headings, items, page_count=page_count)
    headings = apply_namespaces_to_headings(headings, namespaces)
    sections = assemble_sections(items, headings)

    return {
        "namespaces": namespaces,
        "sections": sections,
        "diagnostics": build_diagnostics(items, headings, namespaces, sections),
    }


def extract_headings(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    headings: list[dict[str, Any]] = []

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue

        item_type = item.get("type")
        text = _one_line(item.get("md") or item.get("value"))

        if item_type != "heading" and not text.startswith("#"):
            continue

        markdown_level, clean_title = _parse_markdown_heading(text)
        number, title_without_number = _parse_numbered_title(clean_title)

        headings.append(
            {
                "heading_id": len(headings) + 1,
                "item_index": index,
                "page": item.get("page_number"),
                "markdown_level": markdown_level,
                "number": number,
                "title": clean_title,
                "title_without_number": title_without_number,
                "parent_id": None,
                "parent_rule": None,
                "path": None,
                "source_span": _make_span(item, index),
            }
        )

    return headings


def build_number_aware_heading_tree(headings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_number: dict[str, dict[str, Any]] = {}
    stack_by_level: dict[int, dict[str, Any]] = {}

    for heading in headings:
        parent: dict[str, Any] | None = None
        parent_rule: str | None = None

        number = heading.get("number")
        if number:
            for candidate in _number_parent_candidates(str(number)):
                if candidate in by_number:
                    parent = by_number[candidate]
                    parent_rule = "number_prefix:" + candidate
                    break

        if parent is None:
            level = int(heading.get("markdown_level") or 1)
            for candidate_level in range(level - 1, 0, -1):
                if candidate_level in stack_by_level:
                    parent = stack_by_level[candidate_level]
                    parent_rule = "markdown_level"
                    break

        heading["parent_id"] = parent.get("heading_id") if parent else None
        heading["parent_rule"] = parent_rule or "root"
        heading["path"] = _build_heading_path(heading, parent)

        if number:
            by_number[str(number)] = heading

        level = int(heading.get("markdown_level") or 1)
        stack_by_level[level] = heading

        for stale_level in list(stack_by_level):
            if stale_level > level:
                del stack_by_level[stale_level]

    return headings


def build_namespaces(
    headings: list[dict[str, Any]],
    items: list[dict[str, Any]],
    *,
    page_count: int | None = None,
) -> list[dict[str, Any]]:
    effective_page_count = page_count or _infer_page_count(items, headings)

    root_headings = [heading for heading in headings if heading.get("parent_id") is None]

    boundary_candidates: list[dict[str, Any]] = []
    for heading in root_headings:
        namespace_id = _slugify_namespace(heading.get("title"))
        if namespace_id is None:
            continue

        boundary_candidates.append(
            {
                "namespace_id": namespace_id,
                "title": _one_line(heading.get("title")),
                "start_heading_id": heading.get("heading_id"),
                "start_item_index": heading.get("item_index"),
                "page_start": heading.get("page"),
            }
        )

    namespaces = [
        {
            "namespace_id": "front_matter",
            "title": _RU_FRONT_MATTER_TITLE,
            "start_heading_id": headings[0].get("heading_id") if headings else None,
            "start_item_index": 0,
            "page_start": 1,
        },
        *boundary_candidates,
    ]

    namespaces = sorted(
        namespaces,
        key=lambda namespace: (
            namespace.get("start_item_index") if namespace.get("start_item_index") is not None else 10**12,
            namespace.get("page_start") if namespace.get("page_start") is not None else 10**12,
            str(namespace.get("namespace_id")),
        ),
    )

    deduplicated: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for namespace in namespaces:
        namespace_id = str(namespace["namespace_id"])
        if namespace_id in seen_ids:
            continue
        deduplicated.append(namespace)
        seen_ids.add(namespace_id)

    for index, namespace in enumerate(deduplicated):
        next_namespace = deduplicated[index + 1] if index + 1 < len(deduplicated) else None

        if next_namespace:
            namespace["end_item_index_exclusive"] = next_namespace.get("start_item_index")
            namespace["page_end"] = max(
                int(namespace.get("page_start") or 1),
                int(next_namespace.get("page_start") or 1) - 1,
            )
        else:
            namespace["end_item_index_exclusive"] = None
            namespace["page_end"] = effective_page_count

        namespace["ordinal"] = index + 1

    return deduplicated


def apply_namespaces_to_headings(
    headings: list[dict[str, Any]],
    namespaces: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    for heading in headings:
        namespace = _find_namespace_for_item_index(heading.get("item_index"), namespaces)

        if namespace is None:
            heading["namespace_id"] = None
            heading["namespace_title"] = None
            heading["namespaced_path"] = heading.get("path")
            continue

        heading["namespace_id"] = namespace.get("namespace_id")
        heading["namespace_title"] = namespace.get("title")

        local_path = heading.get("path") or ("heading-" + str(heading.get("heading_id")))
        heading["namespaced_path"] = str(namespace["namespace_id"]) + "/" + str(local_path)

    return headings


def assemble_sections(
    items: list[dict[str, Any]],
    headings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    heading_by_item_index = {
        heading.get("item_index"): heading
        for heading in headings
        if heading.get("item_index") is not None
    }
    heading_item_indexes = sorted(int(index) for index in heading_by_item_index)

    sections: list[dict[str, Any]] = []

    for position, heading_item_index in enumerate(heading_item_indexes):
        heading = heading_by_item_index[heading_item_index]

        next_heading_item_index = (
            heading_item_indexes[position + 1]
            if position + 1 < len(heading_item_indexes)
            else len(items)
        )

        heading_item = items[heading_item_index] if 0 <= heading_item_index < len(items) else {}

        content_blocks: list[dict[str, Any]] = []
        source_spans = [_make_span(heading_item, heading_item_index)]
        pages: list[int] = []

        if heading.get("page") is not None:
            pages.append(int(heading["page"]))

        for index in range(heading_item_index + 1, next_heading_item_index):
            item = items[index]
            if not isinstance(item, dict):
                continue

            item_type = item.get("type")
            if item_type in {"header", "footer", "heading"}:
                continue

            text = _one_line(item.get("md") or item.get("value"))
            if not text:
                continue

            source_span = _make_span(item, index)

            block = {
                "item_index": index,
                "type": _content_type_for_item(item),
                "page": item.get("page_number"),
                "text": text,
                "source_span": source_span,
            }

            content_blocks.append(block)
            source_spans.append(source_span)

            page = item.get("page_number")
            if page is not None and int(page) not in pages:
                pages.append(int(page))

        content_text = "\n\n".join(
            block["text"]
            for block in content_blocks
            if block.get("text")
        )

        sections.append(
            {
                "section_id": heading.get("heading_id"),
                "parent_id": heading.get("parent_id"),
                "namespace_id": heading.get("namespace_id"),
                "namespace_title": heading.get("namespace_title"),
                "kind": _section_kind(heading),
                "number": heading.get("number"),
                "title": heading.get("title"),
                "title_without_number": heading.get("title_without_number"),
                "path": heading.get("path"),
                "namespaced_path": heading.get("namespaced_path"),
                "page_start": min(pages) if pages else heading.get("page"),
                "page_end": max(pages) if pages else heading.get("page"),
                "heading_item_index": heading_item_index,
                "next_heading_item_index": next_heading_item_index,
                "content_blocks_count": len(content_blocks),
                "content_text_chars": len(content_text),
                "content_blocks": content_blocks,
                "content_text": content_text,
                "source_spans": source_spans,
            }
        )

    return sections


def build_diagnostics(
    items: list[dict[str, Any]],
    headings: list[dict[str, Any]],
    namespaces: list[dict[str, Any]],
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "items_count": len(items),
        "headings_count": len(headings),
        "namespaces_count": len(namespaces),
        "sections_count": len(sections),
        "item_types": dict(Counter(str(item.get("type")) for item in items if isinstance(item, dict))),
        "sections_by_namespace": dict(Counter(str(section.get("namespace_id")) for section in sections)),
        "sections_by_kind": dict(Counter(str(section.get("kind")) for section in sections)),
        "sections_without_content": sum(1 for section in sections if section.get("content_blocks_count") == 0),
        "sections_with_tables": sum(
            1
            for section in sections
            if any(block.get("type") == "table" for block in section.get("content_blocks", []))
        ),
        "sections_with_lists": sum(
            1
            for section in sections
            if any(block.get("type") == "list" for block in section.get("content_blocks", []))
        ),
    }


def _one_line(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\n", " ")).strip()


def _parse_markdown_heading(text: str) -> tuple[int | None, str]:
    match = _HEADING_MD_RE.match(text)
    if not match:
        return None, text

    return len(match.group("hashes")), match.group("title").strip()


def _parse_numbered_title(title: str) -> tuple[str | None, str]:
    match = _NUMBERED_HEADING_RE.match(title)
    if not match:
        return None, title

    return match.group("number").rstrip("."), match.group("title").strip()


def _number_parent_candidates(number: str) -> list[str]:
    parts = number.split(".")
    return [".".join(parts[:cut]) for cut in range(len(parts) - 1, 0, -1)]


def _build_heading_path(
    heading: dict[str, Any],
    parent: dict[str, Any] | None,
) -> str:
    number = heading.get("number")

    if number and heading.get("parent_rule", "").startswith("number_prefix:"):
        return str(number).replace(".", "/")

    if number and heading.get("parent_rule") == "root":
        return str(number).replace(".", "/")

    if number and parent and parent.get("path"):
        return str(parent["path"]) + "/" + str(number).replace(".", "/")

    if number:
        return str(number).replace(".", "/")

    if parent and parent.get("path"):
        return str(parent["path"]) + "/heading-" + str(heading.get("heading_id"))

    return "heading-" + str(heading.get("heading_id"))


def _normalize_bbox(
    bbox: Any,
    page_width: Any,
    page_height: Any,
) -> dict[str, float] | None:
    if not bbox or not isinstance(bbox, list):
        return None
    if not page_width or not page_height:
        return None

    first = bbox[0]
    if not isinstance(first, dict):
        return None

    return {
        "x": round(float(first.get("x", 0)) / float(page_width), 6),
        "y": round(float(first.get("y", 0)) / float(page_height), 6),
        "w": round(float(first.get("w", 0)) / float(page_width), 6),
        "h": round(float(first.get("h", 0)) / float(page_height), 6),
    }


def _make_span(item: dict[str, Any], item_index: int) -> dict[str, Any]:
    return {
        "item_index": item_index,
        "page": item.get("page_number"),
        "item_type": item.get("type"),
        "bbox": item.get("bbox"),
        "normalized_bbox": _normalize_bbox(
            item.get("bbox"),
            item.get("page_width"),
            item.get("page_height"),
        ),
    }


def _slugify_namespace(title: Any) -> str | None:
    text = _one_line(title).lower()

    if _RU_TOC in text:
        return "toc"
    if _RU_INTRODUCTION in text:
        return "introduction"
    if _RU_PART_I in text and _RU_CLASSIFICATION in text:
        return "classification"
    if _RU_APPENDICES_PART_I in text:
        return "appendices_part_1"
    if _RU_PTNE_FULL in text or _RU_PTNE_SHORT in text:
        return "ptne"
    if _RU_PTNP_FULL in text or _RU_PTNP_SHORT in text:
        return "ptnp"

    return None


def _infer_page_count(
    items: list[dict[str, Any]],
    headings: list[dict[str, Any]],
) -> int:
    pages: list[int] = []

    for item in items:
        if isinstance(item, dict) and item.get("page_number") is not None:
            pages.append(int(item["page_number"]))

    for heading in headings:
        if heading.get("page") is not None:
            pages.append(int(heading["page"]))

    return max(pages) if pages else 1


def _find_namespace_for_item_index(
    item_index: Any,
    namespaces: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if item_index is None:
        return None

    selected: dict[str, Any] | None = None
    item_index = int(item_index)

    for namespace in namespaces:
        start = namespace.get("start_item_index")
        end = namespace.get("end_item_index_exclusive")

        if start is None:
            continue

        if item_index >= int(start) and (end is None or item_index < int(end)):
            selected = namespace

    return selected


def _content_type_for_item(item: dict[str, Any]) -> str:
    item_type = item.get("type")

    if item_type == "table":
        return "table"
    if item_type == "list":
        return "list"
    if item_type == "text":
        return "text"

    return str(item_type or "unknown")


def _section_kind(heading: dict[str, Any]) -> str:
    namespace_id = heading.get("namespace_id")

    if namespace_id == "toc":
        return "toc"
    if namespace_id == "front_matter":
        return "front_matter"
    if namespace_id == "introduction":
        return "introduction"
    if namespace_id == "appendices_part_1":
        return "appendix"
    if heading.get("number"):
        return "numbered_section"

    return "heading_section"
