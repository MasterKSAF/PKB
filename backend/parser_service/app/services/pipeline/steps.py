"""
Отдельные шаги пайплайна. Каждый шаг реализует метод execute(context).
"""
import io
import os
import json
import shutil
import hashlib
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pypdf import PdfReader, PdfWriter
from app.services.standardizer import JsonStandardizer
from app.services.pipeline.context import ProcessingContext
from app.core.minio_client import minio_client
from app.core.validator import Validator
from app.services.parser_factory import ParserFactory
from app.services.normalizer import Normalizer
from app.core.task_store import task_store
from app.core.task_models import TaskStatus
from app.services.result_builder import ResultBuilder
from app.config import settings

logger = logging.getLogger(__name__)


class PipelineStep(ABC):
    """Абстрактный базовый класс для шага пайплайна."""

    @abstractmethod
    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        """Выполняет шаг и возвращает обновлённый контекст."""
        pass


class DownloadStep(PipelineStep):
    """Шаг загрузки файла из MinIO."""

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        logger.debug("Downloading file %s", ctx.file_key)
        ctx.file_bytes = await minio_client.download_file(ctx.file_key)
        ctx.original_file_name = os.path.basename(ctx.file_key)
        logger.debug("Downloaded %d bytes", len(ctx.file_bytes))
        return ctx


class ValidateStep(PipelineStep):
    """Шаг валидации размера, MIME-типа и безопасности файла."""

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        logger.debug("Validating file")
        ctx.mime_type = Validator.validate(ctx.file_bytes)
        logger.debug("Validation passed, MIME=%s", ctx.mime_type)
        return ctx


class PagesTotalStep(PipelineStep):
    """Шаг определения общего количества страниц документа."""

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        total_pages = 1
        if ctx.file_bytes and ctx.mime_type == "application/pdf":
            try:
                reader = PdfReader(io.BytesIO(ctx.file_bytes))
                total_pages = len(reader.pages)
                logger.debug("PDF page count: %d", total_pages)
            except Exception as e:
                logger.warning("Failed to get page count via pypdf: %s", str(e))
                total_pages = 1
        ctx.total_pages = total_pages

        if ctx.track_progress:
            await task_store.update_task(
                ctx.task_id,
                pages_total=total_pages,
                pages_processed=0
            )
        return ctx


class ParseStep(PipelineStep):
    """Шаг парсинга документа через фабрику парсеров."""

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        logger.debug("Parsing with MIME %s", ctx.mime_type)
        parser = ParserFactory.get_parser(ctx.mime_type)
        if parser is None:
            raise ValueError(f"No parser for MIME {ctx.mime_type}")

        ctx.parse_result = await parser.parse(
            ctx.file_bytes,
            ctx.options,
            ctx.task_id,
            total_pages=getattr(ctx, 'total_pages', None)
        )
        if ctx.parse_result.temp_dir:
            ctx.temp_dir = ctx.parse_result.temp_dir
        logger.debug(
            "Parsing completed, total_pages=%d",
            ctx.parse_result.total_pages
        )

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
    """Шаг загрузки извлечённых изображений в MinIO и замены путей в JSON."""

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        if not ctx.track_progress:
            if ctx.temp_dir and os.path.exists(ctx.temp_dir):
                shutil.rmtree(ctx.temp_dir, ignore_errors=True)
                logger.debug("Removed temp dir for preview: %s", ctx.temp_dir)
            return ctx

        if not ctx.parse_result or not ctx.parse_result.images:
            if ctx.temp_dir and os.path.exists(ctx.temp_dir):
                shutil.rmtree(ctx.temp_dir, ignore_errors=True)
            return ctx

        path_to_key = {}
        for idx, (page_num, file_path, ext) in enumerate(ctx.parse_result.images):
            if not os.path.exists(file_path):
                logger.warning("Image file not found: %s", file_path)
                continue

            with open(file_path, "rb") as f:
                img_bytes = f.read()

            file_hash = hashlib.md5(img_bytes).hexdigest()[:16]
            suggested_key = f"task_{ctx.task_id}/{ctx.task_id}_{idx}_{file_hash}{ext}"
            returned_key = await minio_client.upload_image(
                img_bytes, ctx.task_id, page_num, ext, custom_key=suggested_key
            )
            path_to_key[file_path] = returned_key
            os.unlink(file_path)
            logger.debug("Uploaded image %s -> %s", file_path, returned_key)

        def replace_paths(obj):
            if isinstance(obj, dict):
                if "_temp_path" in obj:
                    temp_path = obj["_temp_path"]
                    if temp_path in path_to_key:
                        obj["image_key"] = path_to_key[temp_path]
                        del obj["_temp_path"]
                    for old_key in ("source", "file_path", "path"):
                        if old_key in obj and obj[old_key] == temp_path:
                            del obj[old_key]
                for v in obj.values():
                    replace_paths(v)
            elif isinstance(obj, list):
                for item in obj:
                    replace_paths(item)

        replace_paths(ctx.parse_result.full_json)
        logger.debug(
            "Replaced image paths in JSON for %d images",
            len(path_to_key)
        )

        if ctx.temp_dir and os.path.exists(ctx.temp_dir):
            shutil.rmtree(ctx.temp_dir, ignore_errors=True)
            logger.debug("Removed temp dir: %s", ctx.temp_dir)
        return ctx


