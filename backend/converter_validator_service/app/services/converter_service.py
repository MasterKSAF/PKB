import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import ConversionFailedError
from app.services.document_validator import validate_document
from app.services.hierarchy_builder import build_hierarchy
from app.services.llm_processor import enrich_document
from app.services.metadata_extractor import extract_preview_metadata


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _merge_document_metadata(
    hierarchy: dict[str, Any],
    preview_meta: dict[str, Any],
    raw_json: dict[str, Any],
) -> dict[str, Any]:
    meta = hierarchy.setdefault("metadata", {})
    meta.setdefault("doc_code", preview_meta.get("doc_code") or "")
    meta.setdefault("title", preview_meta.get("title") or "")
    meta["normalized_title"] = " ".join(
        (meta.get("title") or "").lower().split()
    )
    meta.setdefault("group", raw_json.get("group"))
    meta.setdefault("mks_oks_code", raw_json.get("mks_oks_code"))
    meta.setdefault("okstu_code", raw_json.get("okstu_code"))
    meta.setdefault("udc", raw_json.get("udc"))
    meta.setdefault("era", "USSR" if "СССР" in meta.get("title", "") else "RF")
    meta.setdefault("validity_status", "active")
    meta.setdefault("issuing_body", (raw_json.get("document") or {}).get(
        "source", {}
    ).get("author"))
    return hierarchy


async def convert(
    *,
    task_id: str,
    version_id: str,
    raw_json: dict[str, Any],
    use_llm: bool = False,
    llm_model: str = "gpt-4o-mini",
    llm_max_tokens: int = 4096,
    llm_timeout: int = 60,
) -> dict[str, Any]:
    if not raw_json:
        raise ConversionFailedError("raw_json is empty")

    preview_meta = extract_preview_metadata(raw_json)
    try:
        hierarchy = build_hierarchy(raw_json)
    except Exception as exc:
        raise ConversionFailedError(
            f"Hierarchy build failed: {exc}"
        ) from exc

    hierarchy = _merge_document_metadata(hierarchy, preview_meta, raw_json)
    llm_usage = None
    if use_llm:
        hierarchy, llm_usage = await enrich_document(
            hierarchy,
            model=llm_model,
            max_tokens=llm_max_tokens,
            timeout=llm_timeout,
        )

    document_id = str(uuid.uuid4())
    validation = await validate_document(
        hierarchy,
        task_id=task_id,
        version_id=version_id,
        document_id=document_id,
    )
    title_hash = validation["fingerprint"]["title_hash_sha256"]
    hierarchy["metadata"]["title_hash_sha256"] = title_hash

    parser_meta = (raw_json.get("metadata") or {}).get("parser") or {}
    response_metadata = {
        "schema": "validated_v3",
        "task_id": task_id,
        "created_at": _utc_now_iso(),
        "parser": parser_meta,
    }

    result = {
        "task_id": task_id,
        "version_id": version_id,
        "document_id": validation["document_id"],
        "metadata": response_metadata,
        "document": hierarchy,
        "validation": {
            k: v for k, v in validation.items() if k != "document_id"
        },
    }
    if llm_usage:
        result["llm_usage"] = llm_usage
    return result


def extract_metadata(raw_json: dict[str, Any]) -> dict[str, Any]:
    if not raw_json:
        raise ConversionFailedError("raw_json is empty")
    return extract_preview_metadata(raw_json)
