"""Portable public-safe runtime checkpoints for fresh-machine recovery.

A checkpoint is recovery context, not broker truth. It serializes the StateStore's
current records and append-only event history into canonical text files with strong
integrity checks. Financial-authority secrets are rejected before export and again
on import. Restore writes only to a new database; broker reconciliation remains
mandatory before trading authority can become READY.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
from typing import Any
from uuid import uuid4

from goldswingtraderai.persistence.store import (
    DATABASE_SCHEMA_VERSION,
    StateStore,
    StoreSnapshot,
    StoredEvent,
    StoredRecord,
)
from goldswingtraderai.security.financial_secrets import (
    scan_payload_for_financial_secrets,
    scan_text_for_financial_secrets,
)


RUNTIME_CHECKPOINT_SCHEMA_VERSION = 1
CHECKPOINT_MANIFEST_FILENAME = "checkpoint_manifest.json"
RECORDS_FILENAME = "records.jsonl"
EVENTS_FILENAME = "events.jsonl"
_ALLOWED_FILES = {CHECKPOINT_MANIFEST_FILENAME, RECORDS_FILENAME, EVENTS_FILENAME}


class RuntimeCheckpointError(RuntimeError):
    """Portable checkpoint integrity/safety failure."""


@dataclass(frozen=True, slots=True)
class RuntimeCheckpointManifest:
    schema_version: int
    database_schema_version: int
    source_label: str
    source_version: str
    created_at_utc: datetime
    records_file: str
    records_sha256: str
    records_count: int
    events_file: str
    events_sha256: str
    events_count: int
    checkpoint_sha256: str


@dataclass(frozen=True, slots=True)
class ExportedRuntimeCheckpoint:
    path: Path
    checkpoint_sha256: str
    records_count: int
    events_count: int


@dataclass(frozen=True, slots=True)
class ImportedRuntimeCheckpoint:
    path: Path
    manifest: RuntimeCheckpointManifest
    snapshot: StoreSnapshot


@dataclass(frozen=True, slots=True)
class RestoredRuntimeCheckpoint:
    database_path: Path
    checkpoint_sha256: str
    records_count: int
    events_count: int
    broker_reconciliation_required: bool = True


def export_runtime_checkpoint(
    store: StateStore,
    destination: str | Path,
    *,
    source_label: str,
    source_version: str,
    created_at_utc: datetime | None = None,
) -> ExportedRuntimeCheckpoint:
    """Export one immutable, integrity-checked, public-safe runtime checkpoint."""

    label = _required_text(source_label, "checkpoint source label")
    version = _required_text(source_version, "checkpoint source version")
    created = created_at_utc or datetime.now(timezone.utc)
    _require_utc(created)

    destination_path = Path(destination)
    if destination_path.exists() or destination_path.is_symlink():
        raise FileExistsError(f"checkpoint destination already exists: {destination_path}")
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    snapshot = store.export_snapshot()
    _reject_snapshot_secrets(snapshot)
    records_text = _jsonl(_record_payload(record) for record in snapshot.records)
    events_text = _jsonl(_event_payload(event) for event in snapshot.events)

    _reject_financial_secrets(records_text, "runtime checkpoint records")
    _reject_financial_secrets(events_text, "runtime checkpoint events")

    temp_path = destination_path.parent / f".{destination_path.name}.tmp-{uuid4().hex}"
    try:
        temp_path.mkdir(parents=False, exist_ok=False)
        records_path = temp_path / RECORDS_FILENAME
        events_path = temp_path / EVENTS_FILENAME
        records_path.write_text(records_text, encoding="utf-8")
        events_path.write_text(events_text, encoding="utf-8")

        base_manifest = {
            "schema_version": RUNTIME_CHECKPOINT_SCHEMA_VERSION,
            "database_schema_version": snapshot.database_schema_version,
            "source_label": label,
            "source_version": version,
            "created_at_utc": created.isoformat(),
            "records_file": RECORDS_FILENAME,
            "records_sha256": _hash_text(records_text),
            "records_count": len(snapshot.records),
            "events_file": EVENTS_FILENAME,
            "events_sha256": _hash_text(events_text),
            "events_count": len(snapshot.events),
        }
        checkpoint_hash = _hash_payload(base_manifest)
        manifest_payload = {**base_manifest, "checkpoint_sha256": checkpoint_hash}
        manifest_text = _canonical_json(manifest_payload) + "\n"
        _reject_financial_secrets(manifest_text, "runtime checkpoint manifest")
        (temp_path / CHECKPOINT_MANIFEST_FILENAME).write_text(manifest_text, encoding="utf-8")

        os.replace(temp_path, destination_path)
    except Exception:
        shutil.rmtree(temp_path, ignore_errors=True)
        raise

    return ExportedRuntimeCheckpoint(
        path=destination_path,
        checkpoint_sha256=checkpoint_hash,
        records_count=len(snapshot.records),
        events_count=len(snapshot.events),
    )


def import_runtime_checkpoint(path: str | Path) -> ImportedRuntimeCheckpoint:
    """Verify and parse one portable runtime checkpoint without mutating a database."""

    root = Path(path)
    if root.is_symlink() or not root.is_dir():
        raise RuntimeCheckpointError("runtime checkpoint must be a real directory")
    names = {item.name for item in root.iterdir()}
    if names != _ALLOWED_FILES:
        raise RuntimeCheckpointError("runtime checkpoint contains missing or unexpected files")

    manifest_path = root / CHECKPOINT_MANIFEST_FILENAME
    records_path = root / RECORDS_FILENAME
    events_path = root / EVENTS_FILENAME
    for file_path in (manifest_path, records_path, events_path):
        if file_path.is_symlink() or not file_path.is_file():
            raise RuntimeCheckpointError(f"checkpoint file must be a regular file: {file_path.name}")

    manifest_text = manifest_path.read_text(encoding="utf-8")
    records_text = records_path.read_text(encoding="utf-8")
    events_text = events_path.read_text(encoding="utf-8")
    _reject_financial_secrets(manifest_text, "runtime checkpoint manifest")
    _reject_financial_secrets(records_text, "runtime checkpoint records")
    _reject_financial_secrets(events_text, "runtime checkpoint events")

    raw_manifest = _load_object(manifest_text, "checkpoint manifest")
    manifest = _parse_manifest(raw_manifest)
    expected_checkpoint_hash = _hash_payload(
        {key: value for key, value in raw_manifest.items() if key != "checkpoint_sha256"}
    )
    if expected_checkpoint_hash != manifest.checkpoint_sha256:
        raise RuntimeCheckpointError("runtime checkpoint manifest hash mismatch")
    if manifest.records_file != RECORDS_FILENAME or manifest.events_file != EVENTS_FILENAME:
        raise RuntimeCheckpointError("runtime checkpoint uses non-canonical data filenames")
    if _hash_text(records_text) != manifest.records_sha256:
        raise RuntimeCheckpointError("runtime checkpoint records hash mismatch")
    if _hash_text(events_text) != manifest.events_sha256:
        raise RuntimeCheckpointError("runtime checkpoint events hash mismatch")

    records = tuple(_parse_record(item) for item in _parse_jsonl(records_text, "records"))
    events = tuple(_parse_event(item) for item in _parse_jsonl(events_text, "events"))
    if len(records) != manifest.records_count:
        raise RuntimeCheckpointError("runtime checkpoint record count mismatch")
    if len(events) != manifest.events_count:
        raise RuntimeCheckpointError("runtime checkpoint event count mismatch")

    snapshot = StoreSnapshot(
        database_schema_version=manifest.database_schema_version,
        records=records,
        events=events,
    )
    _validate_snapshot_payloads(snapshot)
    _reject_snapshot_secrets(snapshot)
    return ImportedRuntimeCheckpoint(path=root, manifest=manifest, snapshot=snapshot)


def restore_runtime_checkpoint(
    checkpoint_path: str | Path,
    destination_database: str | Path,
) -> RestoredRuntimeCheckpoint:
    """Restore a verified checkpoint into a new SQLite database atomically."""

    imported = import_runtime_checkpoint(checkpoint_path)
    destination = Path(destination_database)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"restore destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    _reject_existing_sidecars(destination)

    temp_database = destination.parent / f".{destination.name}.restore-{uuid4().hex}"
    try:
        store = StateStore(temp_database)
        store.restore_snapshot(imported.snapshot)
        store.checkpoint_database()
        store.integrity_check()
        _remove_sidecars(temp_database)
        os.replace(temp_database, destination)
        restored = StateStore(destination)
        restored.integrity_check()
    except Exception:
        _remove_database_family(temp_database)
        raise

    return RestoredRuntimeCheckpoint(
        database_path=destination,
        checkpoint_sha256=imported.manifest.checkpoint_sha256,
        records_count=len(imported.snapshot.records),
        events_count=len(imported.snapshot.events),
        broker_reconciliation_required=True,
    )


def _record_payload(record: StoredRecord) -> dict[str, Any]:
    return {
        "namespace": record.namespace,
        "key": record.key,
        "schema_version": record.schema_version,
        "payload": record.payload,
        "checksum": record.checksum,
        "updated_at_utc": record.updated_at_utc.isoformat(),
    }


def _event_payload(event: StoredEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "namespace": event.namespace,
        "key": event.key,
        "event_type": event.event_type,
        "payload": event.payload,
        "checksum": event.checksum,
        "created_at_utc": event.created_at_utc.isoformat(),
    }


def _parse_record(payload: dict[str, Any]) -> StoredRecord:
    try:
        return StoredRecord(
            namespace=_required_text(str(payload["namespace"]), "record namespace"),
            key=_required_text(str(payload["key"]), "record key"),
            schema_version=int(payload["schema_version"]),
            payload=_required_object(payload["payload"], "record payload"),
            checksum=_require_sha256(str(payload["checksum"]), "record checksum"),
            updated_at_utc=_parse_utc(str(payload["updated_at_utc"]), "record timestamp"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeCheckpointError("invalid runtime checkpoint record") from exc


def _parse_event(payload: dict[str, Any]) -> StoredEvent:
    try:
        return StoredEvent(
            event_id=int(payload["event_id"]),
            namespace=_required_text(str(payload["namespace"]), "event namespace"),
            key=_required_text(str(payload["key"]), "event key"),
            event_type=_required_text(str(payload["event_type"]), "event type"),
            payload=_required_object(payload["payload"], "event payload"),
            checksum=_require_sha256(str(payload["checksum"]), "event checksum"),
            created_at_utc=_parse_utc(str(payload["created_at_utc"]), "event timestamp"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeCheckpointError("invalid runtime checkpoint event") from exc


def _parse_manifest(payload: dict[str, Any]) -> RuntimeCheckpointManifest:
    try:
        schema_version = int(payload["schema_version"])
        database_schema_version = int(payload["database_schema_version"])
        if schema_version != RUNTIME_CHECKPOINT_SCHEMA_VERSION:
            raise RuntimeCheckpointError("unsupported runtime checkpoint schema version")
        if database_schema_version != DATABASE_SCHEMA_VERSION:
            raise RuntimeCheckpointError("unsupported checkpoint database schema version")
        manifest = RuntimeCheckpointManifest(
            schema_version=schema_version,
            database_schema_version=database_schema_version,
            source_label=_required_text(str(payload["source_label"]), "source label"),
            source_version=_required_text(str(payload["source_version"]), "source version"),
            created_at_utc=_parse_utc(str(payload["created_at_utc"]), "checkpoint timestamp"),
            records_file=str(payload["records_file"]),
            records_sha256=_require_sha256(str(payload["records_sha256"]), "records hash"),
            records_count=int(payload["records_count"]),
            events_file=str(payload["events_file"]),
            events_sha256=_require_sha256(str(payload["events_sha256"]), "events hash"),
            events_count=int(payload["events_count"]),
            checkpoint_sha256=_require_sha256(
                str(payload["checkpoint_sha256"]), "checkpoint hash"
            ),
        )
    except KeyError as exc:
        raise RuntimeCheckpointError("runtime checkpoint manifest is missing fields") from exc
    except (TypeError, ValueError) as exc:
        raise RuntimeCheckpointError("invalid runtime checkpoint manifest") from exc
    if manifest.records_count < 0 or manifest.events_count < 0:
        raise RuntimeCheckpointError("runtime checkpoint counts cannot be negative")
    return manifest


def _validate_snapshot_payloads(snapshot: StoreSnapshot) -> None:
    record_keys: set[tuple[str, str]] = set()
    for record in snapshot.records:
        identity = (record.namespace, record.key)
        if identity in record_keys:
            raise RuntimeCheckpointError("duplicate runtime checkpoint record identity")
        record_keys.add(identity)
        if record.schema_version <= 0:
            raise RuntimeCheckpointError("runtime checkpoint record schema must be positive")
        if _hash_text(_canonical_json(record.payload)) != record.checksum:
            raise RuntimeCheckpointError("runtime checkpoint record checksum mismatch")

    previous_event_id = 0
    seen_event_ids: set[int] = set()
    for event in snapshot.events:
        if event.event_id in seen_event_ids or event.event_id <= previous_event_id:
            raise RuntimeCheckpointError("runtime checkpoint event ids are not chronological")
        seen_event_ids.add(event.event_id)
        previous_event_id = event.event_id
        if _hash_text(_canonical_json(event.payload)) != event.checksum:
            raise RuntimeCheckpointError("runtime checkpoint event checksum mismatch")


def _reject_snapshot_secrets(snapshot: StoreSnapshot) -> None:
    for record in snapshot.records:
        findings = scan_payload_for_financial_secrets(
            record.payload,
            path=f"record[{record.namespace}/{record.key}]",
        )
        if findings:
            raise RuntimeCheckpointError(
                "FINANCIAL_SECRET_DETECTED in runtime checkpoint record payload"
            )
    for event in snapshot.events:
        findings = scan_payload_for_financial_secrets(
            event.payload,
            path=f"event[{event.namespace}/{event.key}#{event.event_id}]",
        )
        if findings:
            raise RuntimeCheckpointError(
                "FINANCIAL_SECRET_DETECTED in runtime checkpoint event payload"
            )


def _parse_jsonl(text: str, label: str) -> tuple[dict[str, Any], ...]:
    if not text:
        return ()
    items: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            raise RuntimeCheckpointError(f"blank line in checkpoint {label} at {line_number}")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeCheckpointError(
                f"invalid JSON in checkpoint {label} at line {line_number}"
            ) from exc
        if not isinstance(value, dict):
            raise RuntimeCheckpointError(
                f"checkpoint {label} line {line_number} must be an object"
            )
        items.append(value)
    return tuple(items)


def _jsonl(items) -> str:
    lines = [_canonical_json(item) for item in items]
    return "" if not lines else "\n".join(lines) + "\n"


def _load_object(text: str, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeCheckpointError(f"invalid JSON in {label}") from exc
    if not isinstance(payload, dict):
        raise RuntimeCheckpointError(f"{label} must be an object")
    return payload


def _required_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeCheckpointError(f"{label} must be an object")
    return dict(value)


def _required_text(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise RuntimeCheckpointError(f"{label} cannot be empty")
    return cleaned


def _parse_utc(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise RuntimeCheckpointError(f"invalid {label}") from exc
    _require_utc(parsed)
    return parsed


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise RuntimeCheckpointError("checkpoint timestamps must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise RuntimeCheckpointError("checkpoint timestamps must be UTC")


def _require_sha256(value: str, label: str) -> str:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise RuntimeCheckpointError(f"{label} must be lowercase SHA-256 hex")
    return value


def _reject_financial_secrets(text: str, label: str) -> None:
    findings = scan_text_for_financial_secrets(text)
    if findings:
        reasons = ", ".join(sorted(set(findings)))
        raise RuntimeCheckpointError(f"FINANCIAL_SECRET_DETECTED in {label}: {reasons}")


def _hash_payload(payload: dict[str, Any]) -> str:
    return _hash_text(_canonical_json(payload))


def _hash_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


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
        raise RuntimeCheckpointError("checkpoint payload is not canonical JSON compatible") from exc


def _reject_existing_sidecars(database: Path) -> None:
    for path in _database_family(database):
        if path != database and (path.exists() or path.is_symlink()):
            raise FileExistsError(f"restore sidecar already exists: {path}")


def _remove_sidecars(database: Path) -> None:
    for path in _database_family(database):
        if path == database:
            continue
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def _remove_database_family(database: Path) -> None:
    for path in _database_family(database):
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def _database_family(database: Path) -> tuple[Path, Path, Path]:
    return (
        database,
        Path(f"{database}-wal"),
        Path(f"{database}-shm"),
    )
