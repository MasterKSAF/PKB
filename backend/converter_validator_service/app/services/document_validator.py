import hashlib
import uuid
from typing import Any

from app.services.metadata_extractor import extract_preview_metadata
from app.services.normalizer import (
    BusinessKeyResult,
    compute_business_key,
    infer_era,
    infer_source_type,
)
from app.services.registry_client import validate_classifiers
from app.core.exceptions import MetadataValidationError


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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


def _compute_fingerprint(
    document: dict[str, Any],
    preview_meta: dict[str, Any],
    *,
    task_id: int,
    version_id: int,
) -> dict[str, str]:
    meta = document.get("metadata") or {}
    source = document.get("source") or {}
    title = meta.get("title") or preview_meta.get("title") or ""
    doc_code = meta.get("doc_code") or preview_meta.get("doc_code") or ""
    issuing_body = meta.get("issuing_body") or source.get("author")
    era = meta.get("era") or infer_era(title, issuing_body, source.get("title"))
    source_type = meta.get("source_type") or infer_source_type(
        doc_code,
        title,
        source.get("title"),
    )
    try:
        key_result = compute_business_key(
            era=era,
            source_type=source_type,
            doc_code=doc_code,
            title=title,
            mks_oks_code=meta.get("mks_oks_code"),
            okstu_code=meta.get("okstu_code"),
        )
        title_hash = key_result.title_hash_sha256
        title_key = key_result.title_key
    except MetadataValidationError:
        # doc_code/title могут отсутствовать (циркулярные письма, не-ГОСТы).
        # Создаём fallback fingerprint из task_id.
        fallback_raw = f"{task_id}:{version_id or '0'}:no_doc_code"
        title_hash = _sha256_hex(fallback_raw)
        title_key = f"fallback:{fallback_raw}"

    file_hash = source.get("file_hash_sha256") or ""
    if not file_hash:
        file_hash = _sha256_hex(f"{task_id}:{version_id or '0'}")

    return {
        "file_hash_sha256": file_hash,
        "title_hash_sha256": title_hash,
        "title_key": title_key,
    }


async def validate_document(
    document: dict[str, Any],
    *,
    task_id: int,
    version_id: int | None = None,
    document_id: int | None = None,
) -> dict[str, Any]:
    preview_meta = extract_preview_metadata({"document": document})
    structure_ok = _structure_valid(document)
    fingerprint = _compute_fingerprint(
        document,
        preview_meta,
        task_id=task_id,
        version_id=version_id,
    )

    class_input = _extract_classification(document, preview_meta)
    classification = await validate_classifiers(class_input)

    matching = {
        "predecessor_doc_id": None,
        "successor_doc_id": None,
    }
    hints = document.get("_matching") or {}
    if isinstance(hints, dict):
        pred = hints.get("predecessor_doc_id")
        succ = hints.get("successor_doc_id")
        matching["predecessor_doc_id"] = int(pred) if pred is not None else None
        matching["successor_doc_id"] = int(succ) if succ is not None else None

    status = "completed" if structure_ok else "failed"
    return {
        "validation_id": f"val-{uuid.uuid4().hex[:8]}",
        "document_id": document_id,
        "structure_valid": structure_ok,
        "classification": classification,
        "fingerprint": fingerprint,
        "matching": matching,
        "cross_references": _build_cross_references(
            document.get("references") or []
        ),
        "decision": _decision(structure_ok, classification),
        "status": status,
    }
