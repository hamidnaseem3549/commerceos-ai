"""Structured logging."""
import json
import logging
import sys
from datetime import UTC, datetime


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {"timestamp": datetime.now(UTC).isoformat(),
                 "level": record.levelname, "logger": record.name,
                 "message": record.getMessage()}
        for attr in ("agent", "action"):
            if hasattr(record, attr):
                entry[attr] = getattr(record, attr)
        return json.dumps(entry)


def get_logger(name: str) -> logging.Logger:
    """Get or create a structured JSON logger.

    Args:
        name: Logger name (typically ``__name__``).

    Returns:
        A ``logging.Logger`` instance that outputs JSON-formatted
        log lines to stdout.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
