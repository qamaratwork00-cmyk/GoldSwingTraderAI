"""Immutable, integrity-checked packages for reproducible research evidence.

The package persists one canonical ResearchEvidenceManifest without copying a large
historical dataset. Dataset binding is content-addressed through dataset_sha256 and,
when supplied, the verified portable dataset bundle manifest SHA-256.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

from goldswingtraderai.research.datasets import import_replay_dataset_bundle
from goldswingtraderai.research.evidence import (
    ResearchEvidenceManifest,
    canonical_manifest_json,
)


EVIDENCE_PACKAGE_SCHEMA_VERSION = 1
_PACKAGE_MANIFEST = "package_manifest.json"
_EVIDENCE_MANIFEST = "evidence_manifest.json"


class EvidencePackageError(RuntimeError):
    """Base evidence-package error."""


class EvidencePackageIntegrityError(EvidencePackageError):
    """Package bytes or identities do not match declared hashes."""


class EvidencePackageVersionError(EvidencePackageError):
    """Package schema is unsupported."""


@dataclass(frozen=True, slots=True)
class ExportedEvidencePackage:
    path: Path
    package_sha256: str
    evidence_manifest_sha256: str
    dataset_sha256: str
    dataset_bundle_manifest_sha256: str | None


@dataclass(frozen=True, slots=True)
class ImportedEvidencePackage:
    path: Path
    package_sha256: str
    evidence_payload: dict[str, Any]
    evidence_manifest_sha256: str
    input_fingerprint_sha256: str
    dataset_sha256: str
    dataset_bundle_manifest_sha256: str | None


def export_research_evidence_package(
    evidence: ResearchEvidenceManifest,
    destination: str | Path,
    *,
    dataset_bundle: str | Path | None = None,
) -> ExportedEvidencePackage:
    """Persist one evidence record in a write-new integrity-checked directory."""

    target = Path(destination)
    if target.exists():
        raise FileExistsError(f"evidence package destination already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)

    bundle_manifest_hash: str | None = None
    if dataset_bundle is not None:
        verified = import_replay_dataset_bundle(dataset_bundle)
        if verified.dataset_sha256 != evidence.dataset.dataset_sha256:
            raise EvidencePackageIntegrityError(
                "dataset bundle identity does not match evidence dataset"
            )
        bundle_manifest_hash = verified.manifest_sha256

    temporary = Path(
        tempfile.mkdtemp(prefix=f".{target.name}.tmp-", dir=str(target.parent))
    )
    try:
        evidence_path = temporary / _EVIDENCE_MANIFEST
        evidence_path.write_text(
            canonical_manifest_json(evidence) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        evidence_file_hash = _file_sha256(evidence_path)
        payload = {
            "schema_version": EVIDENCE_PACKAGE_SCHEMA_VERSION,
            "evidence_file": _EVIDENCE_MANIFEST,
            "evidence_file_sha256": evidence_file_hash,
            "evidence_manifest_sha256": evidence.manifest_sha256,
            "input_fingerprint_sha256": evidence.input_fingerprint_sha256,
            "dataset_sha256": evidence.dataset.dataset_sha256,
            "dataset_bundle_manifest_sha256": bundle_manifest_hash,
        }
        package_hash = _payload_sha256(payload)
        package_manifest = {**payload, "package_sha256": package_hash}
        (temporary / _PACKAGE_MANIFEST).write_text(
            _canonical_json(package_manifest) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        temporary.rename(target)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    return ExportedEvidencePackage(
        path=target,
        package_sha256=package_hash,
        evidence_manifest_sha256=evidence.manifest_sha256,
        dataset_sha256=evidence.dataset.dataset_sha256,
        dataset_bundle_manifest_sha256=bundle_manifest_hash,
    )


def import_research_evidence_package(
    source: str | Path,
    *,
    dataset_bundle: str | Path | None = None,
) -> ImportedEvidencePackage:
    """Verify a package and optional external dataset bundle before returning evidence."""

    root = Path(source)
    package_path = root / _PACKAGE_MANIFEST
    evidence_path = root / _EVIDENCE_MANIFEST
    if not root.is_dir():
        raise EvidencePackageError("evidence package directory is missing")
    if (
        not package_path.is_file()
        or package_path.is_symlink()
        or not evidence_path.is_file()
        or evidence_path.is_symlink()
    ):
        raise EvidencePackageIntegrityError("evidence package files are missing or unsafe")

    package = _read_json_object(package_path, "package manifest")
    if package.get("schema_version") != EVIDENCE_PACKAGE_SCHEMA_VERSION:
        raise EvidencePackageVersionError(
            f"unsupported evidence package schema: {package.get('schema_version')!r}"
        )
    claimed_package_hash = _required_sha256(package.get("package_sha256"), "package_sha256")
    package_payload = dict(package)
    package_payload.pop("package_sha256", None)
    if _payload_sha256(package_payload) != claimed_package_hash:
        raise EvidencePackageIntegrityError("evidence package manifest checksum mismatch")
    if package.get("evidence_file") != _EVIDENCE_MANIFEST:
        raise EvidencePackageIntegrityError("evidence package filename is not canonical")
    claimed_evidence_file_hash = _required_sha256(
        package.get("evidence_file_sha256"),
        "evidence_file_sha256",
    )
    if _file_sha256(evidence_path) != claimed_evidence_file_hash:
        raise EvidencePackageIntegrityError("evidence manifest file checksum mismatch")

    evidence = _read_json_object(evidence_path, "evidence manifest")
    _verify_evidence_payload(evidence, package)

    package_bundle_hash = package.get("dataset_bundle_manifest_sha256")
    if package_bundle_hash is not None:
        package_bundle_hash = _required_sha256(
            package_bundle_hash,
            "dataset_bundle_manifest_sha256",
        )
    if dataset_bundle is not None:
        verified = import_replay_dataset_bundle(dataset_bundle)
        if verified.dataset_sha256 != package["dataset_sha256"]:
            raise EvidencePackageIntegrityError(
                "supplied dataset bundle does not match evidence package dataset"
            )
        if (
            package_bundle_hash is not None
            and verified.manifest_sha256 != package_bundle_hash
        ):
            raise EvidencePackageIntegrityError(
                "supplied dataset bundle manifest does not match evidence package"
            )

    return ImportedEvidencePackage(
        path=root,
        package_sha256=claimed_package_hash,
        evidence_payload=evidence,
        evidence_manifest_sha256=str(package["evidence_manifest_sha256"]),
        input_fingerprint_sha256=str(package["input_fingerprint_sha256"]),
        dataset_sha256=str(package["dataset_sha256"]),
        dataset_bundle_manifest_sha256=package_bundle_hash,
    )


def _verify_evidence_payload(evidence: dict[str, Any], package: dict[str, Any]) -> None:
    claimed_manifest_hash = _required_sha256(
        evidence.get("manifest_sha256"),
        "evidence.manifest_sha256",
    )
    manifest_payload = dict(evidence)
    manifest_payload.pop("manifest_sha256", None)
    if _payload_sha256(manifest_payload) != claimed_manifest_hash:
        raise EvidencePackageIntegrityError("evidence manifest internal checksum mismatch")

    input_payload = {
        key: evidence.get(key)
        for key in (
            "schema_version",
            "evidence_kind",
            "code_revision",
            "policy_version",
            "dataset",
            "configuration",
        )
    }
    claimed_input_hash = _required_sha256(
        evidence.get("input_fingerprint_sha256"),
        "evidence.input_fingerprint_sha256",
    )
    if _payload_sha256(input_payload) != claimed_input_hash:
        raise EvidencePackageIntegrityError("evidence input fingerprint mismatch")

    dataset = evidence.get("dataset")
    if not isinstance(dataset, dict):
        raise EvidencePackageIntegrityError("evidence dataset identity is missing")
    evidence_dataset_hash = _required_sha256(
        dataset.get("dataset_sha256"),
        "evidence.dataset.dataset_sha256",
    )
    for field, actual in (
        ("evidence_manifest_sha256", claimed_manifest_hash),
        ("input_fingerprint_sha256", claimed_input_hash),
        ("dataset_sha256", evidence_dataset_hash),
    ):
        expected = _required_sha256(package.get(field), field)
        if actual != expected:
            raise EvidencePackageIntegrityError(f"evidence/package identity mismatch: {field}")


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidencePackageIntegrityError(f"{label} is unreadable/invalid JSON") from exc
    if not isinstance(value, dict):
        raise EvidencePackageIntegrityError(f"{label} must be a JSON object")
    return value


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _payload_sha256(payload: Any) -> str:
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _required_sha256(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise EvidencePackageIntegrityError(f"missing SHA-256 field: {name}")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise EvidencePackageIntegrityError(f"invalid SHA-256 field: {name}")
    return value
