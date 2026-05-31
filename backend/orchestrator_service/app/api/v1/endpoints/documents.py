"""Documents API endpoints — upload, list, view, delete, reprocess, errors, pages, parameters, queue, tasks, versions, approve, history."""

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
    ApproveRequest,
    ApproveResponse,
    ClassificationStatus,
    DecideRequest,
    DecideResponse,
    DocMetadata,
    DocumentCreateResponse,
    DocumentDeleteResponse,
    DocumentDetailResponse,
    DocumentErrorsResponse,
    DocumentFileResponse,
    DocumentHistoryResponse,
    DocumentListItem,
    DocumentListResponse,
    DocumentPagesResponse,
    DocumentParametersResponse,
    DocumentQueueResponse,
    DocumentStatus,
    DocumentStatusProcessing,
    DocumentStatusResponse,
    DocumentStatusReviewRequired,
    DocumentStatusReadyForPromotion,
    DocumentSummary,
    DuplicateCandidate,
    HistoryComment,
    HistoryItem,
    LatestVersionInfo,
    PageBlockDetail,
    PageInfo,
    PagePreviewResponse,
    PageTextResponse,
    PageViewResponse,
    ParameterItem,
    ParameterRange,
    PreviewBlock,
    PreviewMetadata,
    ProcessingError,
    QueueItem,
    QueueMeta,
    QueuePipelineSteps,
    QueuePipelineField,
    ReprocessMode,
    ReprocessRequest,
    ReprocessResponse,
    SourceType,
    TaskPreviewResponse,
    TaskPreviewStatusResponse,
    VersionCreateResponse,
    VersionItem,
    VersionMeta,
    VersionsListResponse,
    DecideAction,
    StepStatusEnum,
    PipelineStatusEnum,
    OcrParserStep,
    ConverterValidatorStep,
    DecisionStep,
    PreviewPhase,
    ParsingStep,
    ValidationStep,
    ValidationErrorItem,
    RegistryStep,
    FormationPipeline,
    RagIndexingStep,
    IndexationPipeline,
    StatusPipelines,
    PipelinesField,
    ChunkSummary,
)
from app.services.integration_client import IntegrationServiceClient
from app.services.rag_client import RAGServiceClient

router = APIRouter()

MOCK_USER_ID = "u-mock-001"
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB

# Supported MIME types for upload
ALLOWED_MIME = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/tiff",
}


def _mock_user() -> str:
    """Return the mock user ID used during development."""
    return MOCK_USER_ID


def _compute_sha256(content: bytes) -> str:
    """Compute SHA-256 hex digest."""
    import hashlib
    return hashlib.sha256(content).hexdigest()


