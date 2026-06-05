import hashlib
import uuid
from typing import Any

from app.services.metadata_extractor import extract_preview_metadata
from app.services.registry_client import validate_classifiers


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_title(title: str) -> str:
    return " ".join(title.lower().split())


def _extract_classification(
    document: dict[str, Any],
    preview_meta: dict[str, Any],
) -> dict[str, Any]:
    meta = document.get("metadata") or {}
    return {
        "mks_oks_code": meta.get("mks_oks_code"),
        "okstu_code": meta.get("okstu_code"),
        "udk_code": meta.get("udc") or meta.get("udk_code"),
        "doc_code": preview_meta.get("doc_code"),
        "document_type": preview_meta.get("document_type"),
    }


def _structure_valid(document: dict[str, Any]) -> bool:
    content = document.get("content") or []
    source = document.get("source") or {}
    if not content:
        return False
    if not source.get("file_name") and not source.get("file_hash_sha256"):
        return False
    return True


def _build_cross_references(
    references: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    cross_refs = []
    for ref in references:
        cross_refs.append({
            "target_doc_code": ref.get("target_doc_code"),
            "type": ref.get("type", "single"),
            "status": ref.get("current_status", "active"),
        })
    return cross_refs


def _decision(
    structure_valid: bool,
    classification: dict[str, Any],
) -> str:
    if not structure_valid:
        return "review_required"
    if classification.get("overall_status") == "CONFIRMED":
        return "auto"
    return "review_required"


async def validate_document(
    document: dict[str, Any],
    *,
    task_id: str,
    version_id: str,
    document_id: str | None = None,
) -> dict[str, Any]:
    preview_meta = extract_preview_metadata({"document": document})
    structure_ok = _structure_valid(document)

    title = (document.get("metadata") or {}).get("title") or preview_meta["title"]
    file_hash = (document.get("source") or {}).get("file_hash_sha256") or ""
    title_hash = _sha256_hex(_normalize_title(title))

    class_input = _extract_classification(document, preview_meta)
    classification = await validate_classifiers(class_input)

    matching = {
        "predecessor_doc_id": None,
        "successor_doc_id": None,
    }
    hints = document.get("_matching") or {}
    if isinstance(hints, dict):
        matching["predecessor_doc_id"] = hints.get("predecessor_doc_id")
        matching["successor_doc_id"] = hints.get("successor_doc_id")

    status = "completed" if structure_ok else "failed"
    return {
        "validation_id": f"val-{uuid.uuid4().hex[:8]}",
        "document_id": document_id or str(uuid.uuid4()),
        "structure_valid": structure_ok,
        "classification": classification,
        "fingerprint": {
            "file_hash_sha256": file_hash or _sha256_hex(task_id + version_id),
            "title_hash_sha256": title_hash,
        },
        "matching": matching,
        "cross_references": _build_cross_references(
            document.get("references") or []
        ),
        "decision": _decision(structure_ok, classification),
        "status": status,
    }
