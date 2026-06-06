from fastapi import APIRouter, status

from app.api.v1.schemas import (
    ConvertRequest,
    ConvertResponse,
    PreviewMetadataResponse,
    RawJsonRequest,
)
from app.services import converter_service

router = APIRouter()


@router.post(
    "/preview/metadata",
    status_code=status.HTTP_200_OK,
    response_model=PreviewMetadataResponse,
)
async def preview_metadata(request: RawJsonRequest):
    meta = converter_service.extract_metadata(request.raw_json)
    return PreviewMetadataResponse(**meta)


@router.post(
    "/convert",
    status_code=status.HTTP_200_OK,
    response_model=ConvertResponse,
)
async def convert_document(request: ConvertRequest):
    result = await converter_service.convert(
        task_id=request.task_id,
        version_id=request.version_id,
        raw_json=request.raw_json,
        use_llm=request.use_llm,
        llm_model=request.llm_model,
        llm_max_tokens=request.llm_max_tokens,
        llm_timeout=request.llm_timeout,
    )
    return ConvertResponse(**result)
