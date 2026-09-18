"""Verified local checkpoint cadence, retention and catalog management.

Remote publication is intentionally outside this module because authenticated
GitHub/cloud credentials must remain external to repository/runtime checkpoint
state. This owner manages only local public-safe checkpoint artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
from typing import Any
from uuid import uuid4

from goldswingtraderai.persistence.checkpoint import (
    RuntimeCheckpointError,
    export_runtime_checkpoint,
    import_runtime_checkpoint,
)
from goldswingtraderai.persistence.store import StateStore
from goldswingtraderai.security.financial_secrets import scan_text_for_financial_secrets


BACKUP_CATALOG_SCHEMA_VERSION = 1
BACKUP_CATALOG_FILENAME = "backup_catalog.json"
CHECKPOINTS_DIRECTORY = "checkpoints"


class BackupCatalogError(RuntimeError):
    """Backup catalog integrity or layout failure."""


class BackupRunStatus(StrEnum):
    CREATED = "CREATED"
    SKIPPED_NOT_DUE = "SKIPPED_NOT_DUE"


@dataclass(frozen=True, slots=True)
class BackupPolicy:
    interval_minutes: int = 15
    keep_latest: int = 96

    def __post_init__(self) -> None:
        if self.interval_minutes <= 0:
            raise ValueError("backup interval must be positive minutes")
        if self.keep_latest <= 0:
            raise ValueError("backup retention count must be positive")


@dataclass(frozen=True, slots=True)
class BackupCatalogEntry:
    name: str
    created_at_utc: datetime
    checkpoint_sha256: str
    records_count: int
    events_count: int


@dataclass(frozen=True, slots=True)
class BackupCatalog:
    schema_version: int
    updated_at_utc: datetime
    entries: tuple[BackupCatalogEntry, ...]
    catalog_sha256: str


@dataclass(frozen=True, slots=True)
class BackupRunResult:
    status: BackupRunStatus
    entry: BackupCatalogEntry | None
    catalog: BackupCatalog


def create_backup_if_due(
    store: StateStore,
    root: str | Path,
    *,
    source_label: str,
    source_version: str,
    policy: BackupPolicy | None = None,
    now_utc: datetime | None = None,
) -> BackupRunResult:
    """Create, verify, catalog and retain one checkpoint when cadence is due."""

    cfg = policy or BackupPolicy()
    now = now_utc or datetime.now(timezone.utc)
    _require_utc(now)
    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    checkpoints_root = root_path / CHECKPOINTS_DIRECTORY
    checkpoints_root.mkdir(parents=True, exist_ok=True)

    current = _load_catalog_optional(root_path, verify_checkpoints=True)
    if current.entries:
        due_at = current.entries[-1].created_at_utc + timedelta(minutes=cfg.interval_minutes)
        if now < due_at:
            return BackupRunResult(BackupRunStatus.SKIPPED_NOT_DUE, None, current)

    staging = checkpoints_root / f".pending-{uuid4().hex}"
    try:
        exported = export_runtime_checkpoint(
            store,
            staging,
            source_label=source_label,
            source_version=source_version,
            created_at_utc=now,
        )
        verified = import_runtime_checkpoint(staging)
        if verified.manifest.checkpoint_sha256 != exported.checkpoint_sha256:
            raise BackupCatalogError("new checkpoint identity verification failed")

        name = f"runtime-{now.strftime('%Y%m%dT%H%M%SZ')}-{exported.checkpoint_sha256[:12]}"
        _validate_entry_name(name)
        final_path = checkpoints_root / name
        if final_path.exists() or final_path.is_symlink():
            raise FileExistsError(f"verified backup destination already exists: {final_path}")
        os.replace(staging, final_path)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    entry = BackupCatalogEntry(
        name=name,
        created_at_utc=now,
        checkpoint_sha256=exported.checkpoint_sha256,
        records_count=exported.records_count,
        events_count=exported.events_count,
    )
    all_entries = tuple(sorted((*current.entries, entry), key=lambda item: item.created_at_utc))
    kept = all_entries[-cfg.keep_latest :]

    # Publish the new known-good catalog before pruning. A crash can therefore
    # leave only harmless unreferenced old directories, never a catalog that
    # points at a backup deliberately deleted first.
    catalog = _write_catalog(root_path, kept, updated_at_utc=now)
    keep_names = {item.name for item in kept}
    for old in all_entries:
        if old.name not in keep_names:
            shutil.rmtree(checkpoints_root / old.name, ignore_errors=True)

    return BackupRunResult(BackupRunStatus.CREATED, entry, catalog)


def load_backup_catalog(root: str | Path, *, verify_checkpoints: bool = True) -> BackupCatalog:
    root_path = Path(root)
    if not (root_path / BACKUP_CATALOG_FILENAME).exists():
        raise FileNotFoundError(f"backup catalog does not exist: {root_path}")
    return _load_catalog_optional(root_path, verify_checkpoints=verify_checkpoints)


def latest_verified_checkpoint(root: str | Path) -> Path | None:
    root_path = Path(root)
    if not (root_path / BACKUP_CATALOG_FILENAME).exists():
        return None
    catalog = _load_catalog_optional(root_path, verify_checkpoints=True)
    if not catalog.entries:
        return None
    return root_path / CHECKPOINTS_DIRECTORY / catalog.entries[-1].name


def _load_catalog_optional(root: Path, *, verify_checkpoints: bool) -> BackupCatalog:
    path = root / BACKUP_CATALOG_FILENAME
    if not path.exists():
        return _empty_catalog()
    if path.is_symlink() or not path.is_file():
        raise BackupCatalogError("backup catalog must be a regular file")

    text = path.read_text(encoding="utf-8")
    _reject_financial_secrets(text)
    raw = _load_object(text)
    expected_hash = _hash_payload({key: value for key, value in raw.items() if key != "catalog_sha256"})

    try:
        schema = int(raw["schema_version"])
        if schema != BACKUP_CATALOG_SCHEMA_VERSION:
            raise BackupCatalogError("unsupported backup catalog schema version")
        entries_raw = raw["entries"]
        if not isinstance(entries_raw, list):
            raise BackupCatalogError("backup catalog entries must be a list")
        entries = tuple(_parse_entry(item) for item in entries_raw)
        catalog = BackupCatalog(
            schema_version=schema,
            updated_at_utc=_parse_utc(str(raw["updated_at_utc"])),
            entries=entries,
            catalog_sha256=_require_sha256(str(raw["catalog_sha256"]), "catalog hash"),
        )
    except KeyError as exc:
        raise BackupCatalogError("backup catalog is missing required fields") from exc

    if catalog.catalog_sha256 != expected_hash:
        raise BackupCatalogError("backup catalog hash mismatch")
    if entries != tuple(sorted(entries, key=lambda item: item.created_at_utc)):
        raise BackupCatalogError("backup catalog entries must be chronological")
    if len({item.name for item in entries}) != len(entries):
        raise BackupCatalogError("backup catalog contains duplicate checkpoint names")

    if verify_checkpoints:
        checkpoints_root = root / CHECKPOINTS_DIRECTORY
        for entry in entries:
            try:
                imported = import_runtime_checkpoint(checkpoints_root / entry.name)
            except (RuntimeCheckpointError, FileNotFoundError, OSError) as exc:
                raise BackupCatalogError(f"invalid catalogued checkpoint: {entry.name}") from exc
            if imported.manifest.checkpoint_sha256 != entry.checkpoint_sha256:
                raise BackupCatalogError(f"catalog checkpoint hash mismatch: {entry.name}")
            if len(imported.snapshot.records) != entry.records_count:
                raise BackupCatalogError(f"catalog record count mismatch: {entry.name}")
            if len(imported.snapshot.events) != entry.events_count:
                raise BackupCatalogError(f"catalog event count mismatch: {entry.name}")
    return catalog


def _write_catalog(
    root: Path,
    entries: tuple[BackupCatalogEntry, ...],
    *,
    updated_at_utc: datetime,
) -> BackupCatalog:
    _require_utc(updated_at_utc)
    base = {
        "schema_version": BACKUP_CATALOG_SCHEMA_VERSION,
        "updated_at_utc": updated_at_utc.isoformat(),
        "entries": [_entry_payload(item) for item in entries],
    }
    digest = _hash_payload(base)
    text = _canonical_json({**base, "catalog_sha256": digest}) + "\n"
    _reject_financial_secrets(text)

    destination = root / BACKUP_CATALOG_FILENAME
    temporary = root / f".{BACKUP_CATALOG_FILENAME}.tmp-{uuid4().hex}"
    try:
        temporary.write_text(text, encoding="utf-8")
        os.replace(temporary, destination)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    return BackupCatalog(
        schema_version=BACKUP_CATALOG_SCHEMA_VERSION,
        updated_at_utc=updated_at_utc,
        entries=entries,
        catalog_sha256=digest,
    )


def _empty_catalog() -> BackupCatalog:
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    base = {
        "schema_version": BACKUP_CATALOG_SCHEMA_VERSION,
        "updated_at_utc": epoch.isoformat(),
        "entries": [],
    }
    return BackupCatalog(
        schema_version=BACKUP_CATALOG_SCHEMA_VERSION,
        updated_at_utc=epoch,
        entries=(),
        catalog_sha256=_hash_payload(base),
    )


def _parse_entry(value: Any) -> BackupCatalogEntry:
    if not isinstance(value, dict):
        raise BackupCatalogError("backup catalog entry must be an object")
    try:
        name = str(value["name"])
        _validate_entry_name(name)
        entry = BackupCatalogEntry(
            name=name,
            created_at_utc=_parse_utc(str(value["created_at_utc"])),
            checkpoint_sha256=_require_sha256(str(value["checkpoint_sha256"]), "checkpoint hash"),
            records_count=int(value["records_count"]),
            events_count=int(value["events_count"]),
        )
    except KeyError as exc:
        raise BackupCatalogError("backup catalog entry is missing fields") from exc
    if entry.records_count < 0 or entry.events_count < 0:
        raise BackupCatalogError("backup catalog counts cannot be negative")
    return entry


def _entry_payload(entry: BackupCatalogEntry) -> dict[str, Any]:
    return {
        "name": entry.name,
        "created_at_utc": entry.created_at_utc.isoformat(),
        "checkpoint_sha256": entry.checkpoint_sha256,
        "records_count": entry.records_count,
        "events_count": entry.events_count,
    }


def _load_object(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise BackupCatalogError("backup catalog contains invalid JSON") from exc
    if not isinstance(value, dict):
        raise BackupCatalogError("backup catalog must be a JSON object")
    return value


def _validate_entry_name(name: str) -> None:
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise BackupCatalogError("invalid backup checkpoint name")
    if Path(name).name != name:
        raise BackupCatalogError("backup checkpoint name must be a basename")


def _parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise BackupCatalogError("invalid backup catalog UTC timestamp") from exc
    _require_utc(parsed)
    return parsed


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise BackupCatalogError("backup timestamps must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise BackupCatalogError("backup timestamps must be UTC")


def _require_sha256(value: str, label: str) -> str:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise BackupCatalogError(f"{label} must be lowercase SHA-256 hex")
    return value


def _reject_financial_secrets(text: str) -> None:
    if scan_text_for_financial_secrets(text):
        raise BackupCatalogError("FINANCIAL_SECRET_DETECTED in backup catalog")


def _hash_payload(payload: dict[str, Any]) -> str:
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _canonical_json(payload: dict[str, Any]) -> str:
    try:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise BackupCatalogError("backup catalog is not canonical JSON compatible") from exc
