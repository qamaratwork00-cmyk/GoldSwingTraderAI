from __future__ import annotations

import importlib.util
from pathlib import Path

_SCANNER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "scan_financial_secrets.py"
_SPEC = importlib.util.spec_from_file_location("scan_financial_secrets", _SCANNER_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_SCANNER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_SCANNER)
scan_text = _SCANNER.scan_text


def test_scanner_detects_credential_assignment() -> None:
    sample = "password = " + '"supersecret123"'
    findings = scan_text(sample)
    assert "credential-like assignment" in findings


def test_scanner_allows_redacted_placeholder() -> None:
    sample = "api_key = " + '"[REDACTED]"'
    assert scan_text(sample) == []


def test_scanner_detects_private_key_header() -> None:
    sample = "-----BEGIN " + "PRIVATE KEY-----\nnot-real-key-material"
    assert "private-key material" in scan_text(sample)
