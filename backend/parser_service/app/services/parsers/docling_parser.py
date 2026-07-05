"""
Парсер на основе Docling + Markdown конвейер.
Использует ProcessPoolExecutor для вызова парсинга в отдельном процессе.
"""
import tempfile
import os
import json
import asyncio
import logging
from typing import Optional, Dict, Any

from app.services.parsers.base import BaseParser, ParseResult
from app.config import settings
from app.core.executor import process_pool_executor
from app.services.parsers.docling_worker import parse_pdf_worker
from app.services.parsers.docling.quality_metrics import assess_quality_from_json

logger = logging.getLogger(__name__)

# Таймаут для Docling (можно переопределить через переменную окружения)
DOCLING_TIMEOUT = int(os.getenv("DOCLING_TIMEOUT", "1800"))  # 30 минут по умолчанию


class DoclingParser(BaseParser):
    """
    Парсер на основе Docling + Markdown конвейер.
    """

    def __init__(self):
        logger.debug("DoclingParser initialized")

    async def parse(
        self,
        file_bytes: bytes,
        options: Dict[str, bool],
        task_id: int,
        total_pages: Optional[int] = None,
    ) -> ParseResult:
        logger.info("DoclingParser: processing task %d", task_id)

        max_pages = options.get("max_pages")
        page_start = 1

        try:
            loop = asyncio.get_running_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    process_pool_executor,
                    parse_pdf_worker,
                    file_bytes,
                    max_pages,
                    page_start,
                ),
                timeout=DOCLING_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.error(f"Docling parsing timeout after {DOCLING_TIMEOUT}s for task {task_id}")
            raise RuntimeError(f"Docling parsing timeout after {DOCLING_TIMEOUT}s for task {task_id}")
        except Exception as e:
            logger.exception(f"Docling executor failed for task {task_id}")
            raise RuntimeError(f"Docling executor failed: {e}")

        # Проверяем, не вернулась ли ошибка
        if isinstance(result, dict) and "error" in result:
            error_msg = result["error"]
            logger.error(f"Docling worker returned error for task {task_id}: {error_msg}")
            raise RuntimeError(f"Docling parsing failed: {error_msg}")

        json_result = result

        # ---- Расчёт качества через quality_metrics ----
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_json:
                json.dump(json_result, tmp_json)
                tmp_json_path = tmp_json.name

            reports = await asyncio.to_thread(assess_quality_from_json, tmp_json_path)
            os.unlink(tmp_json_path)

            if reports:
                scores = [r.overall_score for r in reports.values()]
                avg_conf = round(sum(scores) / len(scores), 3) if scores else 0.0
                if 'content' in json_result and 'quality' in json_result['content']:
                    json_result['content']['quality']['confidence'] = avg_conf
                    for pp in json_result['content']['quality'].get('per_page', []):
                        page = pp.get('page')
                        if page in reports:
                            pp['confidence'] = round(reports[page].overall_score, 3)
                            pp['status'] = 'low_confidence' if reports[page].is_problematic else 'ok'
                logger.info(f"Docling quality recalculated: avg_confidence={avg_conf}")
        except Exception as e:
            logger.warning(f"Quality recalculation failed: {e}")

        total_pages_in_result = (
            json_result.get("content", {})
            .get("document", {})
            .get("source", {})
            .get("page_count", 1)
        )

        images = []

        return ParseResult(
            full_json=json_result,
            images=images,
            total_pages=total_pages_in_result,
            temp_dir=None,
        )