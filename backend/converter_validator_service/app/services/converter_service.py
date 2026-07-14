from datetime import datetime, timezone
from typing import Any

from app.config import settings
from app.core.exceptions import ConversionFailedError, MetadataExtractionFailedError
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
    for field in (
        "doc_code",
        "title",
        "mks_oks_code",
        "okstu_code",
        "document_type",
        "era",
        "validity_status",
        "issuing_body",
        "source_type",
        "language",
        "jurisdiction",
    ):
        value = preview_meta.get(field)
        if value is not None:
            meta.setdefault(field, value)

    meta.setdefault("doc_code", None)
    meta.setdefault("title", None)
    meta["normalized_title"] = " ".join(
        (meta.get("title") or "").lower().split()
    )
    udk = preview_meta.get("udk_code")
    if udk:
        meta.setdefault("udk_code", udk)
        meta.setdefault("udc", udk)
    meta.setdefault("group", raw_json.get("group"))
    if raw_json.get("mks_oks_code"):
        meta.setdefault("mks_oks_code", raw_json["mks_oks_code"])
    if raw_json.get("okstu_code"):
        meta.setdefault("okstu_code", raw_json["okstu_code"])
    if raw_json.get("udc"):
        meta.setdefault("udc", raw_json["udc"])
    return hierarchy


def _extract_document_id(raw_json: dict[str, Any]) -> int | None:
    val = raw_json.get("document_id")
    if val is None:
        return None
    return int(val)


async def convert(
    *,
    task_id: int,
    version_id: int | None = None,
    raw_json: dict[str, Any],
    document_id: int | None = None,
    use_llm: bool = True,
    llm_max_tokens: int | None = None,
    llm_timeout: int | None = None,
    preview_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not raw_json:
        raise MetadataExtractionFailedError("raw_json is empty")

    # Если переданы preview-метаданные (уже извлечены на preview и возможно изменены пользователем),
    # используем их вместо повторного извлечения из raw_json.
    preview_meta = preview_metadata if preview_metadata else extract_preview_metadata(raw_json)
    try:
        hierarchy = build_hierarchy(raw_json)
    except Exception as exc:
        raise ConversionFailedError(
            f"Hierarchy build failed: {exc}"
        ) from exc

    if not hierarchy.get("content"):
        raise ConversionFailedError(
            "Hierarchy has no content — raw_json contains no document blocks"
        )

    hierarchy = _merge_document_metadata(hierarchy, preview_meta, raw_json)
    llm_usage = None
    if use_llm:
        max_tokens = llm_max_tokens if llm_max_tokens is not None else settings.llm_max_tokens
        timeout = llm_timeout if llm_timeout is not None else settings.llm_timeout
        hierarchy, llm_usage = await enrich_document(
            hierarchy,
            max_tokens=max_tokens,
            timeout=timeout,
        )

    document_id = document_id or _extract_document_id(raw_json)
    validation = await validate_document(
        hierarchy,
        task_id=task_id,
        version_id=version_id,
        document_id=document_id,
    )
    title_hash = validation["fingerprint"]["title_hash_sha256"]
    hierarchy["metadata"]["title_hash_sha256"] = title_hash

    parser_meta = (raw_json.get("metadata") or {}).get("parser") or {}
    # Пробрасываем качество из parser JSON в metadata документа
    raw_quality = (raw_json.get("metadata") or {}).get("quality") or raw_json.get("quality")
    if raw_quality and isinstance(raw_quality, dict):
        hierarchy.setdefault("metadata", {})["quality"] = raw_quality

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
        raise MetadataExtractionFailedError("raw_json is empty")
    meta = extract_preview_metadata(raw_json)
    if not meta.get("doc_code") or not meta.get("title"):
        raise MetadataExtractionFailedError(
            "Failed to extract required metadata: doc_code and title"
        )
    return meta
