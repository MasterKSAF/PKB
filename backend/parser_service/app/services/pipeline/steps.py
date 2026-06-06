"""
Отдельные шаги пайплайна. Каждый шаг реализует метод execute(context).
"""
import io
import os
import json
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
from app.config import settings


class PipelineStep(ABC):
    """Абстрактный базовый класс для всех шагов пайплайна."""
    @abstractmethod
    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        pass


class DownloadStep(PipelineStep):
    """Загружает файл из MinIO и сохраняет оригинальное имя файла."""
    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        ctx.file_bytes = await minio_client.download_file(ctx.file_key)
        ctx.original_file_name = os.path.basename(ctx.file_key)
        return ctx


class ValidateStep(PipelineStep):
    """Валидирует файл: размер, MIME, безопасность. Устанавливает ctx.mime_type."""
    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        ctx.mime_type = Validator.validate(ctx.file_bytes)
        return ctx


class ParseStep(PipelineStep):
    """Запускает парсер, получает ParseResult и сохраняет общее число страниц в task_store."""
    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        parser = ParserFactory.get_parser(ctx.mime_type)
        if parser is None:
            raise ValueError(f"No parser for MIME {ctx.mime_type}")
        ctx.parse_result = await parser.parse(ctx.file_bytes, ctx.options)

        # Сохраняем реальное количество страниц в хранилище задач
        await task_store.update_task(
            ctx.task_id,
            pages_total=ctx.parse_result.total_pages,
            pages_processed=0
        )

        # Если задан max_pages (для preview), урезаем результат
        if ctx.max_pages is not None and ctx.parse_result.total_pages > ctx.max_pages:
            ctx.parse_result.total_pages = ctx.max_pages
            ctx.parse_result.images = [img for img in ctx.parse_result.images if img[0] <= ctx.max_pages]
        return ctx


class NormalizeStep(PipelineStep):
    """Нормализует ParseResult в финальный JSON-контейнер."""
    def __init__(self, normalizer: Normalizer):
        self.normalizer = normalizer

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        ctx.final_json = await self.normalizer.normalize(ctx.parse_result, ctx.task_id)
        return ctx


class StoreResultStep(PipelineStep):
    """Сохраняет результат в task_store и завершает задачу со статусом COMPLETED."""
    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        await task_store.update_task(
            ctx.task_id,
            status=TaskStatus.COMPLETED,
            result=ctx.final_json,
            pages_processed=ctx.parse_result.total_pages if ctx.parse_result else 0,
            pages_total=ctx.parse_result.total_pages if ctx.parse_result else 0,
            completed_at=datetime.now(timezone.utc),
            step="completed",
            step_detail="Результат сохранён",
            progress_percent=100
        )
        return ctx


class TruncatePdfStep(PipelineStep):
    """Обрезает PDF до указанного количества страниц (max_pages)."""
    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        if ctx.max_pages is None or ctx.max_pages <= 0:
            return ctx
        if not ctx.file_bytes:
            raise ValueError("No file bytes to truncate")
        reader = PdfReader(io.BytesIO(ctx.file_bytes))
        total_pages = len(reader.pages)
        if ctx.max_pages >= total_pages:
            return ctx
        writer = PdfWriter()
        for i in range(ctx.max_pages):
            writer.add_page(reader.pages[i])
        output = io.BytesIO()
        writer.write(output)
        ctx.file_bytes = output.getvalue()
        return ctx


class StandardizeStep(PipelineStep):
    """Приводит JSON к целевому формату контракта."""
    def __init__(self, standardizer: JsonStandardizer):
        self.standardizer = standardizer

    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        if ctx.final_json is None:
            raise ValueError("No final JSON to standardize")
        standardized = self.standardizer.transform(ctx.final_json, file_name=ctx.original_file_name)
        ctx.final_json = standardized
        return ctx


class SaveJsonToFileStep(PipelineStep):
    """Опционально сохраняет итоговый JSON в файл (если включено в настройках)."""
    async def execute(self, ctx: ProcessingContext) -> ProcessingContext:
        if not settings.save_json_to_dir:
            return ctx
        output_dir = settings.json_output_dir
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"task_{ctx.task_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(ctx.final_json, f, indent=2, ensure_ascii=False)
        return ctx