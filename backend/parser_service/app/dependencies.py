"""
Фабрики зависимостей для внедрения сервисов в эндпоинты.
Инициализация выполняется один раз при старте приложения.
"""
import logging
from app.services.task_service import TaskService
from app.services.pipeline_service import PipelineService
from app.core.task_store import task_store
from app.core.minio_client import minio_client
from app.config import settings

logger = logging.getLogger(__name__)

_task_service = None
_pipeline_service = None


def init_services(shutdown_event):
    """
    Вызывается в lifespan для создания экземпляров сервисов.
    """
    global _task_service, _pipeline_service
    logger.debug("Initializing services")
    _pipeline_service = PipelineService(minio_client, task_store, settings, shutdown_event)
    _task_service = TaskService(task_store, _pipeline_service, shutdown_event)
    logger.info("Services initialized successfully")


def get_task_service() -> TaskService:
    """
    Возвращает экземпляр TaskService.
    """
    if _task_service is None:
        logger.error("TaskService accessed before initialization")
        raise RuntimeError("TaskService not initialized")
    return _task_service


def get_pipeline_service() -> PipelineService:
    """
    Возвращает экземпляр PipelineService.
    """
    if _pipeline_service is None:
        logger.error("PipelineService accessed before initialization")
        raise RuntimeError("PipelineService not initialized")
    return _pipeline_service