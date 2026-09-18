"""Single-controller lease/fencing contracts for broker-write ownership."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Callable, Protocol

from goldswingtraderai.domain.enums import HardDecision
from goldswingtraderai.domain.ids import EntityId
from goldswingtraderai.execution.models import AuthorityTrace


class CoordinationError(RuntimeError):
    """Shared coordination truth is unavailable or invalid."""


@dataclass(frozen=True, slots=True)
class LeaseSnapshot:
    scope: str
    holder_id: EntityId
    epoch: int
    expires_at_utc: datetime
    renewed_at_utc: datetime

    def __post_init__(self) -> None:
        if not self.scope.strip():
            raise ValueError("lease scope cannot be empty")
        if self.epoch <= 0:
            raise ValueError("lease epoch must be positive")
        _require_utc(self.expires_at_utc)
        _require_utc(self.renewed_at_utc)
        if self.expires_at_utc <= self.renewed_at_utc:
            raise ValueError("lease expiry must follow renewal time")

    def expired(self, now_utc: datetime) -> bool:
        _require_utc(now_utc)
        return now_utc >= self.expires_at_utc


class CoordinationStore(Protocol):
    """Backend contract; production implementation must be cross-machine atomic."""

    def read(self, scope: str) -> LeaseSnapshot | None: ...

    def try_acquire(
        self,
        scope: str,
        holder_id: EntityId,
        ttl: timedelta,
    ) -> LeaseSnapshot | None: ...

    def renew(self, lease: LeaseSnapshot, ttl: timedelta) -> LeaseSnapshot | None: ...

    def release(self, lease: LeaseSnapshot) -> bool: ...


@dataclass(frozen=True, slots=True)
class ControllerStatus:
    decision: HardDecision
    reason: str
    lease: LeaseSnapshot | None

    def as_trace(self) -> AuthorityTrace:
        return AuthorityTrace("controller", self.decision, self.reason)


class ControllerLeaseManager:
    def __init__(
        self,
        store: CoordinationStore,
        scope: str,
        controller_id: EntityId,
        *,
        ttl: timedelta = timedelta(seconds=30),
    ) -> None:
        if not scope.strip():
            raise ValueError("controller scope cannot be empty")
        if ttl <= timedelta(0):
            raise ValueError("controller TTL must be positive")
        self.store = store
        self.scope = scope.strip()
        self.controller_id = controller_id
        self.ttl = ttl
        self.lease: LeaseSnapshot | None = None
        self._takeover_reconciliation_required = False

    @property
    def takeover_reconciliation_required(self) -> bool:
        return self._takeover_reconciliation_required

    def acquire(self) -> ControllerStatus:
        """Acquire one epoch; expired-lease takeover remains blocked until reconciled."""

        try:
            previous = self.store.read(self.scope)
            lease = self.store.try_acquire(self.scope, self.controller_id, self.ttl)
        except Exception as exc:  # backend boundary: convert failure into safe authority state
            raise CoordinationError("controller coordination acquire failed") from exc
        if lease is None:
            return ControllerStatus(HardDecision.BLOCK, "ANOTHER_ACTIVE_CONTROLLER", None)

        self.lease = lease
        self._takeover_reconciliation_required = (
            previous is not None and lease.epoch > previous.epoch
        )
        if self._takeover_reconciliation_required:
            return ControllerStatus(
                HardDecision.BLOCK,
                "CONTROLLER_TAKEOVER_RECONCILIATION_REQUIRED",
                lease,
            )
        return ControllerStatus(HardDecision.PASS, "CONTROLLER_PRIMARY", lease)

    def renew(self) -> ControllerStatus:
        if self.lease is None:
            return ControllerStatus(HardDecision.UNKNOWN, "CONTROLLER_OWNERSHIP_UNKNOWN", None)
        try:
            renewed = self.store.renew(self.lease, self.ttl)
        except Exception as exc:
            raise CoordinationError("controller coordination renew failed") from exc
        if renewed is None:
            self.lease = None
            self._takeover_reconciliation_required = False
            return ControllerStatus(HardDecision.UNKNOWN, "CONTROLLER_OWNERSHIP_UNKNOWN", None)
        self.lease = renewed
        if self._takeover_reconciliation_required:
            return ControllerStatus(
                HardDecision.BLOCK,
                "CONTROLLER_TAKEOVER_RECONCILIATION_REQUIRED",
                renewed,
            )
        return ControllerStatus(HardDecision.PASS, "CONTROLLER_PRIMARY", renewed)

    def complete_takeover_reconciliation(self, now_utc: datetime) -> ControllerStatus:
        """Mark externally completed durable/broker reconciliation for this takeover.

        The caller must perform the actual reconciliation before invoking this method.
        We then freshly re-verify that the same holder/epoch is still authoritative.
        """

        status = self._verify_current_authority(now_utc)
        if status.decision is not HardDecision.PASS:
            return status
        self._takeover_reconciliation_required = False
        return ControllerStatus(HardDecision.PASS, "CONTROLLER_PRIMARY", status.lease)

    def verify_write_authority(self, now_utc: datetime) -> ControllerStatus:
        """Freshly verify holder, epoch and expiry immediately before a broker write."""

        status = self._verify_current_authority(now_utc)
        if status.decision is not HardDecision.PASS:
            return status
        if self._takeover_reconciliation_required:
            return ControllerStatus(
                HardDecision.BLOCK,
                "CONTROLLER_TAKEOVER_RECONCILIATION_REQUIRED",
                status.lease,
            )
        return status

    def release(self) -> bool:
        if self.lease is None:
            self._takeover_reconciliation_required = False
            return True
        try:
            released = self.store.release(self.lease)
        except Exception as exc:
            raise CoordinationError("controller coordination release failed") from exc
        if released:
            self.lease = None
            self._takeover_reconciliation_required = False
        return released

    def _verify_current_authority(self, now_utc: datetime) -> ControllerStatus:
        _require_utc(now_utc)
        if self.lease is None:
            return ControllerStatus(HardDecision.UNKNOWN, "CONTROLLER_OWNERSHIP_UNKNOWN", None)
        try:
            current = self.store.read(self.scope)
        except Exception:
            return ControllerStatus(
                HardDecision.UNKNOWN,
                "CONTROLLER_COORDINATION_UNAVAILABLE",
                self.lease,
            )
        if current is None:
            return ControllerStatus(HardDecision.UNKNOWN, "CONTROLLER_OWNERSHIP_UNKNOWN", self.lease)
        if current.expired(now_utc):
            return ControllerStatus(HardDecision.UNKNOWN, "CONTROLLER_OWNERSHIP_UNKNOWN", current)
        if current.holder_id != self.controller_id:
            return ControllerStatus(HardDecision.BLOCK, "ANOTHER_ACTIVE_CONTROLLER", current)
        if current.epoch != self.lease.epoch:
            return ControllerStatus(HardDecision.UNKNOWN, "CONTROLLER_OWNERSHIP_UNKNOWN", current)
        self.lease = current
        return ControllerStatus(HardDecision.PASS, "CONTROLLER_PRIMARY", current)


class InMemoryCoordinationStore:
    """Deterministic test backend only; never sufficient for cross-laptop production."""

    def __init__(self, now: Callable[[], datetime]) -> None:
        self._now = now
        self._leases: dict[str, LeaseSnapshot] = {}
        self._last_epoch: dict[str, int] = {}
        self._lock = Lock()

    def read(self, scope: str) -> LeaseSnapshot | None:
        with self._lock:
            return self._leases.get(scope)

    def try_acquire(
        self,
        scope: str,
        holder_id: EntityId,
        ttl: timedelta,
    ) -> LeaseSnapshot | None:
        with self._lock:
            now = self._verified_now()
            current = self._leases.get(scope)
            if current is not None and not current.expired(now):
                return None
            epoch = self._last_epoch.get(scope, 0) + 1
            lease = LeaseSnapshot(
                scope=scope,
                holder_id=holder_id,
                epoch=epoch,
                expires_at_utc=now + ttl,
                renewed_at_utc=now,
            )
            self._leases[scope] = lease
            self._last_epoch[scope] = epoch
            return lease

    def renew(self, lease: LeaseSnapshot, ttl: timedelta) -> LeaseSnapshot | None:
        with self._lock:
            now = self._verified_now()
            current = self._leases.get(lease.scope)
            if current is None or current.expired(now):
                return None
            if current.holder_id != lease.holder_id or current.epoch != lease.epoch:
                return None
            renewed = LeaseSnapshot(
                scope=lease.scope,
                holder_id=lease.holder_id,
                epoch=lease.epoch,
                expires_at_utc=now + ttl,
                renewed_at_utc=now,
            )
            self._leases[lease.scope] = renewed
            return renewed

    def release(self, lease: LeaseSnapshot) -> bool:
        with self._lock:
            current = self._leases.get(lease.scope)
            if current is None:
                return True
            if current.holder_id != lease.holder_id or current.epoch != lease.epoch:
                return False
            del self._leases[lease.scope]
            return True

    def _verified_now(self) -> datetime:
        value = self._now()
        _require_utc(value)
        return value


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("controller time must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("controller time must be UTC")
