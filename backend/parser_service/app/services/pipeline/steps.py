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
        ctx.parse_result = await parser.parse(
            ctx.file_bytes,
            ctx.options,
            ctx.task_id,
            total_pages=getattr(ctx, "total_pages", None),
        )
        if ctx.parse_result.temp_dir:
            ctx.temp_dir = ctx.parse_result.temp_dir
        logger.debug("Parsing completed, total_pages=%d", ctx.parse_result.total_pages)
        if ctx.max_pages is not None and ctx.parse_result.total_pages > ctx.max_pages:
            ctx.parse_result.total_pages = ctx.max_pages
            ctx.parse_result.images = [
                img for img in ctx.parse_result.images if img[0] <= ctx.max_pages
            ]
            if not ctx.track_progress and ctx.parse_result.total_pages > ctx.max_pages:
                ctx.preview_not_supported = True
            logger.debug("Truncated to %d pages", ctx.max_pages)
        return ctx


class UploadImagesStep(PipelineStep):
    """
    Шаг загрузки изображений в MinIO.
    Логирует только итоговый результат: количество успешно загруженных изображений и ошибок.
    """
    def __init__(self, minio_client):
        self.minio_client = minio_client

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        if not ctx.track_progress:
            logger.debug("Preview mode: keeping temp dir %s (cleanup delegated to OS)", ctx.temp_dir)
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

        if upload_tasks:
            keys = await asyncio.gather(*upload_tasks, return_exceptions=True)
            success_count = 0
            error_count = 0
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

        # Заменяем пути в JSON
        _replace_image_paths(ctx.parse_result.full_json, path_to_key)
        logger.debug("Replaced image paths in JSON for %d images", len(path_to_key))

        if ctx.temp_dir and os.path.exists(ctx.temp_dir):
            shutil.rmtree(ctx.temp_dir, ignore_errors=True)
            logger.debug("Removed temp dir: %s", ctx.temp_dir)
        return ctx


class TransformStep(PipelineStep):
    """
    Шаг, объединяющий нормализацию и стандартизацию.
    """
    def __init__(self, normalizer: Normalizer):
        self.normalizer = normalizer
        self.standardizer = StandardizerFactory.get_standardizer(settings.parsing_schema)

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        logger.debug("Normalizing JSON for task %d", ctx.task_id)
        ctx.final_json = await self.normalizer.normalize(ctx.parse_result, ctx.task_id)

        if ctx.final_json is None:
            raise ValueError("No final JSON to standardize")
        logger.debug("Standardizing JSON with schema %s", settings.parsing_schema)
        standardized = await asyncio.to_thread(
            self.standardizer.transform,
            ctx.final_json,
            ctx.original_file_name,
        )
        ctx.final_json = standardized
        return ctx


class SaveJsonToFileStep(PipelineStep):
    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        if not settings.save_json_to_dir:
            return ctx

        # Формируем полный результат (обёртку), идентичный тому, что сохраняется в task_store
        result_payload = build_result(
            task_id=ctx.task_id,
            draft_id=ctx.draft_id,
            final_json=ctx.final_json,
            mode="full",  # этот шаг выполняется только в full режиме
            preview_not_supported=False,
        )

        output_dir = settings.json_output_dir
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"task_{ctx.task_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, indent=2, ensure_ascii=False)
        logger.info("Saved JSON to %s", file_path)
        return ctx


class StoreResultStep(PipelineStep):
    def __init__(self, task_store, max_result_size_bytes: int):
        self.task_store = task_store
        self.max_result_size_bytes = max_result_size_bytes

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        if not ctx.track_progress:
            return ctx

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

        # Проверяем размер результата
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