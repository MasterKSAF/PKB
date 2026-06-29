"""
Pydantic schemas for Tasks API (GET /tasks, GET /tasks/{task_id}/status).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import PaginationMeta


class TaskStepItem(BaseModel):
    """Single step in task status response."""

    step_name: str = Field(..., description="Название шага")
    service_name: str = Field(..., description="Сервис-исполнитель")
    status: str = Field(..., description="Статус шага")
    input_data: Optional[Dict[str, Any]] = Field(None, description="Входные данные")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Выходные данные")
    started_at: Optional[datetime] = Field(None, description="Время начала")
    completed_at: Optional[datetime] = Field(None, description="Время завершения")


class TaskStatusResponse(BaseModel):
    """Response for GET /tasks/{task_id}/status."""

    task_id: int = Field(..., description="ID задачи")
    draft_id: int = Field(..., description="ID черновика")
    document_id: Optional[int] = Field(None, description="ID документа (после approve)")
    version_id: Optional[int] = Field(None, description="ID версии документа")
    status: str = Field(..., description="Статус задачи: active, completed, failed")
    pipeline_stage: str = Field(..., description="Этап пайплайна")
    progress_percent: int = Field(0, description="Прогресс (0-100)")
    has_notifications: bool = Field(False, description="Есть уведомления о качестве")
    critical_count: int = Field(0, description="Количество критических уведомлений")
    error_code: Optional[str] = Field(None, description="Код ошибки")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")
    steps: List[TaskStepItem] = Field(default_factory=list, description="Шаги задачи")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: Optional[datetime] = Field(None, description="Время обновления")


class TaskListItem(BaseModel):
    """Task item in list response."""

    task_id: int = Field(..., description="ID задачи")
    draft_id: int = Field(..., description="ID черновика")
    document_id: Optional[int] = Field(None, description="ID документа")
    pipeline_type: str = Field(..., description="Тип пайплайна")
    status: str = Field(..., description="Статус задачи")
    pipeline_stage: str = Field(..., description="Этап пайплайна")
    progress_percent: int = Field(0, description="Прогресс")
    error_code: Optional[str] = Field(None, description="Код ошибки")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: Optional[datetime] = Field(None, description="Время обновления")


class TaskListResponse(BaseModel):
    """Response for GET /tasks."""

    items: List[TaskListItem] = Field(default_factory=list, description="Список задач")
    meta: PaginationMeta = Field(
        default_factory=lambda: PaginationMeta(total=0, page=1, page_size=50),
        description="Метаданные пагинации",
    )


class TaskStatsResponse(BaseModel):
    """Task statistics."""

    total: int = Field(0, description="Всего задач")
    by_status: Dict[str, int] = Field(
        default_factory=dict,
        description=(
            "Количество задач по статусам: "
            "uploaded, previewing, ready_for_approve, processing, "
            "created, indexing, indexed, failed"
        ),
    )
    by_stage: Dict[str, int] = Field(
        default_factory=dict,
        description=(
            "Количество задач по этапам: "
            "upload, preview, decision, full, registry, indexation"
        ),
    )


class TaskStepsListResponse(BaseModel):
    """Response for GET /tasks/{id}/steps."""

    task_id: int = Field(..., description="ID задачи")
    total: int = Field(0, description="Всего шагов")
    steps: List[TaskStepItem] = Field(default_factory=list, description="Список шагов")


class DraftTaskItem(BaseModel):
    """Task item in draft tasks list (GET /drafts/{draft_id}/tasks)."""

    task_id: int = Field(..., description="ID задачи")
    status: str = Field(..., description="Статус задачи")
    pipeline_stage: str = Field(..., description="Этап пайплайна")
    initiated_by: Optional[str] = Field(None, description="Кто инициировал")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: Optional[datetime] = Field(None, description="Время обновления")


class DraftTasksResponse(BaseModel):
    """Response for GET /drafts/{draft_id}/tasks."""

    draft_id: int = Field(..., description="ID черновика")
    tasks: List[DraftTaskItem] = Field(default_factory=list, description="Список задач")


class DocumentTasksResponse(BaseModel):
    """Response for GET /documents/{doc_id}/tasks."""

    document_id: int = Field(..., description="ID документа")
    tasks: List[DraftTaskItem] = Field(default_factory=list, description="Список задач пайплайна")
