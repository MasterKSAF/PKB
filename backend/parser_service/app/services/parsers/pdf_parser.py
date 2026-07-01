"""
Парсер PDF-файлов с использованием opendataloader_pdf.
Версия: 5.1.0 (быстрая) – блочная обработка по 100 страниц.
"""
import tempfile
import os
import json
import shutil
import logging
import asyncio
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union

from app.services.parsers.base import BaseParser, ParseResult
from app.config import settings
from pypdf import PdfReader
import opendataloader_pdf

from app.services.standardizer import JsonStandardizer
from .quality_metrics import assess_quality_from_json

logger = logging.getLogger(__name__)


class PdfParser(BaseParser):
    """Парсер для PDF-файлов (оптимизированная блочная версия)."""

    def __init__(self):
        self.threads = settings.parser_threads or min(os.cpu_count() or 4, 8)
        self.parallel_workers = settings.parser_parallel_workers or min(os.cpu_count() or 4, 8)
        self.hybrid_mode = settings.parser_use_hybrid
        self.image_format = settings.parser_image_format
        self.max_pages_standard = settings.parser_max_pages_for_standard
        self.max_size_mb_standard = settings.parser_max_size_mb_for_standard
        self.enable_page_by_page = settings.parser_enable_page_by_page
        self.java_opts = settings.parser_java_opts
        self.chunk_size = settings.parser_chunk_size  # новый параметр
        self.standardizer = JsonStandardizer()

        logger.debug(
            "PdfParser initialized: hybrid=%s, threads=%d, page_by_page=%s, chunk_size=%d",
            self.hybrid_mode, self.threads, self.enable_page_by_page, self.chunk_size
        )

    # ---------- Вспомогательные методы ----------
    def _get_page_count(self, file_bytes: bytes) -> Optional[int]:
        try:
            import io
            reader = PdfReader(io.BytesIO(file_bytes))
            return len(reader.pages)
        except Exception as e:
            logger.warning(f"Не удалось определить число страниц: {e}")
            return None

    def _get_file_size_mb(self, file_bytes: bytes) -> float:
        return len(file_bytes) / (1024 * 1024)

    async def _run_cli(self, pdf_path: str, output_dir: str, page_num: Optional[Union[int, str]],
                       images_dir: str, threads: int, hybrid: bool, timeout: int) -> bool:
        """
        Запуск CLI через синхронный subprocess.run в отдельном потоке.
        page_num может быть int (для одной страницы) или str (диапазон "1-100").
        """
        env = os.environ.copy()
        env["JAVA_OPTS"] = self.java_opts

        cmd = [
            "opendataloader-pdf",
            pdf_path,
            "--output", output_dir,
            "--format", "markdown,html,json",
            "--keep-line-breaks",
            "--quiet",
            "--threads", str(threads),
            "--image-output", "external",
            "--image-format", self.image_format,
            "--image-dir", images_dir
        ]
        if page_num is not None:
            # если page_num — строка (диапазон), передаём как есть
            if isinstance(page_num, str):
                cmd.extend(["--pages", page_num])
            else:
                cmd.extend(["--pages", str(page_num)])
        if hybrid and self.hybrid_mode:
            cmd.extend(["--hybrid", "docling-fast"])

        logger.debug(f"Запуск команды: {' '.join(cmd)}")

        def run_sync():
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=env
                )
                if result.returncode != 0:
                    logger.error(f"CLI ошибка (код {result.returncode}): {result.stderr}")
                    return False
                if result.stdout:
                    for line in result.stdout.splitlines():
                        if not any(x in line for x in ["Format 14 cmap", "List is not added"]):
                            logger.info(line)
                return True
            except subprocess.TimeoutExpired:
                logger.error(f"CLI превысил время ожидания ({timeout} сек)")
                return False
            except Exception as e:
                logger.error(f"CLI ошибка: {e}")
                return False

        return await asyncio.to_thread(run_sync)

    async def _run_python_api(self, pdf_path: str, output_dir: str, page_num: Optional[Union[int, str]],
                              images_dir: str, timeout: int) -> bool:
        """
        Запуск Python API (fallback).
        page_num может быть int или str (диапазон).
        """
        def sync_convert():
            try:
                kwargs = {
                    "input_path": pdf_path,
                    "output_dir": output_dir,
                    "format": "markdown,html,json",
                    "keep_line_breaks": True,
                    "quiet": True,
                    "image_output": "external",
                    "image_format": self.image_format,
                    "image_dir": images_dir
                }
                if page_num is not None:
                    kwargs["pages"] = str(page_num)  # всегда преобразуем в строку
                if self.hybrid_mode:
                    kwargs["hybrid"] = "docling-fast"
                opendataloader_pdf.convert(**kwargs)
                return True
            except Exception as e:
                logger.error(f"Python API ошибка: {e}")
                return False

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(sync_convert),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Python API превысил таймаут ({timeout} сек)")
            return False

    async def _run_parser(self, pdf_path: str, output_dir: str,
                          page_num: Optional[Union[int, str]] = None,
                          images_dir: Optional[str] = None,
                          is_page_mode: bool = False) -> bool:
        """
        Последовательно пробует CLI_hybrid, CLI_no_hybrid, PythonAPI.
        page_num может быть int или str (диапазон).
        """
        threads = 1 if is_page_mode else self.threads
        timeout = settings.parser_page_timeout if is_page_mode else settings.parser_timeout

        attempts = []
        if self.hybrid_mode:
            attempts.append(("CLI_hybrid", True, False))
        attempts.append(("CLI_no_hybrid", False, False))
        attempts.append(("PythonAPI", False, True))

        for mode_name, hybrid_flag, use_python in attempts:
            success = False
            try:
                if use_python:
                    success = await self._run_python_api(pdf_path, output_dir, page_num, images_dir, timeout)
                else:
                    success = await self._run_cli(pdf_path, output_dir, page_num, images_dir,
                                                  threads, hybrid_flag, timeout)
            except Exception as e:
                logger.error(f"Исключение в {mode_name}: {e}")
                success = False

            if success:
                logger.info(f"   ✅ Успешная попытка: {mode_name}")
                return True
            else:
                logger.warning(f"   ❌ Попытка {mode_name} не удалась")

        logger.error("❌ Все попытки запуска парсера не удались")
        return False

    # ---------- Обработка блоков страниц ----------
    def _copy_images_with_rename(self, src_dir: str, dst_dir: str, page_offset: int) -> None:
        """Копирует изображения из src_dir в dst_dir с переименованием, учитывая смещение страниц."""
        if not os.path.exists(src_dir):
            return
        image_files = []
        for f in os.listdir(src_dir):
            full_path = os.path.join(src_dir, f)
            if os.path.isfile(full_path):
                ext = os.path.splitext(f)[1].lower()
                if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']:
                    image_files.append(f)
        image_files.sort()
        for idx, img_file in enumerate(image_files, start=1):
            src_path = os.path.join(src_dir, img_file)
            ext = os.path.splitext(img_file)[1]
            # Номер страницы = смещение + индекс
            page_num = page_offset + idx
            new_name = f"page_{page_num}_{idx}{ext}"
            dst_path = os.path.join(dst_dir, new_name)
            counter = 1
            while os.path.exists(dst_path):
                dst_path = os.path.join(dst_dir, f"page_{page_num}_{idx}_{counter}{ext}")
                counter += 1
            shutil.copy2(src_path, dst_path)

    def _merge_chunk_results(self, chunk_jsons: Dict[int, Dict[str, Any]],
                             total_pages: int, output_json_path: str, pdf_filename: str) -> None:
        """
        Объединяет JSON-ы из нескольких блоков в один итоговый JSON.
        chunk_jsons: {start_page: data}
        """
        all_blocks = []
        for start, data in sorted(chunk_jsons.items()):
            if "kids" in data:
                for block in data["kids"]:
                    # Убедимся, что у блока есть номер страницы
                    if "page number" not in block:
                        # Номер страницы можно вычислить по порядку, но лучше, если он уже есть
                        pass
                    all_blocks.append(block)
            else:
                logger.warning(f"Блок с начальной страницей {start} не содержит 'kids'")

        final_data = {
            "file name": pdf_filename,
            "number of pages": total_pages,
            "kids": all_blocks
        }
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Объединённый JSON сохранён: {output_json_path}")

    async def _process_pdf_chunked(self, pdf_path: str, output_dir: str,
                                   global_images_dir: str, total_pages: int) -> bool:
        """
        Обрабатывает PDF блоками по chunk_size страниц.
        """
        chunk_size = self.chunk_size
        logger.info(f"🔸 Блочный режим ({total_pages} стр., блок по {chunk_size} стр.)")

        chunk_jsons = {}
        temp_dirs = []

        try:
            for start in range(1, total_pages + 1, chunk_size):
                end = min(start + chunk_size - 1, total_pages)
                page_range = f"{start}-{end}"
                logger.info(f"   Обработка блока страниц {start}-{end}")

                # Создаём временную папку для блока
                block_temp_dir = tempfile.mkdtemp(prefix=f"block_{start}_{end}_")
                temp_dirs.append(block_temp_dir)

                # Запускаем парсер для диапазона страниц
                success = await self._run_parser(
                    pdf_path, block_temp_dir,
                    page_num=page_range,
                    images_dir=os.path.join(block_temp_dir, "images"),
                    is_page_mode=False  # используем стандартные потоки
                )
                if not success:
                    logger.error(f"Ошибка обработки блока {start}-{end}")
                    return False

                # Находим JSON в папке блока
                json_files = list(Path(block_temp_dir).glob("*.json"))
                if not json_files:
                    logger.error(f"JSON не найден для блока {start}-{end}")
                    return False
                json_path = str(json_files[0])
                with open(json_path, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)

                # Сохраняем данные блока
                chunk_jsons[start] = chunk_data

                # Копируем изображения из блока в глобальную папку
                src_images = os.path.join(block_temp_dir, "images")
                if os.path.exists(src_images) and os.listdir(src_images):
                    # Переименовываем с учётом номера страницы
                    self._copy_images_with_rename(src_images, global_images_dir, start - 1)
                    logger.debug(f"   Изображения скопированы из блока {start}-{end}")

                # Очищаем временную папку блока
                shutil.rmtree(block_temp_dir, ignore_errors=True)
                temp_dirs.remove(block_temp_dir)

            # Объединяем все блоки в один JSON
            output_json = os.path.join(output_dir, f"{Path(pdf_path).stem}.json")
            self._merge_chunk_results(chunk_jsons, total_pages, output_json, os.path.basename(pdf_path))
            return True

        except Exception as e:
            logger.error(f"Ошибка в блочной обработке: {e}")
            # Очистка временных папок
            for tmp in temp_dirs:
                shutil.rmtree(tmp, ignore_errors=True)
            return False

    # ---------- Сбор изображений из JSON ----------
    def _collect_image_paths(self, obj: Any, base_dir: str) -> List[Tuple[int, str, str]]:
        images = []

        def collect(node, page_num=1):
            if isinstance(node, dict):
                if "page_num" in node:
                    page_num = node["page_num"]
                for key in ("image_key", "source", "file_path", "path"):
                    if key in node and isinstance(node[key], str):
                        path = node[key]
                        full_path = os.path.join(base_dir, path) if not os.path.isabs(path) else path
                        if not os.path.exists(full_path) and not os.path.isabs(path):
                            alt_path = os.path.join(base_dir, "images", os.path.basename(path))
                            if os.path.exists(alt_path):
                                full_path = alt_path
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
        logger.debug(f"Собрано {len(images)} изображений")
        return images

    # ---------- Стандартизация и качество ----------
    def _update_quality(self, standardized: Dict[str, Any], quality_report: Dict[str, Any]) -> Dict[str, Any]:
        if not quality_report:
            return standardized

        avg_conf = quality_report.get("avg_confidence")
        if avg_conf is not None:
            standardized["quality"]["confidence"] = avg_conf

        problematic = quality_report.get("problematic_pages", [])
        if problematic:
            notifications = standardized["quality"].get("notifications", [])
            notifications.append({"message": f"problematic_pages: {problematic}"})
            standardized["quality"]["notifications"] = notifications

        per_page = standardized["quality"].get("per_page", [])
        pages_reports = {r["page_num"]: r for r in quality_report.get("pages", [])}
        for item in per_page:
            page_num = item.get("page")
            if page_num in pages_reports:
                overall = pages_reports[page_num].get("overall_score")
                if overall is not None:
                    item["confidence"] = overall
                    item["status"] = "low_confidence" if overall < 0.65 else "ok"

        return standardized

    # ---------- Основной метод ----------
    async def parse(
        self,
        file_bytes: bytes,
        options: Dict[str, bool],
        task_id: int,
        total_pages: Optional[int] = None,
    ) -> ParseResult:
        logger.info(f"Parsing PDF for task {task_id}, options={options}")

        original_file_name = options.get("original_file_name", "unknown.pdf")

        if total_pages is None:
            total_pages = self._get_page_count(file_bytes) or 1
        size_mb = self._get_file_size_mb(file_bytes)
        logger.info(f"File size: {size_mb:.2f} MB, pages: {total_pages}")

        # Решение о блочной обработке: если включён постраничный режим и страниц > 200
        use_chunked = (
            self.enable_page_by_page and
            (total_pages > 200 or size_mb > self.max_size_mb_standard)
        )

        temp_dir = tempfile.mkdtemp(prefix=f"pdf_parser_{task_id}_")
        logger.debug(f"Temp dir: {temp_dir}")

        global_images_dir = os.path.join(temp_dir, "images")
        os.makedirs(global_images_dir, exist_ok=True)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
            tmp_pdf.write(file_bytes)
            pdf_path = tmp_pdf.name

        raw_json = None

        try:
            if use_chunked:
                success = await self._process_pdf_chunked(pdf_path, temp_dir,
                                                          global_images_dir, total_pages)
                if not success:
                    raise RuntimeError("Блочная обработка не удалась")
            else:
                logger.info(f"🔹 Стандартный режим ({total_pages} стр., {self.threads} потоков)")
                success = await self._run_parser(pdf_path, temp_dir, page_num=None,
                                                 images_dir=global_images_dir, is_page_mode=False)
                if not success and self.enable_page_by_page:
                    logger.warning("Стандартный режим не удался, пробуем блочный")
                    success = await self._process_pdf_chunked(pdf_path, temp_dir,
                                                              global_images_dir, total_pages)
                if not success:
                    raise RuntimeError("Все попытки обработки не удались")

            json_files = list(Path(temp_dir).glob("*.json"))
            if not json_files:
                raise FileNotFoundError("JSON файл не найден")
            json_path = str(json_files[0])
            with open(json_path, 'r', encoding='utf-8') as f:
                raw_json = json.load(f)

            # ---- Стандартизация ----
            logger.info("   🔄 Стандартизация")
            try:
                standardized = self.standardizer.transform(raw_json, original_file_name)
            except Exception as e:
                logger.error(f"Ошибка стандартизации: {e}")
                raise RuntimeError(f"Стандартизация не удалась: {e}")

            # ---- Оценка качества (по сырому JSON) ----
            reports = assess_quality_from_json(json_path)
            quality_report = None
            if reports:
                scores = [r.overall_score for r in reports.values()]
                avg_conf = sum(scores) / len(scores) if scores else 0.0
                quality_report = {
                    "file": original_file_name,
                    "total_pages": len(reports),
                    "problematic_pages": [p for p, r in reports.items() if r.is_problematic],
                    "avg_confidence": round(avg_conf, 3),
                    "pages": [r.to_dict() for r in reports.values()]
                }
                logger.info(f"📊 Отчёт о качестве: avg_confidence={avg_conf:.3f}")
            else:
                logger.warning("⚠️ Не удалось сформировать отчёт о качестве")

            if quality_report:
                try:
                    standardized = self._update_quality(standardized, quality_report)
                    logger.info("   ✅ Качество обновлено")
                except Exception as e:
                    logger.warning(f"   ⚠️ Ошибка обновления качества: {e}")

            images = self._collect_image_paths(standardized, temp_dir)
            if not options.get("extract_images", True):
                images = []

            return ParseResult(
                full_json=standardized,
                images=images,
                total_pages=total_pages,
                temp_dir=temp_dir,
            )

        except Exception as e:
            logger.exception(f"Ошибка парсинга для задачи {task_id}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise
        finally:
            try:
                os.unlink(pdf_path)
            except Exception:
                pass