from pathlib import Path
from datetime import timedelta, timezone

from loguru import logger

from rag_builder.core.config import settings


UTC_PLUS_3 = timezone(timedelta(hours=3))


def configure_logging() -> None:
    logs_dir = Path(__file__).resolve().parents[3] / settings.log_dir
    logs_dir.mkdir(parents=True, exist_ok=True)
    logger.remove()
    patched_logger = logger.patch(
        lambda record: record["extra"].update(
            {"time_utc3": record["time"].astimezone(UTC_PLUS_3).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]}
        )
    )
    patched_logger.add(
        logs_dir / settings.log_file,
        level=settings.log_level,
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression=settings.log_compression,
        enqueue=True,
        backtrace=True,
        diagnose=False,
        format="{extra[time_utc3]} UTC+3 | {level} | {name}:{function}:{line} | {message}",
    )
