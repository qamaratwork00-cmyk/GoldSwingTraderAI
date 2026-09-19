"""Fail when likely authority-bearing credentials are present in repository text files.

This scanner is intentionally conservative and pattern-based. It complements, not
replaces, provider-side secret scanning. Strategy/research content is allowed;
actual credential-looking values are not.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterator
from pathlib import Path

from goldswingtraderai.security.financial_secrets import scan_text_for_financial_secrets


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


def iter_text_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name == ".env.example" or path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def scan_text(text: str) -> list[str]:
    """Backward-compatible script-level wrapper around the shared detector."""

    return scan_text_for_financial_secrets(text)


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
