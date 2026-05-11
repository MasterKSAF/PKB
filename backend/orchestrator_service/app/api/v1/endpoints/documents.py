"""Documents API endpoints — upload, list, view, delete, reprocess, errors, pages, parameters, queue."""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from app.api.deps import CurrentUser, get_current_user
from app.schemas.common import ErrorResponse, PaginationMeta
from app.schemas.documents import (
    BlockCoordinates,
    DocumentCreateResponse,
    DocumentDeleteResponse,
    DocumentDetailMetadata,
    DocumentDetailResponse,
    DocumentErrorsResponse,
    DocumentFileResponse,
    DocumentListItem,
    DocumentListResponse,
    DocumentPagesResponse,
    DocumentParameters,
    DocumentParametersResponse,
    DocumentQueueResponse,
    DocumentStatus,
    DocumentStatusCompleted,
    DocumentStatusFailed,
    DocumentStatusProcessing,
    DocumentSummary,
    DocumentType,
    PageBlock,
    PageBlockDetail,
    PageInfo,
    PagePreviewResponse,
    PageTextResponse,
    PageViewResponse,
    ProcessingError,
    QueueItem,
    QueueMeta,
    ReprocessRequest,
    ReprocessResponse,
    SpecificationItem,
    StatusSteps,
    StepStatus,
)
from app.services.integration_client import IntegrationServiceClient
from app.services.rag_client import RAGServiceClient
from app.services.validate_client import ValidationServiceClient

router = APIRouter()

MOCK_USER_ID = "u-mock-001"
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB


def _mock_user() -> str:
    """Return the mock user ID used during development."""
    return MOCK_USER_ID


