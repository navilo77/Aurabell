"""Structured logging configuration (BE-08).

Provides JSON-structured logs with request ID correlation for observability.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from app.core.config import settings


class StructuredFormatter(logging.Formatter):
    """JSON formatter with request ID and context."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request ID if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName", "relativeCreated",
                "thread", "threadName", "exc_info", "exc_text", "stack_info",
                "request_id", "asctime"
            ):
                log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class RequestIdFilter(logging.Filter):
    """Add request ID from context to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Try to get request_id from context vars if available
        try:
            from contextvars import ContextVar
            request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
            request_id = request_id_var.get()
            if request_id:
                record.request_id = request_id
        except Exception:
            pass
        return True


def setup_logging() -> None:
    """Configure application logging."""
    log_level = logging.DEBUG if settings.APP_ENV == "development" else logging.INFO

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler with structured formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    if settings.APP_ENV == "production":
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

    # Add request ID filter
    root_logger.addFilter(RequestIdFilter())


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


# Context variable for request ID
from contextvars import ContextVar
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_request_id(request_id: str) -> None:
    """Set request ID in context for logging."""
    request_id_var.set(request_id)


def clear_request_id() -> None:
    """Clear request ID from context."""
    request_id_var.set(None)