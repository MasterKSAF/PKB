"""Drafts API endpoints — управление черновиками (POST, preview, decide, delete).

Чтение черновиков (GET /drafts, GET /drafts/{id}) — через Registry.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
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

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, get_current_user
from app.core.config import settings
from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.core.trace import set_draft_id, set_document_id, set_version_id
from app.db.base import get_db
from app.schemas.drafts import (
    DecideRequest,
    DecideResponse,
    DraftCreateResponse,
    DraftPreviewResponse,
    DraftPreviewStatusResponse,
    PreviewMetadata,
)
from app.models.pipeline import Task
from app.schemas.tasks import DraftTaskItem, DraftTasksResponse
from app.services.registry_client import RegistryServiceClient

logger = logging.getLogger(__name__)

router = APIRouter()

MOCK_USER_ID = "u-mock-001"
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB

ALLOWED_SOURCE_TYPES = {
    "GOST", "GOST_R", "OST", "RD", "TU", "ISO", "DNV", "ASTM", "RMRS", "OTHER",
}

ALLOWED_ERA = {"USSR", "CIS", "RF", "CURRENT"}

ALLOWED_JURISDICTIONS = {"RU", "EU", "US", "NO", "INTL"}

ALLOWED_MIME = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/tiff",
}

# Actions that can be performed on a draft
EXTERNAL_ACTIONS = {"approve", "reject"}
INTERNAL_ACTIONS = {"proceed", "stop_duplicate", "force_new_version"}
ALL_ACTIONS = EXTERNAL_ACTIONS | INTERNAL_ACTIONS


def _compute_sha256(content: bytes) -> str:
    """Compute SHA-256 hex digest."""
    return hashlib.sha256(content).hexdigest()


# ---------------------------------------------------------------------------
#  POST /drafts  — Upload file & create draft
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=DraftCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"description": "Неподдерживаемый формат / размер"},
        409: {"description": "Дубликат задачи для черновика"},
        413: {"description": "Файл превышает 100 МБ"},
        422: {"description": "Ошибка валидации"},
    },
)
async def create_draft(
    file: UploadFile = File(..., description="Бинарный файл (PDF, PNG, JPG, TIFF)"),
    document_key: str = Form(..., description="Ключ документа (business key)"),
    source_type: str = Form(..., description="Тип источника: GOST, GOST_R, OST, RD, TU, ISO, DNV, ASTM, RMRS, OTHER"),
    title: Optional[str] = Form(None, description="Название документа"),
    doc_code: Optional[str] = Form(None, description="Регистрационный номер (напр. 20868-81)"),
    mks_oks_code: Optional[str] = Form(None, description="Код МКС/ОКС"),
    okstu_code: Optional[str] = Form(None, description="Код ОКСТУ"),
    era: Optional[str] = Form(None, description="Эпоха: USSR, CIS, RF, CURRENT"),
    jurisdiction: Optional[str] = Form(None, description="Юрисдикция: RU, EU, US, NO, INTL"),
    issuing_body: Optional[str] = Form(None, description="Организация-издатель"),
    metadata: Optional[str] = Form(None, description="JSON-строка с доп. данными"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DraftCreateResponse:
    """Upload a file and create a draft for processing.

    Единая точка входа для загрузки документов (draft-first).
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
    if source_type not in ALLOWED_SOURCE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Недопустимый source_type: {source_type}",
                    "details": {"allowed_values": sorted(ALLOWED_SOURCE_TYPES)},
                }
            },
        )

    # --- Validate era ---
    if era is not None and era not in ALLOWED_ERA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Недопустимый era: {era}",
                    "details": {"allowed_values": sorted(ALLOWED_ERA)},
                }
            },
        )

    # --- Validate jurisdiction ---
    if jurisdiction is not None and jurisdiction not in ALLOWED_JURISDICTIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Недопустимый jurisdiction: {jurisdiction}",
                    "details": {"allowed_values": sorted(ALLOWED_JURISDICTIONS)},
                }
            },
        )

    # --- Parse metadata JSON if provided ---
    parsed_metadata: Dict[str, Any] = {}
    if metadata:
        try:
            parsed_metadata = json.loads(metadata)
            if not isinstance(parsed_metadata, dict):
                raise ValueError("metadata must be a JSON object")
        except (json.JSONDecodeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": f"Некорректный JSON в поле metadata: {exc}",
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

    # --- Read file content ---
    content = await file.read()
    file_size = len(content)

    # Validate file size after reading
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": "Размер файла превышает 100 МБ",
                    "details": {
                        "max_size_mb": 100,
                        "actual_size_mb": round(file_size / (1024 * 1024), 1),
                    },
                }
            },
        )

    file_hash = _compute_sha256(content)
    title_hash = _compute_sha256(title.encode("utf-8")) if title else None

    # --- Generate file key (no external storage) ---
    file_key = f"f-{file_hash[:12]}"

    # --- Compute title_key (DB-28): конкатенация ключевых полей ---
    title_key_parts = []
    if era:
        title_key_parts.append(era)
    title_key_parts.append(source_type)
    if jurisdiction:
        title_key_parts.append(jurisdiction)
    if doc_code:
        title_key_parts.append(doc_code)
    if mks_oks_code:
        title_key_parts.append(mks_oks_code)
    if title:
        title_key_parts.append(title)
    title_key = "|".join(title_key_parts) if title_key_parts else None

    # --- Build metadata_fields from form data ---
    metadata_fields: Dict[str, Any] = {}
    if source_type:
        metadata_fields["source_type"] = source_type
    if title:
        metadata_fields["title"] = title
    if doc_code:
        metadata_fields["doc_code"] = doc_code
    if mks_oks_code:
        metadata_fields["mks_oks_code"] = mks_oks_code
    if okstu_code:
        metadata_fields["okstu_code"] = okstu_code
    if era:
        metadata_fields["era"] = era
    if jurisdiction:
        metadata_fields["jurisdiction"] = jurisdiction
    if issuing_body:
        metadata_fields["issuing_body"] = issuing_body
    # Merge any parsed metadata on top
    metadata_fields.update(parsed_metadata)

    # --- Check duplicates via Registry ---
    registry = RegistryServiceClient()
    is_duplicate_file = False
    is_duplicate_document = False
    try:
        uniqueness = await registry.check_uniqueness(
            title=title or document_key,
            doc_code=doc_code,
            era=era,
            source_type=source_type,
            file_size_bytes=file_size,
        )
        data = uniqueness.get("data", {})
        is_duplicate_file = data.get("is_duplicate_file", False)
        is_duplicate_document = data.get("is_duplicate", False)
    except Exception as exc:
        logger.warning(f"Uniqueness check failed: {exc}")
    finally:
        await registry.close()

    # --- Create draft in Registry ---
    registry = RegistryServiceClient()
    try:
        draft_result = await registry.create_draft(
            file_key=file_key,
            document_key=document_key,
            created_by=current_user.user_id if current_user else MOCK_USER_ID,
            file_hash_sha256=file_hash,
            title_hash_sha256=title_hash,
            title_key=title_key,
            metadata_fields=metadata_fields if metadata_fields else None,
        )
        draft_id = draft_result.get("data", {}).get("id", 0)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "DRAFT_CREATION_FAILED",
                    "message": "Ошибка при создании черновика в Registry",
                    "details": {"original_error": str(exc)},
                }
            },
        )
    finally:
        await registry.close()

    # Store draft_id in context for downstream correlation (CM-5)
    set_draft_id(str(draft_id))

    # --- Check: Task for this draft_id already exists? ---
    from sqlalchemy import select
    from app.models.pipeline import Task
    existing = await db.execute(
        select(Task).where(
            Task.draft_id == draft_id,
            Task.pipeline_type == "formation",
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "TASK_ALREADY_EXISTS",
                    "message": f"Задача для черновика {draft_id} уже существует",
                }
            },
        )

    # --- Create Task in local DB ---
    orchestrator = PipelineOrchestrator(db)
    try:
        task = await orchestrator.task_repo.create_task(
            draft_id=draft_id,
            pipeline_type="formation",
            total_steps=6,
        )
    except IntegrityError as exc:
        logger.warning(
            f"Task creation race condition for draft {draft_id}: {exc}"
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "TASK_ALREADY_EXISTS",
                    "message": f"Задача для черновика {draft_id} уже существует",
                }
            },
        )

    # --- Start pipeline (preview phase) ---
    mime_type = file.content_type or "application/octet-stream"
    await orchestrator.start_pipeline(
        draft_id=draft_id,
        task_id=task.id,
        file_key=file_key,
        mime_type=mime_type,
        metadata_fields=metadata_fields if metadata_fields else None,
    )

    return DraftCreateResponse(
        draft_id=draft_id,
        task_id=task.id,
        status="uploaded",
        file_hash_sha256=file_hash,
        file_size_bytes=file_size,
        is_duplicate_file=is_duplicate_file,
        is_duplicate_document=is_duplicate_document,
        title_hash_sha256=title_hash,
        title_key=title_key,
        created_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
#  GET /drafts/{draft_id}/preview  — Preview metadata
# ---------------------------------------------------------------------------


@router.get(
    "/{draft_id}/preview",
    response_model=DraftPreviewResponse,
    responses={404: {"description": "Черновик не найден"}},
)
async def get_draft_preview(
    draft_id: int,
    current_user: CurrentUser = Depends(get_current_user),
) -> DraftPreviewResponse:
    """Get preview metadata (proxies to Registry)."""
    registry = RegistryServiceClient()
    try:
        result = await registry.get_draft_preview(draft_id)
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Черновик {draft_id} не найден",
                    }
                },
            )
        data = result.get("data", {})
        return DraftPreviewResponse(
            draft_id=draft_id,
            preview=PreviewMetadata(
                doc_code=data.get("doc_code"),
                title=data.get("title"),
                document_type=data.get("document_type"),
                source_type=data.get("source_type"),
                year=data.get("year"),
                revision=data.get("revision"),
                era=data.get("era"),
                jurisdiction=data.get("jurisdiction"),
                mks_oks_code=data.get("mks_oks_code"),
                okstu_code=data.get("okstu_code"),
                issuing_body=data.get("issuing_body"),
                udk_code=data.get("udk_code"),
            ),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Черновик {draft_id} не найден",
                    "details": {"original_error": str(exc)},
                }
            },
        )
    finally:
        await registry.close()