# ---------------------------------------------------------------------------
#  POST /documents/
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=DocumentCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Неподдерживаемый формат / размер",
        },
        413: {"model": ErrorResponse, "description": "Файл превышает 100 МБ"},
        422: {"model": ErrorResponse, "description": "Поврежденный файл"},
    },
)
async def upload_document(
    file: UploadFile = File(..., description="Бинарный файл (PDF, PNG, JPG, TIFF)"),
    document_type: str = Form(
        ...,
        description="Тип документа: normative, archival_scan, drawing, specification",
    ),
    metadata: Optional[str] = Form(None, description="JSON-строка с метаданными"),
    current_user: CurrentUser = Depends(get_current_user),
) -> DocumentCreateResponse:
    """Upload a new document for processing.

    Returns 202 with the created document metadata.
    """
    # --- Validate file type ---
    allowed_mime = {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/tiff",
    }
    if file.content_type not in allowed_mime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "BAD_REQUEST",
                    "message": "Неподдерживаемый формат файла",
                    "details": {"allowed_types": list(allowed_mime)},
                }
            },
        )

    # --- Validate file size (via Content-Length header if present) ---
    content_length: Optional[int] = None
    if hasattr(file, "headers") and file.headers:
        try:
            cl = file.headers.get("content-length")
            if cl:
                content_length = int(cl)
        except (ValueError, TypeError):
            content_length = None

    if content_length is not None and content_length > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": "Размер файла превышает 100 МБ",
                    "details": {
                        "max_size_mb": 100,
                        "actual_size_mb": round(content_length / (1024 * 1024), 1),
                    },
                }
            },
        )

    # --- Upload file to integration / storage service ---
    document_id = f"doc-{uuid.uuid4().hex[:7]}"
    task_id = f"task-ocr-{uuid.uuid4().hex[:6]}"

    integration_client = IntegrationServiceClient()
    try:
        content = await file.read()
        await integration_client.upload_file(
            file_data=content,
            filename=file.filename or "uploaded_file",
            related_document_id=document_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "UPLOAD_FAILED",
                    "message": "Ошибка при загрузке файла в хранилище",
                    "details": {"original_error": str(exc)},
                }
            },
        )
    finally:
        await integration_client.close()

    return DocumentCreateResponse(
        document_id=document_id,
        status=DocumentStatus.QUEUED,
        user_id=current_user.user_id,
        task_id=task_id,
        created_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
#  GET /documents/
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=DocumentListResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Неверные параметры запроса"},
    },
)
async def list_documents(
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    type: Optional[str] = Query(None, description="Фильтр по типу документа"),
    date_from: Optional[datetime] = Query(None, description="Дата начала (ISO 8601)"),
    date_to: Optional[datetime] = Query(None, description="Дата окончания"),
    search: Optional[str] = Query(None, description="Поиск по имени файла"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> DocumentListResponse:
    """List documents with optional filtering."""
    user_id = _mock_user()
    now = datetime.utcnow()

    items = [
        DocumentListItem(
            document_id="doc-8a3f2b",
            title="21900M2_spec.pdf",
            document_type=DocumentType.SPECIFICATION,
            source="upload",
            version=1,
            pages=12,
            ocr_status="in_progress",
            index_status="pending",
            user_id=user_id,
            uploaded_by=user_id,
            created_at=now,
            updated_at=now,
        )
    ]

    page = (offset // limit) + 1 if limit else 1

    return DocumentListResponse(
        summary=DocumentSummary(
            total=1,
            ocr_completed=0,
            indexed=0,
            need_attention=0,
        ),
        items=items,
        meta=PaginationMeta(total=1, page=page, page_size=limit),
    )


# ---------------------------------------------------------------------------
#  GET /documents/queue
# ---------------------------------------------------------------------------


@router.get(
    "/queue",
    response_model=DocumentQueueResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Неверные параметры запроса"},
    },
)
async def get_queue(
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(50, ge=1, le=200, description="Записей на странице"),
) -> DocumentQueueResponse:
    """Get the current document processing queue."""
    user_id = _mock_user()
    now = datetime.utcnow()

    queue = [
        QueueItem(
            document_id="doc-8a3f2b",
            title="21900M2_spec.pdf",
            document_type=DocumentType.SPECIFICATION,
            status=DocumentStatus.PROCESSING,
            progress_percent=41.7,
            steps=StatusSteps(
                ocr=StepStatus.IN_PROGRESS,
                layout_parsing=StepStatus.PENDING,
                indexing=StepStatus.PENDING,
            ),
            user_id=user_id,
            uploaded_by=user_id,
            created_at=now,
            started_at=now,
            estimated_completion=now,
        )
    ]

    return DocumentQueueResponse(
        queue=queue,
        meta=QueueMeta(total_in_queue=len(queue), page=page, page_size=page_size),
    )


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}
# ---------------------------------------------------------------------------


@router.get(
    "/{doc_id}",
    response_model=DocumentDetailResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Документ не найден"},
    },
)
async def get_document(doc_id: str) -> DocumentDetailResponse:
    """Get detailed document information."""
    user_id = _mock_user()
    now = datetime.utcnow()

    return DocumentDetailResponse(
        document_id=doc_id,
        filename="21900M2_spec.pdf",
        document_type=DocumentType.SPECIFICATION,
        status=DocumentStatus.PROCESSED,
        file_size=2_048_576,
        pages_total=12,
        pages_processed=12,
        pages_failed=0,
        user_id=user_id,
        uploaded_by=user_id,
        created_at=now,
        updated_at=now,
        metadata=DocumentDetailMetadata(project="21900M2", author="Иванов"),
    )


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/status
# ---------------------------------------------------------------------------


@router.get(
    "/{doc_id}/status",
    response_model=(
        DocumentStatusProcessing | DocumentStatusCompleted | DocumentStatusFailed
    ),
    responses={
        404: {"model": ErrorResponse, "description": "Документ не найден"},
    },
)
async def get_document_status(
    doc_id: str,
) -> DocumentStatusProcessing | DocumentStatusCompleted | DocumentStatusFailed:
    """Get current processing status for a document.

    Returns one of three shapes depending on where the document is
    in its lifecycle:
      - **processing** — still running
      - **completed**  — finished successfully
      - **failed**     — finished with an error
    """
    user_id = _mock_user()
    now = datetime.utcnow()

    return DocumentStatusProcessing(
        document_id=doc_id,
        user_id=user_id,
        status=DocumentStatus.PROCESSING,
        progress_percent=41.7,
        steps=StatusSteps(
            ocr=StepStatus.IN_PROGRESS,
            layout_parsing=StepStatus.PENDING,
            indexing=StepStatus.PENDING,
        ),
        started_at=now,
        estimated_completion=now,
    )


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/file
# ---------------------------------------------------------------------------


