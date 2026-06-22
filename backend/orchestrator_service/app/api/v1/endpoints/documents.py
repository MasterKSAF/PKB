"""Documents API endpoints — только pipeline-операция reprocess.

Все остальные GET /documents/*, POST /documents/{id}/versions, POST /documents/{id}/approve,
DELETE /documents/{id} перенесены в registry-service (см. docs/api/registry_service_api.md,
группа documents).

Здесь осталась только `POST /documents/{id}/reprocess` (P2I-9) — операция переиндексации,
требующая управления Celery-задачей, поэтому она принадлежит оркестратору.
"""

import logging
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.db.base import get_db
from app.schemas.documents import (
    ReprocessRequest,
    ReprocessResponse,
)

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
        created_at=datetime.now(UTC),
    )