# ---------------------------------------------------------------------------
#  POST /drafts/{draft_id}/preview  — Start preview
# ---------------------------------------------------------------------------


@router.post(
    "/{draft_id}/preview",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        404: {"description": "Черновик не найден"},
        409: {"description": "Preview уже запущен или некорректный статус"},
    },
)
async def start_preview(
    draft_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Start preview phase for a draft.

    Idempotency: returns 409 if preview already running or completed.
    """
    # Get draft info from Registry
    registry = RegistryServiceClient()
    try:
        draft = await registry.get_draft(draft_id)
        draft_data = draft.get("data", {})
        if not draft_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Черновик {draft_id} не найден",
                    }
                },
            )
        if draft_data.get("status") != "uploaded":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "CONFLICT",
                        "message": f"Некорректный статус для preview: {draft_data.get('status')}",
                    }
                },
            )
        file_key = draft_data.get("file_key")
        # Get mime_type from draft metadata if available
        mime_type = draft_data.get("mime_type", "application/pdf")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Черновик {draft_id} не найден",
                    "details": {"original_error": str(exc)},
                }
            },
        )
    finally:
        await registry.close()

    # --- Idempotency check (OR-2): check if task already has running preview ---
    from sqlalchemy import select
    from app.models.pipeline import Task, TaskStep
    result = await db.execute(
        select(Task).where(Task.draft_id == draft_id).order_by(Task.created_at.desc())
    )
    task = result.scalar_one_or_none()
    if task:
        # Check if preview steps exist and are in progress
        steps_result = await db.execute(
            select(TaskStep).where(
                TaskStep.task_id == task.id,
                TaskStep.step_name.in_(["preview_ocr", "preview_converter"]),
            )
        )
        existing_steps = list(steps_result.scalars().all())
        if existing_steps:
            running_or_completed = any(
                s.status in ("running", "completed") for s in existing_steps
            )
            if running_or_completed:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": {
                            "code": "PREVIEW_ALREADY_RUNNING",
                            "message": f"Preview для черновика {draft_id} уже запущен или завершён",
                        }
                    },
                )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Задача для черновика {draft_id} не найдена",
                }
            },
        )

    # Start pipeline with actual mime_type
    orchestrator = PipelineOrchestrator(db)
    await orchestrator.start_pipeline(
        draft_id=draft_id,
        task_id=task.id,
        file_key=file_key or "",
        mime_type=mime_type,
    )

    return {
        "draft_id": draft_id,
        "task_id": task.id,
        "status": "previewing",
        "message": "Preview phase started",
    }


# ---------------------------------------------------------------------------
#  Longpoll helpers — poll DB for preview step completion
# ---------------------------------------------------------------------------


async def _wait_for_preview(
    db: AsyncSession,
    task_id: int,
    timeout: int = 15,
    poll_interval: float = 1.0,
) -> dict:
    """Poll DB for preview step completion with timeout.

    Returns a dict with:
      "status": "completed" | "failed" | "processing"
      "steps": dict[step_name -> status]
    """
    from sqlalchemy import select
    from app.models.pipeline import TaskStep
    import asyncio

    PREVIEW_STEP_NAMES = ("preview_ocr", "preview_converter")
    deadline = asyncio.get_event_loop().time() + timeout

    while asyncio.get_event_loop().time() < deadline:
        result = await db.execute(
            select(TaskStep)
            .where(TaskStep.task_id == task_id)
            .where(TaskStep.step_name.in_(PREVIEW_STEP_NAMES))
        )
        steps = list(result.scalars().all())

        if not steps:
            # Steps may not have been created yet
            await asyncio.sleep(poll_interval)
            continue

        statuses = {s.step_name: s.status for s in steps}
        all_completed = all(s == "completed" for s in statuses.values())
        any_failed = any(s == "failed" for s in statuses.values())

        if all_completed:
            return {"status": "completed", "steps": statuses}
        if any_failed:
            return {"status": "failed", "steps": statuses}

        await asyncio.sleep(poll_interval)

    # Timeout — return current progress
    return {"status": "processing", "steps": {}}


async def _build_preview_status(
    db: AsyncSession,
    draft_id: int,
    task,
    steps: list,
) -> DraftPreviewStatusResponse:
    """Build DraftPreviewStatusResponse from current task/steps state."""
    from app.models.pipeline import TaskStep

    preview_steps = [s for s in steps if s.step_name in ("preview_ocr", "preview_converter")]
    all_completed = all(s.status == "completed" for s in preview_steps)
    any_failed = any(s.status == "failed" for s in preview_steps)

    if all_completed:
        status_str = "completed"
        preview_meta = None
        for s in steps:
            if s.step_name == "preview_converter" and s.output_data:
                meta = s.output_data.get("metadata", {})
                if meta:
                    preview_meta = PreviewMetadata(
                        doc_code=meta.get("doc_code"),
                        title=meta.get("title"),
                        document_type=meta.get("document_type"),
                        source_type=meta.get("source_type"),
                        year=meta.get("year"),
                        revision=meta.get("revision"),
                        era=meta.get("era"),
                        jurisdiction=meta.get("jurisdiction"),
                        mks_oks_code=meta.get("mks_oks_code"),
                        okstu_code=meta.get("okstu_code"),
                        issuing_body=meta.get("issuing_body"),
                        udk_code=meta.get("udk_code"),
                    )
                    break
        decision_required = task.pipeline_stage == "decision"
    elif any_failed:
        status_str = "failed"
        preview_meta = None
        decision_required = False
    else:
        status_str = "processing"
        preview_meta = None
        decision_required = False

    return DraftPreviewStatusResponse(
        draft_id=draft_id,
        task_id=task.id,
        status=status_str,
        progress_percent=task.progress_percent,
        preview=preview_meta,
        decision_required=decision_required,
    )


async def _find_task_for_draft(
    db: AsyncSession, draft_id: int
):
    """Find the latest Task for a draft_id."""
    from sqlalchemy import select
    from app.models.pipeline import Task

    result = await db.execute(
        select(Task).where(Task.draft_id == draft_id).order_by(Task.created_at.desc())
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Задача для черновика {draft_id} не найдена",
                }
            },
        )
    return task


# ---------------------------------------------------------------------------
#  GET /drafts/{draft_id}/preview/status  — Preview status
# ---------------------------------------------------------------------------


@router.get(
    "/{draft_id}/preview/status",
    response_model=DraftPreviewStatusResponse,
    responses={404: {"description": "Черновик не найден"}},
)
async def get_preview_status(
    draft_id: int,
    longpoll: int = Query(15, ge=0, le=60, description="Время ожидания (сек)"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DraftPreviewStatusResponse:
    """Get preview status with longpoll support.

    If longpoll > 0 and preview is still processing, the server will
    wait up to `longpoll` seconds for completion before responding.
    """
    from sqlalchemy import select
    from app.models.pipeline import TaskStep

    # Проверяем, что draft существует через Registry (не через локальную БД)
    registry = RegistryServiceClient()
    try:
        draft_result = await registry.get_draft(draft_id)
        if "error" in draft_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Черновик {draft_id} не найден или удалён",
                    }
                },
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(f"Registry check failed for draft {draft_id}: {exc}")
    finally:
        await registry.close()

    task = await _find_task_for_draft(db, draft_id)

    # If longpoll=0 or task already finished, return immediately
    if longpoll == 0 or task.status in ("completed", "failed"):
        steps_result = await db.execute(
            select(TaskStep).where(TaskStep.task_id == task.id).order_by(TaskStep.step_index)
        )
        steps = list(steps_result.scalars().all())
        return await _build_preview_status(db, draft_id, task, steps)

    # Check current preview status — maybe it's already done
    steps_result = await db.execute(
        select(TaskStep).where(TaskStep.task_id == task.id).order_by(TaskStep.step_index)
    )
    steps = list(steps_result.scalars().all())

    preview_steps = [s for s in steps if s.step_name in ("preview_ocr", "preview_converter")]
    if not preview_steps or all(s.status in ("completed", "failed") for s in preview_steps):
        return await _build_preview_status(db, draft_id, task, steps)

    # Still processing — wait with polling
    poll_result = await _wait_for_preview(db, task.id, timeout=longpoll)

    # Re-read after wait to get latest data
    steps_result = await db.execute(
        select(TaskStep).where(TaskStep.task_id == task.id).order_by(TaskStep.step_index)
    )
    steps = list(steps_result.scalars().all())
    return await _build_preview_status(db, draft_id, task, steps)


# ---------------------------------------------------------------------------
#  PATCH /drafts/{draft_id}/decide  — Decision
# ---------------------------------------------------------------------------


@router.patch(
    "/{draft_id}/decide",
    response_model=DecideResponse,
    responses={
        400: {"description": "Неизвестное действие"},
        404: {"description": "Черновик не найден"},
        409: {"description": "Некорректный статус для решения"},
    },
)
async def decide_draft(
    draft_id: int,
    request: DecideRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DecideResponse:
    """Submit user decision after preview phase.

    External actions (UI): approve, reject
    Internal actions (pipeline): proceed, stop_duplicate, force_new_version
    """
    # Validate action
    if request.action not in ALL_ACTIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "BAD_REQUEST",
                    "message": (
                        f"Неизвестное действие: {request.action}. "
                        f"Допустимо: {', '.join(sorted(ALL_ACTIONS))}"
                    ),
                }
            },
        )

    # Find task for this draft
    from sqlalchemy import select
    from app.models.pipeline import Task

    result = await db.execute(
        select(Task).where(Task.draft_id == draft_id).order_by(Task.created_at.desc())
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Задача для черновика {draft_id} не найдена",
                }
            },
        )

    # --- State validation: check task is in correct state for action ---
    if task.status in ("completed", "failed"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "TASK_ALREADY_TERMINAL",
                    "message": (
                        f"Задача {task.id} уже в терминальном статусе "
                        f"({task.status}). Действие {request.action} невозможно."
                    ),
                }
            },
        )

    if request.action in ("approve", "reject", "proceed", "force_new_version"):
        if task.pipeline_stage != "decision":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "INVALID_STAGE",
                        "message": (
                            f"Действие {request.action} требует этапа 'decision', "
                            f"текущий этап: {task.pipeline_stage}"
                        ),
                    }
                },
            )

    if request.action == "stop_duplicate":
        if task.pipeline_stage not in ("preview", "decision"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "INVALID_STAGE",
                        "message": (
                            f"Действие stop_duplicate требует этапа 'preview' или 'decision', "
                            f"текущий этап: {task.pipeline_stage}"
                        ),
                    }
                },
            )

    orchestrator = PipelineOrchestrator(db)

    if request.action == "approve":
        result_data = await orchestrator.approve_draft(
            draft_id, task.id,
            metadata_overrides=request.metadata_overrides,
        )
        # Set correlation IDs for downstream (CM-5)
        doc_id = result_data.get("document_id")
        ver_id = result_data.get("version_id")
        if doc_id:
            set_document_id(str(doc_id))
        if ver_id:
            set_version_id(str(ver_id))
        return DecideResponse(
            draft_id=draft_id,
            task_id=task.id,
            document_id=doc_id,
            version_id=ver_id,
            is_new_document=result_data.get("is_new_document", True),
            status="proceeding",
            action="approve",
            message="Запущена полная обработка документа",
        )

    elif request.action == "reject":
        await orchestrator.reject_draft(draft_id, task.id)
        return DecideResponse(
            draft_id=draft_id,
            task_id=task.id,
            status="discarded",
            action="reject",
            message="Черновик отклонён",
        )

    elif request.action == "proceed":
        result_data = await orchestrator.proceed_draft(
            draft_id, task.id,
            metadata_overrides=request.metadata_overrides,
        )
        doc_id = result_data.get("document_id")
        ver_id = result_data.get("version_id")
        if doc_id:
            set_document_id(str(doc_id))
        if ver_id:
            set_version_id(str(ver_id))
        return DecideResponse(
            draft_id=draft_id,
            task_id=task.id,
            document_id=doc_id,
            version_id=ver_id,
            is_new_document=result_data.get("is_new_document", True),
            status="proceeding",
            action="proceed",
            message="Обработка продолжена (internal)",
        )

    elif request.action == "stop_duplicate":
        result_data = await orchestrator.stop_duplicate_draft(draft_id, task.id)
        return DecideResponse(
            draft_id=draft_id,
            task_id=task.id,
            status=result_data.get("status", "discarded"),
            action="stop_duplicate",
            message=result_data.get("message", "Дубликат остановлен"),
        )

    elif request.action == "force_new_version":
        result_data = await orchestrator.force_new_version_draft(draft_id, task.id)
        doc_id = result_data.get("document_id")
        ver_id = result_data.get("version_id")
        if doc_id:
            set_document_id(str(doc_id))
        if ver_id:
            set_version_id(str(ver_id))
        return DecideResponse(
            draft_id=draft_id,
            task_id=task.id,
            document_id=doc_id,
            version_id=ver_id,
            is_new_document=False,
            status="proceeding",
            action="force_new_version",
            message=result_data.get("message", "Принудительное создание новой версии"),
        )

    # Should never reach here
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error": {
                "code": "BAD_REQUEST",
                "message": f"Неизвестное действие: {request.action}",
            }
        },
    )


# ---------------------------------------------------------------------------
#  DELETE /drafts/{draft_id}  — Delete draft
# ---------------------------------------------------------------------------


@router.delete(
    "/{draft_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"description": "Черновик не найден"}},
)
async def delete_draft(
    draft_id: int,
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    """Delete a draft (proxies to Registry)."""
    registry = RegistryServiceClient()
    try:
        result = await registry.delete_draft(draft_id)
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Черновик {draft_id} не найден",
                    }
                },
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Черновик {draft_id} не найден",
                    "details": {"original_error": str(exc)},
                }
            },
        )
    finally:
        await registry.close()


# ---------------------------------------------------------------------------
#  GET /drafts/{draft_id}/tasks  — List tasks for a draft
# ---------------------------------------------------------------------------


@router.get(
    "/{draft_id}/tasks",
    response_model=DraftTasksResponse,
    responses={404: {"description": "Черновик не найден"}},
)
async def get_draft_tasks(
    draft_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DraftTasksResponse:
    """List pipeline tasks for a draft."""
    result = await db.execute(
        select(Task)
        .where(Task.draft_id == draft_id, Task.deleted_at.is_(None))
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

    return DraftTasksResponse(
        draft_id=draft_id,
        tasks=task_items,
    )
