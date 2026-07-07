"""
Глобальный ProcessPoolExecutor для парсинга документов.
Использует spawn-контекст для изоляции и предотвращения проблем с fork.

С docling-serve (HTTP) воркеры не загружают модели — можно больше процессов.
"""
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from app.config import settings
from app.services.parsers.docling_worker import init_worker
import logging

logger = logging.getLogger(__name__)

# Используем spawn-контекст для надёжности
context = multiprocessing.get_context('spawn')

# Количество воркеров — из настроек (модели не загружаются, память не проблема)
max_workers = settings.max_concurrent_full_pipelines

process_pool_executor = ProcessPoolExecutor(
    max_workers=max_workers,
    mp_context=context,
    initializer=init_worker,
)

def shutdown_executor():
    """Завершает executor при остановке приложения."""
    logger.info("Shutting down ProcessPoolExecutor...")
    process_pool_executor.shutdown(wait=True)
    logger.info("ProcessPoolExecutor shut down")