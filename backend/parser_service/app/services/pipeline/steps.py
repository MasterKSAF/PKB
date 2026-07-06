"""
Отдельные шаги пайплайна. Каждый шаг реализует метод execute(context).
"""
import io
import os
import json
import shutil
import hashlib
import logging
import asyncio
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from pypdf import PdfReader, PdfWriter

from app.services.standardizer_factory import StandardizerFactory
from app.services.pipeline.context import ProcessingContext
from app.core.validator import validate
from app.services.parser_factory import ParserFactory
from app.services.normalizer import Normalizer
from app.core.task_models import TaskStatus
from app.services.result_builder import build_result
from app.config import settings

# Импорт модуля проверки качества PDF
from app.services.shared.pdf_text_quality_module import analyze_pdf_file

logger = logging.getLogger(__name__)


# ---------- Базовый класс шага ----------
class PipelineStep(ABC):
    @abstractmethod
    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        pass


# ---------- Вспомогательная функция для замены путей изображений ----------
def _replace_image_paths(obj, path_to_key):
    """
    Рекурсивно заменяет временные пути на ключи в MinIO.
    Модифицирует объект на месте.
    """
    if isinstance(obj, dict):
        if "_temp_path" in obj:
            temp_path = obj["_temp_path"]
            if temp_path in path_to_key and path_to_key[temp_path] is not None:
                obj["image_key"] = path_to_key[temp_path]
                del obj["_temp_path"]
            for old_key in ("source", "file_path", "path"):
                if old_key in obj and obj[old_key] == temp_path:
                    del obj[old_key]
        for v in obj.values():
            _replace_image_paths(v, path_to_key)
    elif isinstance(obj, list):
        for item in obj:
            _replace_image_paths(item, path_to_key)


# ---------- Конкретные шаги ----------
class DownloadStep(PipelineStep):
    def __init__(self, minio_client):
        self.minio_client = minio_client

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        logger.debug("Downloading file %s", ctx.file_key)
        ctx.file_bytes = await self.minio_client.download_file(ctx.file_key)
        ctx.original_file_name = os.path.basename(ctx.file_key)
        logger.debug("Downloaded %d bytes", len(ctx.file_bytes))
        return ctx


class ValidateStep(PipelineStep):
    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        logger.debug("Validating file")
        ctx.mime_type = await validate(ctx.file_bytes, ctx.original_file_name)
        logger.debug("Validation passed, MIME=%s", ctx.mime_type)
        return ctx


class QualityCheckStep(PipelineStep):
    """Проверяет качество PDF-файла и сохраняет код качества в контекст."""

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        if not ctx.file_bytes:
            return ctx

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(ctx.file_bytes)
            tmp_path = tmp.name

        try:
            result = analyze_pdf_file(tmp_path, pages_limit=5)
            quality_dict = result.to_dict()
            ctx.quality_code = quality_dict.get("code_name", "UNKNOWN")
            logger.debug(f"Quality check for task {ctx.task_id}: {ctx.quality_code}")
        except Exception as e:
            logger.warning(f"Quality check failed for task {ctx.task_id}: {e}")
            ctx.quality_code = "ERROR"
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        return ctx


class PagesTotalStep(PipelineStep):
    def __init__(self, task_store):
        self.task_store = task_store

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        total_pages = 1
        if ctx.file_bytes and ctx.mime_type == "application/pdf":
            try:
                reader = PdfReader(io.BytesIO(ctx.file_bytes))
                total_pages = len(reader.pages)
                logger.debug("PDF page count: %d", total_pages)
            except Exception as e:
                logger.warning("Failed to get page count via pypdf: %s", e)
                total_pages = 1
        ctx.total_pages = total_pages
        if ctx.track_progress:
            await self.task_store.update_task(
                ctx.task_id,
                pages_total=total_pages,
                pages_processed=0,
            )
        return ctx