@router.get(
    "/{doc_id}/file",
    response_model=DocumentFileResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Документ не найден"},
    },
)
async def get_document_file(doc_id: str) -> DocumentFileResponse:
    """Get file download information for a document."""
    return DocumentFileResponse(
        document_id=doc_id,
        document_title="21900M2_spec.pdf",
        content_type="application/pdf",
        file_url=f"/files/{doc_id}/download",
    )


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/pages
# ---------------------------------------------------------------------------


@router.get(
    "/{doc_id}/pages",
    response_model=DocumentPagesResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Документ не найден"},
    },
)
async def get_document_pages(
    doc_id: str,
    page: int = Query(1, ge=1, description="Номер страницы для пагинации"),
    page_size: int = Query(50, ge=1, le=200, description="Записей на странице"),
) -> DocumentPagesResponse:
    """Get a paginated list of pages for a document."""
    pages = [
        PageInfo(
            page=1,
            width=2480,
            height=3508,
            ocr_status="completed",
            confidence=0.98,
            has_text_layer=True,
        ),
        PageInfo(
            page=2,
            width=2480,
            height=3508,
            ocr_status="completed",
            confidence=0.95,
            has_text_layer=True,
        ),
    ]

    return DocumentPagesResponse(
        document_id=doc_id,
        pages_total=len(pages),
        pages=pages,
        meta=PaginationMeta(total=len(pages), page=page, page_size=page_size),
    )


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/pages/{page_num}
# ---------------------------------------------------------------------------


@router.get(
    "/{doc_id}/pages/{page_num}",
    response_model=PageViewResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Документ или страница не найдены",
        },
    },
)
async def get_page_view(
    doc_id: str,
    page_num: int,
    highlight: Optional[str] = Query(None, description="ID блока для подсветки"),
) -> PageViewResponse:
    """Get a page image with highlighted block overlays."""
    return PageViewResponse(
        image_url=f"/files/page-img/{doc_id}_{page_num}.png",
        page=page_num,
        width=2480,
        height=3508,
        blocks=[
            PageBlock(
                block_id="blk-001",
                type="title_block",
                coordinates=BlockCoordinates(x=200, y=100, width=800, height=50),
                text="Спецификация 21900M2.362135.0903",
                highlighted=False,
            ),
            PageBlock(
                block_id=highlight or "blk-002",
                type="table",
                coordinates=BlockCoordinates(x=150, y=200, width=1800, height=600),
                text="...",
                highlighted=highlight is not None,
            ),
        ],
    )


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/pages/{page_num}/text
# ---------------------------------------------------------------------------


@router.get(
    "/{doc_id}/pages/{page_num}/text",
    response_model=PageTextResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Документ или страница не найдены",
        },
    },
)
async def get_page_text(doc_id: str, page_num: int) -> PageTextResponse:
    """Get the text layer and block structure of a page."""
    return PageTextResponse(
        page=page_num,
        full_text="Спецификация...\nПоз. 1 Кница...",
        blocks=[
            PageBlockDetail(
                block_id="blk-001",
                type="title_block",
                coordinates=BlockCoordinates(x=200, y=100, width=800, height=50),
                text="Спецификация 21900M2.362135.0903",
                confidence=0.98,
            ),
            PageBlockDetail(
                block_id="blk-002",
                type="table",
                coordinates=BlockCoordinates(x=150, y=200, width=1800, height=600),
                text="Поз.|Наименование|Кол.|Масса|Материал",
                confidence=0.92,
                table_data=[
                    ["Поз.", "Наименование", "Кол.", "Масса", "Материал"],
                    ["1", "Кница", "2", "0.5", "сталь 09Г2С"],
                ],
            ),
        ],
    )


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/pages/{page_num}/preview
# ---------------------------------------------------------------------------


@router.get(
    "/{doc_id}/pages/{page_num}/preview",
    response_model=PagePreviewResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Документ или страница не найдены",
        },
    },
)
async def get_page_preview(
    doc_id: str,
    page_num: int,
    highlight: Optional[str] = Query(None, description="ID блока для подсветки"),
) -> PagePreviewResponse:
    """Get a preview image (thumbnail) of a page."""
    return PagePreviewResponse(
        document_id=doc_id,
        document_title="21900M2_spec.pdf",
        page=page_num,
        content_type="image/png",
        preview_url=f"/files/page-img/{doc_id}_{page_num}_prev.png",
        text=None,
        highlight=highlight,
    )


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/errors
# ---------------------------------------------------------------------------


