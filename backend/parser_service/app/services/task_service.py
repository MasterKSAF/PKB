"""
Сервис управления задачами.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging

from app.core.task_models import TaskInfo, TaskStatus
from app.api.v1.schemas import ProcessRequest, ProcessResponse, ProcessingMode

logger = logging.getLogger(__name__)


class TaskService:
    """
    Сервис для управления задачами обработки документов.
    """
    def __init__(self, task_store, pipeline_service, shutdown_event=None):
        self.task_store = task_store
        self.pipeline_service = pipeline_service
        self.shutdown_event = shutdown_event
        logger.debug("TaskService initialized")

    async def get_existing_task_response(self, task_id: int) -> Optional[ProcessResponse]:
        """
        Проверяет, существует ли активная (не завершённая) задача с данным task_id.
        Если существует – возвращает ProcessResponse с текущим статусом и оценкой времени.
        Если задача отсутствует или уже завершена – возвращает None.
        """
        existing = await self.task_store.get(task_id)
        if existing and existing.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            estimated = datetime.now(timezone.utc) + timedelta(seconds=30)
            logger.debug(
                "Task %d is active with status %s, returning existing response",
                task_id,
                existing.status.value,
            )
            return ProcessResponse(
                task_id=task_id,
                status=existing.status.value,
                estimated_completion=estimated,
            )
        return None

    async def start_processing(self, request: ProcessRequest):
        """
        Запускает обработку документа: для preview сразу выполняет, для full создаёт задачу.
        """
        if request.mode == ProcessingMode.PREVIEW:
            logger.debug("Preview mode for task %d", request.task_id)
            return await self.pipeline_service.run_preview(request)

        # Проверяем, не запущена ли уже задача
        existing_response = await self.get_existing_task_response(request.task_id)
        if existing_response:
            return existing_response

        # Создаём новую задачу
        task_info = TaskInfo(
            task_id=request.task_id,
            draft_id=request.draft_id,
            file_key=request.file_key,
            options=request.options or {},
        )
        await self.task_store.add(task_info)
        logger.info(
            "Task %d created for draft %d, file %s",
            request.task_id,
            request.draft_id,
            request.file_key,
        )

        estimated = datetime.now(timezone.utc) + timedelta(seconds=60)
        return ProcessResponse(
            task_id=request.task_id,
            status="accepted",
            mode=request.mode,
            estimated_completion=estimated,
        )

    async def get_task(self, task_id: int):
        """
        Возвращает информацию о задаче.
        """
        task = await self.task_store.get(task_id)
        if task:
            logger.debug("Task %d retrieved", task_id)
        else:
            logger.debug("Task %d not found", task_id)
        return task

    async def get_active_tasks(self):
        """
        Возвращает список активных задач.
        """
        tasks = await self.task_store.get_active_tasks()
        logger.debug("Retrieved %d active tasks", len(tasks))
        return tasks

    async def update_task(self, task_id: int, **kwargs):
        """
        Обновляет задачу.
        """
        updated = await self.task_store.update_task(task_id, **kwargs)
        if updated:
            logger.debug("Task %d updated with %s", task_id, kwargs)
        else:
            logger.warning("Task %d update failed (not found)", task_id)

    async def wait_for_change(self, task_id: int, current_version: int, timeout: float) -> bool:
        """
        Ожидает изменения задачи (long polling).
        """
        result = await self.task_store.wait_for_change(task_id, current_version, timeout)
        logger.debug(
            "Wait for change task %d returned %s",
            task_id,
            "changed" if result else "timeout",
        )
        return result

    async def create_task(self, task_id: int, draft_id: int, file_key: str, options: dict):
        """
        Создаёт новую задачу (используется при постановке в очередь).
        """
        task_info = TaskInfo(task_id=task_id, draft_id=draft_id, file_key=file_key, options=options)
        await self.task_store.add(task_info)
        logger.debug("Task %d created (internal)", task_id)

    async def remove_task(self, task_id: int):
        """Удаляет задачу из хранилища (при откате)."""
        await self.task_store.remove_task(task_id)
        logger.info("Task %d removed from storage (rollback)", task_id)