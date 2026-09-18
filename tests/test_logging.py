from __future__ import annotations

import json
import logging
from io import StringIO

from goldswingtraderai.diagnostics.logging import JsonFormatter, SensitiveDataFilter, redact_mapping


def test_redact_mapping_hides_sensitive_keys_recursively() -> None:
    redacted = redact_mapping(
        {
            "account": 123,
            "password": "secret-password",
            "nested": {"api_key": "paid-key", "symbol": "XAUUSDm"},
        }
    )

    assert redacted["account"] == 123
    assert redacted["password"] == "[REDACTED]"
    assert redacted["nested"]["api_key"] == "[REDACTED]"
    assert redacted["nested"]["symbol"] == "XAUUSDm"


def test_json_formatter_redacts_structured_context() -> None:
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(SensitiveDataFilter())
    handler.setFormatter(JsonFormatter())

    logger = logging.getLogger("test.goldswing")
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    logger.info(
        "startup",
        extra={
            "event": "STARTUP",
            "context": {
                "symbol": "XAUUSDm",
                "token": "must-not-leak",
                "nested": {"private_key": "must-not-leak-either"},
            },
        },
    )

    payload = json.loads(stream.getvalue())
    assert payload["event"] == "STARTUP"
    assert payload["context"]["symbol"] == "XAUUSDm"
    assert payload["context"]["token"] == "[REDACTED]"
    assert payload["context"]["nested"]["private_key"] == "[REDACTED]"
    assert "must-not-leak" not in stream.getvalue()
