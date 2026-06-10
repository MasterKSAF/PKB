import tempfile
import os
import json
import shutil
import logging
from typing import Dict, Any, List, Tuple, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pypdf import PdfReader
from app.services.parsers.base import BaseParser, ParseResult
from app.config import settings

logger = logging.getLogger(__name__)


class PdfParser(BaseParser):
    """Парсер для PDF-файлов, использующий opendataloader_pdf."""

    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=2)
        logger.debug("PdfParser initialized with ThreadPoolExecutor")

    async def parse(
        self,
        file_bytes: bytes,
        options: Dict[str, bool],
        task_id: int,
        total_pages: Optional[int] = None
    ) -> ParseResult:
        """
        Выполняет парсинг PDF-файла.

        Args:
            file_bytes: Содержимое PDF в байтах.
            options: Опции парсинга (extract_tables, extract_images).
            task_id: ID задачи для логирования.
            total_pages: Опционально известное количество страниц.

        Returns:
            ParseResult с JSON и списком изображений.

        Raises:
            TimeoutError: Если парсинг превысил таймаут.
        """
        logger.info("Parsing PDF for task %d, options=%s", task_id, options)
        import opendataloader_pdf

        if total_pages is None:
            try:
                reader = PdfReader(file_bytes)
                total_pages_original = len(reader.pages)
                logger.debug("Page count determined by PdfReader: %d", total_pages_original)
            except Exception as e:
                total_pages_original = 1
                logger.warning("Failed to get page count via pypdf: %s", str(e))
        else:
            total_pages_original = total_pages
            logger.debug("Using provided total_pages=%d", total_pages_original)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
            tmp_pdf.write(file_bytes)
            tmp_pdf_path = tmp_pdf.name
            logger.debug("Temporary PDF file created: %s", tmp_pdf_path)

        output_dir = tempfile.mkdtemp()
        logger.debug("Temporary output directory created: %s", output_dir)

        try:
            loop = asyncio.get_running_loop()
            await asyncio.wait_for(
                loop.run_in_executor(
                    self._executor,
                    lambda: opendataloader_pdf.convert(
                        input_path=tmp_pdf_path,
                        output_dir=output_dir,
                        format="markdown,html,json",
                        keep_line_breaks=True,
                        quiet=False
                    )
                ),
                timeout=settings.parser_timeout
            )
            logger.info("opendataloader_pdf conversion completed for task %d", task_id)

            files = os.listdir(output_dir)
            json_path = next((os.path.join(output_dir, f) for f in files if f.endswith('.json')), None)
            if not json_path:
                raise FileNotFoundError("JSON file not generated")

            with open(json_path, 'r', encoding='utf-8') as f:
                full_json = json.load(f)
            logger.debug("Loaded JSON from %s", json_path)

            images = self._collect_image_paths(full_json, output_dir)
            logger.info("Found %d image references in JSON", len(images))

            if not options.get('extract_images', True):
                images = []
                logger.debug("Image extraction disabled by options")

            return ParseResult(
                full_json=full_json,
                images=images,
                total_pages=total_pages_original,
                temp_dir=output_dir
            )
        except asyncio.TimeoutError:
            logger.error(
                "PDF parsing timeout after %d seconds for task %d",
                settings.parser_timeout, task_id, exc_info=True
            )
            shutil.rmtree(output_dir, ignore_errors=True)
            raise TimeoutError(
                f"PDF parsing timeout after {settings.parser_timeout}s for task {task_id}"
            )
        except Exception as e:
            logger.exception("PDF parsing error for task %d", task_id)
            shutil.rmtree(output_dir, ignore_errors=True)
            raise
        finally:
            try:
                os.unlink(tmp_pdf_path)
                logger.debug("Temporary PDF file removed: %s", tmp_pdf_path)
            except Exception:
                pass

    def _collect_image_paths(self, obj: Any, base_dir: str) -> List[Tuple[int, str, str]]:
        """
        Рекурсивно собирает пути к изображениям из JSON.

        Args:
            obj: Часть JSON (словарь или список).
            base_dir: Базовая временная директория.

        Returns:
            Список кортежей (page_num, full_path, extension).
        """
        images = []
        logger.debug("Collecting image paths in %s", base_dir)

        def collect(node, page_num=1):
            if isinstance(node, dict):
                if "page_num" in node:
                    page_num = node["page_num"]
                for key in ("image_key", "source", "file_path", "path"):
                    if key in node and isinstance(node[key], str):
                        path = node[key]
                        if not os.path.isabs(path):
                            full_path = os.path.join(base_dir, path)
                        else:
                            full_path = path
                        if os.path.exists(full_path) and full_path.startswith(base_dir):
                            _, ext = os.path.splitext(full_path)
                            images.append((page_num, full_path, ext))
                            node["_temp_path"] = full_path
                for v in node.values():
                    collect(v, page_num)
            elif isinstance(node, list):
                for item in node:
                    collect(item, page_num)

        collect(obj)
        logger.debug("Collected %d images", len(images))
        return images