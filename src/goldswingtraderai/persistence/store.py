"""Small transactional SQLite store for durable runtime state.

Critical state is stored as canonical JSON with a checksum and explicit schema
version. Corruption/version mismatch raises an error; it never becomes a blank
safe-looking default.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Any, Mapping


DATABASE_SCHEMA_VERSION = 1


class StateStoreError(RuntimeError):
    """Base persistence error."""


class StateIntegrityError(StateStoreError):
    """Stored bytes/JSON/checksum are inconsistent."""


class StateVersionError(StateStoreError):
    """Record/database schema is unsupported."""


@dataclass(frozen=True, slots=True)
class StoredRecord:
    namespace: str
    key: str
    schema_version: int
    payload: dict[str, Any]
    checksum: str
    updated_at_utc: datetime


@dataclass(frozen=True, slots=True)
class StoredEvent:
    event_id: int
    namespace: str
    key: str
    event_type: str
    payload: dict[str, Any]
    checksum: str
    created_at_utc: datetime

    def __post_init__(self) -> None:
        if self.event_id <= 0:
            raise ValueError("stored event id must be positive")


@dataclass(frozen=True, slots=True)
class StoreSnapshot:
    database_schema_version: int
    records: tuple[StoredRecord, ...]
    events: tuple[StoredEvent, ...]

    def __post_init__(self) -> None:
        if self.database_schema_version != DATABASE_SCHEMA_VERSION:
            raise StateVersionError(
                "portable snapshot database schema does not match this runtime"
            )


class StateStore:
    """Transactional key/value + append-only event storage backed by SQLite."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def save_record(
        self,
        namespace: str,
        key: str,
        payload: Mapping[str, Any],
        *,
        schema_version: int = 1,
        event_type: str | None = None,
    ) -> StoredRecord:
        namespace = _required_text(namespace, "namespace")
        key = _required_text(key, "key")
        if schema_version <= 0:
            raise ValueError("record schema version must be positive")
        data = dict(payload)
        encoded = _canonical_json(data)
        checksum = _checksum(encoded)
        now = datetime.now(timezone.utc)
        timestamp = now.isoformat()

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT INTO state_records(
                    namespace, record_key, schema_version,
                    payload_json, checksum, updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(namespace, record_key) DO UPDATE SET
                    schema_version=excluded.schema_version,
                    payload_json=excluded.payload_json,
                    checksum=excluded.checksum,
                    updated_at_utc=excluded.updated_at_utc
                """,
                (namespace, key, schema_version, encoded, checksum, timestamp),
            )
            if event_type is not None:
                connection.execute(
                    """
                    INSERT INTO state_events(
                        namespace, record_key, event_type,
                        payload_json, checksum, created_at_utc
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        namespace,
                        key,
                        _required_text(event_type, "event type"),
                        encoded,
                        checksum,
                        timestamp,
                    ),
                )

        return StoredRecord(
            namespace=namespace,
            key=key,
            schema_version=schema_version,
            payload=data,
            checksum=checksum,
            updated_at_utc=now,
        )

    def load_record(
        self,
        namespace: str,
        key: str,
        *,
        expected_schema_version: int | None = None,
    ) -> StoredRecord | None:
        namespace = _required_text(namespace, "namespace")
        key = _required_text(key, "key")
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT schema_version, payload_json, checksum, updated_at_utc
                FROM state_records
                WHERE namespace=? AND record_key=?
                """,
                (namespace, key),
            ).fetchone()
        if row is None:
            return None

        schema_version, payload_json, checksum, updated_at = row
        return _decode_record(
            namespace,
            key,
            int(schema_version),
            str(payload_json),
            str(checksum),
            str(updated_at),
            expected_schema_version=expected_schema_version,
        )

    def delete_record(self, namespace: str, key: str, *, event_type: str | None = None) -> None:
        namespace = _required_text(namespace, "namespace")
        key = _required_text(key, "key")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if event_type is not None:
                empty_json = _canonical_json({})
                connection.execute(
                    """
                    INSERT INTO state_events(
                        namespace, record_key, event_type,
                        payload_json, checksum, created_at_utc
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        namespace,
                        key,
                        _required_text(event_type, "event type"),
                        empty_json,
                        _checksum(empty_json),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
            connection.execute(
                "DELETE FROM state_records WHERE namespace=? AND record_key=?",
                (namespace, key),
            )

    def integrity_check(self) -> None:
        """Verify SQLite integrity plus every current record and event checksum."""

        with self._connect() as connection:
            quick = connection.execute("PRAGMA quick_check").fetchone()
            if quick is None or quick[0] != "ok":
                raise StateIntegrityError(f"SQLite quick_check failed: {quick}")
            record_rows = connection.execute(
                """
                SELECT namespace, record_key, schema_version,
                       payload_json, checksum, updated_at_utc
                FROM state_records
                ORDER BY namespace, record_key
                """
            ).fetchall()
            event_rows = connection.execute(
                """
                SELECT event_id, namespace, record_key, event_type,
                       payload_json, checksum, created_at_utc
                FROM state_events
                ORDER BY event_id
                """
            ).fetchall()

        for namespace, key, schema_version, payload_json, checksum, updated_at in record_rows:
            _decode_record(
                str(namespace),
                str(key),
                int(schema_version),
                str(payload_json),
                str(checksum),
                str(updated_at),
            )
        for row in event_rows:
            _decode_event(row)

    def export_snapshot(self) -> StoreSnapshot:
        """Return a deterministic integrity-checked view for portable backup tooling."""

        self.integrity_check()
        with self._connect() as connection:
            version_row = connection.execute(
                "SELECT value FROM metadata WHERE name='database_schema_version'"
            ).fetchone()
            record_rows = connection.execute(
                """
                SELECT namespace, record_key, schema_version,
                       payload_json, checksum, updated_at_utc
                FROM state_records
                ORDER BY namespace, record_key
                """
            ).fetchall()
            event_rows = connection.execute(
                """
                SELECT event_id, namespace, record_key, event_type,
                       payload_json, checksum, created_at_utc
                FROM state_events
                ORDER BY event_id
                """
            ).fetchall()
        if version_row is None:
            raise StateIntegrityError("database schema metadata is missing")
        version = int(version_row[0])
        if version != DATABASE_SCHEMA_VERSION:
            raise StateVersionError(
                f"unsupported database schema {version}; expected {DATABASE_SCHEMA_VERSION}"
            )
        records = tuple(
            _decode_record(
                str(namespace),
                str(key),
                int(schema_version),
                str(payload_json),
                str(checksum),
                str(updated_at),
            )
            for namespace, key, schema_version, payload_json, checksum, updated_at in record_rows
        )
        events = tuple(_decode_event(row) for row in event_rows)
        return StoreSnapshot(
            database_schema_version=version,
            records=records,
            events=events,
        )

    def restore_snapshot(self, snapshot: StoreSnapshot) -> None:
        """Restore one verified snapshot into an otherwise empty initialized store."""

        if snapshot.database_schema_version != DATABASE_SCHEMA_VERSION:
            raise StateVersionError(
                "portable snapshot database schema does not match this runtime"
            )
        _validate_snapshot(snapshot)

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            counts = connection.execute(
                "SELECT (SELECT COUNT(*) FROM state_records), (SELECT COUNT(*) FROM state_events)"
            ).fetchone()
            if counts is None or int(counts[0]) != 0 or int(counts[1]) != 0:
                raise StateIntegrityError("restore target store must contain no records or events")

            for record in snapshot.records:
                payload_json = _canonical_json(record.payload)
                connection.execute(
                    """
                    INSERT INTO state_records(
                        namespace, record_key, schema_version,
                        payload_json, checksum, updated_at_utc
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.namespace,
                        record.key,
                        record.schema_version,
                        payload_json,
                        record.checksum,
                        record.updated_at_utc.isoformat(),
                    ),
                )
            for event in snapshot.events:
                payload_json = _canonical_json(event.payload)
                connection.execute(
                    """
                    INSERT INTO state_events(
                        event_id, namespace, record_key, event_type,
                        payload_json, checksum, created_at_utc
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.event_id,
                        event.namespace,
                        event.key,
                        event.event_type,
                        payload_json,
                        event.checksum,
                        event.created_at_utc.isoformat(),
                    ),
                )

        self.integrity_check()

    def event_count(self, namespace: str | None = None) -> int:
        with self._connect() as connection:
            if namespace is None:
                row = connection.execute("SELECT COUNT(*) FROM state_events").fetchone()
            else:
                row = connection.execute(
                    "SELECT COUNT(*) FROM state_events WHERE namespace=?",
                    (_required_text(namespace, "namespace"),),
                ).fetchone()
        return int(row[0]) if row is not None else 0

    def checkpoint_database(self) -> None:
        """Force WAL contents into the main database before an external file move."""

        with self._connect() as connection:
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata(
                    name TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS state_records(
                    namespace TEXT NOT NULL,
                    record_key TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    payload_json TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    updated_at_utc TEXT NOT NULL,
                    PRIMARY KEY(namespace, record_key)
                );
                CREATE TABLE IF NOT EXISTS state_events(
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    namespace TEXT NOT NULL,
                    record_key TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL
                );
                """
            )
            row = connection.execute(
                "SELECT value FROM metadata WHERE name='database_schema_version'"
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO metadata(name, value) VALUES('database_schema_version', ?)",
                    (str(DATABASE_SCHEMA_VERSION),),
                )
            elif int(row[0]) != DATABASE_SCHEMA_VERSION:
                raise StateVersionError(
                    f"unsupported database schema {row[0]}; expected {DATABASE_SCHEMA_VERSION}"
                )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5.0)
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        return connection


def _decode_record(
    namespace: str,
    key: str,
    schema_version: int,
    payload_json: str,
    checksum: str,
    updated_at: str,
    *,
    expected_schema_version: int | None = None,
) -> StoredRecord:
    if schema_version <= 0:
        raise StateVersionError(f"invalid record version for {namespace}/{key}")
    if expected_schema_version is not None and schema_version != expected_schema_version:
        raise StateVersionError(
            f"unsupported record version {schema_version}; expected {expected_schema_version}"
        )
    if _checksum(payload_json) != checksum:
        raise StateIntegrityError(f"checksum mismatch for {namespace}/{key}")
    payload = _decode_payload(payload_json, f"{namespace}/{key}")
    try:
        updated_at_utc = datetime.fromisoformat(updated_at)
    except ValueError as exc:
        raise StateIntegrityError(f"invalid timestamp for {namespace}/{key}") from exc
    _require_utc(updated_at_utc)
    return StoredRecord(
        namespace=namespace,
        key=key,
        schema_version=schema_version,
        payload=payload,
        checksum=checksum,
        updated_at_utc=updated_at_utc,
    )


def _decode_event(row: tuple[Any, ...]) -> StoredEvent:
    event_id, namespace, key, event_type, payload_json, checksum, created_at = row
    namespace = str(namespace)
    key = str(key)
    event_type = _required_text(str(event_type), "event type")
    payload_json = str(payload_json)
    checksum = str(checksum)
    if _checksum(payload_json) != checksum:
        raise StateIntegrityError(f"event checksum mismatch for {namespace}/{key}#{event_id}")
    payload = _decode_payload(payload_json, f"event {namespace}/{key}#{event_id}")
    try:
        created_at_utc = datetime.fromisoformat(str(created_at))
    except ValueError as exc:
        raise StateIntegrityError(
            f"invalid event timestamp for {namespace}/{key}#{event_id}"
        ) from exc
    _require_utc(created_at_utc)
    return StoredEvent(
        event_id=int(event_id),
        namespace=namespace,
        key=key,
        event_type=event_type,
        payload=payload,
        checksum=checksum,
        created_at_utc=created_at_utc,
    )


def _validate_snapshot(snapshot: StoreSnapshot) -> None:
    record_ids: set[tuple[str, str]] = set()
    for record in snapshot.records:
        identity = (_required_text(record.namespace, "namespace"), _required_text(record.key, "key"))
        if identity in record_ids:
            raise StateIntegrityError(f"duplicate snapshot record: {identity[0]}/{identity[1]}")
        record_ids.add(identity)
        if record.schema_version <= 0:
            raise StateVersionError(f"invalid snapshot record version: {identity[0]}/{identity[1]}")
        _require_utc(record.updated_at_utc)
        if _checksum(_canonical_json(record.payload)) != record.checksum:
            raise StateIntegrityError(f"snapshot record checksum mismatch: {identity[0]}/{identity[1]}")

    event_ids: set[int] = set()
    previous_event_id = 0
    for event in snapshot.events:
        if event.event_id in event_ids or event.event_id <= previous_event_id:
            raise StateIntegrityError("snapshot event ids must be unique and chronological")
        event_ids.add(event.event_id)
        previous_event_id = event.event_id
        _required_text(event.namespace, "namespace")
        _required_text(event.key, "key")
        _required_text(event.event_type, "event type")
        _require_utc(event.created_at_utc)
        if _checksum(_canonical_json(event.payload)) != event.checksum:
            raise StateIntegrityError(
                f"snapshot event checksum mismatch: {event.namespace}/{event.key}#{event.event_id}"
            )


def _decode_payload(payload_json: str, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(payload_json)
    except json.JSONDecodeError as exc:
        raise StateIntegrityError(f"invalid JSON for {label}") from exc
    if not isinstance(payload, dict):
        raise StateIntegrityError(f"record payload must be object: {label}")
    return payload


def _canonical_json(payload: Mapping[str, Any]) -> str:
    try:
        return json.dumps(
            dict(payload),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("state payload must be canonical JSON-compatible data") from exc


def _checksum(payload_json: str) -> str:
    return sha256(payload_json.encode("utf-8")).hexdigest()


def _required_text(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{label} cannot be empty")
    return cleaned


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise StateIntegrityError("stored timestamp must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise StateIntegrityError("stored timestamp must be UTC")
