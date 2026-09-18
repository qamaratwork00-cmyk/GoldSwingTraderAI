"""Fail when likely authority-bearing credentials are present in repository text files.

This scanner is intentionally conservative and pattern-based. It complements, not
replaces, provider-side secret scanning. Strategy/research content is allowed;
actual credential-looking values are not.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
}

TEXT_SUFFIXES = {
    ".py",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".ini",
    ".cfg",
    ".conf",
    ".txt",
    ".md",
    ".env",
    ".example",
    ".sh",
    ".ps1",
}

PRIVATE_KEY_HEADER = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
ASSIGNMENT_SECRET = re.compile(
    r"(?i)\b(?:password|passwd|access[_-]?token|auth[_-]?token|api[_-]?key|"
    r"github[_-]?pat|private[_-]?key|recovery[_-]?key|client[_-]?secret)\b"
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


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name == ".env.example" or path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def scan_text(text: str) -> list[str]:
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


def scan_repository(root: Path) -> list[tuple[Path, str]]:
    findings: list[tuple[Path, str]] = []
    for path in iter_text_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for reason in scan_text(text):
            findings.append((path, reason))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan repository for financial-authority secrets")
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    findings = scan_repository(root)
    if findings:
        print("FINANCIAL_SECRET_DETECTED")
        for path, reason in findings:
            print(f"- {path.relative_to(root)}: {reason}")
        return 2

    print("Financial-secret scan: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
