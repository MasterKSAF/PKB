import re
from typing import Any

_CLAUSE_RE = re.compile(r"^(\d+(?:\.\d+)*)\s*(.*)$")
_GOST_REF_RE = re.compile(
    r"(?:ГОСТ|GOST)\s*(\d[\d.]*(?:-\d{2,4})?)",
    re.IGNORECASE,
)


def _build_page_size_cache(raw_json: dict[str, Any]) -> dict[int, tuple[float, float]]:
    """Build a {page: (width, height)} cache for fast lookup."""
    pages = (raw_json.get("document") or {}).get("pages") or []
    cache = {}
    for p in pages:
        page = p.get("page")
        if page is not None:
            cache[int(page)] = (
                float(p.get("width") or 210.0),
                float(p.get("height") or 297.0),
            )
    return cache


def _page_size(
    page_size_cache: dict[int, tuple[float, float]], page: int
) -> tuple[float, float]:
    result = page_size_cache.get(page)
    if result:
        return result
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
    page_size_cache: dict[int, tuple[float, float]],
    clause_ctx: dict[str, Any],
) -> dict[str, Any] | None:
    page = int(block.get("page") or block.get("page number") or 1)
    page_w, page_h = _page_size(page_size_cache, page)
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
            # Skip font dict for default values — saves memory and alloc
            if (font.get("size", 10.0) == 10.0
                    and font.get("color", "#000000") == "#000000"
                    and not font.get("bold")
                    and not font.get("italic")
                    and not font.get("underline")):
                parts.append({"content": part.get("content", "")})
            else:
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
        # Extract columns from parser's `content` field (pipe-separated headers)
        # html_to_json.py stores headers as ' | '.join(header_cells) in `content`
        if not content["columns"]:
            content_str = block.get("content") or ""
            if "|" in content_str:
                content["columns"] = [c.strip() for c in content_str.split("|")]
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
    new_ctx = dict(ctx)
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
    source = doc_in.get("source") or {}
    blocks = doc_in.get("block") or []

    page_size_cache = _build_page_size_cache(raw_json)

    clause_ctx: dict[str, Any] = {
        "clause": None, "title": None, "level": 0,
        "parent_clause": None, "path": None,
    }
    table_idx = 0
    fig_idx = 0

    content: list[dict[str, Any]] = []
    seen_refs: set[str] = set()
    references: list[dict[str, Any]] = doc_in.get("references") or []
    have_refs = bool(references)

    for i, block in enumerate(blocks):
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

        item = _build_content_item(block, page_size_cache, clause_ctx)
        if item:
            if suffix and item["path"] == clause_ctx.get("clause"):
                item["path"] = (clause_ctx.get("clause") or "") + suffix
            content.append(item)

        if not have_refs:
            text = block.get("content")
            if isinstance(text, str):
                for match in _GOST_REF_RE.finditer(text):
                    code = f"ГОСТ {match.group(1)}"
                    if code in seen_refs:
                        continue
                    seen_refs.add(code)
                    references.append({
                        "target_doc_code": code,
                        "type": "single",
                        "context": text[:120],
                        "current_status": "active",
                        "note": None,
                    })

    terminology = doc_in.get("terminology") or []

    return {
        "source": {
            "file_name": source.get("file_name", ""),
            "file_hash_sha256": source.get("file_hash_sha256", ""),
            "page_count": int(source.get("page_count") or 1),
        },
        "metadata": {},
        "content": content,
        "terminology": terminology,
        "references": references,
    }



