from pathlib import Path
from datetime import timedelta, timezone

from loguru import logger

from rag_builder.core.config import settings


UTC_PLUS_3 = timezone(timedelta(hours=3))


def _format_record(record: dict[str, object]) -> str:
    time_value = record["time"].astimezone(UTC_PLUS_3)  # type: ignore[union-attr]
    level = record["level"].name  # type: ignore[union-attr]
    name = record["name"]
    function = record["function"]
    line = record["line"]
    message = record["message"]
    return (
        f"{time_value.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} UTC+3 | "
        f"{level} | {name}:{function}:{line} | {message}\n"
    )


def configure_logging() -> None:
    logs_dir = Path(__file__).resolve().parents[3] / settings.log_dir
    logs_dir.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(
        logs_dir / settings.log_file,
        level=settings.log_level,
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression=settings.log_compression,
        enqueue=True,
        backtrace=True,
        diagnose=False,
        format=_format_record,
    )
