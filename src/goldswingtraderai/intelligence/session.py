"""Timezone-safe Asia/London/New York session context.

This module publishes soft market context only. Broker OPEN/CLOSED/PRE_CLOSE
permission remains outside market intelligence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from zoneinfo import ZoneInfo

from goldswingtraderai.domain.market import Candle


class SessionName(StrEnum):
    ASIA = "ASIA"
    LONDON = "LONDON"
    NEW_YORK = "NEW_YORK"
    LONDON_NY_OVERLAP = "LONDON_NY_OVERLAP"
    OFF_HOURS = "OFF_HOURS"


@dataclass(frozen=True, slots=True)
class SessionConfig:
    asia_start_utc: int = 0
    asia_end_utc: int = 8
    london_start_local: int = 8
    london_end_local: int = 16
    new_york_start_local: int = 8
    new_york_end_local: int = 17

    def __post_init__(self) -> None:
        for value in (
            self.asia_start_utc,
            self.asia_end_utc,
            self.london_start_local,
            self.london_end_local,
            self.new_york_start_local,
            self.new_york_end_local,
        ):
            if not 0 <= value <= 24:
                raise ValueError("session hours must be between 0 and 24")


@dataclass(frozen=True, slots=True)
class SessionReport:
    current: SessionName
    current_high: float | None
    current_low: float | None
    current_range: float | None
    previous: SessionName | None
    previous_high: float | None
    previous_low: float | None
    overlap: bool
    holiday_context: bool
    coverage: float


def classify_session(
    when_utc: datetime,
    config: SessionConfig | None = None,
) -> SessionName:
    """Classify one UTC timestamp with DST-aware London/New York conversion."""

    _require_utc(when_utc)
    cfg = config or SessionConfig()
    london = when_utc.astimezone(ZoneInfo("Europe/London"))
    new_york = when_utc.astimezone(ZoneInfo("America/New_York"))

    london_active = cfg.london_start_local <= _hour_fraction(london) < cfg.london_end_local
    ny_active = cfg.new_york_start_local <= _hour_fraction(new_york) < cfg.new_york_end_local
    asia_active = cfg.asia_start_utc <= _hour_fraction(when_utc) < cfg.asia_end_utc

    if london_active and ny_active:
        return SessionName.LONDON_NY_OVERLAP
    if london_active:
        return SessionName.LONDON
    if ny_active:
        return SessionName.NEW_YORK
    if asia_active:
        return SessionName.ASIA
    return SessionName.OFF_HOURS


def analyze_session(
    candles: tuple[Candle, ...],
    as_of_utc: datetime,
    *,
    holiday_context: bool = False,
    config: SessionConfig | None = None,
) -> SessionReport:
    """Summarize current and most recent prior session from completed candles."""

    _require_utc(as_of_utc)
    cfg = config or SessionConfig()
    current = classify_session(as_of_utc, cfg)
    eligible = tuple(candle for candle in candles if candle.time_utc <= as_of_utc)

    current_candles = _trailing_session_group(eligible, current, cfg)
    previous_name, previous_candles = _previous_group(eligible, current_candles, cfg)

    current_high, current_low = _high_low(current_candles)
    previous_high, previous_low = _high_low(previous_candles)
    current_range = (
        current_high - current_low
        if current_high is not None and current_low is not None
        else None
    )
    coverage = 1.0 if current_candles else (0.5 if eligible else 0.0)

    return SessionReport(
        current=current,
        current_high=current_high,
        current_low=current_low,
        current_range=current_range,
        previous=previous_name,
        previous_high=previous_high,
        previous_low=previous_low,
        overlap=current is SessionName.LONDON_NY_OVERLAP,
        holiday_context=holiday_context,
        coverage=coverage,
    )


def _trailing_session_group(
    candles: tuple[Candle, ...],
    session: SessionName,
    cfg: SessionConfig,
) -> tuple[Candle, ...]:
    if not candles:
        return ()
    selected: list[Candle] = []
    started = False
    for candle in reversed(candles):
        label = classify_session(candle.time_utc, cfg)
        if label is session:
            selected.append(candle)
            started = True
        elif started:
            break
    return tuple(reversed(selected))


def _previous_group(
    candles: tuple[Candle, ...],
    current_group: tuple[Candle, ...],
    cfg: SessionConfig,
) -> tuple[SessionName | None, tuple[Candle, ...]]:
    if not candles:
        return None, ()
    cutoff = current_group[0].time_utc if current_group else candles[-1].time_utc
    earlier = tuple(candle for candle in candles if candle.time_utc < cutoff)
    if not earlier:
        return None, ()
    previous = classify_session(earlier[-1].time_utc, cfg)
    return previous, _trailing_session_group(earlier, previous, cfg)


def _high_low(candles: tuple[Candle, ...]) -> tuple[float | None, float | None]:
    if not candles:
        return None, None
    return max(candle.high for candle in candles), min(candle.low for candle in candles)


def _hour_fraction(value: datetime) -> float:
    return value.hour + value.minute / 60.0 + value.second / 3600.0


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("session timestamps must be timezone-aware UTC")
    if value.utcoffset().total_seconds() != 0:
        raise ValueError("session timestamps must be UTC")
