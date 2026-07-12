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
