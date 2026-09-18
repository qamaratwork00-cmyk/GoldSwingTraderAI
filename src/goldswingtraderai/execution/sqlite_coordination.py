"""Durable atomic controller coordination backed by SQLite.

This backend provides transactionally atomic lease acquire/renew/release and a
monotonic fencing epoch across independent processes opening the same database.
It is suitable for deterministic multi-process verification and for deployments
whose shared filesystem/SQLite locking semantics have been explicitly certified.
The module does not claim every network filesystem is safe for cross-laptop use.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3

from goldswingtraderai.domain.ids import EntityId
from goldswingtraderai.execution.controller import CoordinationError, LeaseSnapshot


COORDINATION_SCHEMA_VERSION = 1


class SQLiteCoordinationStore:
    """Atomic durable `CoordinationStore` implementation using SQLite transactions."""

    def __init__(
        self,
        path: str | Path,
        now: Callable[[], datetime] | None = None,
        *,
        shared_locking_verified: bool = False,
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._now = now or (lambda: datetime.now(timezone.utc))
        self.shared_locking_verified = bool(shared_locking_verified)
        self._initialize()

    @property
    def cross_machine_certified(self) -> bool:
        """Deployment assertion only; deterministic code cannot prove filesystem locks."""

        return self.shared_locking_verified

    def read(self, scope: str) -> LeaseSnapshot | None:
        scope = _required_scope(scope)
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT holder_id, epoch, expires_at_utc, renewed_at_utc
                    FROM controller_leases
                    WHERE scope=?
                    """,
                    (scope,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise CoordinationError("SQLite coordination read failed") from exc
        return None if row is None else _lease_from_row(scope, row)

    def try_acquire(
        self,
        scope: str,
        holder_id: EntityId,
        ttl: timedelta,
    ) -> LeaseSnapshot | None:
        scope = _required_scope(scope)
        _require_positive_ttl(ttl)
        now = self._verified_now()
        try:
            connection = self._connect()
            try:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    """
                    SELECT holder_id, epoch, expires_at_utc, renewed_at_utc
                    FROM controller_leases
                    WHERE scope=?
                    """,
                    (scope,),
                ).fetchone()
                current = None if row is None else _lease_from_row(scope, row)
                if current is not None and not current.expired(now):
                    connection.rollback()
                    return None

                epoch_row = connection.execute(
                    "SELECT last_epoch FROM controller_epochs WHERE scope=?",
                    (scope,),
                ).fetchone()
                last_epoch = int(epoch_row[0]) if epoch_row is not None else 0
                if current is not None:
                    last_epoch = max(last_epoch, current.epoch)
                epoch = last_epoch + 1
                lease = LeaseSnapshot(
                    scope=scope,
                    holder_id=holder_id,
                    epoch=epoch,
                    expires_at_utc=now + ttl,
                    renewed_at_utc=now,
                )
                connection.execute(
                    """
                    INSERT INTO controller_epochs(scope, last_epoch)
                    VALUES (?, ?)
                    ON CONFLICT(scope) DO UPDATE SET last_epoch=excluded.last_epoch
                    """,
                    (scope, epoch),
                )
                connection.execute(
                    """
                    INSERT INTO controller_leases(
                        scope, holder_id, epoch, expires_at_utc, renewed_at_utc
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(scope) DO UPDATE SET
                        holder_id=excluded.holder_id,
                        epoch=excluded.epoch,
                        expires_at_utc=excluded.expires_at_utc,
                        renewed_at_utc=excluded.renewed_at_utc
                    """,
                    _lease_values(lease),
                )
                connection.commit()
                return lease
            finally:
                connection.close()
        except sqlite3.Error as exc:
            raise CoordinationError("SQLite coordination acquire failed") from exc

    def renew(self, lease: LeaseSnapshot, ttl: timedelta) -> LeaseSnapshot | None:
        _require_positive_ttl(ttl)
        now = self._verified_now()
        try:
            connection = self._connect()
            try:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    """
                    SELECT holder_id, epoch, expires_at_utc, renewed_at_utc
                    FROM controller_leases
                    WHERE scope=?
                    """,
                    (lease.scope,),
                ).fetchone()
                current = None if row is None else _lease_from_row(lease.scope, row)
                if (
                    current is None
                    or current.expired(now)
                    or current.holder_id != lease.holder_id
                    or current.epoch != lease.epoch
                ):
                    connection.rollback()
                    return None

                renewed = LeaseSnapshot(
                    scope=lease.scope,
                    holder_id=lease.holder_id,
                    epoch=lease.epoch,
                    expires_at_utc=now + ttl,
                    renewed_at_utc=now,
                )
                cursor = connection.execute(
                    """
                    UPDATE controller_leases
                    SET expires_at_utc=?, renewed_at_utc=?
                    WHERE scope=? AND holder_id=? AND epoch=?
                    """,
                    (
                        renewed.expires_at_utc.isoformat(),
                        renewed.renewed_at_utc.isoformat(),
                        renewed.scope,
                        str(renewed.holder_id),
                        renewed.epoch,
                    ),
                )
                if cursor.rowcount != 1:
                    connection.rollback()
                    return None
                connection.commit()
                return renewed
            finally:
                connection.close()
        except sqlite3.Error as exc:
            raise CoordinationError("SQLite coordination renew failed") from exc

    def release(self, lease: LeaseSnapshot) -> bool:
        try:
            connection = self._connect()
            try:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT holder_id, epoch FROM controller_leases WHERE scope=?",
                    (lease.scope,),
                ).fetchone()
                if row is None:
                    connection.rollback()
                    return True
                if str(row[0]) != str(lease.holder_id) or int(row[1]) != lease.epoch:
                    connection.rollback()
                    return False
                cursor = connection.execute(
                    """
                    DELETE FROM controller_leases
                    WHERE scope=? AND holder_id=? AND epoch=?
                    """,
                    (lease.scope, str(lease.holder_id), lease.epoch),
                )
                if cursor.rowcount != 1:
                    connection.rollback()
                    return False
                connection.commit()
                return True
            finally:
                connection.close()
        except sqlite3.Error as exc:
            raise CoordinationError("SQLite coordination release failed") from exc

    def integrity_check(self) -> None:
        """Verify SQLite structure and persisted lease/epoch invariants."""

        try:
            with self._connect() as connection:
                quick = connection.execute("PRAGMA quick_check").fetchone()
                if quick is None or quick[0] != "ok":
                    raise CoordinationError(f"SQLite coordination quick_check failed: {quick}")
                rows = connection.execute(
                    """
                    SELECT l.scope, l.holder_id, l.epoch, l.expires_at_utc,
                           l.renewed_at_utc, e.last_epoch
                    FROM controller_leases AS l
                    LEFT JOIN controller_epochs AS e ON e.scope=l.scope
                    ORDER BY l.scope
                    """
                ).fetchall()
        except sqlite3.Error as exc:
            raise CoordinationError("SQLite coordination integrity check failed") from exc

        for scope, holder, epoch, expires, renewed, last_epoch in rows:
            lease = LeaseSnapshot(
                scope=str(scope),
                holder_id=EntityId.parse(str(holder)),
                epoch=int(epoch),
                expires_at_utc=_parse_utc(str(expires)),
                renewed_at_utc=_parse_utc(str(renewed)),
            )
            if last_epoch is None or int(last_epoch) < lease.epoch:
                raise CoordinationError("coordination epoch ledger is behind active lease")

    def _initialize(self) -> None:
        try:
            with self._connect() as connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS coordination_metadata(
                        name TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS controller_epochs(
                        scope TEXT PRIMARY KEY,
                        last_epoch INTEGER NOT NULL CHECK(last_epoch > 0)
                    );
                    CREATE TABLE IF NOT EXISTS controller_leases(
                        scope TEXT PRIMARY KEY,
                        holder_id TEXT NOT NULL,
                        epoch INTEGER NOT NULL CHECK(epoch > 0),
                        expires_at_utc TEXT NOT NULL,
                        renewed_at_utc TEXT NOT NULL
                    );
                    """
                )
                row = connection.execute(
                    "SELECT value FROM coordination_metadata WHERE name='schema_version'"
                ).fetchone()
                if row is None:
                    connection.execute(
                        "INSERT INTO coordination_metadata(name, value) VALUES('schema_version', ?)",
                        (str(COORDINATION_SCHEMA_VERSION),),
                    )
                elif int(row[0]) != COORDINATION_SCHEMA_VERSION:
                    raise CoordinationError(
                        f"unsupported coordination schema {row[0]}; "
                        f"expected {COORDINATION_SCHEMA_VERSION}"
                    )
        except sqlite3.Error as exc:
            raise CoordinationError("SQLite coordination initialization failed") from exc

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5.0)
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def _verified_now(self) -> datetime:
        value = self._now()
        _require_utc(value)
        return value


def _lease_values(lease: LeaseSnapshot) -> tuple[str, str, int, str, str]:
    return (
        lease.scope,
        str(lease.holder_id),
        lease.epoch,
        lease.expires_at_utc.isoformat(),
        lease.renewed_at_utc.isoformat(),
    )


def _lease_from_row(scope: str, row: tuple[object, ...]) -> LeaseSnapshot:
    holder_id, epoch, expires, renewed = row
    return LeaseSnapshot(
        scope=scope,
        holder_id=EntityId.parse(str(holder_id)),
        epoch=int(epoch),
        expires_at_utc=_parse_utc(str(expires)),
        renewed_at_utc=_parse_utc(str(renewed)),
    )


def _parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CoordinationError("invalid persisted coordination UTC timestamp") from exc
    _require_utc(parsed)
    return parsed


def _required_scope(scope: str) -> str:
    cleaned = scope.strip()
    if not cleaned:
        raise ValueError("coordination scope cannot be empty")
    return cleaned


def _require_positive_ttl(ttl: timedelta) -> None:
    if ttl <= timedelta(0):
        raise ValueError("coordination TTL must be positive")


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("coordination clock must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("coordination clock must be UTC")
