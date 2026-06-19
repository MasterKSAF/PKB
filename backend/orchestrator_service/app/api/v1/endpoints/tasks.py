"""Tasks API endpoints — GET /tasks, GET /tasks/{task_id}/status."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.db.base import get_db
from app.models.pipeline import Task, TaskStep
from app.schemas.tasks import (
    TaskListResponse,
    TaskListItem,
    TaskStatsResponse,
    TaskStatusResponse,
    TaskStepItem,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=TaskListResponse,
    responses={400: {"description": "Ошибка пагинации"}},
)
async def list_tasks(
    draft_id: Optional[int] = Query(None, description="Фильтр по ID черновика"),
    status: Optional[str] = Query(None, description="Фильтр по статусу: active, completed, failed"),
    pipeline_type: Optional[str] = Query(None, description="Фильтр по типу: formation, indexation, reprocess"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(50, ge=1, le=200, description="Записей на странице"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskListResponse:
    """List pipeline tasks with filtering and pagination (read-only)."""
    conditions = []
    if draft_id is not None:
        conditions.append(Task.draft_id == draft_id)
    if status is not None:
        conditions.append(Task.status == status)
    if pipeline_type is not None:
        conditions.append(Task.pipeline_type == pipeline_type)

    # Count total
    count_query = select(func.count(Task.id))
    if conditions:
        count_query = count_query.where(*conditions)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch page
    query = select(Task).order_by(Task.created_at.desc())
    if conditions:
        query = query.where(*conditions)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    tasks = list(result.scalars().all())

    items = [
        TaskListItem(
            task_id=t.id,
            draft_id=t.draft_id,
            document_id=t.document_id,
            pipeline_type=t.pipeline_type,
            status=t.status,
            pipeline_stage=t.pipeline_stage,
            progress_percent=t.progress_percent,
            error_code=t.error_code,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in tasks
    ]

    return TaskListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/stats",
    response_model=TaskStatsResponse,
)
async def get_task_stats(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskStatsResponse:
    """Get task statistics (admin)."""
    # Total
    total_result = await db.execute(select(func.count(Task.id)))
    total = total_result.scalar() or 0

    # By status
    active_result = await db.execute(
        select(func.count(Task.id)).where(Task.status == "active")
    )
    active = active_result.scalar() or 0

    completed_result = await db.execute(
        select(func.count(Task.id)).where(Task.status == "completed")
    )
    completed = completed_result.scalar() or 0

    failed_result = await db.execute(
        select(func.count(Task.id)).where(Task.status == "failed")
    )
    failed = failed_result.scalar() or 0

    # By type
    type_result = await db.execute(
        select(Task.pipeline_type, func.count(Task.id)).group_by(Task.pipeline_type)
    )
    by_type = {row[0]: row[1] for row in type_result.all()}

    return TaskStatsResponse(
        total=total,
        active=active,
        completed=completed,
        failed=failed,
        by_type=by_type,
    )


@router.get(
    "/{task_id}",
    response_model=TaskStatusResponse,
    responses={404: {"description": "Задача не найдена"}},
)
async def get_task_by_id(
    task_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskStatusResponse:
    """Get task by ID with full details."""
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

    # Count notifications
    has_notifications = False
    critical_count = 0
    try:
        from app.models.pipeline import DraftNotification
        notif_result = await db.execute(
            select(DraftNotification).where(DraftNotification.task_id == task_id)
        )
        notifications = list(notif_result.scalars().all())
        has_notifications = len(notifications) > 0
        critical_count = sum(1 for n in notifications if n.severity == "critical")
    except Exception:
        pass

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
        version_id=task.version_id,
        status=task.status,
        pipeline_stage=task.pipeline_stage,
        progress_percent=task.progress_percent,
        has_notifications=has_notifications,
        critical_count=critical_count,
        steps=step_items,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )



