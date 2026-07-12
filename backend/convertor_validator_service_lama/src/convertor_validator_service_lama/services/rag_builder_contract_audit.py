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
