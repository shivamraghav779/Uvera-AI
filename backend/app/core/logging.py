"""Structured logging with request correlation and secret redaction."""

import json
import logging
import sys
from collections.abc import Mapping
from datetime import UTC, datetime

from app.core.config import LogFormat
from app.core.context import get_request_id
from app.core.security import is_sensitive_key

REDACTED = "***REDACTED***"

_STANDARD_ATTRIBUTES = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "message",
    "asctime",
    "taskName",
}
_NOISY_LOGGERS = ("httpx", "httpcore", "uvicorn.access")
_HANDLER_MARKER = "_generative_ui_handler"


def _must_hide(key: str, value: object) -> bool:
    # Numbers and flags are never credentials (e.g. ``prompt_tokens`` is a count).
    return is_sensitive_key(key) and not isinstance(value, int | float | type(None))


def redact(value: object) -> object:
    """Replace values stored under secret-looking keys, recursively."""
    if isinstance(value, Mapping):
        return {
            str(key): REDACTED if _must_hide(str(key), nested) else redact(nested)
            for key, nested in value.items()
        }
    if isinstance(value, list | tuple):
        return [redact(item) for item in value]
    return value


def _extra_fields(record: logging.LogRecord) -> dict[str, object]:
    extras = {
        key: value for key, value in record.__dict__.items() if key not in _STANDARD_ATTRIBUTES
    }
    redacted = redact(extras)
    assert isinstance(redacted, dict)
    return redacted


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
            "request_id": get_request_id(),
            **_extra_fields(record),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=UTC).strftime("%H:%M:%S")
        fields = {"request_id": get_request_id(), **_extra_fields(record)}
        rendered = " ".join(f"{key}={value}" for key, value in fields.items() if value is not None)
        line = f"{timestamp} {record.levelname:<7} {record.name}: {record.getMessage()} {rendered}"
        if record.exc_info:
            line = f"{line}\n{self.formatException(record.exc_info)}"
        return line.rstrip()


def configure_logging(level: str, log_format: LogFormat) -> None:
    """Install the application log handler. Safe to call more than once."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if log_format is LogFormat.JSON else ConsoleFormatter())
    setattr(handler, _HANDLER_MARKER, True)

    root = logging.getLogger()
    for existing in list(root.handlers):
        if getattr(existing, _HANDLER_MARKER, False):
            root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level)

    # These log full request URLs / duplicate our own request logs.
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
