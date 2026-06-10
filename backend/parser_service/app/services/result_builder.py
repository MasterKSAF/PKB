"""
Построитель финального JSON-контейнера для сохранения в task_store.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


class ResultBuilder:
    """Собирает итоговый JSON, который будет передан оркестратору."""

    @staticmethod
    def build(
        task_id: int,
        final_json: Dict[str, Any],
        mode: str,
        preview_not_supported: bool = False
    ) -> Dict[str, Any]:
        """
        Формирует результат в формате, ожидаемом API.

        Args:
            task_id: ID задачи.
            final_json: Нормализованный JSON (с полями document_info, content, metadata).
            mode: "full" или "preview".
            preview_not_supported: Флаг, что предпросмотр не поддерживается (для v2).

        Returns:
            Словарь с полями task_id, metadata, document, quality, errors, status.
        """
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

        result = {
            "task_id": task_id,
            "metadata": {
                "schema": settings.parsing_schema,
                "mode": mode,
                "preview_not_supported": preview_not_supported,
                "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "parser": parser_info
            },
            "document": document,
            "quality": quality,
            "errors": errors,
            "status": status
        }

        logger.debug("Result built for task %d, mode=%s", task_id, mode)
        return result