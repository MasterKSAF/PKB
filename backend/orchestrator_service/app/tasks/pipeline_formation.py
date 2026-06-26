"""
Pipeline 1 (Formation) Celery tasks.

Preview phase (triggered immediately after upload):
1. upload — file registered (handled by orchestrator directly)
2. preview_ocr (or preview_parser) — OCR or Parser processes first pages
3. preview_converter — Converter-validator validates preview

Full phase (triggered after user approve, or auto-approve):
1. full_ocr (or full_parser) — full OCR/Parser processing
2. full_converter — full conversion and validation
3. registry_creation — persist in Registry
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from app.celery_app import celery_app
from app.core.config import settings
from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.core.trace import set_trace_id
from app.db.session import get_db_context
from app.services.ocr_client import OCRServiceClient
from app.services.parser_client import ParserServiceClient
from app.services.converter_client import ConverterValidatorClient
from app.services.registry_client import RegistryServiceClient

logger = logging.getLogger("tasks.pipeline_1")


def _run_async(coro):
    """Run an async coroutine synchronously from a Celery task."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ------------------------------------------------------------------
#  Preview steps
# ------------------------------------------------------------------


@celery_app.task(
    bind=True, max_retries=3, default_retry_delay=60,
    name="tasks.pipeline.run_ocr_preview_step"
)
def run_ocr_preview_step(
    self, task_id: int, draft_id: int, file_key: str, max_pages: int = 3,
    trace_id: str = "",
):
    """
    Preview OCR step — recognize text from first pages.
    """
    if trace_id:
        set_trace_id(trace_id)
    try:
        logger.info(f"OCR preview started: task={task_id} draft={draft_id}")

        async def _do_ocr_preview():
            client = OCRServiceClient()
            try:
                return await client.process(
                    task_id=task_id, file_key=file_key, draft_id=draft_id, mode="preview", max_pages=max_pages
                )
            finally:
                await client.close()

        result = _run_async(_do_ocr_preview())

        input_data = {"file_key": file_key, "mode": "preview", "max_pages": max_pages, "draft_id": draft_id}
        output_data = {
            "preview_not_supported": result.get("data", {}).get("preview_not_supported", False),
            "pages_processed": result.get("data", {}).get("pages_processed", 0),
            "metadata": result.get("data", {}).get("metadata", {}),
            "quality": result.get("data", {}).get("quality", {}),
        }

        _run_async(_notify_step_completed(task_id, "preview_ocr", input_data, output_data))

        logger.info(f"OCR preview completed: task={task_id}")
        return {"status": "completed", "step": "preview_ocr", "task_id": task_id}

    except Exception as exc:
        logger.error(f"OCR preview failed: {exc}")
        _run_async(_notify_step_failed(task_id, "preview_ocr", "OCR_ERROR", str(exc)))
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True, max_retries=3, default_retry_delay=60,
    name="tasks.pipeline.run_parser_preview_step"
)
def run_parser_preview_step(
    self, task_id: int, draft_id: int, file_key: str, max_pages: int = 3,
    trace_id: str = "",
):
    """
    Preview Parser step — extract structure from digital PDF first pages.
    """
    if trace_id:
        set_trace_id(trace_id)
    try:
        logger.info(f"Parser preview started: task={task_id} draft={draft_id}")

        async def _do_parse():
            client = ParserServiceClient()
            try:
                result = await client.process(
                    task_id=task_id, file_key=file_key, draft_id=draft_id, mode="preview", max_pages=max_pages
                )
            finally:
                await client.close()
            return result

        result = _run_async(_do_parse())

        input_data = {"file_key": file_key, "mode": "preview", "max_pages": max_pages, "draft_id": draft_id}
        # Передаём полный результат парсера для запуска конвертера
        full_result = result.get("data", {})
        if not full_result:
            full_result = result  # fallback — весь ответ
        output_data = {
            "preview_not_supported": full_result.get("preview_not_supported", False),
            "pages_processed": full_result.get("pages_processed", 0),
            "metadata": full_result.get("metadata", {}),
            "quality": full_result.get("quality", {}),
            "full_result": full_result,  # для converter
        }

        # The orchestrator uses "preview_ocr" as the step name for both OCR and Parser
        _run_async(_notify_step_completed(task_id, "preview_ocr", input_data, output_data))

        logger.info(f"Parser preview completed: task={task_id}")
        return {"status": "completed", "step": "preview_ocr", "task_id": task_id}

    except Exception as exc:
        logger.error(f"Parser preview failed: {exc}")
        _run_async(_notify_step_failed(task_id, "preview_ocr", "PARSER_ERROR", str(exc)))
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True, max_retries=3, default_retry_delay=60,
    name="tasks.pipeline.run_converter_preview_step"
)
def run_converter_preview_step(
    self, task_id: int, draft_id: int, file_key: str,
    trace_id: str = "", raw_json: Optional[dict] = None,
):
    """
    Preview Converter step — validate and transform preview data.
    """
    if trace_id:
        set_trace_id(trace_id)
    try:
        logger.info(f"Converter preview started: task={task_id} draft={draft_id}")

        async def _do_converter_preview():
            client = ConverterValidatorClient()
            try:
                body = {"file_key": file_key, "draft_id": draft_id}
                if raw_json:
                    body["raw_json"] = raw_json
                    body["task_id"] = task_id
                    body["version_id"] = 1
                return await client.convert_preview(body)
            finally:
                await client.close()

        result = _run_async(_do_converter_preview())

        input_data = {"file_key": file_key, "mode": "preview", "draft_id": draft_id}
        output_data = {
            "validated": result.get("data", {}).get("validated", True),
            "metadata": result.get("data", {}).get("metadata", {}),
        }

        _run_async(_notify_step_completed(task_id, "preview_converter", input_data, output_data))

        logger.info(f"Converter preview completed: task={task_id}")
        return {"status": "completed", "step": "preview_converter", "task_id": task_id}

    except Exception as exc:
        logger.error(f"Converter preview failed: {exc}")
        _run_async(_notify_step_failed(task_id, "preview_converter", "CONVERTER_ERROR", str(exc)))
        raise self.retry(exc=exc)


