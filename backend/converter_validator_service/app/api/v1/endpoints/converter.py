import logging

from fastapi import APIRouter, status

from app.api.v1.schemas import (
    ConvertRequest,
    ConvertResponse,
    PreviewMetadataResponse,
    RawJsonRequest,
)
from app.config import settings
from app.core.exceptions import MetadataExtractionFailedError
from app.services import converter_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/preview",
    status_code=status.HTTP_200_OK,
    response_model=PreviewMetadataResponse,
)
async def preview(request: RawJsonRequest):
    try:
        meta = converter_service.extract_metadata(request.raw_json)
        return PreviewMetadataResponse(**meta)
    except MetadataExtractionFailedError as exc:
        # Сканированный PDF без текстового слоя — метаданные не извлечены.
        # Возвращаем 200 с пустыми полями, чтобы оркестратор мог
        # выполнить OCR fallback вместо жёсткой ошибки.
        logger.warning(
            f"Metadata extraction failed for task {request.task_id}: {exc}. "
            f"Returning empty preview — orchestrator will fallback to OCR."
        )
        return PreviewMetadataResponse()


@router.post(
    "/convert",
    status_code=status.HTTP_200_OK,
    response_model=ConvertResponse,
)
async def convert_document(request: ConvertRequest):
    llm_max_tokens = request.llm_max_tokens or settings.llm_max_tokens
    llm_timeout = request.llm_timeout or settings.llm_timeout
    result = await converter_service.convert(
        task_id=request.task_id,
        version_id=request.version_id,
        raw_json=request.raw_json,
        document_id=request.document_id,
        use_llm=request.use_llm,
        llm_max_tokens=llm_max_tokens,
        llm_timeout=llm_timeout,
    )
    return ConvertResponse(**result)
