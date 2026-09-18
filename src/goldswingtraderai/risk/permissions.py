"""Hard session/news permission derived from verified facts.

This module does not score trades. It turns broker-session and scheduled-news truth
into explicit PASS/BLOCK/UNKNOWN states for the later centralized execution gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

from goldswingtraderai.domain.enums import HardDecision, MarketState, NewsSafetyState
from goldswingtraderai.intelligence.news import NewsFacts


class ClosureKind(StrEnum):
    DAILY = "DAILY"
    WEEKEND = "WEEKEND"


@dataclass(frozen=True, slots=True)
class BrokerSessionFacts:
    """Verified broker/session facts needed for hard market permission."""

    tradeable: bool
    schedule_verified: bool
    next_close_utc: datetime | None
    next_close_kind: ClosureKind | None
    reopened_at_utc: datetime | None = None
    reopen_kind: ClosureKind | None = None
    clean_completed_m5_since_reopen: int = 0
    execution_normalized: bool = True
    unresolved_gap_or_reconciliation: bool = False
    weekend_gap_assessed: bool = True
    holiday_context: bool = False

    def __post_init__(self) -> None:
        for value in (self.next_close_utc, self.reopened_at_utc):
            if value is not None:
                _require_utc(value)
        if self.clean_completed_m5_since_reopen < 0:
            raise ValueError("clean M5 count cannot be negative")
        if self.next_close_utc is not None and self.next_close_kind is None:
            raise ValueError("next close kind is required with next close time")
        if self.reopened_at_utc is not None and self.reopen_kind is None:
            raise ValueError("reopen kind is required with reopen time")


@dataclass(frozen=True, slots=True)
class MarketPermission:
    decision: HardDecision
    state: MarketState
    reason: str
    new_entries_allowed: bool
    flatten_required: bool
    minutes_to_close: float | None = None
    clean_m5_required: int = 0
    clean_m5_observed: int = 0


@dataclass(frozen=True, slots=True)
class NewsRecoveryFacts:
    """Post-blackout recovery state supplied by the runtime/execution observer."""

    active: bool = False
    severe_dislocation: bool = False
    execution_normalized: bool = True
    clean_completed_m5_after_event: int = 0

    def __post_init__(self) -> None:
        if self.clean_completed_m5_after_event < 0:
            raise ValueError("post-news clean M5 count cannot be negative")


@dataclass(frozen=True, slots=True)
class NewsPermission:
    decision: HardDecision
    state: NewsSafetyState
    reason: str
    active_event_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SessionNewsPermission:
    decision: HardDecision
    reasons: tuple[str, ...]
    flatten_required: bool
    market: MarketPermission
    news: NewsPermission


def evaluate_market_permission(
    facts: BrokerSessionFacts,
    now_utc: datetime,
) -> MarketPermission:
    """Evaluate OPEN/PRE_CLOSE/CLOSED/REOPEN_WARMUP from broker facts."""

    _require_utc(now_utc)
    if not facts.tradeable:
        return MarketPermission(
            decision=HardDecision.BLOCK,
            state=MarketState.CLOSED,
            reason="SESSION_CLOSED",
            new_entries_allowed=False,
            flatten_required=False,
        )

    warmup = _reopen_warmup(facts)
    if warmup is not None:
        return warmup

    if not facts.schedule_verified or facts.next_close_utc is None:
        return MarketPermission(
            decision=HardDecision.UNKNOWN,
            state=MarketState.OPEN,
            reason="SESSION_SCHEDULE_UNKNOWN",
            new_entries_allowed=False,
            flatten_required=False,
        )

    seconds_to_close = (facts.next_close_utc - now_utc).total_seconds()
    if seconds_to_close < 0:
        return MarketPermission(
            decision=HardDecision.UNKNOWN,
            state=MarketState.OPEN,
            reason="SESSION_SCHEDULE_STALE",
            new_entries_allowed=False,
            flatten_required=False,
            minutes_to_close=seconds_to_close / 60.0,
        )

    minutes_to_close = seconds_to_close / 60.0
    no_entry_minutes, flatten_minutes = _preclose_thresholds(facts.next_close_kind)
    if minutes_to_close <= no_entry_minutes:
        flatten = minutes_to_close <= flatten_minutes
        return MarketPermission(
            decision=HardDecision.BLOCK,
            state=MarketState.PRE_CLOSE,
            reason="PRE_CLOSE_FLATTEN" if flatten else "SESSION_PRE_CLOSE",
            new_entries_allowed=False,
            flatten_required=flatten,
            minutes_to_close=minutes_to_close,
        )

    state = MarketState.HOLIDAY_CAUTION if facts.holiday_context else MarketState.OPEN
    return MarketPermission(
        decision=HardDecision.PASS,
        state=state,
        reason="HOLIDAY_CAUTION" if facts.holiday_context else "SESSION_OPEN",
        new_entries_allowed=True,
        flatten_required=False,
        minutes_to_close=minutes_to_close,
    )


def evaluate_news_permission(
    news: NewsFacts | None,
    now_utc: datetime,
    recovery: NewsRecoveryFacts | None = None,
) -> NewsPermission:
    """Apply frozen Tier-1/Tier-2 windows and explicit post-news recovery."""

    _require_utc(now_utc)
    if news is None or not news.required_event_truth_available:
        return NewsPermission(
            decision=HardDecision.UNKNOWN,
            state=NewsSafetyState.NEWS_SAFETY_UNKNOWN,
            reason="NEWS_SAFETY_UNKNOWN",
        )

    active_windows = tuple(
        window for window in news.windows if window.start_utc <= now_utc <= window.end_utc
    )
    if active_windows:
        event_ids = tuple(
            event_id
            for window in active_windows
            for event_id in window.event_ids
        )
        return NewsPermission(
            decision=HardDecision.BLOCK,
            state=NewsSafetyState.NEWS_BLACKOUT,
            reason="NEWS_BLACKOUT",
            active_event_ids=event_ids,
        )

    recovery_state = recovery or NewsRecoveryFacts()
    if recovery_state.active:
        severe_ready = (
            not recovery_state.severe_dislocation
            or recovery_state.clean_completed_m5_after_event >= 1
        )
        if not recovery_state.execution_normalized or not severe_ready:
            return NewsPermission(
                decision=HardDecision.BLOCK,
                state=NewsSafetyState.POST_NEWS_WARMUP,
                reason="POST_NEWS_WARMUP",
            )

    return NewsPermission(
        decision=HardDecision.PASS,
        state=NewsSafetyState.NEWS_CLEAR,
        reason="NEWS_CLEAR",
    )


def combine_session_news_permission(
    market: MarketPermission,
    news: NewsPermission,
) -> SessionNewsPermission:
    """Combine only session/news authority; Phase 7 adds the remaining gate inputs."""

    reasons = tuple(
        reason
        for reason in (market.reason, news.reason)
        if reason not in {"SESSION_OPEN", "NEWS_CLEAR"}
    )
    if HardDecision.BLOCK in {market.decision, news.decision}:
        decision = HardDecision.BLOCK
    elif HardDecision.UNKNOWN in {market.decision, news.decision}:
        decision = HardDecision.UNKNOWN
    else:
        decision = HardDecision.PASS
    return SessionNewsPermission(
        decision=decision,
        reasons=reasons,
        flatten_required=market.flatten_required,
        market=market,
        news=news,
    )


def _reopen_warmup(facts: BrokerSessionFacts) -> MarketPermission | None:
    if facts.reopened_at_utc is None:
        return None
    required = 2 if facts.reopen_kind is ClosureKind.WEEKEND else 1
    gap_ready = facts.weekend_gap_assessed or facts.reopen_kind is not ClosureKind.WEEKEND
    normalized = (
        facts.execution_normalized
        and not facts.unresolved_gap_or_reconciliation
        and gap_ready
    )
    if facts.clean_completed_m5_since_reopen >= required and normalized:
        return None
    return MarketPermission(
        decision=HardDecision.BLOCK,
        state=MarketState.REOPEN_WARMUP,
        reason="REOPEN_WARMUP",
        new_entries_allowed=False,
        flatten_required=False,
        clean_m5_required=required,
        clean_m5_observed=facts.clean_completed_m5_since_reopen,
    )


def _preclose_thresholds(kind: ClosureKind | None) -> tuple[float, float]:
    if kind is ClosureKind.WEEKEND:
        return 60.0, 30.0
    if kind is ClosureKind.DAILY:
        return 20.0, 10.0
    raise ValueError("verified next close requires a closure kind")


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("permission timestamps must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("permission timestamps must be UTC")
