"""Documents API endpoints — pipeline-операции и связь с задачами.

Оркестратор управляет:
- `POST /documents/{id}/reprocess` (P2I-9) — переиндексация через Celery
- `POST /documents/{id}/versions` — загрузка версии файла
- `GET /documents/{id}/tasks` — список pipeline-задач документа
- `GET /documents/{id}/errors` — журнал ошибок обработки

Все остальные GET /documents/*, POST /documents/{id}/approve,
DELETE /documents/{id} перенесены в registry-service (см. docs/api/registry_service_api.md,
группа documents).
"""

import hashlib
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, get_current_user
from app.db.base import get_db
from app.models.pipeline import DraftNotification, Task, TaskStep
from app.schemas.common import PaginationMeta
from app.schemas.documents import (
    CreateVersionResponse,
    DocumentErrorItem,
    DocumentErrorsResponse,
    DocumentStatusResponse,
    ReprocessRequest,
    ReprocessResponse,
)
from app.schemas.tasks import DocumentTasksResponse, DraftTaskItem

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
#  GET /documents/queue — очередь обработки
# ---------------------------------------------------------------------------


@router.get(
    "/queue",
    responses={"200": {"description": "Очередь обработки документов"}},
)
async def document_queue():
    """Return processing queue."""
    return {"queue": [], "meta": {"total": 0, "page": 1, "page_size": 50}}


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/status  — Processing status for a document
# ---------------------------------------------------------------------------


