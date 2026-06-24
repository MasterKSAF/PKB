from fastapi import APIRouter, status

from app.api.v1.schemas import (
    RawJsonRequest,
    ValidateDocumentResponse,
    ValidateMetadataRequest,
    ValidateMetadataResponse,
)
from app.services.document_validator import validate_document
from app.services.hierarchy_builder import build_hierarchy
from app.services.metadata_extractor import extract_preview_metadata
from app.services.normalizer import compute_business_key

router = APIRouter()


@router.post(
    "/metadata",
    status_code=status.HTTP_200_OK,
    response_model=ValidateMetadataResponse,
)
async def validate_metadata_endpoint(request: ValidateMetadataRequest):
    result = compute_business_key(
        era=request.era,
        source_type=request.source_type,
        doc_code=request.doc_code,
        title=request.title,
        mks_oks_code=request.mks_oks_code,
        okstu_code=request.okstu_code,
    )
    return ValidateMetadataResponse(
        title_hash_sha256=result.title_hash_sha256,
        title_key=result.title_key,
        normalized_title=result.normalized_title,
        source_type_normalized=result.source_type_normalized,
        era_normalized=result.era_normalized,
    )


@router.post(
    "/document",
    status_code=status.HTTP_200_OK,
    response_model=ValidateDocumentResponse,
)
async def validate_document_endpoint(request: RawJsonRequest):
    raw = request.raw_json
    if raw.get("document", {}).get("content"):
        document = raw["document"]
    else:
        preview_meta = extract_preview_metadata(raw)
        hierarchy = build_hierarchy(raw)
        hierarchy = hierarchy | {"metadata": hierarchy.get("metadata") or {}}
        meta = hierarchy["metadata"]
        for field in (
            "doc_code",
            "title",
            "mks_oks_code",
            "okstu_code",
            "era",
            "source_type",
            "udk_code",
            "issuing_body",
        ):
            value = preview_meta.get(field)
            if value is not None:
                meta.setdefault(field, value)
        document = hierarchy

    validation = await validate_document(
        document,
        task_id=request.task_id,
        version_id=request.version_id,
        document_id=request.document_id,
    )
    return ValidateDocumentResponse(**validation)
