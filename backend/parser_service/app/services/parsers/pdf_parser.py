"""
PDF парсер на основе opendataloader_pdf.
Извлекает текст, таблицы, изображения (из base64 в JSON).
"""
import tempfile
import os
import json
import shutil
import base64
import re
from typing import Dict, Any, List, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor
import opendataloader_pdf
from app.services.parsers.base import BaseParser, ParseResult
import logging

logger = logging.getLogger(__name__)


class PdfParser(BaseParser):
    """Реализация парсера для PDF-файлов."""

    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=2)

    async def parse(self, file_bytes: bytes, options: Dict[str, bool]) -> ParseResult:
        """
        Запускает opendataloader_pdf.convert в отдельном потоке,
        читает сгенерированный JSON, извлекает изображения из base64.
        """
        # Создание временных файлов
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
            tmp_pdf.write(file_bytes)
            tmp_pdf_path = tmp_pdf.name
        output_dir = tempfile.mkdtemp()

        try:
            # Асинхронный вызов синхронного конвертера
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                self._executor,
                lambda: opendataloader_pdf.convert(
                    input_path=tmp_pdf_path,
                    output_dir=output_dir,
                    format="markdown,html,json",
                    keep_line_breaks=True,
                    quiet=False
                )
            )

            # Поиск JSON-файла
            files = os.listdir(output_dir)
            json_path = next((os.path.join(output_dir, f) for f in files if f.endswith('.json')), None)
            if not json_path:
                raise Exception("JSON file not generated")

            with open(json_path, 'r', encoding='utf-8') as f:
                full_json = json.load(f)

            # Извлечение изображений из base64 (если требуется)
            images = []
            if options.get('extract_images', True):
                images = self._extract_images_from_json(full_json)
                logger.info(f"Extracted {len(images)} images from JSON")

            # Определение количества страниц
            total_pages = self._get_total_pages(full_json)
            logger.info(f"Total pages: {total_pages}")

            return ParseResult(
                full_json=full_json,
                images=images,
                total_pages=total_pages
            )

        finally:
            # Очистка временных файлов
            os.unlink(tmp_pdf_path)
            shutil.rmtree(output_dir, ignore_errors=True)

    def _extract_images_from_json(self, obj: Any) -> List[Tuple[int, bytes, str]]:
        """Рекурсивно собирает изображения из полей 'data' (base64)."""
        images = []

        def extract(node, page_num=1):
            if isinstance(node, dict):
                if "page_num" in node:
                    page_num = node["page_num"]
                if "images" in node and isinstance(node["images"], list):
                    for img in node["images"]:
                        if "data" in img:
                            data = img["data"]
                            if isinstance(data, str):
                                try:
                                    data = base64.b64decode(data)
                                except Exception:
                                    data = data.encode()
                            ext = img.get("format", ".png")
                            if not ext.startswith("."):
                                ext = f".{ext}"
                            images.append((page_num, data, ext))
                for v in node.values():
                    extract(v, page_num)
            elif isinstance(node, list):
                for item in node:
                    extract(item, page_num)

        extract(obj)
        return images

    def _get_total_pages(self, full_json: dict) -> int:
        """Определяет количество страниц из JSON (разные возможные форматы)."""
        if "pages" in full_json and isinstance(full_json["pages"], list):
            return len(full_json["pages"])
        if "page_count" in full_json:
            return full_json["page_count"]
        if "metadata" in full_json and "pages" in full_json["metadata"]:
            return full_json["metadata"]["pages"]
        # Рекурсивный поиск максимального номера страницы
        max_page = 1
        def find_max(obj):
            nonlocal max_page
            if isinstance(obj, dict):
                if "page_num" in obj:
                    max_page = max(max_page, obj["page_num"])
                for v in obj.values():
                    find_max(v)
            elif isinstance(obj, list):
                for item in obj:
                    find_max(item)
        find_max(full_json)
        return max_page