@router.get(
    "/{doc_id}/status",
    response_model=DocumentStatusResponse,
    responses={404: {"description": "Документ не найден"}},
)
async def get_document_status(
    doc_id: int,
    longpoll: int = 15,
    db: AsyncSession = Depends(get_db),
) -> DocumentStatusResponse:
    """Get document processing status (supports longpoll).

    Returns aggregated status from pipeline tasks.
    Statuses: `processing`, `approval_required`, `completed`.
    """
    # Find all non-deleted tasks for this document
    result = await db.execute(
        select(Task)
        .where(Task.document_id == doc_id, Task.deleted_at.is_(None))
        .order_by(Task.created_at.desc())
    )
    tasks = list(result.scalars().all())

    if not tasks:
        return DocumentStatusResponse(
            document_id=doc_id,
            status="processing",
            progress_percent=0,
            steps={
                "pipeline": {
                    "formation": {"status": "pending"},
                    "indexation": {"status": "pending"},
                }
            },
        )

    # Find latest formation and indexation tasks
    formation_task = next(
        (t for t in tasks if t.pipeline_type in ("formation", "reprocess")),
        None,
    )
    indexation_task = next(
        (t for t in tasks if t.pipeline_type == "indexation"),
        None,
    )

    # Helper to determine pipeline status from task
    def _pipeline_status(task) -> str:
        if task is None:
            return "pending"
        if task.status == "completed":
            return "completed"
        if task.status == "failed":
            return "failed"
        return "in_progress"

    # Determine document status
    if indexation_task and indexation_task.status == "completed":
        doc_status = "completed"
    elif (
        formation_task
        and formation_task.status == "active"
        and formation_task.pipeline_stage == "decision"
    ):
        doc_status = "approval_required"
    else:
        doc_status = "processing"

    # Build formation steps
    formation_steps = {"status": _pipeline_status(formation_task)}
    if formation_task:
        # Get steps from DB
        steps_result = await db.execute(
            select(TaskStep)
            .where(TaskStep.task_id == formation_task.id, TaskStep.deleted_at.is_(None))
            .order_by(TaskStep.step_index)
        )
        form_steps = list(steps_result.scalars().all())
    else:
        form_steps = []

    # Map TaskStep statuses to pipeline format
    step_status_map: dict[str, dict] = {}
    for s in form_steps:
        mapped_status = s.status  # pending, running, completed, failed
        step_data = {"status": mapped_status}
        if s.status == "completed" and s.output_data:
            if "pages_processed" in s.output_data:
                step_data["pages_processed"] = s.output_data["pages_processed"]
            if "metadata_extracted" in s.output_data:
                step_data["metadata_extracted"] = s.output_data["metadata_extracted"]
            if "chunks_generated" in s.output_data:
                step_data["chunks_generated"] = s.output_data["chunks_generated"]
        step_status_map[s.step_name] = step_data

    # Build nested pipeline structure
    pipeline: dict = {"pipeline": {}}

    # Formation block
    formation_block: dict = {"status": _pipeline_status(formation_task)}

    preview_block = {
        "status": step_status_map.get("preview_ocr", {}).get("status", "pending"),
    }
    if "preview_ocr" in step_status_map or "preview_converter" in step_status_map:
        ocr_status = step_status_map.get("preview_ocr", {}).get("status", "pending")
        converter_status = step_status_map.get("preview_converter", {}).get("status", "pending")
        preview_block["ocr_parser"] = {
            "status": ocr_status,
        }
        if step_status_map.get("preview_ocr", {}).get("pages_processed"):
            preview_block["ocr_parser"]["pages_processed"] = (
                step_status_map["preview_ocr"]["pages_processed"]
            )
        preview_block["converter_validator"] = {
            "status": converter_status,
        }
        if step_status_map.get("preview_converter", {}).get("metadata_extracted"):
            preview_block["converter_validator"]["metadata_extracted"] = (
                step_status_map["preview_converter"]["metadata_extracted"]
            )

    decision_block: dict = {"status": "pending"}
    if formation_task:
        if formation_task.pipeline_stage == "decision":
            decision_block["status"] = "in_progress"
        elif formation_task.pipeline_stage in ("full", "registry"):
            decision_block["status"] = "completed"
            # Check for stored action (from task steps output)
            action_step = step_status_map.get("registry_creation", {})
            if action_step:
                decision_block["action"] = "approve"
            else:
                decision_block["action"] = "approve"
        elif formation_task.pipeline_stage == "preview":
            preview_block["status"] = "in_progress"

    formation_block["preview"] = preview_block
    formation_block["decision"] = decision_block

    # Add full processing steps if present
    full_steps = [s for s in form_steps if s.step_name.startswith("full_")]
    if full_steps:
        full_block: dict = {"status": "pending"}
        for s in full_steps:
            if s.status == "completed":
                full_block["status"] = "completed"
            elif s.status == "running":
                full_block["status"] = "in_progress"
            elif s.status == "failed":
                full_block["status"] = "failed"
        formation_block["full"] = full_block

    pipeline["pipeline"]["formation"] = formation_block

    # Indexation block
    if indexation_task:
        idx_steps_result = await db.execute(
            select(TaskStep)
            .where(TaskStep.task_id == indexation_task.id, TaskStep.deleted_at.is_(None))
            .order_by(TaskStep.step_index)
        )
        idx_steps = list(idx_steps_result.scalars().all())
    else:
        idx_steps = []

    idx_step_map: dict[str, dict] = {}
    for s in idx_steps:
        mapped_status = s.status
        step_data = {"status": mapped_status}
        if s.status == "completed" and s.output_data:
            if "chunks_generated" in s.output_data:
                step_data["chunks_generated"] = s.output_data["chunks_generated"]
        idx_step_map[s.step_name] = step_data

    rag_status = "pending"
    chunks_generated = None
    if "rag_indexing" in idx_step_map:
        rag_status = idx_step_map["rag_indexing"]["status"]
        chunks_generated = idx_step_map["rag_indexing"].get("chunks_generated")

    indexation_block: dict = {"status": _pipeline_status(indexation_task)}
    indexation_block["rag_indexing"] = {"status": rag_status}
    if chunks_generated is not None:
        indexation_block["rag_indexing"]["chunks_generated"] = chunks_generated

    pipeline["pipeline"]["indexation"] = indexation_block

    # Build response
    response_kwargs: dict = {
        "document_id": doc_id,
        "status": doc_status,
        "progress_percent": 0.0,
        "steps": pipeline,
    }

    # Compute progress based on tasks
    completed_tasks = sum(1 for t in tasks if t.status == "completed")
    total_tasks = len(tasks)
    if total_tasks > 0:
        response_kwargs["progress_percent"] = round(
            (completed_tasks / total_tasks) * 100, 1
        )

    # Timestamps
    if formation_task:
        if formation_task.started_at:
            response_kwargs["started_at"] = formation_task.started_at

        if formation_task.completed_at:
            response_kwargs["completed_at"] = formation_task.completed_at

    if indexation_task and indexation_task.completed_at:
        response_kwargs["completed_at"] = indexation_task.completed_at

    # Chunk summary for completed
    if doc_status == "completed" and chunks_generated is not None:
        response_kwargs["chunk_summary"] = {
            "sections": 0,
            "chunks": chunks_generated,
            "embeddings": 0,
        }

    return DocumentStatusResponse(**response_kwargs)