# ---------------------------------------------------------------------------
#  POST /documents/  — Upload file
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=DocumentCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": ErrorResponse, "description": "Неподдерживаемый формат / размер"},
        413: {"model": ErrorResponse, "description": "Файл превышает 100 МБ"},
        422: {"model": ErrorResponse, "description": "Поврежденный файл"},
    },
)
async def upload_document(
    file: UploadFile = File(..., description="Бинарный файл (PDF, PNG, JPG, TIFF)"),
    source_type: str = Form(
        ...,
        description="Тип источника: GOST, GOST_R, OST, RD, TU, ISO, DNV, ASTM, OTHER",
    ),
    title: Optional[str] = Form(None, description="Название документа"),
    doc_code: Optional[str] = Form(None, description="Регистрационный номер"),
    mks_oks_code: Optional[str] = Form(None, description="Код МКС/ОКС"),
    okstu_code: Optional[str] = Form(None, description="Код ОКСТУ"),
    era: Optional[str] = Form(None, description="Эпоха: USSR, CIS, RF, CURRENT"),
    jurisdiction: Optional[str] = Form(None, description="Юрисдикция: RU, EU, US, NO, INTL"),
    issuing_body: Optional[str] = Form(None, description="Организация-издатель"),
    metadata: Optional[str] = Form(None, description="JSON-строка с доп. данными"),
    current_user: CurrentUser = Depends(get_current_user),
) -> DocumentCreateResponse:
    """Upload a new document for processing.

    Returns 202 with the created document metadata.
    """
    # --- Validate file type ---
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "BAD_REQUEST",
                    "message": "Неподдерживаемый формат файла",
                    "details": {"allowed_types": list(ALLOWED_MIME)},
                }
            },
        )

    # --- Validate source_type ---
    try:
        SourceType(source_type)
    except ValueError:
        valid_types = [e.value for e in SourceType]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "BAD_REQUEST",
                    "message": f"Недопустимый source_type: {source_type}",
                    "details": {"allowed_values": valid_types},
                }
            },
        )

    # --- Validate file size ---
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

    # --- Read file content for hash ---
    content = await file.read()
    file_hash = _compute_sha256(content)
    file_size = len(content)

    # --- Upload file to integration / storage service ---
    document_id = f"doc-{uuid.uuid4().hex[:12]}"
    task_id = int(uuid.uuid4().int % 1000000)
    version_id = str(uuid.uuid4())

    integration_client = IntegrationServiceClient()
    try:
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

    # Compute title hash for business key
    title_hash = None
    if title:
        title_hash = _compute_sha256(title.encode("utf-8"))

    return DocumentCreateResponse(
        task_id=task_id,
        version_id=version_id,
        status="uploaded",
        file_hash_sha256=file_hash,
        file_size_bytes=file_size,
        is_duplicate_file=False,
        is_duplicate_document=False,
        title_hash_sha256=title_hash,
        created_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
#  POST /tasks/{task_id}/preview  — Start preview phase
# ---------------------------------------------------------------------------


@router.post(
    "/tasks/{task_id}/preview",
    response_model=TaskPreviewResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        404: {"model": ErrorResponse, "description": "Задача не найдена"},
    },
)
async def start_preview(
    task_id: int,
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskPreviewResponse:
    """Start the preview phase for a document."""
    from datetime import timedelta

    return TaskPreviewResponse(
        task_id=task_id,
        status="previewing",
        estimated_completion=datetime.utcnow() + timedelta(seconds=30),
    )


# ---------------------------------------------------------------------------
#  GET /tasks/{task_id}/preview/status  — Preview status with longpoll
# ---------------------------------------------------------------------------


@router.get(
    "/tasks/{task_id}/preview/status",
    response_model=TaskPreviewStatusResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Задача не найдена"},
    },
)
async def get_preview_status(
    task_id: int,
    longpoll: int = Query(15, ge=0, le=60, description="Время ожидания (сек)"),
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskPreviewStatusResponse:
    """Get preview status with longpoll support."""
    return TaskPreviewStatusResponse(
        document_id=f"doc-{uuid.uuid4().hex[:12]}",
        status="completed",
        ocr_parser_status="completed",
        converter_validator_status="completed",
        preview=PreviewMetadata(
            doc_code="ГОСТ 20868-81",
            title="СТОЙКИ УСТАНОВОЧНЫЕ КРЕПЕЖНЫЕ. Технические требования",
            document_type="normative",
            year="1981",
            revision=None,
        ),
        duplicates=[
            DuplicateCandidate(
                document_id=f"doc-{uuid.uuid4().hex[:12]}",
                doc_code="ГОСТ 20868-81",
                title="Стойки установочные крепежные. Технические требования",
                similarity=0.97,
            )
        ],
        decision_required=True,
    )


# ---------------------------------------------------------------------------
#  POST /tasks/{task_id}/decide  — User decision after preview
# ---------------------------------------------------------------------------


@router.post(
    "/tasks/{task_id}/decide",
    response_model=DecideResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        404: {"model": ErrorResponse, "description": "Задача не найдена"},
        409: {"model": ErrorResponse, "description": "Некорректный статус для решения"},
    },
)
async def decide_task(
    task_id: int,
    request: DecideRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> DecideResponse:
    """Submit user decision after preview phase."""
    doc_id = f"doc-{uuid.uuid4().hex[:12]}"

    messages = {
        DecideAction.PROCEED: "Запущена полная обработка документа",
        DecideAction.STOP_DUPLICATE: "Остановлено. Документ помечен как дубликат",
        DecideAction.FORCE_NEW_VERSION: "Принудительное создание новой версии",
    }

    statuses = {
        DecideAction.PROCEED: "proceeding",
        DecideAction.STOP_DUPLICATE: "stopped",
        DecideAction.FORCE_NEW_VERSION: "forcing",
    }

    return DecideResponse(
        document_id=doc_id,
        status=statuses[request.action],
        action=request.action,
        message=messages[request.action],
    )


# ---------------------------------------------------------------------------
#  POST /documents/{doc_id}/versions  — Upload new version
# ---------------------------------------------------------------------------


@router.post(
    "/{doc_id}/versions",
    response_model=VersionCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        404: {"model": ErrorResponse, "description": "Документ не найден"},
    },
)
async def upload_version(
    doc_id: str,
    file: UploadFile = File(..., description="Бинарный файл новой версии"),
    current_user: CurrentUser = Depends(get_current_user),
) -> VersionCreateResponse:
    """Upload a new file version for an existing document."""
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "BAD_REQUEST",
                    "message": "Неподдерживаемый формат файла",
                    "details": {"allowed_types": list(ALLOWED_MIME)},
                }
            },
        )

    content = await file.read()
    file_hash = _compute_sha256(content)
    task_id = int(uuid.uuid4().int % 1000000)
    version_id = str(uuid.uuid4())

    return VersionCreateResponse(
        document_id=doc_id,
        version_id=version_id,
        version_number=2,
        status="uploaded",
        task_id=task_id,
        file_hash_sha256=file_hash,
        is_duplicate_file=False,
        created_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/versions  — List versions
# ---------------------------------------------------------------------------


@router.get(
    "/{doc_id}/versions",
    response_model=VersionsListResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Документ не найден"},
    },
)
async def list_versions(
    doc_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> VersionsListResponse:
    """List all file versions of a document."""
    now = datetime.utcnow()
    return VersionsListResponse(
        document_id=doc_id,
        versions=[
            VersionItem(
                version_id=str(uuid.uuid4()),
                version_number=1,
                format_code="pdf_digital",
                format_label="PDF (цифровой)",
                file_key=f"{doc_id}/v1/e3b0c442...855.pdf",
                file_hash_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                size_bytes=2048576,
                uploaded_at=now,
                uploaded_by="Иванов И.И.",
            )
        ],
        meta=VersionMeta(total=1),
    )


# ---------------------------------------------------------------------------
#  GET /documents/  — List documents
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=DocumentListResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Неверные параметры запроса"},
    },
)
async def list_documents(
    status: Optional[str] = Query(None, description="Фильтр по статусу FSM"),
    source_type: Optional[str] = Query(None, description="Фильтр по типу источника"),
    era: Optional[str] = Query(None, description="Фильтр по эпохе"),
    validity_status: Optional[str] = Query(None, description="Фильтр по статусу действия"),
    jurisdiction: Optional[str] = Query(None, description="Фильтр по юрисдикции"),
    mks_oks_code: Optional[str] = Query(None, description="Фильтр по коду МКС/ОКС"),
    okstu_code: Optional[str] = Query(None, description="Фильтр по коду ОКСТУ"),
    doc_code: Optional[str] = Query(None, description="Поиск по номеру документа"),
    search: Optional[str] = Query(None, description="Поиск по названию"),
    date_from: Optional[datetime] = Query(None, description="Дата начала (ISO 8601)"),
    date_to: Optional[datetime] = Query(None, description="Дата окончания"),
    sort_by: Optional[str] = Query(None, description="Поле сортировки: created_at, title, status"),
    order: Optional[str] = Query("desc", description="Направление: asc, desc"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Записей на странице"),
    current_user: CurrentUser = Depends(get_current_user),
) -> DocumentListResponse:
    """List documents with optional filtering and sorting."""
    user_id = _mock_user()
    now = datetime.utcnow()

    items = [
        DocumentListItem(
            document_id="doc-8a3f2b",
            title="Стойки установочные",
            doc_code="20868-81",
            source_type=SourceType.GOST,
            era="USSR",
            validity_status="active",
            jurisdiction="RU",
            issuing_body="Госстандарт СССР",
            mks_oks_code="31.240",
            okstu_code=None,
            classification_status=ClassificationStatus(
                mks_status="CONFIRMED",
                okstu_status="NOT_USED",
                udk_code=None,
                extracted_at=now,
                extracted_by="purgatory_parser_v2",
                confidence=0.95,
            ),
            file_hash_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            file_size_bytes=2048576,
            status=DocumentStatus.APPROVED,
            latest_version=1,
            total_versions=2,
            user_id=user_id,
            uploaded_by="Иванов И.И.",
            created_at=now,
            updated_at=now,
        )
    ]

    return DocumentListResponse(
        summary=DocumentSummary(
            total=1,
            uploaded=0,
            previewing=0,
            awaiting_decision=0,
            parsing=0,
            validation=0,
            review_required=0,
            ready_for_promotion=0,
            approved=1,
            failed=0,
            archived=0,
        ),
        items=items,
        meta=PaginationMeta(total=1, page=page, page_size=page_size),
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
    current_user: CurrentUser = Depends(get_current_user),
) -> DocumentQueueResponse:
    """Get the current document processing queue."""
    user_id = _mock_user()
    now = datetime.utcnow()

    queue_items = [
        QueueItem(
            document_id="doc-8a3f2b",
            title="Стойки установочные",
            doc_code="20868-81",
            source_type=SourceType.GOST,
            status=DocumentStatus.VALIDATION,
            progress_percent=60.0,
            current_step="validation",
            steps=QueuePipelineSteps(
                pipeline=QueuePipelineField(
                    formation={
                        "status": "in_progress",
                        "parsing": "completed",
                        "validation": "in_progress",
                        "registry": "pending",
                    },
                    indexation={
                        "status": "pending",
                        "rag_indexing": "pending",
                    },
                ),
            ),
            user_id=user_id,
            uploaded_by="Иванов И.И.",
            created_at=now,
            started_at=now,
            estimated_completion=None,
        )
    ]

    return DocumentQueueResponse(
        queue=queue_items,
        meta=QueueMeta(total_in_queue=len(queue_items), page=page, page_size=page_size),
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
async def get_document(
    doc_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> DocumentDetailResponse:
    """Get detailed document information with all metadata."""
    user_id = _mock_user()
    now = datetime.utcnow()

    return DocumentDetailResponse(
        document_id=doc_id,
        title="Стойки установочные",
        doc_code="20868-81",
        source_type=SourceType.GOST,
        title_hash_sha256="a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
        status=DocumentStatus.APPROVED,
        era="USSR",
        validity_status="active",
        jurisdiction="RU",
        issuing_body="Госстандарт СССР",
        industry_code=None,
        enterprise_id=None,
        mks_oks_code="31.240",
        okstu_code=None,
        classification_status=ClassificationStatus(
            mks_status="CONFIRMED",
            okstu_status="NOT_USED",
            udk_code=None,
            extracted_at=now,
            extracted_by="purgatory_parser_v2",
            confidence=0.95,
        ),
        metadata=DocMetadata(
            year="1981",
            udc="629.5.021",
            tags=["судостроение", "стойки"],
        ),
        latest_version=LatestVersionInfo(
            version_id=str(uuid.uuid4()),
            version_number=1,
            format_code="pdf_digital",
            file_hash_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            size_bytes=2048576,
        ),
        total_versions=2,
        user_id=user_id,
        uploaded_by="Иванов И.И.",
        created_by="system_registry_sync",
        updated_by="ivanov_ai",
        created_at=now,
        updated_at=now,
    )


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/status  — FSM-aware status
# ---------------------------------------------------------------------------


@router.get(
    "/{doc_id}/status",
    response_model=DocumentStatusResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Документ не найден"},
    },
)
async def get_document_status(
    doc_id: str,
    longpoll: int = Query(15, ge=0, le=60, description="Время ожидания (сек)"),
    current_user: CurrentUser = Depends(get_current_user),
) -> DocumentStatusResponse:
    """Get current FSM-aware processing status for a document.

    Supports longpoll — server holds the connection, returns on status
    change or timeout.
    """
    from datetime import timedelta

    now = datetime.utcnow()

    return DocumentStatusProcessing(
        document_id=doc_id,
        status="processing",
        progress_percent=60.0,
        steps=StatusPipelines(
            pipeline=PipelinesField(
                formation=FormationPipeline(
                    status=PipelineStatusEnum.IN_PROGRESS,
                    preview=PreviewPhase(
                        status=StepStatusEnum.COMPLETED,
                        ocr_parser=OcrParserStep(
                            status=StepStatusEnum.COMPLETED,
                            pages_processed=3,
                        ),
                        converter_validator=ConverterValidatorStep(
                            status=StepStatusEnum.COMPLETED,
                            metadata_extracted=True,
                        ),
                        decision=DecisionStep(
                            status="awaiting",
                            action=None,
                        ),
                    ),
                    parsing=ParsingStep(
                        status=StepStatusEnum.COMPLETED,
                        pages_processed=12,
                        pages_failed=0,
                        avg_confidence=0.92,
                    ),
                    validation=ValidationStep(
                        status="in_progress",
                        errors_found=0,
                    ),
                    registry=RegistryStep(
                        status=StepStatusEnum.PENDING,
                    ),
                ),
                indexation=IndexationPipeline(
                    status=PipelineStatusEnum.PENDING,
                    rag_indexing=RagIndexingStep(
                        status=StepStatusEnum.PENDING,
                    ),
                ),
            ),
        ),
        started_at=now,
        estimated_completion=now + timedelta(minutes=2),
    )


# ---------------------------------------------------------------------------
#  POST /documents/{doc_id}/approve
# ---------------------------------------------------------------------------


@router.post(
    "/{doc_id}/approve",
    response_model=ApproveResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        404: {"model": ErrorResponse, "description": "Документ не найден"},
        409: {"model": ErrorResponse, "description": "Неверный статус для аппрува"},
        422: {"model": ErrorResponse, "description": "Контейнер не валиден (без force)"},
    },
)
async def approve_document(
    doc_id: str,
    request: ApproveRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> ApproveResponse:
    """Approve a document in review_required state.

    Transitions document from review_required → approved and starts
    the promotion to Registry.
    """
    promotion_task_id = f"promo-{uuid.uuid4().hex[:8]}"

    return ApproveResponse(
        document_id=doc_id,
        status="approved",
        promotion_task_id=promotion_task_id,
        approved_by=current_user.user_id,
        approved_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/history
# ---------------------------------------------------------------------------


@router.get(
    "/{doc_id}/history",
    response_model=DocumentHistoryResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Документ не найден"},
    },
)
async def get_document_history(
    doc_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> DocumentHistoryResponse:
    """Get the status transition history (audit log) for a document."""
    now = datetime.utcnow()

    return DocumentHistoryResponse(
        document_id=doc_id,
        history=[
            HistoryItem(
                history_id="h-001",
                old_status=None,
                new_status="uploaded",
                comment=HistoryComment(
                    reason="initial_upload",
                    details=None,
                ),
                changed_by="ivanov_ai",
                changed_at=now,
            ),
            HistoryItem(
                history_id="h-002",
                old_status="ready_for_promotion",
                new_status="approved",
                comment=HistoryComment(
                    reason="manual_approve",
                    details="Утверждено главным инженером",
                ),
                changed_by="ivanov_ai",
                changed_at=now,
            ),
        ],
        meta=VersionMeta(total=2),
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
async def get_document_file(
    doc_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> DocumentFileResponse:
    """Get file download information for a document (latest version)."""
    return DocumentFileResponse(
        document_id=doc_id,
        version_id=str(uuid.uuid4()),
        content_type="application/pdf",
        file_url=f"/files/{doc_id}/full.pdf",
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
    current_user: CurrentUser = Depends(get_current_user),
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
    responses={
        404: {"model": ErrorResponse, "description": "Документ или страница не найдены"},
    },
)
async def get_page_view(
    doc_id: str,
    page_num: int,
    highlight: Optional[str] = Query(None, description="ID блока для подсветки"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a page image with highlighted block overlays.

    Returns binary image data (PNG/JPEG).
    """
    # In mock mode, return metadata
    from fastapi.responses import JSONResponse

    return JSONResponse(
        content={
            "document_id": doc_id,
            "page": page_num,
            "image_url": f"/files/page-img/{doc_id}_{page_num}.png",
            "width": 2480,
            "height": 3508,
            "blocks": [],
        }
    )


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/pages/{page_num}/text
# ---------------------------------------------------------------------------


@router.get(
    "/{doc_id}/pages/{page_num}/text",
    response_model=PageTextResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Документ или страница не найдены"},
    },
)
async def get_page_text(
    doc_id: str,
    page_num: int,
    current_user: CurrentUser = Depends(get_current_user),
) -> PageTextResponse:
    """Get the text layer and block structure of a page.

    Blocks use normalized bbox coordinates [x1, y1, x2, y2] in 0..1 range.
    """
    return PageTextResponse(
        document_id=doc_id,
        page=page_num,
        width=2480,
        height=3508,
        blocks=[
            PageBlockDetail(
                number=1,
                type="paragraph",
                bbox=[0.05, 0.056, 1.0, 0.111],
                content="Настоящий стандарт распространяется...",
                confidence=0.95,
            ),
            PageBlockDetail(
                number=5,
                type="table",
                bbox=[0.05, 0.417, 1.0, 0.694],
                content={
                    "columns": ["L, мм", "нормальная", "повышенная"],
                    "rows": [["От 6 до 50", "0,1", "0,05"]],
                },
                confidence=0.88,
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
        404: {"model": ErrorResponse, "description": "Документ или страница не найдены"},
    },
)
async def get_page_preview(
    doc_id: str,
    page_num: int,
    highlight: Optional[str] = Query(None, description="ID блока для подсветки"),
    format: Optional[str] = Query("json", description="Формат: json (default) или html"),
    current_user: CurrentUser = Depends(get_current_user),
) -> PagePreviewResponse:
    """Get an aggregated page preview with image URL, blocks and text layer."""
    return PagePreviewResponse(
        document_id=doc_id,
        page=page_num,
        image_url=f"/documents/{doc_id}/pages/{page_num}",
        blocks=[
            PreviewBlock(
                number=1,
                type="paragraph",
                bbox=[0.05, 0.056, 1.0, 0.111],
                content="Настоящий стандарт распространяется...",
            ),
        ],
        text_layer="Настоящий стандарт распространяется...",
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
        None, description="Этап: upload, ocr, parsing, indexing"
    ),
    severity: Optional[str] = Query(None, description="Уровень: warning, error"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=200, description="Записей на странице"),
    current_user: CurrentUser = Depends(get_current_user),
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

    return DocumentErrorsResponse(
        errors=errors,
        meta=PaginationMeta(total=len(errors), page=page, page_size=page_size),
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
async def get_document_parameters(
    doc_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> DocumentParametersResponse:
    """Get extracted structured parameters from a document.

    Parameters are extracted from tables, formulas and specifications.
    """
    return DocumentParametersResponse(
        document_id=doc_id,
        parameters=[
            ParameterItem(
                symbol="R_доп",
                description="Допустимый радиус",
                unit="мм",
                value=0.05,
                source_clause="6.1",
                source_page=1,
            ),
            ParameterItem(
                symbol="L",
                description="Длина стойки",
                unit="мм",
                range=ParameterRange(min=6, max=80),
                source_clause="6.1.table1",
                source_page=2,
            ),
        ],
        total=2,
    )


# ---------------------------------------------------------------------------
#  DELETE /documents/{doc_id}  — Soft delete
# ---------------------------------------------------------------------------


@router.delete(
    "/{doc_id}",
    response_model=DocumentDeleteResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Документ не найден"},
    },
)
async def delete_document(
    doc_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> DocumentDeleteResponse:
    """Soft-delete a document and all related data.

    The document is marked as deleted (deleted_at), but the record
    is preserved. Related entities (sections, versions, history,
    chunks) are marked as unavailable.
    """
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
        409: {"model": ErrorResponse, "description": "Документ уже обрабатывается"},
    },
)
async def reprocess_document(
    doc_id: str,
    request: ReprocessRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> ReprocessResponse:
    """Re-process an already-uploaded document with specified mode."""
    task_id = f"task-repro-{uuid.uuid4().hex[:8]}"

    return ReprocessResponse(
        mode=request.mode,
        document_id=doc_id,
        user_id=current_user.user_id,
        task_id=task_id,
        status="reprocessing_queued",
        created_at=datetime.utcnow(),
    )
