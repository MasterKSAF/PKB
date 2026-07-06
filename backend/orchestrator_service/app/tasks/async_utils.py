"""
Async utilities for Celery tasks — единый event-loop на задачу.

Позволяет переиспользовать один event-loop в рамках одной синхронной
Celery-задачи вместо создания нового на каждый ``_run_async`` вызов.

Использование::

    from app.tasks.async_utils import run_async, close_async_loop

    @celery_app.task
    def my_task(...):
        try:
            result = run_async(some_coro())
            run_async(another_coro())
        finally:
            close_async_loop()
"""

import asyncio
import threading

_logger = __import__("logging").getLogger("tasks.async_utils")

# Thread-local storage: один loop на поток (Celery-задача в одном потоке).
_local = threading.local()


def run_async(coro):
    """Execute a coroutine in the current task's event loop.

    Reuses the same event loop for all calls within one Celery task.
    The loop is created lazily on the first call and must be closed
    via ``close_async_loop()`` in the task's ``finally`` block.
    """
    loop = getattr(_local, "_loop", None)
    if loop is None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        _local._loop = loop
        _logger.debug("Created new event loop for Celery task")
    return loop.run_until_complete(coro)


def close_async_loop():
    """Close and release the event loop for the current Celery task.

    Must be called in ``finally`` block of every Celery task that uses ``run_async``.
    """
    loop = getattr(_local, "_loop", None)
    if loop is not None:
        try:
            loop.close()
        except Exception:
            pass
        _local._loop = None
        del _local._loop
        _logger.debug("Closed event loop for Celery task")