class ParseStep(PipelineStep):
    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        logger.debug("Parsing with MIME %s", ctx.mime_type)
        parser = ParserFactory.get_parser(ctx.mime_type)
        if parser is None:
            raise ValueError(f"No parser for MIME {ctx.mime_type}")

        ctx.options["original_file_name"] = ctx.original_file_name

        # ---- ДОБАВЛЯЕМ: передаём max_pages в options для DoclingParser ----
        if ctx.max_pages is not None:
            ctx.options["max_pages"] = ctx.max_pages

        # ── Preview mode: обрезаем PDF до max_pages страниц ──────────────
        # Чтобы CLI парсер не обрабатывал весь документ (что может висеть >300с),
        # передаём только первые max_pages страниц.
        # ctx.total_pages НЕ затираем — он хранит оригинальное количество страниц
        # для корректного определения preview_not_supported ниже.
        file_bytes = ctx.file_bytes
        _original_total = None
        if ctx.max_pages is not None and ctx.mime_type == "application/pdf" and file_bytes:
            try:
                reader = PdfReader(io.BytesIO(file_bytes))
                total = len(reader.pages)
                if total > ctx.max_pages:
                    _original_total = total
                    writer = PdfWriter()
                    for i in range(ctx.max_pages):
                        writer.add_page(reader.pages[i])
                    buf = io.BytesIO()
                    writer.write(buf)
                    file_bytes = buf.getvalue()
                    logger.info(
                        "Truncated PDF from %d to %d pages for preview (task %d)",
                        total, ctx.max_pages, ctx.task_id,
                    )
            except Exception as e:
                logger.warning("Failed to truncate PDF for preview: %s", e)

        ctx.parse_result = await parser.parse(
            file_bytes,
            ctx.options,
            ctx.task_id,
            total_pages=getattr(ctx, "total_pages", None),
        )
        if ctx.parse_result.temp_dir:
            ctx.temp_dir = ctx.parse_result.temp_dir
        logger.debug("Parsing completed, total_pages=%d", ctx.parse_result.total_pages)
        # Определяем реальное количество страниц: если PDF обрезали до max_pages,
        # то parse_result.total_pages = max_pages, но оригинал мог быть больше.
        if ctx.max_pages is not None:
            _actual_total = max(ctx.parse_result.total_pages, _original_total or 0)
            if _actual_total > ctx.max_pages:
                ctx.parse_result.total_pages = ctx.max_pages
                ctx.parse_result.images = [
                    img for img in ctx.parse_result.images if img[0] <= ctx.max_pages
                ]
                if not ctx.track_progress:
                    ctx.preview_not_supported = True
                logger.debug("Truncated to %d pages (original %d)", ctx.max_pages, _actual_total)

        # Если preview (track_progress=False), удаляем временную папку сразу
        if not ctx.track_progress and ctx.temp_dir and os.path.exists(ctx.temp_dir):
            shutil.rmtree(ctx.temp_dir, ignore_errors=True)
            logger.debug("Removed temp dir for preview task %d", ctx.task_id)
            ctx.temp_dir = None

        return ctx


class UpdateProgressStep(PipelineStep):
    """Обновляет прогресс задачи после завершения парсинга."""
    
    def __init__(self, task_store):
        self.task_store = task_store

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        if not ctx.track_progress:
            return ctx

        if ctx.parse_result is None:
            logger.warning(f"UpdateProgressStep: parse_result is None for task {ctx.task_id}")
            return ctx

        total_pages = ctx.total_pages or 0
        full_json = ctx.parse_result.full_json
        avg_confidence = 0.0

        if full_json and isinstance(full_json, dict):
            quality = full_json.get("quality")
            if quality and isinstance(quality, dict):
                avg_confidence = quality.get("confidence", 0.0)

        await self.task_store.update_task(
            ctx.task_id,
            pages_processed=total_pages,
            avg_confidence=avg_confidence,
        )

        logger.info(
            f"Updated progress for task {ctx.task_id}: pages_processed={total_pages}, avg_confidence={avg_confidence}"
        )
        return ctx


class UploadImagesStep(PipelineStep):
    def __init__(self, minio_client):
        self.minio_client = minio_client

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        if not ctx.track_progress:
            # Preview: удаляем temp_dir, если он ещё существует
            if ctx.temp_dir and os.path.exists(ctx.temp_dir):
                shutil.rmtree(ctx.temp_dir, ignore_errors=True)
                logger.debug("Removed temp dir for preview task %d", ctx.task_id)
                ctx.temp_dir = None
            return ctx

        if not ctx.parse_result or not ctx.parse_result.images:
            if ctx.temp_dir and os.path.exists(ctx.temp_dir):
                shutil.rmtree(ctx.temp_dir, ignore_errors=True)
                logger.debug("Removed empty temp dir: %s", ctx.temp_dir)
            return ctx

        upload_tasks = []
        path_to_key = {}
        total_images = len(ctx.parse_result.images)
        logger.debug("Starting upload of %d images for task %d", total_images, ctx.task_id)

        for idx, (page_num, file_path, ext) in enumerate(ctx.parse_result.images):
            if not os.path.exists(file_path):
                logger.warning("Image file not found: %s", file_path)
                continue
            with open(file_path, "rb") as f:
                img_bytes = f.read()
            hash_sha256 = await asyncio.to_thread(hashlib.sha256, img_bytes)
            hash_hex = hash_sha256.hexdigest()
            suggested_key = f"{hash_hex}{ext}"
            upload_tasks.append(
                self.minio_client.upload_image(
                    img_bytes,
                    ctx.task_id,
                    page_num,
                    ext,
                    custom_key=suggested_key,
                )
            )
            path_to_key[file_path] = None

        # Ограничение параллельности загрузки
        max_concurrent = settings.max_concurrent_image_uploads
        success_count = 0
        error_count = 0
        keys = []
        for i in range(0, len(upload_tasks), max_concurrent):
            chunk = upload_tasks[i:i+max_concurrent]
            chunk_results = await asyncio.gather(*chunk, return_exceptions=True)
            keys.extend(chunk_results)

        for file_path, key_or_exc in zip(path_to_key.keys(), keys):
            if isinstance(key_or_exc, Exception):
                logger.error("Failed to upload image %s: %s", file_path, key_or_exc)
                error_count += 1
                continue
            path_to_key[file_path] = key_or_exc
            success_count += 1
            try:
                os.unlink(file_path)
            except Exception as e:
                logger.warning("Failed to unlink %s: %s", file_path, e)

        logger.info(
            "Uploaded %d/%d images for task %d (errors: %d)",
            success_count,
            total_images,
            ctx.task_id,
            error_count,
        )

        _replace_image_paths(ctx.parse_result.full_json, path_to_key)
        logger.debug("Replaced image paths in JSON for %d images", len(path_to_key))

        if ctx.temp_dir and os.path.exists(ctx.temp_dir):
            shutil.rmtree(ctx.temp_dir, ignore_errors=True)
            logger.debug("Removed temp dir: %s", ctx.temp_dir)
        return ctx


class TransformStep(PipelineStep):
    def __init__(self, normalizer: Normalizer):
        self.normalizer = normalizer
        self.standardizer = StandardizerFactory.get_standardizer(settings.parsing_schema)

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        logger.debug("TransformStep for task %d", ctx.task_id)
        if ctx.parse_result is None:
            raise ValueError("No parse result to transform")

        full_json = ctx.parse_result.full_json

        # Проверка: уже стандартизированный JSON (ODL или Docling)
        is_standardized = (
            ("document" in full_json and "quality" in full_json)
            or (
                "content" in full_json
                and "document" in full_json["content"]
                and "quality" in full_json["content"]
            )
        )
        if is_standardized:
            logger.debug("JSON already standardized, skipping transformation")
            ctx.final_json = full_json
            return ctx

        logger.debug("Normalizing JSON for task %d", ctx.task_id)
        normalized = await self.normalizer.normalize(ctx.parse_result, ctx.task_id)
        if normalized is None:
            raise ValueError("Normalization returned None")

        logger.debug("Standardizing JSON with schema %s", settings.parsing_schema)
        standardized = await asyncio.to_thread(
            self.standardizer.transform,
            normalized,
            ctx.original_file_name,
        )
        ctx.final_json = standardized
        return ctx


class SaveJsonToFileStep(PipelineStep):
    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        if not settings.save_json_to_dir:
            return ctx

        try:
            output_dir = settings.json_output_dir
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, f"task_{ctx.task_id}.json")
            result_payload = build_result(
                task_id=ctx.task_id,
                draft_id=ctx.draft_id,
                final_json=ctx.final_json,
                mode="full",
                preview_not_supported=False,
            )
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(result_payload, f, indent=2, ensure_ascii=False)
            logger.info("Saved JSON to %s", file_path)
        except Exception as e:
            logger.warning("Failed to save JSON to %s: %s", settings.json_output_dir, e)
            # Не прерываем выполнение пайплайна

        return ctx


class StoreResultStep(PipelineStep):
    def __init__(self, task_store, max_result_size_bytes: int):
        self.task_store = task_store
        self.max_result_size_bytes = max_result_size_bytes

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        # Формируем уведомление о качестве (для всех режимов)
        task_info = await self.task_store.get(ctx.task_id)
        pages_total = task_info.pages_total if task_info else (
            ctx.parse_result.total_pages if ctx.parse_result else 0
        )
        mode = "preview" if ctx.max_pages is not None else "full"
        result_payload = build_result(
            task_id=ctx.task_id,
            draft_id=ctx.draft_id,
            final_json=ctx.final_json,
            mode=mode,
            preview_not_supported=ctx.preview_not_supported,
        )

        # ---- Объединяем уведомления о качестве и проблемных страницах ----
        notifications = result_payload["quality"].get("notifications", [])
        problematic_pages_str = None
        new_notifications = []

        for note in notifications:
            if note.get("category") == "quality":
                continue
            if "message" in note and note["message"].startswith("problematic_pages:"):
                match = re.search(r'\[(.*?)\]', note["message"])
                if match:
                    problematic_pages_str = match.group(1)
                continue
            new_notifications.append(note)

        # Добавляем уведомление с категорией quality (всегда)
        if ctx.quality_code:
            category = f"quality: {ctx.quality_code}"
            if problematic_pages_str is not None:
                message = f"problematic_pages: [{problematic_pages_str}]"
            else:
                message = ""
            new_notifications.append({
                "category": category,
                "message": message
            })

        result_payload["quality"]["notifications"] = new_notifications

        # Если preview — просто возвращаем результат (не сохраняем в task_store)
        if not ctx.track_progress:
            ctx.final_json = result_payload  # обновляем контекст с уведомлением
            return ctx

        # ---- Для full-режима: проверка размера и сохранение ----
        serialized = json.dumps(result_payload)
        size_bytes = len(serialized.encode("utf-8"))
        if size_bytes > self.max_result_size_bytes:
            logger.error(
                "Result too large for task %d: %d bytes (limit %d)",
                ctx.task_id,
                size_bytes,
                self.max_result_size_bytes,
            )
            await self.task_store.update_task(
                ctx.task_id,
                status=TaskStatus.FAILED,
                error={
                    "code": "RESULT_TOO_LARGE",
                    "message": f"Result size {size_bytes} exceeds limit {self.max_result_size_bytes}",
                },
                completed_at=datetime.now(timezone.utc),
            )
            raise RuntimeError(f"Result too large: {size_bytes} > {self.max_result_size_bytes}")

        await self.task_store.update_task(
            ctx.task_id,
            status=TaskStatus.COMPLETED,
            result=result_payload,
            pages_processed=pages_total,
            pages_total=pages_total,
            completed_at=datetime.now(timezone.utc),
            step="completed",
            step_detail="Результат сохранён",
            progress_percent=100,
        )
        logger.info("Result stored for task %d", ctx.task_id)
        return ctx


class TruncatePdfStep(PipelineStep):
    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        if ctx.max_pages is None or ctx.max_pages <= 0:
            return ctx
        if not ctx.file_bytes:
            raise ValueError("No file bytes to truncate")
        reader = PdfReader(io.BytesIO(ctx.file_bytes))
        total_pages = len(reader.pages)
        if ctx.max_pages >= total_pages:
            logger.debug("No truncation needed (max_pages=%d >= total=%d)", ctx.max_pages, total_pages)
            return ctx
        writer = PdfWriter()
        for i in range(ctx.max_pages):
            writer.add_page(reader.pages[i])
        output = io.BytesIO()
        writer.write(output)
        ctx.file_bytes = output.getvalue()
        logger.debug("Truncated PDF from %d to %d pages", total_pages, ctx.max_pages)
        return ctx