"""
Построитель финального JSON-контейнера для сохранения в task_store.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


def build_result(
    task_id: int,
    draft_id: int,
    final_json: Optional[Dict[str, Any]],
    mode: str,
    preview_not_supported: bool = False,
) -> Dict[str, Any]:
    """
    Формирует результат в формате, ожидаемом API.

    Args:
        task_id: ID задачи.
        draft_id: ID черновика.
        final_json: Нормализованный JSON (с полями document_info, content, metadata).
                     Может быть None – тогда используется пустая структура.
        mode: "full" или "preview".
        preview_not_supported: Флаг, что предпросмотр не поддерживается (для v2).

    Returns:
        Словарь с полями metadata, document, quality, errors, status.
    """
    logger.debug("Building result for task %d, mode=%s", task_id, mode)

    # Защита от None
    if final_json is None:
        logger.warning("final_json is None for task %d, using empty document", task_id)
        final_json = {}

    # Определяем, является ли final_json контейнером (содержит content)
    if "content" in final_json and "document_info" in final_json:
        # Контейнер от нормализатора
        content = final_json.get("content", {})
        document = content.get("document", {})
        quality = content.get("quality", {})
        errors = content.get("errors", [])
        status = content.get("status", "completed")
    elif "document" in final_json:
        # Уже готовый результат (например, от стандартизатора напрямую)
        document = final_json.get("document", {})
        quality = final_json.get("quality", {})
        errors = final_json.get("errors", [])
        status = final_json.get("status", "completed")
    elif "content" in final_json and "document" in final_json.get("content", {}):
        # Docling-формат: {"content": {"document": {...}, "quality": {...}}, "metadata": {...}}
        content = final_json["content"]
        document = content.get("document", {})
        quality = content.get("quality", {})
        errors = content.get("errors", [])
        status = content.get("status", "completed")
    else:
        # Пустой случай
        document = {}
        quality = {}
        errors = []
        status = "completed"

    parser_info = {
        "name": "docling",
        "version": "2.0",
        "ocr_engine": "docling",
        "ocr_fallback": False,
    }

    # Формируем created_at в формате ISO 8601 с Z (UTC) без миллисекунд
    created_at_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Собираем metadata согласно спецификации (table.txt)
    metadata = {
        "schema": settings.parsing_schema,
        "task_id": task_id,
        "draft_id": draft_id,
        "created_at": created_at_str,
        "mode": mode,
        "preview_not_supported": preview_not_supported,
        "parser": parser_info,
    }

    result = {
        "metadata": metadata,
        "document": document,
        "quality": quality,
        "errors": errors,
        "status": status,
    }

    logger.info("Result built for task %d, mode=%s", task_id, mode)
    return result