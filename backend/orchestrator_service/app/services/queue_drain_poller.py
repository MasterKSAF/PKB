"""
QueueDrainPoller — фоновый опрос очереди задач.

Каждые POLL_INTERVAL секунд проверяет, есть ли задачи в статусе 'queued'
свободные слоты для выполнения, и диспатчит их через PipelineOrchestrator.drain_queue().

Запускается в lifespan FastAPI приложения.
"""

import asyncio
import logging

from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.db.session import get_db_context

logger = logging.getLogger("orchestrator.queue_drain")


class QueueDrainPoller:
    """Фоновый опрос очереди pipeline-задач.

    Периодически пытается диспатчить задачи из очереди (queued → active),
    если есть свободные execution slots.
    """

    POLL_INTERVAL = 5  # секунд между циклами

    async def run(self) -> None:
        """Основной цикл опроса очереди."""
        logger.info(
            "QueueDrainPoller started",
            extra={"poll_interval": self.POLL_INTERVAL},
        )
        while True:
            try:
                await self._drain_once()
            except Exception as e:
                logger.error(f"Queue drain cycle failed: {e}", exc_info=True)
            await asyncio.sleep(self.POLL_INTERVAL)

    async def _drain_once(self) -> None:
        """Один цикл: пытаемся диспатчить queued задачи."""
        async with get_db_context() as db:
            orchestrator = PipelineOrchestrator(db)
            dequeued = await orchestrator.drain_queue()
            if dequeued:
                logger.info(
                    "Queue drain cycle: dispatched %d task(s)",
                    dequeued,
                    extra={"dequeued": dequeued},
                )


# ------------------------------------------------------------------
#  Singleton + lifecycle helpers
# ------------------------------------------------------------------

_poller_task: asyncio.Task | None = None


async def start_queue_drain_poller() -> None:
    """Start the QueueDrainPoller as a background asyncio task."""
    global _poller_task
    if _poller_task is not None:
        logger.warning("QueueDrainPoller already running, skipping")
        return
    poller = QueueDrainPoller()
    _poller_task = asyncio.create_task(poller.run())
    logger.info("QueueDrainPoller background task created")


async def stop_queue_drain_poller() -> None:
    """Stop the QueueDrainPoller."""
    global _poller_task
    if _poller_task is None:
        return
    _poller_task.cancel()
    try:
        await _poller_task
    except asyncio.CancelledError:
        pass
    _poller_task = None
    logger.info("QueueDrainPoller stopped")
