"""
Эндпоинт POST /parser/process – асинхронный запуск обработки документа.
Использует пайплайн с шагами: Download, Validate, Parse, Normalize, Standardize, SaveJson (опционально), StoreResult.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, status

from app.api.v1.schemas import ProcessRequest, ProcessResponse
from app.core.task_store import task_store
from app.core.task_models import TaskInfo, TaskStatus
from app.services.pipeline.pipeline import Pipeline
from app.services.pipeline.steps import (
    DownloadStep, ValidateStep, ParseStep, NormalizeStep,
    StandardizeStep, SaveJsonToFileStep, StoreResultStep
)
from app.services.pipeline.context import ProcessingContext
from app.services.normalizer import Normalizer
from app.services.standardizer import JsonStandardizer

router = APIRouter()


def get_process_pipeline() -> Pipeline:
    """
    Создаёт и возвращает пайплайн для полной обработки документа.
    Включает нормализацию, стандартизацию, опциональное сохранение JSON в файл.
    """
    normalizer = Normalizer()
    standardizer = JsonStandardizer()
    steps = [
        DownloadStep(),
        ValidateStep(),
        ParseStep(),
        NormalizeStep(normalizer),
        StandardizeStep(standardizer),
        SaveJsonToFileStep(),            # опциональное сохранение на диск
        StoreResultStep()
    ]
    return Pipeline(steps)


async def _run_pipeline(task_id: int, version_id: str, file_key: str, options: dict):
    """Фоновая задача: создаёт контекст и запускает пайплайн."""
    ctx = ProcessingContext(
        task_id=task_id,
        version_id=version_id,
        file_key=file_key,
        options=options
    )
    pipeline = get_process_pipeline()
    await pipeline.run(ctx)


@router.post("/process", status_code=status.HTTP_202_ACCEPTED, response_model=ProcessResponse)
async def start_processing(request: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Принимает запрос на обработку документа:
    - Проверяет идемпотентность (если задача уже существует и не завершена – возвращает её статус).
    - Создаёт новую задачу в task_store.
    - Запускает _run_pipeline в фоне.
    - Возвращает 202 Accepted с предполагаемым временем завершения.
    """
    # Идемпотентность: проверяем, нет ли уже активной задачи
    existing = task_store.get(request.task_id)
    if existing and existing.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
        return ProcessResponse(
            task_id=request.task_id,
            status=existing.status,
            version_id=request.version_id,
            estimated_completion=datetime.now(timezone.utc) + timedelta(seconds=30)
        )

    # Создаём новую задачу
    task_info = TaskInfo(
        task_id=request.task_id,
        version_id=request.version_id,
        file_key=request.file_key,
        options=request.options or {}
    )
    task_store.add(task_info)

    # Запускаем фоновую обработку
    background_tasks.add_task(
        _run_pipeline,
        request.task_id,
        request.version_id,
        request.file_key,
        request.options or {}
    )

    return ProcessResponse(
        task_id=request.task_id,
        status="accepted",
        version_id=request.version_id,
        estimated_completion=datetime.now(timezone.utc) + timedelta(seconds=30)
    )