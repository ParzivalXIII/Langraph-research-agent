"""Structured logging configuration using structlog."""

import sys
from typing import Any

import structlog


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog with JSON output for production environments.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging integration
    import logging

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )


def get_logger(name: str) -> Any:
    """Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger with context binding
    """
    return structlog.get_logger(name)
