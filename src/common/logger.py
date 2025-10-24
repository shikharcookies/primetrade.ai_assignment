import logging
import json
import sys
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        # Optional structured fields
        if hasattr(record, "event"):
            payload["event"] = getattr(record, "event")
        if hasattr(record, "data"):
            payload["data"] = getattr(record, "data")
        if hasattr(record, "error"):
            payload["error"] = getattr(record, "error")
        return json.dumps(payload)


def get_logger(name: str = "bot", log_file_path: str = "bot.log") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # File handler
        fh = logging.FileHandler(log_file_path)
        fh.setLevel(logging.INFO)
        fh.setFormatter(JsonFormatter())

        # Stdout handler
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.INFO)
        sh.setFormatter(JsonFormatter())

        logger.addHandler(fh)
        logger.addHandler(sh)
        logger.propagate = False

    return logger