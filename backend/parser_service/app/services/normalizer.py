"""
Нормализация: обёртка сырого JSON от парсера в единый контейнер.
"""
import logging
from typing import Dict, Any
from app.services.parsers.base import ParseResult

logger = logging.getLogger(__name__)


class Normalizer:
    """Приводит результат парсера к единой структуре (контейнеру)."""

    async def normalize(self, parse_result: ParseResult, task_id: int) -> Dict[str, Any]:
        """
        Оборачивает сырой JSON в структуру с метаинформацией.

        Args:
            parse_result: Результат парсинга.
            task_id: ID задачи.

        Returns:
            Словарь с полями document_info, content, metadata.
        """
        logger.debug("Normalizing result for task %d", task_id)

        container = {
            "document_info": {
                "task_id": task_id,
                "parser_version": "1.0",
                "extraction_options": parse_result.full_json.get("options", {})
            },
            "content": parse_result.full_json,
            "metadata": {
                "total_pages": parse_result.total_pages,
                "has_tables": "table" in str(parse_result.full_json).lower()
            }
        }

        logger.debug("Normalization completed for task %d", task_id)
        return container