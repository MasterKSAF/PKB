"""Tasks API endpoints — GET /tasks/{task_id}/status."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.db.base import get_db
from app.models.pipeline import Task, TaskStep
from app.schemas.tasks import TaskStatusResponse, TaskStepItem

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/{task_id}/status",
    response_model=TaskStatusResponse,
    responses={404: {"description": "Задача не найдена"}},
)
async def get_task_status(
    task_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskStatusResponse:
    """Get task status with step details."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Задача {task_id} не найдена",
                }
            },
        )

    steps_result = await db.execute(
        select(TaskStep)
        .where(TaskStep.task_id == task_id)
        .order_by(TaskStep.step_index)
    )
    steps = list(steps_result.scalars().all())

    step_items = [
        TaskStepItem(
            step_name=s.step_name,
            service_name=s.service_name,
            status=s.status,
            input_data=s.input_data,
            output_data=s.output_data,
            started_at=s.started_at,
            completed_at=s.completed_at,
        )
        for s in steps
    ]

    return TaskStatusResponse(
        task_id=task.id,
        draft_id=task.draft_id,
        document_id=task.document_id,
        status=task.status,
        pipeline_stage=task.pipeline_stage,
        progress_percent=task.progress_percent,
        steps=step_items,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )
