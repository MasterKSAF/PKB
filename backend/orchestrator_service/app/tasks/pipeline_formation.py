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
from app.services.rag_client import RAGBuilderClient
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

        # Converter returns flat PreviewMetadataResponse (doc_code, title, ...)
        # Detect format and build metadata accordingly
        if "doc_code" in result or "title" in result:
            # New flat format from /api/v1/converter/preview
            metadata = {k: v for k, v in result.items() if v is not None}
            output_data = {
                "validated": True,
                "metadata": metadata,
            }
        else:
            # Legacy format: {"data": {"validated": ..., "metadata": ...}}
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
                # Step 1: запуск асинхронного парсинга
                resp = await client.process(task_id=task_id, file_key=file_key, draft_id=draft_id, mode="full")
                data = resp.get("data", resp)
                parser_task_id = data.get("task_id")
                if not parser_task_id:
                    logger.warning(f"Parser did not return task_id, using orchestrator task_id")
                    return data

                # Step 2: ждём завершения парсинга (poll до 5 минут)
                max_poll = 30  # 30 * 10s = 5 min timeout
                for i in range(max_poll):
                    status_resp = await client.get_status(parser_task_id)
                    status_data = status_resp.get("data", status_resp)
                    p_status = status_data.get("status", "")
                    logger.info(f"Parser status poll [{i+1}/{max_poll}]: {p_status}")
                    if p_status == "completed":
                        break
                    elif p_status == "failed":
                        raise Exception(f"Parser processing failed: {status_data.get('error', 'unknown')}")
                    await asyncio.sleep(10)
                else:
                    raise Exception(f"Parser did not complete within timeout for task {parser_task_id}")

                # Step 3: получаем результат
                result_resp = await client.get_result(parser_task_id)
                return result_resp.get("data", result_resp)
            finally:
                await client.close()

        full_parser_result = _run_async(_do_parser_full())

        # Transform parser blocks into sections format for RAG Builder
        # Parser returns {document: {block: [{number, type, page, content, ...}, ...]}}
        # RAG Builder expects [{section_id, document_id, level, path, page, type, content: {text}},...]
        sections = full_parser_result.get("sections", [])
        if not sections:
            raw_blocks = full_parser_result.get("document", {}).get("block", [])
            sections = [
                {
                    "section_id": b.get("number", i + 1),
                    "document_id": draft_id,
                    "level": 1 if b.get("type") == "heading" else 2,
                    "path": str(b.get("number", i + 1)),
                    "page": b.get("page", 1),
                    "type": "text",
                    "content": {"text": b.get("content", "")},
                    "bbox": b.get("bbox"),
                }
                for i, b in enumerate(raw_blocks)
                if b.get("content", "").strip()
            ]
            if sections:
                logger.info(
                    f"Transformed {len(sections)} parser blocks into sections for RAG"
                )

        input_data = {"file_key": file_key, "mode": "full", "draft_id": draft_id}
        output_data = {
            "sections": sections,
            "full_result": full_parser_result,
            "status": "completed",
        }

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
    trace_id: str = "", raw_json: Optional[dict] = None,
    version_id: int = 1,
):
    """Full Converter step — convert and validate full document."""
    if trace_id:
        set_trace_id(trace_id)
    try:
        logger.info(f"Converter full started: task={task_id} draft={draft_id}")

        async def _do_converter_full():
            client = ConverterValidatorClient()
            try:
                body = {"file_key": file_key, "draft_id": draft_id}
                if raw_json:
                    body["raw_json"] = raw_json
                    body["task_id"] = task_id
                    body["version_id"] = version_id
                return await client.convert_full(body)
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
                # approve_draft already updated status to "approved";
                # this call is idempotent — 409 means already done, treat as success
                result = await client.update_draft_status(
                    draft_id=draft_id, status="approved", document_id=document_id,
                )
                return result
            except Exception as exc:
                # 409 Conflict = draft already in approved state (idempotent)
                if "409" in str(exc) or "DRAFT_ALREADY_DECIDED" in str(exc):
                    logger.info(
                        f"Draft {draft_id} already approved, treating registry step as completed (idempotent)",
                        extra={"task_id": task_id, "draft_id": draft_id},
                    )
                    return {"status": "already_approved", "draft_id": draft_id}
                raise
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


@celery_app.task(
    bind=True, max_retries=2, default_retry_delay=30,
    name="tasks.pipeline.run_rag_index_step"
)
def run_rag_index_step(
    self, task_id: int, draft_id: int, document_id: int,
    sections: Optional[list] = None,
    trace_id: str = "",
):
    """RAG index step — build vector index via RAG Builder."""
    if trace_id:
        set_trace_id(trace_id)
    try:
        logger.info(f"RAG index started: task={task_id} doc={document_id}")

        async def _do_rag_index():
            client = RAGBuilderClient()
            try:
                result = await client.index_document(
                    document_id=document_id,
                    sections=sections or [],
                )
                txn_id = result.get("indexing_txn_id")
                if txn_id:
                    # Poll until indexing completes
                    for i in range(12):
                        status_resp = await client.get_build_status(
                            document_id=str(document_id), longpoll=10
                        )
                        idx_status = status_resp.get("status", "")
                        if idx_status in ("indexed", "completed"):
                            logger.info(f"RAG indexing completed: doc={document_id}")
                            break
                        elif idx_status == "failed":
                            raise Exception(f"RAG indexing failed: {status_resp}")
                        await asyncio.sleep(5)
                return result
            finally:
                await client.close()

        result = _run_async(_do_rag_index())

        input_data = {"document_id": document_id, "draft_id": draft_id}
        output_data = {
            "document_id": document_id,
            "status": "indexed",
            "chunks_count": result.get("chunks_count", 0),
        }

        _run_async(_notify_step_completed(task_id, "rag_index", input_data, output_data))

        return {"status": "completed", "step": "rag_index", "task_id": task_id}

    except Exception as exc:
        logger.error(f"RAG index failed: {exc}")
        _run_async(_notify_step_failed(task_id, "rag_index", "RAG_INDEX_ERROR", str(exc)))
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
