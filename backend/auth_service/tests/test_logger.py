import logging
from app.core.logger import get_logger, setup_logging


def test_get_logger_returns_logger():
    logger = get_logger("test.module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test.module"


def test_setup_logging_configures_stdout(capsys):
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    setup_logging()
    try:
        logger = get_logger("test.output")
        logger.info("hello logging")
        captured = capsys.readouterr()
        assert "hello logging" in captured.out
        assert "INFO" in captured.out
    finally:
        for handler in root.handlers[:]:
            root.removeHandler(handler)
