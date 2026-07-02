"""
BackgroundTaskPoller — асинхронный опрос внешних задач.

Вместо блокирующего polling'а внутри Celery tasks (которые держат worker),
этот сервис каждые N секунд проверяет таблицу external_tasks и завершает
или помечает как failed задачи, ожидающие ответа от внешних сервисов.

Запускается в lifespan FastAPI приложения.
"""

import asyncio
import logging
from datetime import datetime, timezone

from app.core.config import settings
from app.db.base import AsyncSessionLocal
from app.repositories.external_task_repo import ExternalTaskRepository

logger = logging.getLogger("orchestrator.poller")


class BackgroundTaskPoller:
    """Фоновый опрос внешних асинхронных задач.

    Каждые POLL_INTERVAL секунд проверяет external_tasks, дёргает статус
    внешнего сервиса и, при завершении, уведомляет orchestrator.
    """

    POLL_INTERVAL = 3  # секунд между циклами

    async def run(self) -> None:
        """Основной цикл опроса. Запускается как asyncio background task."""
        logger.info(
            "BackgroundTaskPoller started",
            extra={
                "poll_interval": self.POLL_INTERVAL,
                "timeout": settings.pipeline.EXTERNAL_TASK_TIMEOUT,
            },
        )
        while True:
            try:
                await self._poll_once()
            except Exception as e:
                logger.error(f"Poll cycle failed: {e}", exc_info=True)
            await asyncio.sleep(self.POLL_INTERVAL)

    async def _poll_once(self) -> None:
        """Один цикл опроса: читаем pending задачи и проверяем каждую."""
        async with AsyncSessionLocal() as db:
            repo = ExternalTaskRepository(db)
            pending = await repo.get_pending_tasks()

            if not pending:
                return

            logger.debug(f"Poll cycle: {len(pending)} pending external tasks")

            for task in pending:
                try:
                    await self._process_task(task, repo)
                    await db.commit()
                except Exception as e:
                    await db.rollback()
                    logger.error(
                        f"Failed to process external task {task.id}: {e}",
                        extra={
                            "task_id": task.id,
                            "external_task_id": task.external_task_id,
                            "service": task.external_service,
                        },
                        exc_info=True,
                    )

    async def _process_task(
        self, task, repo: ExternalTaskRepository,
    ) -> None:
        """Проверить статус одной внешней задачи и обработать результат."""

        # Safety valve: timeout check (3 hours by default)
        now = datetime.now(timezone.utc)
        if task.created_at:
            age_seconds = (now - task.created_at).total_seconds()
            if age_seconds > settings.pipeline.EXTERNAL_TASK_TIMEOUT:
                logger.warning(
                    f"External task {task.external_task_id} timed out "
                    f"(age={age_seconds:.0f}s, timeout={settings.pipeline.EXTERNAL_TASK_TIMEOUT}s)",
                    extra={
                        "task_id": task.id,
                        "service": task.external_service,
                        "step": task.step_name,
                    },
                )
                await self._handle_failed(
                    task, repo, "EXTERNAL_TASK_TIMEOUT",
                    f"External task timed out after {age_seconds:.0f}s",
                )
                return

        # Dispatch to service-specific handler
        if task.external_service == "parser":
            await self._check_parser_status(task, repo)
        elif task.external_service == "rag_builder":
            await self._check_rag_builder_status(task, repo)
        else:
            logger.warning(
                f"Unknown external service: {task.external_service}",
                extra={"task_id": task.id},
            )
            await self._handle_failed(
                task, repo, "UNKNOWN_SERVICE",
                f"Unknown external service: {task.external_service}",
            )

    # ------------------------------------------------------------------
    #  Parser handlers
    # ------------------------------------------------------------------

    async def _check_parser_status(
        self, task, repo: ExternalTaskRepository,
    ) -> None:
        """Check Parser status and handle completion/failure."""
        from app.services.parser_client import ParserServiceClient

        client = ParserServiceClient()
        try:
            status_resp = await client.get_status(task.external_task_id)
        finally:
            await client.close()

        status_data = status_resp.get("data", status_resp)
        p_status = status_data.get("status", "")

        if p_status == "completed":
            await self._handle_parser_completed(task, repo)
        elif p_status == "failed":
            error_msg = status_data.get("error", "Parser processing failed")
            await self._handle_failed(task, repo, "PARSER_FAILED", error_msg)
        else:
            # processing/pending — skip until next cycle
            logger.debug(
                f"Parser task {task.external_task_id} still processing",
                extra={"task_id": task.id},
            )

    async def _handle_parser_completed(
        self, task, repo: ExternalTaskRepository,
    ) -> None:
        """Fetch parser result, transform, notify orchestrator."""
        from app.services.parser_client import ParserServiceClient
        from app.tasks.pipeline_formation import process_parser_full_result

        client = ParserServiceClient()
        try:
            result_resp = await client.get_result(task.external_task_id)
        finally:
            await client.close()

        full_result = result_resp.get("data", result_resp)
        ctx = task.context_data or {}

        await process_parser_full_result(
            task_id=int(task.orchestrator_task_id),
            draft_id=ctx.get("draft_id", 0),
            file_key=ctx.get("file_key", ""),
            full_parser_result=full_result,
        )

        await repo.delete(task.id)
        logger.info(
            f"Parser task {task.external_task_id} completed, orchestrator notified",
            extra={"orchestrator_task_id": task.orchestrator_task_id},
        )

    # ------------------------------------------------------------------
    #  RAG Builder handlers
    # ------------------------------------------------------------------

    async def _check_rag_builder_status(
        self, task, repo: ExternalTaskRepository,
    ) -> None:
        """Check RAG Builder build status and handle completion/failure."""
        from app.services.rag_client import RAGBuilderClient

        client = RAGBuilderClient()
        try:
            status_result = await client.get_build_status(
                document_id=task.external_task_id,
            )
        finally:
            await client.close()

        final_status = status_result.get("status", "")

        if final_status == "indexed" or final_status == "completed":
            await self._handle_rag_builder_completed(task, repo, status_result)
        elif final_status == "failed":
            error_msg = status_result.get("errors", "RAG Build failed")
            await self._handle_failed(task, repo, "RAG_BUILD_FAILED", error_msg)
        else:
            # still indexing/pending — skip
            logger.debug(
                f"RAG build for doc {task.external_task_id} still {final_status}",
                extra={"task_id": task.id},
            )

    async def _handle_rag_builder_completed(
        self, task, repo: ExternalTaskRepository, status_result: dict,
    ) -> None:
        """Handle RAG Builder completion: dispatch by step_name."""
        step_name = task.step_name

        if step_name == "rag_index":
            from app.tasks.pipeline_indexation import process_rag_index_result

            await process_rag_index_result(
                job_id=str(task.orchestrator_task_id),
                document_id=task.external_task_id,
                status_result=status_result,
            )
            await repo.delete(task.id)
            logger.info(
                f"RAG index completed for doc {task.external_task_id}",
                extra={"job_id": task.orchestrator_task_id},
            )

        elif step_name == "reprocess":
            from app.tasks.pipeline_indexation import process_reprocess_result

            await process_reprocess_result(
                task_id=task.orchestrator_task_id,
                document_id=task.external_task_id,
                status_result=status_result,
            )
            await repo.delete(task.id)
            logger.info(
                f"Reprocess completed for doc {task.external_task_id}",
                extra={"task_id": task.orchestrator_task_id},
            )

        elif step_name == "activate":
            from app.tasks.pipeline_indexation import process_activate_result

            await process_activate_result(
                document_id=int(task.external_task_id),
            )
            await repo.delete(task.id)
            logger.info(
                f"Activation completed for doc {task.external_task_id}",
            )

        else:
            logger.warning(
                f"Unknown step_name for rag_builder: {step_name}",
                extra={"task_id": task.id},
            )
            await self._handle_failed(
                task, repo, "UNKNOWN_STEP",
                f"Unknown step: {step_name}",
            )

    # ------------------------------------------------------------------
    #  Failure handler
    # ------------------------------------------------------------------

    async def _handle_failed(
        self, task, repo: ExternalTaskRepository,
        error_code: str, error_message: str,
    ) -> None:
        """Handle external task failure: notify orchestrator and clean up."""
        step_name = task.step_name

        if step_name == "full_ocr":
            from app.tasks.pipeline_formation import _notify_step_failed as notify_formation
            await notify_formation(
                task_id=int(task.orchestrator_task_id),
                step_name="full_ocr",
                error_code=error_code,
                error_message=error_message,
            )
        elif step_name == "rag_index":
            from app.tasks.pipeline_indexation import _notify_step_failed as notify_indexation
            await notify_indexation(
                job_id=str(task.orchestrator_task_id),
                step_name="rag_index",
                error_code=error_code,
                error_message=error_message,
            )
        elif step_name == "reprocess":
            from app.tasks.pipeline_indexation import _notify_step_failed as notify_indexation
            await notify_indexation(
                job_id=str(task.orchestrator_task_id),
                step_name="reprocess",
                error_code=error_code,
                error_message=error_message,
            )
        elif step_name == "activate":
            logger.error(
                f"Activation failed for doc {task.external_task_id}: "
                f"[{error_code}] {error_message}",
            )
            # No step notification for activate — it's not a pipeline step

        await repo.delete(task.id)
        logger.info(
            f"External task {task.id} marked as failed: {error_code}",
            extra={
                "step": step_name,
                "error_code": error_code,
                "external_task_id": task.external_task_id,
            },
        )


# ------------------------------------------------------------------
#  Singleton + lifecycle helpers
# ------------------------------------------------------------------

_poller_task: asyncio.Task | None = None


async def start_poller() -> None:
    """Start the BackgroundTaskPoller as a background asyncio task."""
    global _poller_task
    if _poller_task is not None:
        logger.warning("BackgroundTaskPoller already running, skipping")
        return
    poller = BackgroundTaskPoller()
    _poller_task = asyncio.create_task(poller.run())
    logger.info("BackgroundTaskPoller background task created")


async def stop_poller() -> None:
    """Stop the BackgroundTaskPoller."""
    global _poller_task
    if _poller_task is None:
        return
    _poller_task.cancel()
    try:
        await _poller_task
    except asyncio.CancelledError:
        pass
    _poller_task = None
    logger.info("BackgroundTaskPoller stopped")
