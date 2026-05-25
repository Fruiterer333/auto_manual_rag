import logging
import sys
from pathlib import Path

from app.core.config import get_settings


_HANDLER_MARKER = "_auto_manual_rag_handler"
_LOGGER_SIGNATURE = "_auto_manual_rag_signature"
_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def get_logger(name: str) -> logging.Logger:
    settings = get_settings()
    level = _parse_log_level(settings.LOG_LEVEL)
    log_file = settings.LOG_FILE or None

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    _configure_logger_handlers(logger, level, log_file)
    return logger


def _parse_log_level(log_level: str) -> int:
    return getattr(logging, log_level.upper(), logging.INFO)


def _configure_logger_handlers(
    logger: logging.Logger,
    level: int,
    log_file: str | None,
) -> None:
    signature = (level, log_file)
    if getattr(logger, _LOGGER_SIGNATURE, None) == signature:
        for handler in logger.handlers:
            if getattr(handler, _HANDLER_MARKER, False):
                handler.setLevel(level)
        return

    _remove_managed_handlers(logger)
    formatter = logging.Formatter(_LOG_FORMAT)

    console_handler = logging.StreamHandler(sys.stderr)
    setattr(console_handler, _HANDLER_MARKER, True)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_path = Path(log_file)
        if log_path.parent != Path("."):
            log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        setattr(file_handler, _HANDLER_MARKER, True)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    setattr(logger, _LOGGER_SIGNATURE, signature)


def _remove_managed_handlers(logger: logging.Logger) -> None:
    remaining_handlers: list[logging.Handler] = []
    for handler in logger.handlers:
        if getattr(handler, _HANDLER_MARKER, False):
            handler.close()
        else:
            remaining_handlers.append(handler)
    logger.handlers = remaining_handlers
