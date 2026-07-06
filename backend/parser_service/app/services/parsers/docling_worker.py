"""
Воркер для Docling парсинга в отдельном процессе.
Использует оригинальную convert_via_docling_md из docling_mapper.
"""
import tempfile
import os
import sys
import logging
import traceback
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

# Добавляем папку docling в sys.path для корректных импортов
_current_dir = Path(__file__).parent
_docling_dir = _current_dir / 'docling'
if str(_docling_dir) not in sys.path:
    sys.path.insert(0, str(_docling_dir))

from docling_mapper import convert_via_docling_md

logger = logging.getLogger(__name__)


# Кэш конвертера на уровне процесса (создаётся один раз в init_worker)
_converter = None


def init_worker():
    """
    Инициализация воркер-процесса: предзагрузка модели Docling.
    Конвертер создаётся один раз и переиспользуется для всех последующих задач.
    """
    global _converter
    logger.info("Initializing Docling worker process: pre-loading model...")
    # Импортируем _create_converter и создаём экземпляр конвертера
    from docling_mapper import _create_converter
    _converter = _create_converter()
    logger.info("Docling worker process initialized, model loaded (770/770)")


def parse_pdf_worker(file_bytes: bytes, max_pages: Optional[int], page_start: int,
                     images_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Вызывается в отдельном процессе для парсинга PDF.
    Создаёт временную папку, записывает файл, вызывает convert_via_docling_md.
    """
    # Проверка сигнатуры PDF
    if len(file_bytes) < 5 or not file_bytes[:5].startswith(b'%PDF'):
        return {"error": f"File does not start with PDF signature. Got: {file_bytes[:20]}"}

    # Создаём временную папку
    temp_dir = tempfile.mkdtemp(prefix="docling_")
    pdf_path = os.path.join(temp_dir, "document.pdf")

    try:
        # Записываем файл
        with open(pdf_path, "wb") as f:
            f.write(file_bytes)
            f.flush()
            os.fsync(f.fileno())

        # Проверяем размер
        actual_size = os.path.getsize(pdf_path)
        if actual_size != len(file_bytes):
            return {"error": f"File size mismatch: expected {len(file_bytes)}, got {actual_size}"}

        # Преобразуем в абсолютный путь (он уже абсолютный, но на всякий случай)
        abs_path = os.path.abspath(pdf_path)
        logger.debug(f"Temp PDF created: {abs_path}, size: {actual_size} bytes")

        # Вызываем функцию с переиспользуемым конвертером
        result = convert_via_docling_md(
            pdf_path=abs_path,
            max_pages=max_pages,
            page_start=page_start,
            images_dir=images_dir,
            converter=_converter,
        )
        return result

    except Exception as e:
        error_msg = f"Docling parsing failed: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return {"error": error_msg}

    finally:
        # Удаляем временную папку и всё её содержимое
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Failed to remove temp dir {temp_dir}: {e}")