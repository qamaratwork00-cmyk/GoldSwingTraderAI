from __future__ import annotations

from scripts.scan_financial_secrets import scan_text


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
