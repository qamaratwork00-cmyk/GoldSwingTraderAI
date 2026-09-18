"""Immutable Phase-1 domain models.

These contracts intentionally contain no MT5 calls, database code or strategy logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from goldswingtraderai.diagnostics.reasons import ReasonCode
from goldswingtraderai.domain.enums import AccountMode, Direction, HardDecision, Timeframe
from goldswingtraderai.domain.ids import EntityId


def _require_utc_aware(name: str, value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(f"{name} must be UTC")


@dataclass(frozen=True, slots=True)
class Reason:
    code: ReasonCode
    message: str = ""
    details: tuple[tuple[str, str], ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class PermissionResult:
    decision: HardDecision
    primary_reason: Reason | None = None
    secondary_reasons: tuple[Reason, ...] = field(default_factory=tuple)
    would_otherwise_trade: bool | None = None

    def __post_init__(self) -> None:
        if self.decision is HardDecision.PASS and self.primary_reason is not None:
            raise ValueError("PASS permission cannot contain a blocking primary reason")
        if self.decision in {HardDecision.BLOCK, HardDecision.UNKNOWN} and self.primary_reason is None:
            raise ValueError("BLOCK/UNKNOWN permission requires a primary reason")


@dataclass(frozen=True, slots=True)
class MarketSnapshotMeta:
    snapshot_id: EntityId
    symbol: str
    as_of_utc: datetime
    timeframes: tuple[Timeframe, ...]
    data_complete: bool

    def __post_init__(self) -> None:
        _require_utc_aware("as_of_utc", self.as_of_utc)
        if not self.symbol.strip():
            raise ValueError("symbol cannot be empty")
        if not self.timeframes:
            raise ValueError("timeframes cannot be empty")


@dataclass(frozen=True, slots=True)
class DemoGuardResult:
    decision: HardDecision
    account_mode: AccountMode
    reason: Reason | None = None

    def __post_init__(self) -> None:
        if self.decision is HardDecision.PASS:
            if self.account_mode is not AccountMode.DEMO:
                raise ValueError("DEMO guard may PASS only for positively verified DEMO mode")
            if self.reason is not None:
                raise ValueError("passing DEMO guard does not need a blocking reason")
        else:
            if self.reason is None:
                raise ValueError("non-passing DEMO guard requires a reason")


@dataclass(frozen=True, slots=True)
class ControllerLease:
    holder_instance_id: EntityId
    epoch: int
    expires_at_utc: datetime
    last_renewed_at_utc: datetime

    def __post_init__(self) -> None:
        _require_utc_aware("expires_at_utc", self.expires_at_utc)
        _require_utc_aware("last_renewed_at_utc", self.last_renewed_at_utc)
        if self.epoch < 1:
            raise ValueError("controller fencing epoch must be >= 1")
        if self.expires_at_utc <= self.last_renewed_at_utc:
            raise ValueError("controller lease expiry must be after last renewal")

    def is_valid_at(self, now_utc: datetime) -> bool:
        _require_utc_aware("now_utc", now_utc)
        return now_utc < self.expires_at_utc


@dataclass(frozen=True, slots=True)
class ExecutionIntent:
    intent_id: EntityId
    opportunity_id: EntityId
    episode_id: EntityId
    created_at_utc: datetime
    direction: Direction
    volume: float
    approved_entry_reference: float
    structural_sl: float
    broker_tp: float | None = None
    controller_epoch: int | None = None

    def __post_init__(self) -> None:
        _require_utc_aware("created_at_utc", self.created_at_utc)
        if self.direction is Direction.NONE:
            raise ValueError("execution intent direction must be BUY or SELL")
        if self.volume <= 0:
            raise ValueError("execution intent volume must be > 0")
        if self.approved_entry_reference <= 0 or self.structural_sl <= 0:
            raise ValueError("entry reference and structural SL must be > 0")
        if self.broker_tp is not None and self.broker_tp <= 0:
            raise ValueError("broker TP must be > 0 when supplied")
        if self.controller_epoch is not None and self.controller_epoch < 1:
            raise ValueError("controller epoch must be >= 1 when supplied")

        if self.direction is Direction.BUY:
            if self.structural_sl >= self.approved_entry_reference:
                raise ValueError("BUY structural SL must be below approved entry reference")
            if self.broker_tp is not None and self.broker_tp <= self.approved_entry_reference:
                raise ValueError("BUY broker TP must be above approved entry reference")
        elif self.direction is Direction.SELL:
            if self.structural_sl <= self.approved_entry_reference:
                raise ValueError("SELL structural SL must be above approved entry reference")
            if self.broker_tp is not None and self.broker_tp >= self.approved_entry_reference:
                raise ValueError("SELL broker TP must be below approved entry reference")
