"""
Pipeline 1 (Formation) Celery tasks.

Each function represents one step in Pipeline 1:
1. OCR — process document with OCR service
2. Parser — parse OCR output into structured data
3. Converter — convert/validate parsed data
4. Registry — store in document registry

In production, each task calls the appropriate microservice client.
For development, tasks run in mock mode (simulating success).
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from app.celery_app import celery_app
from app.core.config import settings
from app.core.fsm import PIPELINE_1_STEPS
from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.db.session import get_db_context
from app.services.ocr_client import OCRServiceClient
from app.services.registry_client import RegistryServiceClient

logger = logging.getLogger("tasks.pipeline_1")


def _run_async(coro):
    """Run an async coroutine synchronously from a Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, name="tasks.pipeline.run_ocr_step")
def run_ocr_step(self, job_id: str, document_id: str):
    """
    Step 1: OCR Service — recognize text from document.

    In production: calls OCRServiceClient.process_document().
    In mock: simulates success after short delay.
    """
    try:
        logger.info(f"OCR step started: job={job_id} doc={document_id}")

        # In production, call actual OCR service
        # result = asyncio.run(_ocr_service_call(document_id))

        # Mock: simulate OCR completion
        mock_result = {
            "document_id": document_id,
            "pages": [{"page": 1, "text": "Mocked OCR text", "confidence": 0.95}],
            "total_pages": 1,
        }

        # Notify orchestrator of completion
        _run_async(_notify_step_completed(job_id, "ocr", mock_result))

        logger.info(f"OCR step completed: job={job_id}")
        return {"status": "completed", "step": "ocr", "job_id": job_id}

    except Exception as exc:
        logger.error(f"OCR step failed: {exc}")
        _run_async(
            _notify_step_failed(job_id, "ocr", "OCR_ERROR", str(exc))
        )
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, name="tasks.pipeline.run_parser_step")
def run_parser_step(self, job_id: str, document_id: str):
    """
    Step 2: Parser Service — extract structured sections from OCR output.

    In production: calls Parser Service (separate microservice).
    """
    try:
        logger.info(f"Parser step started: job={job_id} doc={document_id}")

        mock_result = {
            "document_id": document_id,
            "sections": [{"type": "text", "content": "Parsed section 1"}],
        }

        _run_async(_notify_step_completed(job_id, "parser", mock_result))

        logger.info(f"Parser step completed: job={job_id}")
        return {"status": "completed", "step": "parser", "job_id": job_id}

    except Exception as exc:
        logger.error(f"Parser step failed: {exc}")
        _run_async(
            _notify_step_failed(job_id, "parser", "PARSER_ERROR", str(exc))
        )
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, name="tasks.pipeline.run_converter_step")
def run_converter_step(self, job_id: str, document_id: str):
    """
    Step 3: Converter-validator — validate and transform parsed data.

    In production: calls Converter-validator Service.
    """
    try:
        logger.info(f"Converter step started: job={job_id} doc={document_id}")

        mock_result = {
            "document_id": document_id,
            "validated": True,
            "parameters": {"thickness": "12mm"},
        }

        _run_async(_notify_step_completed(job_id, "converter", mock_result))

        logger.info(f"Converter step completed: job={job_id}")
        return {"status": "completed", "step": "converter", "job_id": job_id}

    except Exception as exc:
        logger.error(f"Converter step failed: {exc}")
        _run_async(
            _notify_step_failed(job_id, "converter", "CONVERTER_ERROR", str(exc))
        )
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30, name="tasks.pipeline.run_registry_step")
def run_registry_step(self, job_id: str, document_id: str):
    """
    Step 4: Registry — persist document in the registry database.

    Has side-effects (creates DB records), so Saga compensation needed.
    """
    try:
        logger.info(f"Registry step started: job={job_id} doc={document_id}")

        mock_result = {
            "document_id": document_id,
            "registry_id": f"reg-{document_id[:8]}",
            "status": "registered",
        }

        _run_async(_notify_step_completed(job_id, "registry", mock_result))

        logger.info(f"Registry step completed: job={job_id}")
        return {"status": "completed", "step": "registry", "job_id": job_id}

    except Exception as exc:
        logger.error(f"Registry step failed: {exc}")
        _run_async(
            _notify_step_failed(job_id, "registry", "REGISTRY_ERROR", str(exc))
        )
        # Registry has side-effects, will trigger Saga compensation
        raise self.retry(exc=exc)


async def _notify_step_completed(job_id: str, step_name: str, result: Dict[str, Any]):
    """Notify the orchestrator that a step completed successfully."""
    async with get_db_context() as db:
        orchestrator = PipelineOrchestrator(db)
        await orchestrator.on_step_completed(job_id, step_name, result)


async def _notify_step_failed(
    job_id: str, step_name: str, error_code: str, error_message: str
):
    """Notify the orchestrator that a step failed."""
    async with get_db_context() as db:
        orchestrator = PipelineOrchestrator(db)
        await orchestrator.on_step_failed(job_id, step_name, error_code, error_message)
