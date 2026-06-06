from fastapi import APIRouter, status

from app.api.v1.schemas import RawJsonRequest, ValidateDocumentResponse
from app.services.document_validator import validate_document
from app.services.hierarchy_builder import build_hierarchy
from app.services.metadata_extractor import extract_preview_metadata

router = APIRouter()


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
        meta.setdefault("doc_code", preview_meta.get("doc_code"))
        meta.setdefault("title", preview_meta.get("title"))
        document = hierarchy

    validation = await validate_document(
        document,
        task_id=request.task_id,
        version_id=request.version_id,
    )
    return ValidateDocumentResponse(**validation)
