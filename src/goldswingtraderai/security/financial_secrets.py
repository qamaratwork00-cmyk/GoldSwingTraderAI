"""Shared detection for authority-bearing financial/account credentials.

Text scanning preserves the repository scanner's proven source-code semantics.
Structured payload scanning is stricter for exported runtime/evidence artifacts,
where object keys can be inspected without confusing fixture source text for a
real serialized credential.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re
from typing import Any


PRIVATE_KEY_HEADER = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
ASSIGNMENT_SECRET = re.compile(
    r"(?i)\b(?:password|passwd|access[_-]?token|auth[_-]?token|api[_-]?key|"
    r"github[_-]?pat|private[_-]?key|recovery[_-]?key|client[_-]?secret|"
    r"broker[_-]?token|refresh[_-]?token)\b"
    r"\s*[:=]\s*[\"']?([^\s\"'#,;]{8,})"
)
GITHUB_TOKEN = re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b")

SAFE_PLACEHOLDERS = {
    "[redacted]",
    "redacted",
    "changeme",
    "placeholder",
    "example",
    "example-only",
    "not-a-secret",
}

_FORBIDDEN_FIELD_TOKENS = {
    "password",
    "passwd",
    "access_token",
    "auth_token",
    "api_key",
    "github_pat",
    "private_key",
    "recovery_key",
    "client_secret",
    "broker_token",
    "refresh_token",
}


def scan_text_for_financial_secrets(text: str) -> list[str]:
    """Return stable finding labels for likely authority-bearing credentials."""

    findings: list[str] = []
    if PRIVATE_KEY_HEADER.search(text):
        findings.append("private-key material")
    if GITHUB_TOKEN.search(text):
        findings.append("GitHub access token")

    for match in ASSIGNMENT_SECRET.finditer(text):
        value = match.group(1).strip().lower()
        if _is_safe_placeholder(value):
            continue
        findings.append("credential-like assignment")
    return findings


def scan_payload_for_financial_secrets(value: Any, *, path: str = "payload") -> list[str]:
    """Inspect serialized-data structure without treating source fixtures as secrets."""

    findings: list[str] = []
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            normalized = key.lower().replace("-", "_").replace(" ", "_")
            child_path = f"{path}.{key}"
            if any(token in normalized for token in _FORBIDDEN_FIELD_TOKENS):
                if not _value_is_safe_placeholder(child):
                    findings.append(f"credential-like field {child_path}")
            findings.extend(scan_payload_for_financial_secrets(child, path=child_path))
        return findings

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            findings.extend(
                scan_payload_for_financial_secrets(child, path=f"{path}[{index}]")
            )
        return findings

    if isinstance(value, str):
        findings.extend(scan_text_for_financial_secrets(value))
    return findings


def _value_is_safe_placeholder(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return _is_safe_placeholder(value.strip().lower())


def _is_safe_placeholder(value: str) -> bool:
    return value in SAFE_PLACEHOLDERS or value.startswith("${") or value.startswith("<")
