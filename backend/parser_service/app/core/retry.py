"""
Декоратор для повторных попыток выполнения асинхронных операций.
"""
import asyncio
import logging
from functools import wraps
from typing import Type, Tuple

logger = logging.getLogger(__name__)


def retry(
    exceptions: Tuple[Type[Exception], ...],
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
):
    """
    Декоратор для асинхронных функций.

    Args:
        exceptions: Кортеж исключений, при которых выполняется повтор.
        max_attempts: Максимальное число попыток.
        delay: Начальная задержка в секундах.
        backoff: Множитель увеличения задержки после каждой попытки.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            "Retry failed after %d attempts for %s: %s",
                            max_attempts,
                            func.__name__,
                            e,
                            exc_info=True,
                        )
                        raise
                    logger.warning(
                        "Retry %d/%d for %s due to %s, waiting %.2fs",
                        attempt,
                        max_attempts,
                        func.__name__,
                        e,
                        current_delay,
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            # Никогда не должно сюда попадать, но на всякий случай
            raise last_exception

        return wrapper

    return decorator