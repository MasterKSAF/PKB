from pathlib import Path
from datetime import timedelta, timezone
from typing import Any, cast

from loguru import logger

from rag_builder.core.config import settings


UTC_PLUS_3 = timezone(timedelta(hours=3))


def _format_record(record: Any) -> str:
    rec = cast(dict[str, Any], record)
    time_value = rec["time"].astimezone(UTC_PLUS_3)
    level = rec["level"].name
    name = rec["name"]
    function = rec["function"]
    line = rec["line"]
    message = rec["message"]
    return (
        f"{time_value.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} UTC+3 | "
        f"{level} | {name}:{function}:{line} | {message}\n"
    )


def configure_logging() -> None:
    import sys
    logs_dir = Path(__file__).resolve().parents[3] / settings.log_dir
    logs_dir.mkdir(parents=True, exist_ok=True)
    logger.remove()
    # File logging
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
    # Stdout logging (for docker logs)
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format=_format_record,
        enqueue=False,
    )
