"""Documents API endpoints — pipeline-операции и связь с задачами.

Оркестратор управляет только:
- `POST /documents/{id}/reprocess` (P2I-9) — переиндексация через Celery
- `GET /documents/{id}/tasks` — список pipeline-задач документа

Все остальные GET /documents/*, POST /documents/{id}/versions, POST /documents/{id}/approve,
DELETE /documents/{id} перенесены в registry-service (см. docs/api/registry_service_api.md,
группа documents).
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.db.base import get_db
from app.models.pipeline import Task
from app.schemas.documents import (
    ReprocessRequest,
    ReprocessResponse,
)
from app.schemas.tasks import DocumentTasksResponse, DraftTaskItem

logger = logging.getLogger(__name__)

router = APIRouter()


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
    task = await repo.create_task(
        draft_id=0,  # reprocess has no draft
        pipeline_type="reprocess",
        total_steps=1,
    )
    task.document_id = int(doc_id) if doc_id.isdigit() else None
    await db.flush()

    # Trigger reprocess Celery task
    run_reprocess_step.delay(task.id, doc_id)

    return ReprocessResponse(
        mode=request.mode,
        document_id=doc_id,
        task_id=str(task.id),
        status="reprocessing_queued",
        created_at=datetime.now(timezone.utc),
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
