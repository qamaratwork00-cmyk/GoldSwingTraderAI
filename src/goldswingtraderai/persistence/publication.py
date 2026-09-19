"""Public-safe staging for verified runtime backup publication.

This module prepares an immutable publication directory. It never authenticates
to GitHub and never stores a PAT, broker secret or cloud credential; an operator
or external CI job performs the final explicit ``git add/commit/push`` step.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
from uuid import uuid4

from goldswingtraderai.persistence.backup import (
    BACKUP_CATALOG_FILENAME,
    CHECKPOINTS_DIRECTORY,
    BackupCatalogError,
    load_backup_catalog,
    latest_verified_checkpoint,
)
from goldswingtraderai.persistence.checkpoint import import_runtime_checkpoint
from goldswingtraderai.security.financial_secrets import scan_text_for_financial_secrets


PUBLICATION_SCHEMA_VERSION = 1
PUBLICATION_MANIFEST_FILENAME = "publication_manifest.json"


class PublicationError(RuntimeError):
    """Public-backup verification or destination-layout failure."""


@dataclass(frozen=True, slots=True)
class PublicBackupPublication:
    destination: Path
    checkpoint_name: str
    checkpoint_sha256: str
    catalog_sha256: str
    manifest_path: Path


def stage_verified_public_backup(
    backup_root: str | Path,
    destination: str | Path,
    *,
    published_at_utc: datetime | None = None,
) -> PublicBackupPublication:
    """Stage the latest verified checkpoint into a new public-safe directory.

    The destination must not already exist. Versioned destinations make
    publication review/retry recoverable and avoid silently overwriting a
    previously published artifact.
    """

    published_at = published_at_utc or datetime.now(timezone.utc)
    _require_utc(published_at)
    root = Path(backup_root)
    destination_path = Path(destination)
    if destination_path.exists() or destination_path.is_symlink():
        raise PublicationError(f"publication destination already exists: {destination_path}")

    try:
        catalog = load_backup_catalog(root, verify_checkpoints=True)
        checkpoint = latest_verified_checkpoint(root)
    except (BackupCatalogError, FileNotFoundError, OSError) as exc:
        raise PublicationError("verified backup catalog/checkpoint is unavailable") from exc
    if checkpoint is None or not catalog.entries:
        raise PublicationError("backup catalog has no verified checkpoint")
    entry = catalog.entries[-1]
    if checkpoint.name != entry.name:
        raise PublicationError("latest checkpoint does not match catalog ordering")

    imported = import_runtime_checkpoint(checkpoint)
    if imported.manifest.checkpoint_sha256 != entry.checkpoint_sha256:
        raise PublicationError("checkpoint identity changed during publication staging")

    staging = destination_path.parent / f".{destination_path.name}.pending-{uuid4().hex}"
    try:
        staging.mkdir(parents=True, exist_ok=False)
        _copy_public_file(root / BACKUP_CATALOG_FILENAME, staging / BACKUP_CATALOG_FILENAME)
        checkpoint_destination = staging / CHECKPOINTS_DIRECTORY / checkpoint.name
        shutil.copytree(checkpoint, checkpoint_destination, symlinks=False)
        _scan_tree_for_secrets(staging)

        manifest_payload = {
            "schema_version": PUBLICATION_SCHEMA_VERSION,
            "published_at_utc": published_at.isoformat(),
            "artifact_type": "GOLD_SWING_TRADER_AI_PUBLIC_RUNTIME_BACKUP",
            "checkpoint_name": entry.name,
            "checkpoint_sha256": entry.checkpoint_sha256,
            "catalog_sha256": catalog.catalog_sha256,
            "records_count": entry.records_count,
            "events_count": entry.events_count,
            "secret_scan": "PASS",
        }
        manifest_text = _canonical_json(manifest_payload) + "\n"
        _scan_text(manifest_text, "publication manifest")
        (staging / PUBLICATION_MANIFEST_FILENAME).write_text(
            manifest_text,
            encoding="utf-8",
        )
        os.replace(staging, destination_path)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    return PublicBackupPublication(
        destination=destination_path,
        checkpoint_name=entry.name,
        checkpoint_sha256=entry.checkpoint_sha256,
        catalog_sha256=catalog.catalog_sha256,
        manifest_path=destination_path / PUBLICATION_MANIFEST_FILENAME,
    )


def _copy_public_file(source: Path, destination: Path) -> None:
    if source.is_symlink() or not source.is_file():
        raise PublicationError(f"public backup source is not a regular file: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def _scan_tree_for_secrets(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if path.is_symlink() or not path.is_file():
            raise PublicationError(f"public backup contains an invalid path: {path}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise PublicationError(f"public backup contains non-text artifact: {path}") from exc
        _scan_text(text, str(path.relative_to(root)))


def _scan_text(text: str, label: str) -> None:
    findings = scan_text_for_financial_secrets(text)
    if findings:
        raise PublicationError(f"financial secret detected in {label}: {findings[0]}")


def _canonical_json(value: dict[str, object]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("publication timestamp must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("publication timestamp must be UTC")
