import logging


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def setup_logging() -> None:
    """Fallback plain-text logging used only if OTEL is not initialized."""
    import sys

    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    handler.setLevel(logging.INFO)
    root.setLevel(logging.INFO)
    root.addHandler(handler)
