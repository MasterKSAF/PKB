"""
Построитель финального JSON-контейнера для сохранения в task_store.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class ResultBuilder:
    """Собирает итоговый JSON, который будет передан в API ответа."""

    @staticmethod
    def build(
        task_id: int,
        draft_id: int, 
        final_json: Optional[Dict[str, Any]],
        mode: str,
        preview_not_supported: bool = False
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
            Словарь с полями task_id, draft_id, metadata, document, quality, errors, status.
        """
        # Защита от None
        if final_json is None:
            logger.warning("final_json is None for task %d, using empty document", task_id)
            final_json = {}

        content = final_json.get("content", {})
        document = content.get("document", {})
        quality = content.get("quality", {})
        errors = content.get("errors", [])
        status = content.get("status", "completed")

        parser_info = {
            "name": "opendataloader_pdf",
            "version": "1.0",
            "ocr_engine": "none",
            "ocr_fallback": False
        }

        # ISO-формат без Z для совместимости с Pydantic datetime
        created_at_str = datetime.now(timezone.utc).isoformat()

        result = {
            "task_id": task_id,
            "draft_id": draft_id, 
            "metadata": {
                "schema": settings.parsing_schema,
                "mode": mode,
                "preview_not_supported": preview_not_supported,
                "created_at": created_at_str,
                "parser": parser_info
            },
            "document": document,
            "quality": quality,
            "errors": errors,
            "status": status
        }

        logger.debug("Result built for task %d, mode=%s", task_id, mode)
        return result