# ---------------------------------------------------------------------------
#  POST /documents/{doc_id}/reprocess  — переиндексация документа
# ---------------------------------------------------------------------------


@router.post(
    "/{doc_id}/reprocess",
    response_model=ReprocessResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        404: {"description": "Документ не найден"},
        409: {"description": "Документ уже обрабатывается"},
    },
)
async def reprocess_document(
    doc_id: str,
    request: ReprocessRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReprocessResponse:
    """Re-process an already-uploaded document with specified mode (P2I-9).

    Creates a reprocess pipeline task and triggers re-indexation.
    """
    from app.repositories.pipeline import TaskRepository
    from app.tasks.pipeline_indexation import run_reprocess_step

    repo = TaskRepository(db)

    # Create reprocess task
    try:
        task = await repo.create_task(
            draft_id=0,  # reprocess has no draft
            pipeline_type="reprocess",
            total_steps=1,
        )
        task.document_id = int(doc_id) if doc_id.isdigit() else None
        task.status = "active"
        await db.flush()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "TASK_ALREADY_EXISTS",
                    "message": f"Reprocess task for document {doc_id} already exists",
                }
            },
        )

    # Trigger reprocess Celery task
    logger.info(
        "Enqueuing reprocess task",
        extra={
            "celery_task": "tasks.pipeline.indexation.run_reprocess_step",
            "queue": "pipeline",
            "params": {"task_id": task.id, "doc_id": doc_id},
            "task_id": task.id, "doc_id": doc_id,
        },
    )
    run_reprocess_step.delay(task.id, doc_id)

    return ReprocessResponse(
        mode=request.mode,
        document_id=doc_id,
        task_id=str(task.id),
        status="reprocessing_queued",
        created_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
#  POST /documents/{doc_id}/versions  — Upload additional version
# ---------------------------------------------------------------------------


@router.post(
    "/{doc_id}/versions",
    response_model=CreateVersionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        404: {"description": "Документ не найден"},
        409: {"description": "Документ в обработке или файл-дубликат"},
    },
)
async def create_document_version(
    doc_id: int,
    file: UploadFile = File(..., description="Бинарный файл (PDF, PNG, JPG, TIFF)"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CreateVersionResponse:
    """Upload an additional file version for an existing document.

    Saves file to MinIO, creates a task record, and registers
    the version in Registry.
    """
    ALLOWED_MIME = {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/tiff",
    }
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "UNSUPPORTED_FILE_TYPE",
                    "message": "Неподдерживаемый формат файла",
                }
            },
        )

    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": "Размер файла превышает 100 МБ",
                }
            },
        )

    # Compute hash and upload to MinIO
    file_hash = hashlib.sha256(content).hexdigest()
    file_key = f"f-{file_hash[:12]}"

    try:
        from app.storage import upload_file
        await upload_file(
            file_key=file_key,
            content=content,
            content_type=file.content_type or "application/octet-stream",
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": f"Ошибка сохранения файла: {exc}",
                }
            },
        )

    # Create task record for tracking
    from app.repositories.pipeline import TaskRepository
    repo = TaskRepository(db)
    try:
        task = await repo.create_task(
            draft_id=0,  # version upload has no draft
            pipeline_type="formation",
            total_steps=1,
        )
        task.document_id = doc_id
        await db.flush()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "TASK_ALREADY_EXISTS",
                    "message": f"Task for document {doc_id} already exists",
                }
            },
        )

    # Call Registry to register version
    from app.services.registry_client import RegistryServiceClient
    registry = RegistryServiceClient()
    version_result = await registry.create_version(
        doc_id,
        {
            "file_hash_sha256": file_hash,
            "file_key": file_key,
            "size_bytes": file_size,
        },
    )

    version_data = version_result.get("data", {})
    now = datetime.now(timezone.utc)

    return CreateVersionResponse(
        document_id=doc_id,
        version_id=version_data.get("version_id", doc_id * 100 + 1),
        version_number=version_data.get("version_number", 1),
        status="uploaded",
        task_id=task.id,
        file_hash_sha256=file_hash,
        is_duplicate_file=version_data.get("is_duplicate_file", False),
        created_at=now,
    )


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/errors  — Error log for a document
# ---------------------------------------------------------------------------


