"""Shared detection for authority-bearing financial/account credentials.

This is deliberately pattern based and conservative. It protects public/tracked
artifacts and complements provider-side secret scanning. Strategy, research and
non-authority account context are allowed; credential-like values are not.
"""

from __future__ import annotations

import re


PRIVATE_KEY_HEADER = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
ASSIGNMENT_SECRET = re.compile(
    r"(?i)\b(?:password|passwd|access[_-]?token|auth[_-]?token|api[_-]?key|"
    r"github[_-]?pat|private[_-]?key|recovery[_-]?key|client[_-]?secret|"
    r"broker[_-]?token|refresh[_-]?token)\b"
    r"\s*[\"']?\s*[:=]\s*[\"']?([^\s\"'#,;}{]{8,})"
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


def scan_text_for_financial_secrets(text: str) -> list[str]:
    """Return stable finding labels for likely authority-bearing credentials."""

    findings: list[str] = []
    if PRIVATE_KEY_HEADER.search(text):
        findings.append("private-key material")
    if GITHUB_TOKEN.search(text):
        findings.append("GitHub access token")

    for match in ASSIGNMENT_SECRET.finditer(text):
        value = match.group(1).strip().lower()
        if value in SAFE_PLACEHOLDERS or value.startswith("${") or value.startswith("<"):
            continue
        findings.append("credential-like assignment")
    return findings
