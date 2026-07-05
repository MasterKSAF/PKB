"""
Глобальный ProcessPoolExecutor для парсинга документов.
Использует spawn-контекст для изоляции и предотвращения проблем с fork.
"""
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from app.config import settings
from app.services.parsers.docling_worker import init_worker
import logging

logger = logging.getLogger(__name__)

# Используем spawn-контекст для надёжности
context = multiprocessing.get_context('spawn')

# Ограничиваем количество воркеров значением из настроек, но не более 2 для Docling
# (чтобы избежать перегрузки памяти)
max_workers = min(settings.max_concurrent_full_pipelines, 2)

# Создаём executor с initializer
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