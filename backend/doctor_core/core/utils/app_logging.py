import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


DEBUG_LOG_PATH = Path(__file__).resolve().parents[2] / "debug.log"
LOGGER_NAME = "doctor_core"


def configure_debug_logging() -> logging.Logger:
    DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEBUG_LOG_PATH.touch(exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = RotatingFileHandler(
        DEBUG_LOG_PATH,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger(LOGGER_NAME)
    if not any(
        isinstance(existing_handler, RotatingFileHandler)
        and getattr(existing_handler, "baseFilename", None) == str(DEBUG_LOG_PATH)
        for existing_handler in logger.handlers
    ):
        logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    for name in ("uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        if not any(
            isinstance(existing_handler, RotatingFileHandler)
            and getattr(existing_handler, "baseFilename", None) == str(DEBUG_LOG_PATH)
            for existing_handler in uvicorn_logger.handlers
        ):
            uvicorn_logger.addHandler(handler)
        uvicorn_logger.setLevel(logging.INFO)

    return logger


def get_logger(name: str) -> logging.Logger:
    configure_debug_logging()
    return logging.getLogger(f"{LOGGER_NAME}.{name}")
