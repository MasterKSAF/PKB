import copy
import re
from typing import Any

_CLAUSE_RE = re.compile(r"^(\d+(?:\.\d+)*)\s*(.*)$")
_GOST_REF_RE = re.compile(
    r"(?:ГОСТ|GOST)\s*(\d[\d.]*(?:-\d{2,4})?)",
    re.IGNORECASE,
)


def _page_size(
    raw_json: dict[str, Any], page: int
) -> tuple[float, float]:
    pages = (raw_json.get("document") or {}).get("pages") or []
    for page_info in pages:
        if page_info.get("page") == page:
            return (
                float(page_info.get("width") or 210.0),
                float(page_info.get("height") or 297.0),
            )
    return 210.0, 297.0


def _normalize_bbox(
    bbox: list[float], page_w: float, page_h: float
) -> list[float]:
    if not bbox or len(bbox) < 4:
        return [0.0, 0.0, 1.0, 1.0]
    if all(0 <= v <= 1 for v in bbox):
        return bbox[:4]
    x1, y1, x2, y2 = bbox[:4]
    return [
        round(x1 / page_w, 3),
        round(y1 / page_h, 3),
        round(x2 / page_w, 3),
        round(y2 / page_h, 3),
    ]


def _parse_clause_from_text(text: str) -> tuple[str | None, str | None]:
    if not text:
        return None, None
    match = _CLAUSE_RE.match(text.strip())
    if match:
        clause = match.group(1)
        rest = match.group(2).strip() or None
        return clause, rest
    return None, None


def _map_block_type(block_type: str) -> str:
    mapping = {
        "paragraph": "text",
        "heading": "text",
        "text_block": "textBlock",
        "headerFooter": "headerFooter",
        "list": "list",
        "table": "table",
        "image": "image",
        "formula": "formula",
        "caption": "text",
    }
    return mapping.get(block_type, "text")


def _build_content_item(
    block: dict[str, Any],
    raw_json: dict[str, Any],
    clause_ctx: dict[str, Any],
) -> dict[str, Any] | None:
    page = int(block.get("page") or 1)
    page_w, page_h = _page_size(raw_json, page)
    bbox = _normalize_bbox(block.get("bbox") or [], page_w, page_h)
    block_type = block.get("type") or "paragraph"
    out_type = _map_block_type(block_type)

    clause = clause_ctx.get("clause")
    title = clause_ctx.get("title")
    level = int(clause_ctx.get("level") or 1)
    parent_clause = clause_ctx.get("parent_clause")
    path = clause_ctx.get("path") or (clause or f".{out_type}.{block.get('number')}")

    content: dict[str, Any]
    if out_type == "headerFooter":
        text = block.get("content") or ""
        content = {"text": text if isinstance(text, str) else str(text)}
    elif out_type == "textBlock":
        parts = []
        for part in block.get("block") or []:
            font = part.get("font") or {}
            parts.append({
                "font": {
                    "size": font.get("size", 10.0),
                    "color": font.get("color", "#000000"),
                    "bold": font.get("bold", False),
                    "italic": font.get("italic", False),
                    "underline": font.get("underline", False),
                },
                "content": part.get("content", ""),
            })
        content = {"block": parts}
    elif out_type == "list":
        items = []
        for item in block.get("block") or []:
            items.append(item.get("content", ""))
        content = {
            "numbering_style": block.get("numbering_style", "bullet"),
            "items": items,
        }
    elif out_type == "table":
        content = {
            "caption": block.get("caption"),
            "columns": [],
            "rows": [],
            "footnotes": [],
            "amendments": [],
        }
        if block.get("rows"):
            content["rows"] = block["rows"]
    elif out_type == "image":
        content = {
            "caption": block.get("content") or block.get("caption"),
            "image_key": block.get("image_key", ""),
            "description": block.get("description", ""),
        }
    elif out_type == "formula":
        content = {
            "latex": block.get("latex", ""),
            "meaning": block.get("meaning", ""),
            "image_key": block.get("image_key"),
            "parameters": block.get("parameters") or [],
        }
    else:
        text = block.get("content") or ""
        content = {
            "text": text if isinstance(text, str) else str(text),
            "amendments": [],
        }

    return {
        "clause": clause,
        "title": title,
        "level": level,
        "parent_clause": parent_clause,
        "path": path,
        "page": page,
        "bbox": bbox,
        "type": out_type,
        "content": content,
    }


def _update_clause_context(
    block: dict[str, Any], ctx: dict[str, Any], suffix: str = ""
) -> dict[str, Any]:
    new_ctx = copy.copy(ctx)
    text = block.get("content") or ""
    if block.get("type") == "heading" and isinstance(text, str):
        clause, title = _parse_clause_from_text(text)
        if clause:
            parts = clause.split(".")
            new_ctx["clause"] = clause
            new_ctx["title"] = title
            new_ctx["level"] = len(parts)
            new_ctx["parent_clause"] = ".".join(parts[:-1]) if len(parts) > 1 else None
            new_ctx["path"] = clause + suffix
    return new_ctx


def build_hierarchy(raw_json: dict[str, Any]) -> dict[str, Any]:
    doc_in = raw_json.get("document") or {}
    source_in = copy.deepcopy(doc_in.get("source") or {})
    blocks = doc_in.get("block") or []

    content: list[dict[str, Any]] = []
    clause_ctx: dict[str, Any] = {
        "clause": None,
        "title": None,
        "level": 0,
        "parent_clause": None,
        "path": None,
    }

    table_idx = 0
    fig_idx = 0
    for block in blocks:
        block_type = block.get("type") or "paragraph"
        suffix = ""
        if block_type == "table":
            table_idx += 1
            suffix = f".table{table_idx}"
        elif block_type == "image":
            fig_idx += 1
            suffix = f".fig{fig_idx}"

        if block_type in ("heading", "headerFooter"):
            clause_ctx = _update_clause_context(block, clause_ctx, suffix)

        item = _build_content_item(block, raw_json, clause_ctx)
        if item:
            if suffix and item["path"] == clause_ctx.get("clause"):
                item["path"] = (clause_ctx.get("clause") or "") + suffix
            content.append(item)

    terminology = copy.deepcopy(doc_in.get("terminology") or [])
    references = copy.deepcopy(doc_in.get("references") or [])
    if not references:
        references = _extract_references_from_blocks(blocks)

    return {
        "source": {
            "file_name": source_in.get("file_name", ""),
            "file_hash_sha256": source_in.get("file_hash_sha256", ""),
            "page_count": int(source_in.get("page_count") or 1),
        },
        "metadata": {},
        "content": content,
        "terminology": terminology,
        "references": references,
    }


def _extract_references_from_blocks(
    blocks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for block in blocks:
        text = block.get("content")
        if not isinstance(text, str):
            continue
        for match in _GOST_REF_RE.finditer(text):
            code = f"ГОСТ {match.group(1)}"
            if code in seen:
                continue
            seen.add(code)
            refs.append({
                "target_doc_code": code,
                "type": "single",
                "context": text[:120],
                "current_status": "active",
                "note": None,
            })
    return refs
