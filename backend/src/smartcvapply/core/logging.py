"""Structured JSON logging with PII redaction."""
import logging
import sys

import structlog

from smartcvapply.core.config import get_settings
from smartcvapply.utils.pii import PIIRedactor

_redactor = PIIRedactor()


def _redact_processor(_logger, _method, event_dict):
    return _redactor.redact(event_dict)


def configure_logging() -> None:
    s = get_settings()
    level = getattr(logging, s.log_level.upper(), logging.INFO)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _redact_processor,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None):
    return structlog.get_logger(name)
