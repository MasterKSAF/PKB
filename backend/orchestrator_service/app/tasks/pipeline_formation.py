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
from app.repositories.external_task_repo import ExternalTaskRepository
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
            # Сканированные PDF: метаданные не извлечены → validated=False → OCR fallback
            has_metadata = bool(metadata.get("doc_code") or metadata.get("title"))
            output_data = {
                "validated": has_metadata,
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

        # Реальный API возвращает без обёртки data (см. docs/api/ocr_service_api.md)
        ocr_data = result.get("data", result)
        input_data = {"file_key": file_key, "mode": "full", "draft_id": draft_id}
        output_data = {
            "pages_processed": ocr_data.get("pages_processed", 0),
            "full_result": ocr_data,
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
    """Full Parser step — submit to Parser Service, then exit.

    BackgroundTaskPoller handles waiting for completion and notifying the orchestrator.
    """
    if trace_id:
        set_trace_id(trace_id)
    try:
        logger.info(f"Parser full started: task={task_id} draft={draft_id}")

        async def _submit_parser_full():
            client = ParserServiceClient()
            try:
                # Submit async parsing job to Parser Service
                resp = await client.process(
                    task_id=task_id, file_key=file_key, draft_id=draft_id, mode="full"
                )
                data = resp.get("data", resp)
                parser_task_id = data.get("task_id")
                if not parser_task_id:
                    logger.warning(
                        f"Parser did not return task_id, notifying as completed directly"
                    )
                    return data

                # Save to external_tasks — Poller will track completion
                async with get_db_context() as db:
                    repo = ExternalTaskRepository(db)
                    await repo.create(
                        orchestrator_task_id=str(task_id),
                        step_name="full_ocr",
                        external_service="parser",
                        external_task_id=parser_task_id,
                        context_data={
                            "draft_id": draft_id,
                            "file_key": file_key,
                        },
                    )
                    await db.commit()

                logger.info(
                    f"Parser task {parser_task_id} submitted, will be polled by BackgroundTaskPoller",
                    extra={"task_id": task_id, "draft_id": draft_id},
                )
                return {"task_id": parser_task_id, "status": "pending"}
            finally:
                await client.close()

        result = _run_async(_submit_parser_full())
        return {"status": "pending", "step": "full_ocr", "task_id": task_id, "parser_task_id": result.get("task_id")}

    except Exception as exc:
        logger.error(f"Parser full submission failed: {exc}")
        _run_async(_notify_step_failed(task_id, "full_ocr", "PARSER_ERROR", str(exc)))
        raise self.retry(exc=exc)


# ------------------------------------------------------------------
#  Parser result processing (used by BackgroundTaskPoller)
# ------------------------------------------------------------------


def _normalize_bbox(bbox_val):
    """Normalize bbox to list[float, float, float, float] or None."""
    if bbox_val is None:
        return None
    if isinstance(bbox_val, (list, tuple)):
        return [float(v) for v in bbox_val]
    if isinstance(bbox_val, str):
        try:
            parts = [float(x.strip()) for x in bbox_val.replace(";", ",").split(",")]
            return parts if len(parts) == 4 else None
        except (ValueError, TypeError):
            logger.warning(f"Cannot parse bbox string: {bbox_val!r}")
            return None
    return None


async def process_parser_full_result(
    task_id: int,
    draft_id: int,
    file_key: str,
    full_parser_result: dict,
) -> None:
    """Transform parser full result and notify orchestrator step completed.

    Called by BackgroundTaskPoller when Parser external task completes.
    """
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
                "bbox": _normalize_bbox(b.get("bbox")),
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

    await _notify_step_completed(task_id, "full_ocr", input_data, output_data)


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
                body = {"file_key": file_key, "draft_id": draft_id, "task_id": task_id, "version_id": version_id}
                if raw_json:
                    body["raw_json"] = raw_json
                return await client.convert_full(body)
            finally:
                await client.close()

        result = _run_async(_do_converter_full())

        input_data = {"file_key": file_key, "mode": "full", "draft_id": draft_id}
        converter_data = result.get("data", result) if isinstance(result, dict) else {}
        validation = converter_data.get("validation") or {}
        output_data = {
            "validated": validation.get("structure_valid", True),
            "metadata": converter_data.get("metadata", {}),
            "document": converter_data.get("document", {}),
            "validation": validation,
            "document_id": converter_data.get("document_id"),
            "version_id": converter_data.get("version_id"),
            "status": validation.get("status", "completed"),
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
    document_data: Optional[dict] = None,
    metadata: Optional[dict] = None,
    trace_id: str = "",
):
    """Registry step — persist document in the registry.

    Args:
        document_data: Converter output document (with content/sections).
                       If provided, saves full document to Registry via create_document
                       and reads back sections with assigned section_ids.
                       Already contains document metadata (doc_code, title, era, ...)
                       inside document_data["metadata"].
        metadata: Converter response metadata (schema, task_id, created_at, parser).
                  Merged into document_data["metadata"] — document metadata takes priority
                  for overlapping keys so doc_code/title are never lost.
    """
    if trace_id:
        set_trace_id(trace_id)
    try:
        logger.info(f"Registry step started: task={task_id} draft={draft_id} document={document_id}")

        async def _do_registry():
            client = RegistryServiceClient()
            current_doc_id = document_id
            saved_sections = None
            try:
                # --- Step 1: Save full document to Registry (if converter data available) ---
                if document_data:
                    logger.info(
                        f"Saving full document to Registry: draft={draft_id} doc={current_doc_id}",
                        extra={"task_id": task_id, "draft_id": draft_id},
                    )
                    # Build payload in Registry format (section 3.3 API spec)
                    # Nest metadata inside document if provided separately
                    # Merge: response_metadata (schema/task_id/parser) 
                    # with document metadata (doc_code/title/era/source_type)
                    # preserving both — they have different key sets
                    if metadata:
                        existing_doc_meta = document_data.get("metadata", {})
                        document_data["metadata"] = {**metadata, **existing_doc_meta}

                    # Fallback: если конвертер не извлёк doc_code,
                    # генерируем из title (как делает approve_draft)
                    doc_meta = document_data.get("metadata", {})
                    if not doc_meta.get("doc_code"):
                        title = doc_meta.get("title", "") or ""
                        fallback_code = title.strip().upper().replace(" ", "-").replace("/", "-")[:50]
                        if not fallback_code:
                            fallback_code = f"DOC-{draft_id}"
                        doc_meta["doc_code"] = fallback_code
                        logger.info(
                            f"Converter returned empty doc_code, generated fallback: {fallback_code}",
                            extra={"task_id": task_id, "draft_id": draft_id},
                        )
                    doc_payload = {
                        "draft_id": draft_id,
                        "document_id": current_doc_id,  # upsert: обновляем существующий документ, а не создаём новый
                        "document": document_data,
                    }
                    doc_result = await client.create_document(doc_payload)
                    doc_data = doc_result.get("data", {})
                    # Registry may assign a new document_id (if upsert created new)
                    new_doc_id = doc_data.get("document_id")
                    if new_doc_id and new_doc_id != current_doc_id:
                        logger.info(
                            f"Document ID updated by Registry: {current_doc_id} -> {new_doc_id}",
                            extra={"task_id": task_id, "draft_id": draft_id},
                        )
                        current_doc_id = new_doc_id

                # --- Step 2: Read sections with assigned IDs from Registry ---
                # Always try to read sections, even if document_data was empty
                # (document already exists from approve step)
                try:
                    sections_result = await client.get_document_sections(current_doc_id)
                    sections_data = sections_result.get("data", {})
                    saved_sections = sections_data.get("sections", [])
                    logger.info(
                        f"Document sections read from Registry: doc={current_doc_id} sections={len(saved_sections)}",
                        extra={"task_id": task_id, "draft_id": draft_id},
                    )
                except Exception as sec_exc:
                    logger.warning(
                        f"Failed to read sections from Registry: {sec_exc}",
                        extra={"task_id": task_id, "draft_id": draft_id},
                    )

                # --- Step 3: Update draft status (idempotent) ---
                await client.update_draft_status(
                    draft_id=draft_id, status="approved", document_id=current_doc_id,
                )
                return {
                    "document_id": current_doc_id,
                    "sections": saved_sections,
                    "status": "registered",
                }
            except Exception as exc:
                # 409 Conflict = draft already in approved state (idempotent)
                if "409" in str(exc) or "DRAFT_ALREADY_DECIDED" in str(exc):
                    logger.info(
                        f"Draft {draft_id} already approved, treating registry step as completed (idempotent)",
                        extra={"task_id": task_id, "draft_id": draft_id},
                    )
                    # Try to read sections anyway — document may already exist with data
                    if not saved_sections:
                        try:
                            sec_result = await client.get_document_sections(current_doc_id)
                            sec_data = sec_result.get("data", {})
                            saved_sections = sec_data.get("sections", [])
                        except Exception:
                            pass
                    return {
                        "status": "already_approved",
                        "draft_id": draft_id,
                        "document_id": current_doc_id,
                        "sections": saved_sections,
                    }

                raise
            finally:
                await client.close()

        result = _run_async(_do_registry())
        new_document_id = result.get("document_id", document_id)
        saved_sections = result.get("sections")

        input_data = {"draft_id": draft_id, "document_id": document_id}
        output_data = {
            "registry_id": new_document_id,
            "version_id": version_id,
            "status": "registered",
        }
        if saved_sections is not None:
            output_data["sections"] = saved_sections
            output_data["document_id"] = new_document_id

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
    """RAG index step — submit to RAG Builder, then exit.

    BackgroundTaskPoller handles waiting for completion and notifying the orchestrator.
    """
    if trace_id:
        set_trace_id(trace_id)
    try:
        logger.info(f"RAG index started: task={task_id} doc={document_id}")

        async def _submit_rag_index():
            client = RAGBuilderClient()
            try:
                result = await client.index_document(
                    document_id=document_id,
                    sections=sections or [],
                )
                # Save to external_tasks — Poller will track completion
                async with get_db_context() as db:
                    repo = ExternalTaskRepository(db)
                    await repo.create(
                        orchestrator_task_id=str(task_id),
                        step_name="rag_index",
                        external_service="rag_builder",
                        external_task_id=str(document_id),
                        context_data={
                            "draft_id": draft_id,
                            "document_id": document_id,
                            "sections": sections,
                        },
                    )
                    await db.commit()

                logger.info(
                    f"RAG index submitted for doc {document_id}, will be polled by BackgroundTaskPoller",
                    extra={"task_id": task_id, "draft_id": draft_id},
                )
                return result
            finally:
                await client.close()

        _run_async(_submit_rag_index())
        return {"status": "pending", "step": "rag_index", "task_id": task_id}

    except Exception as exc:
        logger.error(f"RAG index submission failed: {exc}")
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
