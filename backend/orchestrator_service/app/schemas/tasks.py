"""
Pydantic schemas for Tasks API (GET /tasks/{task_id}/status).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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
    status: str = Field(..., description="Статус задачи: active, completed, failed")
    pipeline_stage: str = Field(..., description="Этап пайплайна")
    progress_percent: int = Field(0, description="Прогресс (0–100)")
    steps: List[TaskStepItem] = Field(default_factory=list, description="Шаги задачи")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: Optional[datetime] = Field(None, description="Время обновления")