# ------------------------------------------------------------------
#  Full processing steps
# ------------------------------------------------------------------


@celery_app.task(
    bind=True, max_retries=3, default_retry_delay=60,
    name="tasks.pipeline.run_ocr_full_step"
)
def run_ocr_full_step(
    self, task_id: int, draft_id: int, file_key: str,
    trace_id: str = "",
):
    """Full OCR step — process entire document."""
    if trace_id:
        set_trace_id(trace_id)
    try:
        logger.info(f"OCR full started: task={task_id} draft={draft_id}")

        async def _do_ocr_full():
            client = OCRServiceClient()
            try:
                return await client.process(task_id=task_id, file_key=file_key, draft_id=draft_id, mode="full")
            finally:
                await client.close()

        result = _run_async(_do_ocr_full())

        input_data = {"file_key": file_key, "mode": "full", "draft_id": draft_id}
        output_data = {
            "pages_processed": result.get("data", {}).get("pages_processed", 0),
            "status": "completed",
        }

        _run_async(_notify_step_completed(task_id, "full_ocr", input_data, output_data))

        return {"status": "completed", "step": "full_ocr", "task_id": task_id}

    except Exception as exc:
        logger.error(f"OCR full failed: {exc}")
        _run_async(_notify_step_failed(task_id, "full_ocr", "OCR_ERROR", str(exc)))
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True, max_retries=3, default_retry_delay=60,
    name="tasks.pipeline.run_parser_full_step"
)
def run_parser_full_step(
    self, task_id: int, draft_id: int, file_key: str,
    trace_id: str = "",
):
    """Full Parser step — parse entire document."""
    if trace_id:
        set_trace_id(trace_id)
    try:
        logger.info(f"Parser full started: task={task_id} draft={draft_id}")

        async def _do_parser_full():
            client = ParserServiceClient()
            try:
                return await client.process(task_id=task_id, file_key=file_key, draft_id=draft_id, mode="full")
            finally:
                await client.close()

        result = _run_async(_do_parser_full())

        input_data = {"file_key": file_key, "mode": "full", "draft_id": draft_id}
        output_data = {
            "sections": result.get("data", {}).get("sections", []),
            "status": "completed",
        }

        # The orchestrator uses "full_ocr" as the step name for full processing
        _run_async(_notify_step_completed(task_id, "full_ocr", input_data, output_data))

        return {"status": "completed", "step": "full_ocr", "task_id": task_id}

    except Exception as exc:
        logger.error(f"Parser full failed: {exc}")
        _run_async(_notify_step_failed(task_id, "full_ocr", "PARSER_ERROR", str(exc)))
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True, max_retries=3, default_retry_delay=60,
    name="tasks.pipeline.run_converter_full_step"
)
def run_converter_full_step(
    self, task_id: int, draft_id: int, file_key: str,
    trace_id: str = "",
):
    """Full Converter step — convert and validate full document."""
    if trace_id:
        set_trace_id(trace_id)
    try:
        logger.info(f"Converter full started: task={task_id} draft={draft_id}")

        async def _do_converter_full():
            client = ConverterValidatorClient()
            try:
                return await client.convert_full({"file_key": file_key, "draft_id": draft_id})
            finally:
                await client.close()

        result = _run_async(_do_converter_full())

        input_data = {"file_key": file_key, "mode": "full", "draft_id": draft_id}
        output_data = {
            "validated": result.get("data", {}).get("validated", True),
            "parameters": result.get("data", {}).get("parameters", {}),
        }

        _run_async(_notify_step_completed(task_id, "full_converter", input_data, output_data))

        return {"status": "completed", "step": "full_converter", "task_id": task_id}

    except Exception as exc:
        logger.error(f"Converter full failed: {exc}")
        _run_async(_notify_step_failed(task_id, "full_converter", "CONVERTER_ERROR", str(exc)))
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True, max_retries=2, default_retry_delay=30,
    name="tasks.pipeline.run_registry_step"
)
def run_registry_step(
    self, task_id: int, draft_id: int, document_id: int, version_id: Optional[int] = None,
    trace_id: str = "",
):
    """Registry step — persist document in the registry."""
    if trace_id:
        set_trace_id(trace_id)
    try:
        logger.info(f"Registry step started: task={task_id} draft={draft_id} document={document_id}")

        async def _do_registry():
            client = RegistryServiceClient()
            try:
                return await client.update_draft_status(
                    draft_id=draft_id, status="approved", document_id=document_id,
                )
            finally:
                await client.close()

        result = _run_async(_do_registry())

        input_data = {"draft_id": draft_id, "document_id": document_id}
        output_data = {
            "registry_id": document_id,
            "version_id": version_id,
            "status": "registered",
        }

        _run_async(_notify_step_completed(task_id, "registry_creation", input_data, output_data))

        return {"status": "completed", "step": "registry_creation", "task_id": task_id}

    except Exception as exc:
        logger.error(f"Registry step failed: {exc}")
        _run_async(_notify_step_failed(task_id, "registry_creation", "REGISTRY_ERROR", str(exc)))
        raise self.retry(exc=exc)


# ------------------------------------------------------------------
#  Notify orchestrator
# ------------------------------------------------------------------


async def _notify_step_completed(
    task_id: int, step_name: str, input_data: Dict[str, Any], output_data: Dict[str, Any]
):
    """Notify the orchestrator that a step completed successfully."""
    async with get_db_context() as db:
        orchestrator = PipelineOrchestrator(db)
        await orchestrator.on_step_completed(task_id, step_name, input_data, output_data)


async def _notify_step_failed(
    task_id: int, step_name: str, error_code: str, error_message: str
):
    """Notify the orchestrator that a step failed."""
    async with get_db_context() as db:
        orchestrator = PipelineOrchestrator(db)
        await orchestrator.on_step_failed(task_id, step_name, error_code, error_message)
