"""
Парсер на основе Docling + Markdown конвейер.
Использует ProcessPoolExecutor для вызова парсинга в отдельном процессе.
"""
import tempfile
import os
import json
import shutil
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

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

    # ---------- Сбор изображений из JSON ----------
    @staticmethod
    def _collect_image_paths(json_result: Dict[str, Any], base_dir: str) -> List[Tuple[int, str, str]]:
        """
        Собирает изображения из JSON-блоков, у которых есть image_key.
        image_key хранит путь относительно base_dir (например, 'images/page_1_1.png').
        Возвращает список (page_num, full_path, extension).
        """
        images = []
        blocks = json_result.get('content', {}).get('document', {}).get('block', [])
        for block in blocks:
            if block.get('type') != 'image':
                continue
            image_key = block.get('image_key', '')
            if not image_key:
                continue
            full_path = os.path.join(base_dir, image_key)
            if os.path.exists(full_path):
                _, ext = os.path.splitext(full_path)
                page_num = block.get('page number', 1)
                images.append((page_num, full_path, ext))
        logger.debug(f"DoclingParser: collected {len(images)} images")
        return images

    async def parse(
        self,
        file_bytes: bytes,
        options: Dict[str, bool],
        task_id: int,
        total_pages: Optional[int] = None,
    ) -> ParseResult:
        import time as _time
        t0 = _time.time()
        logger.info("DoclingParser: processing task %d", task_id)

        max_pages = options.get("max_pages")
        page_start = 1

        # Создаём временную папку для изображений (как в PdfParser)
        temp_dir = tempfile.mkdtemp(prefix=f"docling_parser_{task_id}_")
        images_dir = os.path.join(temp_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        t_setup = _time.time()

        try:
            loop = asyncio.get_running_loop()
            t_submit = _time.time()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    process_pool_executor,
                    parse_pdf_worker,
                    file_bytes,
                    max_pages,
                    page_start,
                    images_dir,
                ),
                timeout=DOCLING_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.error(f"Docling parsing timeout after {DOCLING_TIMEOUT}s for task {task_id}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"Docling parsing timeout after {DOCLING_TIMEOUT}s for task {task_id}")
        except Exception as e:
            logger.exception(f"Docling executor failed for task {task_id}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"Docling executor failed: {e}")

        # Проверяем, не вернулась ли ошибка
        if isinstance(result, dict) and "error" in result:
            error_msg = result["error"]
            logger.error(f"Docling worker returned error for task {task_id}: {error_msg}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"Docling parsing failed: {error_msg}")

        json_result = result
        t_exec = _time.time()
        logger.info("TIMING DoclingParser.parse: setup=%.3fs, executor=%.3fs (task %d)",
                     t_setup - t0, t_exec - t_submit, task_id)

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

        # ---- Собираем изображения ----
        images = self._collect_image_paths(json_result, temp_dir)
        if not options.get("extract_images", True):
            images = []

        return ParseResult(
            full_json=json_result,
            images=images,
            total_pages=total_pages_in_result,
            temp_dir=temp_dir,
        )