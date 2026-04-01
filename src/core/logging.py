from __future__ import annotations

import logging
import logging.config
from typing import Any

import structlog

from .config import settings


def _get_renderer() -> structlog.types.Processor:
    if settings.debug:
        return structlog.dev.ConsoleRenderer()
    return structlog.processors.JSONRenderer()


def configure_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": _get_renderer(),
                    "foreign_pre_chain": shared_processors,
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {"handlers": ["default"], "level": "DEBUG" if settings.debug else "INFO"},
            "loggers": {
                "uvicorn": {"level": "INFO", "propagate": False, "handlers": ["default"]},
                "uvicorn.error": {"level": "INFO", "propagate": False, "handlers": ["default"]},
                "uvicorn.access": {"level": "INFO", "propagate": False, "handlers": ["default"]},
            },
        }
    )

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if settings.debug else logging.INFO
        ),
        cache_logger_on_first_use=True,
    )


def get_logger(*args: Any, **initial_values: Any) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(*args, **initial_values)
