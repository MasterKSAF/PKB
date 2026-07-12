from __future__ import annotations

from typing import Any


def build_rag_builder_buildrequest_gap_report(payload: dict[str, Any]) -> list[str]:
    """Return missing fields that prevent payload from being a SPD RAG Builder BuildRequest."""

    missing: list[str] = []

    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        missing.append("metadata")
    else:
        _require(metadata, "schema", "metadata.schema", missing)
        _require(metadata, "document_id", "metadata.document_id", missing)

    document = payload.get("document")
    if not isinstance(document, dict):
        missing.append("document")
    else:
        _require(document, "id", "document.id", missing)
        _require(document, "pkb_code", "document.pkb_code", missing)
        _require(document, "doc_code", "document.doc_code", missing)
        _require(document, "title", "document.title", missing)

    sections = payload.get("sections")
    if not isinstance(sections, list):
        missing.append("sections")
        return missing

    for index, section in enumerate(sections):
        if not isinstance(section, dict):
            missing.append(f"sections[{index}]")
            continue

        prefix = f"sections[{index}]"
        _require(section, "section_id", f"{prefix}.section_id", missing)
        _require(section, "level", f"{prefix}.level", missing)
        _require(section, "path", f"{prefix}.path", missing)
        _require(section, "type", f"{prefix}.type", missing)
        _require(section, "content", f"{prefix}.content", missing)

    return missing


def _require(
    data: dict[str, Any],
    key: str,
    label: str,
    missing: list[str],
) -> None:
    if key not in data or data[key] is None:
        missing.append(label)


def build_rag_builder_buildrequest_envelope(
    payload: dict[str, Any],
    *,
    document_id: int,
    pkb_code: str,
    schema: str = "schema_registry_for_rag_v2",
) -> dict[str, Any]:
    """Return payload with SPD RAG Builder metadata/document envelope fields."""

    source_document = payload.get("document")
    if not isinstance(source_document, dict):
        source_document = {}

    document_code = _first_present_str(
        source_document.get("doc_code"),
        source_document.get("document_code"),
        source_document.get("code"),
        "",
    )

    title = _first_present_str(
        source_document.get("title"),
        source_document.get("full_title"),
        "",
    )

    result = dict(payload)
    result["metadata"] = {
        "schema": schema,
        "document_id": document_id,
    }
    result["document"] = {
        "id": document_id,
        "pkb_code": pkb_code,
        "doc_code": document_code,
        "title": title,
        "full_title": source_document.get("full_title"),
        "normalized_title": source_document.get("normalized_title"),
        "validity_status": source_document.get("validity_status"),
        "era": source_document.get("era"),
        "page_count": source_document.get("page_count"),
        "file_hash_sha256": source_document.get("file_hash_sha256"),
    }

    return result


def _first_present_str(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()

    return ""


def build_rag_builder_buildrequest_section_shape(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Return payload with sections normalized to SPD RAG Builder Section shape."""

    sections = payload.get("sections")
    if not isinstance(sections, list):
        return dict(payload)

    result = dict(payload)
    result["sections"] = [
        _build_rag_builder_section(section, fallback_id=index)
        for index, section in enumerate(sections, start=1)
        if isinstance(section, dict)
    ]

    return result


def _build_rag_builder_section(
    section: dict[str, Any],
    *,
    fallback_id: int,
) -> dict[str, Any]:
    raw = section.get("raw")
    if not isinstance(raw, dict):
        raw = {}

    section_id = _first_present_int(
        raw.get("section_id"),
        section.get("section_id"),
        fallback=fallback_id,
    )
    level = _first_present_int(
        section.get("level"),
        raw.get("level"),
        fallback=1,
    )

    title = _first_present_str(section.get("title"), raw.get("title"))
    text = _first_present_str(section.get("text"), raw.get("text"))
    content = _section_content(section=section, raw=raw, text=text, title=title)

    return {
        "section_id": section_id,
        "parent_id": _first_present_optional_int(
            raw.get("parent_id"),
            section.get("parent_id"),
        ),
        "clause": _first_present_optional_str(
            raw.get("clause"),
            section.get("clause"),
        ),
        "title": title or None,
        "level": level,
        "path": _first_present_str(
            section.get("path"),
            raw.get("path"),
            str(section_id),
        ),
        "page": _first_present_optional_int(
            raw.get("page"),
            section.get("page"),
            section.get("page_start"),
        ),
        "bbox": _first_present_list(raw.get("bbox"), section.get("bbox")),
        "type": _normalize_section_type(
            _first_present_str(
                raw.get("type"),
                section.get("type"),
                "text",
            )
        ),
        "content": content,
        "references": section.get("references", []),
    }


def _section_content(
    *,
    section: dict[str, Any],
    raw: dict[str, Any],
    text: str,
    title: str,
) -> dict[str, Any]:
    content = section.get("content")
    if isinstance(content, dict):
        return content

    raw_content = raw.get("content")
    if isinstance(raw_content, dict):
        return raw_content

    if text:
        return {"text": text}

    if title:
        return {"text": title}

    return {}


def _normalize_section_type(value: str) -> str:
    allowed = {
        "headerFooter",
        "text",
        "textBlock",
        "table",
        "list",
        "image",
        "formula",
    }
    if value in allowed:
        return value

    return "text"


def _first_present_int(*values: Any, fallback: int) -> int:
    value = _first_present_optional_int(*values)
    if value is None:
        return fallback

    return value


def _first_present_optional_int(*values: Any) -> int | None:
    for value in values:
        if isinstance(value, bool):
            continue

        if isinstance(value, int):
            return value

        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())

    return None


def _first_present_optional_str(*values: Any) -> str | None:
    value = _first_present_str(*values)
    if value:
        return value

    return None


def _first_present_list(*values: Any) -> list[Any] | None:
    for value in values:
        if isinstance(value, list):
            return value

    return None
