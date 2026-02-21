"""Structured logging configuration for Shadow Ops backend.

Uses structlog.stdlib.LoggerFactory (no PrintLogger) so uvicorn and app code
share the same formatter. ProcessorFormatter + ExtraAdder handle stdlib extra=.
"""

import logging
import sys

import structlog
from structlog.types import Processor

from app.config import settings


def setup_logging() -> None:
    """Configure structlog with stdlib LoggerFactory; uvicorn logs use same formatter."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    shared_processors: list[Processor] = [
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(colors=True)
            if sys.stderr.isatty()
            else structlog.processors.JSONRenderer(),
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    # Route uvicorn loggers through root so all logs use ProcessorFormatter.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.setLevel(log_level)
        logger.propagate = True


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a stdlib-compatible structlog logger for the given name."""
    return structlog.get_logger(name)
