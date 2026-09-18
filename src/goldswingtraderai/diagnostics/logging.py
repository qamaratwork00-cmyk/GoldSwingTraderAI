"""Structured logging utilities with conservative secret redaction."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

_SENSITIVE_KEY_FRAGMENTS = (
    "password",
    "passwd",
    "token",
    "secret",
    "api_key",
    "apikey",
    "authorization",
    "credential",
    "private_key",
    "privatekey",
    "recovery_key",
    "pat",
)
_REDACTED = "[REDACTED]"


def _is_sensitive_key(key: object) -> bool:
    normalized = str(key).strip().lower().replace("-", "_")
    return any(fragment in normalized for fragment in _SENSITIVE_KEY_FRAGMENTS)


def redact_value(value: Any) -> Any:
    """Recursively redact values beneath authority-bearing-looking keys."""

    if isinstance(value, Mapping):
        return {
            str(key): _REDACTED if _is_sensitive_key(key) else redact_value(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, set):
        return sorted(redact_value(item) for item in value)
    return value


def redact_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
    return dict(redact_value(mapping))


class SensitiveDataFilter(logging.Filter):
    """Redact structured context before formatting."""

    def filter(self, record: logging.LogRecord) -> bool:
        for attr in ("context", "event_data"):
            value = getattr(record, attr, None)
            if isinstance(value, Mapping):
                setattr(record, attr, redact_mapping(value))
        return True


class JsonFormatter(logging.Formatter):
    """Small dependency-free JSON formatter for machine-readable runtime logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        event = getattr(record, "event", None)
        if event is not None:
            payload["event"] = str(event)
        context = getattr(record, "context", None)
        if isinstance(context, Mapping):
            payload["context"] = redact_mapping(context)
        event_data = getattr(record, "event_data", None)
        if isinstance(event_data, Mapping):
            payload["event_data"] = redact_mapping(event_data)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)


def configure_logging(level: int | str = logging.INFO) -> None:
    """Configure the root logger once with safe structured output."""

    if isinstance(level, str):
        resolved = getattr(logging, level.upper(), None)
        if not isinstance(resolved, int):
            raise ValueError(f"invalid log level: {level!r}")
        level = resolved

    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.addFilter(SensitiveDataFilter())
    handler.setFormatter(JsonFormatter())

    root.handlers.clear()
    root.addHandler(handler)