@router.get(
    "/{doc_id}/errors",
    response_model=DocumentErrorsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Документ не найден"},
    },
)
async def get_document_errors(
    doc_id: str,
    stage: Optional[str] = Query(
        None, description="Этап: upload, ocr, parsing, indexing, generation"
    ),
    severity: Optional[str] = Query(None, description="Уровень: warning, error"),
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
) -> DocumentErrorsResponse:
    """Get the processing error / warning log for a document."""
    errors: list[ProcessingError] = []

    if not stage or stage == "ocr":
        errors.append(
            ProcessingError(
                error_id="err-001",
                document_id=doc_id,
                page=5,
                stage="ocr",
                error_code="LOW_CONFIDENCE",
                error_message="Качество распознавания страницы ниже порога (confidence=0.62)",
                severity=severity or "warning",
                retry_attempt=0,
                timestamp=datetime.utcnow(),
            )
        )

    page_num = (offset // limit) + 1 if limit else 1

    return DocumentErrorsResponse(
        errors=errors,
        meta=PaginationMeta(total=len(errors), page=page_num, page_size=limit),
    )


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/parameters
# ---------------------------------------------------------------------------


@router.get(
    "/{doc_id}/parameters",
    response_model=DocumentParametersResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Документ не найден"},
    },
)
async def get_document_parameters(doc_id: str) -> DocumentParametersResponse:
    """Get extracted structured parameters from a document.

    Attempts to call the Validation Service first; falls back to mock data.
    """
    validate_client = ValidationServiceClient()
    try:
        result = await validate_client.extract_parameters(
            document_id=doc_id, document_type=DocumentType.SPECIFICATION
        )
        return DocumentParametersResponse(**result)
    except Exception:
        return DocumentParametersResponse(
            document_id=doc_id,
            document_type=DocumentType.SPECIFICATION,
            parameters=DocumentParameters(
                designation="21900M2.362135.0903",
                title="Секция 0903",
                materials=["сталь 09Г2С", "алюминий АМг5"],
                dimensions=["1200x800x6", "L=2500"],
                references=[
                    "21900M2.362135.0901СБ",
                    "21900M2.362135.0902СБ",
                ],
                specification_items=[
                    SpecificationItem(
                        position="1",
                        name="Кница",
                        quantity="2",
                        dimensions="10x200x300",
                        weight="0.5",
                        material="сталь 09Г2С",
                        note="",
                    )
                ],
            ),
            extraction_confidence=0.89,
            unconfirmed_fields=["dimensions позиции 3"],
            updated_at=datetime.utcnow(),
        )
    finally:
        await validate_client.close()


# ---------------------------------------------------------------------------
#  DELETE /documents/{doc_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/{doc_id}",
    response_model=DocumentDeleteResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Документ не найден"},
    },
)
async def delete_document(doc_id: str) -> DocumentDeleteResponse:
    """Delete a document and all related data (including index)."""
    rag_client = RAGServiceClient()
    try:
        await rag_client.delete_index(doc_id)
    except Exception:
        pass  # non-indexed documents are fine
    finally:
        await rag_client.close()

    return DocumentDeleteResponse(
        document_id=doc_id,
        deleted_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
#  POST /documents/{doc_id}/reprocess
# ---------------------------------------------------------------------------


@router.post(
    "/{doc_id}/reprocess",
    response_model=ReprocessResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        404: {"model": ErrorResponse, "description": "Документ не найден"},
        409: {
            "model": ErrorResponse,
            "description": "Документ уже обрабатывается",
        },
    },
)
async def reprocess_document(
    doc_id: str,
    request: ReprocessRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> ReprocessResponse:
    """Re-process an already-uploaded document."""
    task_id = f"task-ocr-{uuid.uuid4().hex[:6]}"

    return ReprocessResponse(
        mode=request.mode,
        document_id=doc_id,
        user_id=current_user.user_id,
        task_id=task_id,
        status="reprocessing_queued",
        created_at=datetime.utcnow(),
    )
