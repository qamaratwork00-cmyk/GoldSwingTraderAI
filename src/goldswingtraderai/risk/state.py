"""Pure Phase-5 risk state transitions.

Persistence arrives in Phase 6; these dataclasses/functions define the durable
semantics now so restart storage can later serialize them without changing policy.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta, timezone
from enum import StrEnum

from goldswingtraderai.domain.ids import EntityId


class ClosedTradeOutcome(StrEnum):
    WIN = "WIN"
    LOSS = "LOSS"
    SCRATCH = "SCRATCH"


class CooldownDecision(StrEnum):
    CLEAR = "CLEAR"
    COOLDOWN = "COOLDOWN"


@dataclass(frozen=True, slots=True)
class RiskDayState:
    utc_day: date
    day_start_equity: float
    net_non_trading_cash_flow: float
    cycle_reference_equity: float
    cycle_start_safety_pl: float
    manual_reset_enabled: bool = False
    manual_reset_count: int = 0

    def __post_init__(self) -> None:
        if self.day_start_equity <= 0 or self.cycle_reference_equity <= 0:
            raise ValueError("risk-day equity references must be positive")
        if self.manual_reset_count not in {0, 1}:
            raise ValueError("V1 manual reset count must be 0 or 1")


@dataclass(frozen=True, slots=True)
class RiskDayMetrics:
    account_safety_pl: float
    cycle_safety_pl: float
    cycle_loss_pct: float
    daily_lock_pct: float
    remaining_loss_budget_pct: float
    loss_locked: bool


@dataclass(frozen=True, slots=True)
class CooldownState:
    consecutive_losses: int = 0
    triggered_at_utc: datetime | None = None
    cooldown_until_utc: datetime | None = None

    def __post_init__(self) -> None:
        if self.consecutive_losses < 0:
            raise ValueError("consecutive losses cannot be negative")
        for value in (self.triggered_at_utc, self.cooldown_until_utc):
            if value is not None:
                _require_utc(value)
        if (
            self.triggered_at_utc is not None
            and self.cooldown_until_utc is not None
            and self.cooldown_until_utc < self.triggered_at_utc
        ):
            raise ValueError("cooldown cannot end before trigger")


@dataclass(frozen=True, slots=True)
class EpisodeRiskState:
    episode_id: EntityId
    entries_taken: int = 0
    losses: int = 0
    locked: bool = False

    def __post_init__(self) -> None:
        if self.entries_taken < 0 or self.losses < 0:
            raise ValueError("episode counters cannot be negative")
        if self.entries_taken > 2:
            raise ValueError("V1 permits at most two entries in one Market Episode")
        if self.losses > self.entries_taken:
            raise ValueError("episode losses cannot exceed entries")


def new_risk_day(
    now_utc: datetime,
    equity: float,
    *,
    manual_reset_enabled: bool = False,
) -> RiskDayState:
    _require_utc(now_utc)
    if equity <= 0:
        raise ValueError("day-start equity must be positive")
    return RiskDayState(
        utc_day=now_utc.date(),
        day_start_equity=equity,
        net_non_trading_cash_flow=0.0,
        cycle_reference_equity=equity,
        cycle_start_safety_pl=0.0,
        manual_reset_enabled=manual_reset_enabled,
    )


def record_non_trading_cash_flow(state: RiskDayState, amount: float) -> RiskDayState:
    """Record deposits/withdrawals/known non-trading balance adjustments."""

    return replace(
        state,
        net_non_trading_cash_flow=state.net_non_trading_cash_flow + amount,
    )


def risk_day_metrics(
    state: RiskDayState,
    current_equity: float,
    daily_lock_pct: float,
) -> RiskDayMetrics:
    if current_equity <= 0:
        raise ValueError("current equity must be positive")
    if daily_lock_pct <= 0:
        raise ValueError("daily lock percentage must be positive")

    account_safety_pl = (
        current_equity
        - state.day_start_equity
        - state.net_non_trading_cash_flow
    )
    cycle_safety_pl = account_safety_pl - state.cycle_start_safety_pl
    cycle_loss_pct = max(
        0.0,
        -cycle_safety_pl / state.cycle_reference_equity * 100.0,
    )
    return RiskDayMetrics(
        account_safety_pl=account_safety_pl,
        cycle_safety_pl=cycle_safety_pl,
        cycle_loss_pct=cycle_loss_pct,
        daily_lock_pct=daily_lock_pct,
        remaining_loss_budget_pct=max(0.0, daily_lock_pct - cycle_loss_pct),
        loss_locked=cycle_loss_pct >= daily_lock_pct,
    )


def manual_reset_loss_lock(
    state: RiskDayState,
    current_equity: float,
    daily_lock_pct: float,
    *,
    double_confirmed: bool,
) -> RiskDayState:
    """Start the one allowed audited loss cycle without erasing day P/L."""

    metrics = risk_day_metrics(state, current_equity, daily_lock_pct)
    if not state.manual_reset_enabled:
        raise PermissionError("manual loss reset is disabled")
    if not metrics.loss_locked:
        raise PermissionError("manual reset is allowed only from LOSS_LOCKED")
    if state.manual_reset_count >= 1:
        raise PermissionError("manual reset already used this UTC risk day")
    if not double_confirmed:
        raise PermissionError("manual reset requires deliberate double confirmation")

    return replace(
        state,
        cycle_reference_equity=current_equity,
        cycle_start_safety_pl=metrics.account_safety_pl,
        manual_reset_count=1,
    )


def record_closed_trade(
    state: CooldownState,
    outcome: ClosedTradeOutcome,
    closed_at_utc: datetime,
    *,
    minimum_cooldown_minutes: int = 30,
) -> CooldownState:
    _require_utc(closed_at_utc)
    if minimum_cooldown_minutes <= 0:
        raise ValueError("minimum cooldown must be positive")

    if outcome is ClosedTradeOutcome.WIN:
        # A win resets the loss counter but does not erase a cooldown that was
        # already triggered by three consecutive losses; its release conditions
        # still have to pass.
        return replace(state, consecutive_losses=0)
    if outcome is ClosedTradeOutcome.SCRATCH:
        return state

    losses = state.consecutive_losses + 1
    if losses < 3:
        return CooldownState(consecutive_losses=losses)
    until = closed_at_utc + timedelta(minutes=minimum_cooldown_minutes)
    return CooldownState(
        consecutive_losses=losses,
        triggered_at_utc=closed_at_utc,
        cooldown_until_utc=until,
    )


def cooldown_decision(
    state: CooldownState,
    now_utc: datetime,
    *,
    latest_completed_m15_utc: datetime | None,
    unresolved_execution_fault: bool,
    fresh_opportunity: bool,
) -> CooldownDecision:
    _require_utc(now_utc)
    if state.cooldown_until_utc is None or state.triggered_at_utc is None:
        return CooldownDecision.CLEAR
    if now_utc < state.cooldown_until_utc:
        return CooldownDecision.COOLDOWN
    if unresolved_execution_fault or not fresh_opportunity:
        return CooldownDecision.COOLDOWN
    if latest_completed_m15_utc is None:
        return CooldownDecision.COOLDOWN
    _require_utc(latest_completed_m15_utc)
    if latest_completed_m15_utc <= state.triggered_at_utc:
        return CooldownDecision.COOLDOWN
    return CooldownDecision.CLEAR


def can_enter_episode(
    state: EpisodeRiskState,
    *,
    fresh_structural_event: bool,
) -> bool:
    if state.locked or state.entries_taken >= 2:
        return False
    if state.entries_taken == 0:
        return True
    return fresh_structural_event


def register_episode_entry(
    state: EpisodeRiskState,
    *,
    fresh_structural_event: bool,
) -> EpisodeRiskState:
    if not can_enter_episode(state, fresh_structural_event=fresh_structural_event):
        raise PermissionError("Market Episode entry/re-entry not permitted")
    return replace(state, entries_taken=state.entries_taken + 1)


def record_episode_loss(state: EpisodeRiskState) -> EpisodeRiskState:
    if state.losses >= state.entries_taken:
        raise ValueError("cannot record an episode loss without an unmatched entry")
    losses = state.losses + 1
    return replace(
        state,
        losses=losses,
        locked=losses >= 2,
    )


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("timestamp must be UTC")