class NormalizeStep(PipelineStep):
    """Шаг нормализации сырого JSON в контейнер."""

    def __init__(self, normalizer: Normalizer):
        self.normalizer = normalizer

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        logger.debug("Normalizing JSON")
        ctx.final_json = await self.normalizer.normalize(ctx.parse_result, ctx.task_id)
        return ctx


class StandardizeStep(PipelineStep):
    """Шаг стандартизации JSON в единый формат документа."""

    def __init__(self, standardizer: JsonStandardizer):
        self.standardizer = standardizer

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        if ctx.final_json is None:
            raise ValueError("No final JSON to standardize")
        logger.debug("Standardizing JSON")
        standardized = self.standardizer.transform(
            ctx.final_json,
            file_name=ctx.original_file_name
        )
        ctx.final_json = standardized
        return ctx


class SaveJsonToFileStep(PipelineStep):
    """Шаг опционального сохранения JSON на диск (для отладки)."""

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        if not settings.save_json_to_dir:
            return ctx
        output_dir = settings.json_output_dir
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"task_{ctx.task_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(ctx.final_json, f, indent=2, ensure_ascii=False)
        logger.debug("Saved JSON to %s", file_path)
        return ctx


class StoreResultStep(PipelineStep):
    """Шаг сохранения результата в task_store и отметки задачи как завершённой."""

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        if not ctx.track_progress:
            return ctx

        task_info = task_store.get(ctx.task_id)
        pages_total = task_info.pages_total if task_info else (
            ctx.parse_result.total_pages if ctx.parse_result else 0
        )
        mode = "preview" if ctx.max_pages is not None else "full"

        result_payload = ResultBuilder.build(
            task_id=ctx.task_id,
            final_json=ctx.final_json,
            mode=mode,
            preview_not_supported=ctx.preview_not_supported
        )

        await task_store.update_task(
            ctx.task_id,
            status=TaskStatus.COMPLETED,
            result=result_payload,
            pages_processed=pages_total,
            pages_total=pages_total,
            completed_at=datetime.now(timezone.utc),
            step="completed",
            step_detail="Результат сохранён",
            progress_percent=100
        )
        logger.info("Result stored for task %d", ctx.task_id)
        return ctx


class TruncatePdfStep(PipelineStep):
    """Шаг обрезания PDF до max_pages страниц (для preview)."""

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        if ctx.max_pages is None or ctx.max_pages <= 0:
            return ctx
        if not ctx.file_bytes:
            raise ValueError("No file bytes to truncate")

        reader = PdfReader(io.BytesIO(ctx.file_bytes))
        total_pages = len(reader.pages)
        if ctx.max_pages >= total_pages:
            logger.debug(
                "No truncation needed (max_pages=%d >= total=%d)",
                ctx.max_pages, total_pages
            )
            return ctx

        writer = PdfWriter()
        for i in range(ctx.max_pages):
            writer.add_page(reader.pages[i])
        output = io.BytesIO()
        writer.write(output)
        ctx.file_bytes = output.getvalue()
        logger.debug(
            "Truncated PDF from %d to %d pages",
            total_pages, ctx.max_pages
        )
        return ctx