"""Provider-neutral scheduled-news facts for Gold/USD intelligence.

This module normalizes supplied calendar records and provider health. It does not
own final NEWS_CLEAR/BLACKOUT/UNKNOWN permission.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum


class ProviderHealth(StrEnum):
    VERIFIED = "VERIFIED"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class EventTier(StrEnum):
    TIER_1 = "TIER_1"
    TIER_2 = "TIER_2"
    TIER_3 = "TIER_3"


@dataclass(frozen=True, slots=True)
class RawScheduledEvent:
    provider_event_id: str
    title: str
    currency: str
    scheduled_at_utc: datetime
    impact: str

    def __post_init__(self) -> None:
        _require_utc(self.scheduled_at_utc)
        if not self.provider_event_id.strip() or not self.title.strip():
            raise ValueError("event id/title cannot be empty")
        if not self.currency.strip():
            raise ValueError("event currency cannot be empty")


@dataclass(frozen=True, slots=True)
class ScheduledEventFact:
    event_id: str
    title: str
    currency: str
    scheduled_at_utc: datetime
    tier: EventTier
    window_before_minutes: int
    window_after_minutes: int

    @property
    def window_start_utc(self) -> datetime:
        return self.scheduled_at_utc - timedelta(minutes=self.window_before_minutes)

    @property
    def window_end_utc(self) -> datetime:
        return self.scheduled_at_utc + timedelta(minutes=self.window_after_minutes)


@dataclass(frozen=True, slots=True)
class EventWindow:
    tier: EventTier
    start_utc: datetime
    end_utc: datetime
    event_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NewsFacts:
    provider: str
    health: ProviderHealth
    fetched_at_utc: datetime | None
    mapping_version: str
    events: tuple[ScheduledEventFact, ...]
    windows: tuple[EventWindow, ...]
    required_event_truth_available: bool


_CRITICAL_TERMS = (
    "fomc",
    "federal funds rate",
    "fed rate decision",
    "powell press conference",
    "fed chair press conference",
    "cpi",
    "consumer price index",
    "nonfarm payroll",
    "non-farm payroll",
    "nfp",
    "core pce",
    "pce price index",
)
_HIGH_TERMS = (
    "ppi",
    "producer price index",
    "retail sales",
    "gdp",
    "ism",
    "jolts",
    "adp",
    "jobless claims",
    "unemployment claims",
)
_MAPPING_VERSION = "v1-baseline-2026-09"


def normalize_news_facts(
    raw_events: tuple[RawScheduledEvent, ...],
    *,
    provider: str,
    provider_health: ProviderHealth,
    fetched_at_utc: datetime | None,
    as_of_utc: datetime,
    freshness_ttl: timedelta = timedelta(minutes=30),
) -> NewsFacts:
    """Normalize provider records into auditable internal tiers/windows."""

    _require_utc(as_of_utc)
    if fetched_at_utc is not None:
        _require_utc(fetched_at_utc)
    if freshness_ttl <= timedelta(0):
        raise ValueError("freshness TTL must be positive")
    if not provider.strip():
        raise ValueError("provider cannot be empty")

    health = _effective_health(provider_health, fetched_at_utc, as_of_utc, freshness_ttl)
    facts = tuple(
        sorted(
            (_normalize_event(event) for event in raw_events),
            key=lambda event: event.scheduled_at_utc,
        )
    )
    windows = _merge_windows(facts)
    usable = health in {ProviderHealth.VERIFIED, ProviderHealth.DEGRADED}
    return NewsFacts(
        provider=provider,
        health=health,
        fetched_at_utc=fetched_at_utc,
        mapping_version=_MAPPING_VERSION,
        events=facts,
        windows=windows,
        required_event_truth_available=usable,
    )


def _normalize_event(raw: RawScheduledEvent) -> ScheduledEventFact:
    tier = classify_event_tier(raw.title, raw.impact, raw.currency)
    before, after = {
        EventTier.TIER_1: (15, 15),
        EventTier.TIER_2: (5, 5),
        EventTier.TIER_3: (0, 0),
    }[tier]
    return ScheduledEventFact(
        event_id=raw.provider_event_id.strip(),
        title=raw.title.strip(),
        currency=raw.currency.strip().upper(),
        scheduled_at_utc=raw.scheduled_at_utc,
        tier=tier,
        window_before_minutes=before,
        window_after_minutes=after,
    )


def classify_event_tier(title: str, impact: str, currency: str) -> EventTier:
    """Baseline auditable mapping; provider-specific mapping may supersede later."""

    normalized = title.casefold()
    currency_code = currency.strip().upper()
    impact_name = impact.strip().casefold()
    if currency_code == "USD" and any(term in normalized for term in _CRITICAL_TERMS):
        return EventTier.TIER_1
    if currency_code == "USD" and (
        any(term in normalized for term in _HIGH_TERMS) or impact_name in {"high", "critical"}
    ):
        return EventTier.TIER_2
    return EventTier.TIER_3


def _effective_health(
    health: ProviderHealth,
    fetched_at_utc: datetime | None,
    as_of_utc: datetime,
    ttl: timedelta,
) -> ProviderHealth:
    if health in {ProviderHealth.UNAVAILABLE, ProviderHealth.UNKNOWN}:
        return health
    if fetched_at_utc is None:
        return ProviderHealth.UNKNOWN
    if as_of_utc - fetched_at_utc > ttl:
        return ProviderHealth.STALE
    return health


def _merge_windows(events: tuple[ScheduledEventFact, ...]) -> tuple[EventWindow, ...]:
    timed = tuple(event for event in events if event.tier is not EventTier.TIER_3)
    if not timed:
        return ()
    output: list[EventWindow] = []
    current = EventWindow(
        tier=timed[0].tier,
        start_utc=timed[0].window_start_utc,
        end_utc=timed[0].window_end_utc,
        event_ids=(timed[0].event_id,),
    )
    for event in timed[1:]:
        can_merge = event.window_start_utc <= current.end_utc
        if can_merge:
            tier = EventTier.TIER_1 if EventTier.TIER_1 in {current.tier, event.tier} else EventTier.TIER_2
            current = EventWindow(
                tier=tier,
                start_utc=min(current.start_utc, event.window_start_utc),
                end_utc=max(current.end_utc, event.window_end_utc),
                event_ids=(*current.event_ids, event.event_id),
            )
            continue
        output.append(current)
        current = EventWindow(
            tier=event.tier,
            start_utc=event.window_start_utc,
            end_utc=event.window_end_utc,
            event_ids=(event.event_id,),
        )
    output.append(current)
    return tuple(output)


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("news timestamps must be timezone-aware UTC")
    if value.utcoffset().total_seconds() != 0:
        raise ValueError("news timestamps must be UTC")
