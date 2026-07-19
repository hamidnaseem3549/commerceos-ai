"""Structured logging."""
import sys
import json
import logging
from datetime import datetime, timezone


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(),
                 "level": record.levelname, "logger": record.name,
                 "message": record.getMessage()}
        for attr in ("agent", "action"):
            if hasattr(record, attr):
                entry[attr] = getattr(record, attr)
        return json.dumps(entry)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