@router.get(
    "/{doc_id}/errors",
    response_model=DocumentErrorsResponse,
    responses={404: {"description": "Документ не найден"}},
)
async def get_document_errors(
    doc_id: int,
    stage: str | None = None,
    severity: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
) -> DocumentErrorsResponse:
    """Journal of processing errors for a document.

    Returns quality notifications from pipeline tasks linked to this document.
    Supports filtering by stage (`ocr`, `parsing`, `indexing`, `upload`)
    and severity (`warning`, `error`, `critical`, `info`).
    """
    # Clamp page_size
    page_size = min(page_size, 100)
    page = max(page, 1)

    # Build query: notifications joined with tasks filtered by document_id
    query = (
        select(DraftNotification, Task)
        .join(Task, DraftNotification.task_id == Task.id)
        .where(
            Task.document_id == doc_id,
            Task.deleted_at.is_(None),
        )
    )

    if stage:
        query = query.where(DraftNotification.service == stage)
    if severity:
        query = query.where(DraftNotification.severity == severity)

    query = query.order_by(DraftNotification.created_at.desc())

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    rows = result.all()

    errors = [
        DocumentErrorItem(
            error_id=f"err-{notification.id:03d}",
            stage=notification.service,
            page=0,  # page not stored in DraftNotification yet
            error_code=notification.code,
            error_message=notification.message,
            severity=notification.severity,
            retry_attempt=task.retry_count,
            timestamp=notification.created_at,
        )
        for notification, task in rows
    ]

    return DocumentErrorsResponse(
        errors=errors,
        meta=PaginationMeta(total=total, page=page, page_size=page_size),
    )


# ---------------------------------------------------------------------------
#  GET /documents/{doc_id}/tasks  — Pipeline tasks for a document
# ---------------------------------------------------------------------------


@router.get(
    "/{doc_id}/tasks",
    response_model=DocumentTasksResponse,
    responses={404: {"description": "Документ не найден"}},
)
async def get_document_tasks(
    doc_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentTasksResponse:
    """List pipeline tasks for a document."""
    result = await db.execute(
        select(Task)
        .where(Task.document_id == doc_id, Task.deleted_at.is_(None))
        .order_by(Task.created_at.desc())
    )
    tasks = list(result.scalars().all())

    task_items = [
        DraftTaskItem(
            task_id=t.id,
            status=t.status,
            pipeline_stage=t.pipeline_stage,
            initiated_by=t.created_by,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in tasks
    ]

    return DocumentTasksResponse(
        document_id=doc_id,
        tasks=task_items,
    )
