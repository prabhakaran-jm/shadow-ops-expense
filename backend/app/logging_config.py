"""Structured logging configuration for Shadow Ops backend."""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from app.config import settings

try:
    _merge_contextvars = structlog.contextvars.merge_contextvars
except AttributeError:
    _merge_contextvars = None


def setup_logging() -> None:
    """Configure structured logging with structlog."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    shared_processors: list[Processor] = [
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    if _merge_contextvars is not None:
        shared_processors.insert(0, _merge_contextvars)

    if sys.stderr.isatty():
        shared_processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        shared_processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=shared_processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer() if not sys.stderr.isatty() else structlog.dev.ConsoleRenderer(colors=True),
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    for name in ("uvicorn", "uvicorn.error"):
        logging.getLogger(name).handlers = [handler]
        logging.getLogger(name).setLevel(log_level)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structured logger for the given module name."""
    return structlog.get_logger(name)
