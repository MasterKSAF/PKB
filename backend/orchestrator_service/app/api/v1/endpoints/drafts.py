"""Drafts API endpoints — upload, list, view, preview, decide, delete."""

import hashlib
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

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, get_current_user
from app.core.config import settings
from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.db.base import get_db
from app.schemas.drafts import (
    DecideRequest,
    DecideResponse,
    DraftCreateResponse,
    DraftDetailResponse,
    DraftItem,
    DraftListResponse,
    DraftPreviewResponse,
    DraftPreviewStatusResponse,
    PreviewMetadata,
)
from app.services.registry_client import RegistryServiceClient

logger = logging.getLogger(__name__)

router = APIRouter()

MOCK_USER_ID = "u-mock-001"
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB

ALLOWED_MIME = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/tiff",
}


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
        413: {"description": "Файл превышает 100 МБ"},
        422: {"description": "Ошибка валидации"},
    },
)
async def create_draft(
    file: UploadFile = File(..., description="Бинарный файл (PDF, PNG, JPG, TIFF)"),
    document_key: str = Form(..., description="Ключ документа (business key)"),
    title: Optional[str] = Form(None, description="Название документа"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DraftCreateResponse:
    """Upload a file and create a draft for processing."""
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

    # Validate file size after reading (catches cases where content-length
    # is missing or spoofed — e.g., during test with TestClient)
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

    # --- Check duplicates via Registry ---
    registry = RegistryServiceClient()
    is_duplicate_file = False
    is_duplicate_document = False
    try:
        uniqueness = await registry.check_uniqueness(
            file_hash_sha256=file_hash,
            title_hash_sha256=title_hash,
        )
        data = uniqueness.get("data", {})
        is_duplicate_file = data.get("is_duplicate_file", False)
        is_duplicate_document = data.get("is_duplicate_document", False)
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
        )
        draft_id = draft_result.get("data", {}).get("draft_id", 0)
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
        created_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
#  GET /drafts  — List drafts
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=DraftListResponse,
    responses={400: {"description": "Ошибка пагинации"}},
)
async def list_drafts(
    document_key: Optional[str] = Query(None, description="Ключ документа"),
    status: Optional[str] = Query(None, description="Статус черновика"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(50, ge=1, le=200, description="Записей на странице"),
    current_user: CurrentUser = Depends(get_current_user),
) -> DraftListResponse:
    """List drafts (proxies to Registry)."""
    registry = RegistryServiceClient()
    try:
        result = await registry.list_drafts(
            page=page,
            page_size=page_size,
            status=status,
        )
        data = result.get("data", [])
        meta = result.get("meta", {"total": 0, "page": page, "page_size": page_size})
        items = [DraftItem(**item) for item in data]
        return DraftListResponse(
            items=items,
            total=meta.get("total", 0),
            page=meta.get("page", page),
            page_size=meta.get("page_size", page_size),
        )
    except Exception as exc:
        logger.error(f"Failed to list drafts: {exc}")
        return DraftListResponse(items=[], total=0, page=page, page_size=page_size)
    finally:
        await registry.close()


# ---------------------------------------------------------------------------
#  GET /drafts/{draft_id}  — Draft details
# ---------------------------------------------------------------------------


@router.get(
    "/{draft_id}",
    response_model=DraftDetailResponse,
    responses={404: {"description": "Черновик не найден"}},
)
async def get_draft(
    draft_id: int,
    current_user: CurrentUser = Depends(get_current_user),
) -> DraftDetailResponse:
    """Get draft details (proxies to Registry)."""
    registry = RegistryServiceClient()
    try:
        result = await registry.get_draft(draft_id)
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
        return DraftDetailResponse(**data)
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
                year=data.get("year"),
                revision=data.get("revision"),
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
        409: {"description": "Некорректный статус для preview"},
    },
)
async def start_preview(
    draft_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Start preview phase for a draft."""
    # Get draft info
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

    # Start pipeline
    orchestrator = PipelineOrchestrator(db)
    await orchestrator.start_pipeline(
        draft_id=draft_id,
        task_id=task.id,
        file_key=file_key or "",
        mime_type="application/pdf",  # best guess
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
                        year=meta.get("year"),
                        revision=meta.get("revision"),
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
    from app.models.drafts import Draft

    # Проверяем, что draft существует и не удалён
    draft = await db.get(Draft, draft_id)
    if not draft or draft.status == "discarded":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Черновик {draft_id} не найден или удалён",
                }
            },
        )

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
    """Submit user decision after preview phase."""
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

    orchestrator = PipelineOrchestrator(db)

    if request.action == "approve":
        await orchestrator.approve_draft(draft_id, task.id)
        return DecideResponse(
            draft_id=draft_id,
            task_id=task.id,
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
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "BAD_REQUEST",
                    "message": f"Неизвестное действие: {request.action}. Допустимо: approve, reject",
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
