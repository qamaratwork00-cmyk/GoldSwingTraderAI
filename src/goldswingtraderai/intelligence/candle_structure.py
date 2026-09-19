"""Causal candle/structure analysis over completed candles only.

Swing confirmation uses a volatility-normalized move-away rule, so every swing has
an explicit pivot time and later `confirmed_at` time. The algorithm never reads a
forming candle and never retroactively exposes a pivot before confirmation.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from math import isfinite
from statistics import median

from goldswingtraderai.domain.enums import (
    BreakState,
    CandleSequenceState,
    Direction,
    StructureState,
    SwingRole,
    SwingSide,
    Timeframe,
)
from goldswingtraderai.domain.market import Candle
from goldswingtraderai.intelligence.indicators import atr_series


@dataclass(frozen=True, slots=True)
class StructureConfig:
    atr_period: int = 14
    swing_reversal_atr: float = 0.80
    qualified_break_atr: float = 0.05
    followthrough_atr: float = 0.05
    expansion_range_atr: float = 1.40
    compression_range_atr: float = 0.75
    rejection_wick_body: float = 1.50
    sequence_lookback: int = 5

    def __post_init__(self) -> None:
        if self.atr_period <= 0 or self.sequence_lookback < 2:
            raise ValueError("periods/lookbacks must be positive")
        thresholds = (
            self.swing_reversal_atr,
            self.qualified_break_atr,
            self.followthrough_atr,
            self.expansion_range_atr,
            self.compression_range_atr,
            self.rejection_wick_body,
        )
        if any(not isfinite(value) for value in thresholds):
            raise ValueError("structure thresholds must be finite")
        if any(value <= 0 for value in thresholds):
            raise ValueError("structure thresholds must be positive")


@dataclass(frozen=True, slots=True)
class CandleFacts:
    time_utc: datetime
    direction: Direction
    range_size: float
    body_size: float
    body_ratio: float
    upper_wick: float
    lower_wick: float
    close_position: float
    range_atr: float | None


@dataclass(frozen=True, slots=True)
class SwingPoint:
    side: SwingSide
    price: float
    pivot_time: datetime
    confirmed_at: datetime
    role: SwingRole
    significance_atr: float


@dataclass(frozen=True, slots=True)
class BreakEvent:
    state: BreakState
    direction: Direction
    level: float
    level_pivot_time: datetime
    event_time: datetime


@dataclass(frozen=True, slots=True)
class StructureReport:
    timeframe: Timeframe
    state: StructureState
    sequence: CandleSequenceState
    latest_candle: CandleFacts
    swings: tuple[SwingPoint, ...]
    protected_high: SwingPoint | None
    protected_low: SwingPoint | None
    events: tuple[BreakEvent, ...]
    bull_evidence: float
    bear_evidence: float
    coverage: float


def candle_facts(candle: Candle, atr: float | None = None) -> CandleFacts:
    range_size = candle.high - candle.low
    body = abs(candle.close - candle.open)
    upper = candle.high - max(candle.open, candle.close)
    lower = min(candle.open, candle.close) - candle.low
    if candle.close > candle.open:
        direction = Direction.BUY
    elif candle.close < candle.open:
        direction = Direction.SELL
    else:
        direction = Direction.NONE

    return CandleFacts(
        time_utc=candle.time_utc,
        direction=direction,
        range_size=range_size,
        body_size=body,
        body_ratio=body / range_size if range_size > 0 else 0.0,
        upper_wick=upper,
        lower_wick=lower,
        close_position=(candle.close - candle.low) / range_size if range_size > 0 else 0.5,
        range_atr=(range_size / atr) if atr is not None and atr > 0 else None,
    )


def analyze_structure(
    candles: tuple[Candle, ...],
    timeframe: Timeframe,
    config: StructureConfig | None = None,
    *,
    atr_values: tuple[float | None, ...] | None = None,
) -> StructureReport:
    """Build a causal structural report from chronological completed candles."""

    if not candles:
        raise ValueError("structure analysis requires completed candles")
    cfg = config or StructureConfig()
    atr = atr_values if atr_values is not None else atr_series(candles, cfg.atr_period)
    if len(atr) != len(candles):
        raise ValueError("precomputed ATR must match candle count")
    latest_atr = atr[-1] if atr else None
    latest_facts = candle_facts(candles[-1], latest_atr)

    swings = _confirmed_swings(candles, atr, cfg)
    events, protected_high, protected_low, state = _break_events(candles, atr, swings, cfg)
    promoted_swings = _promote_protected(swings, protected_high, protected_low)
    sequence = _sequence_state(candles, atr, cfg)
    bull, bear = _directional_evidence(sequence, state, events)

    available = sum(
        value is not None
        for value in (
            latest_atr,
            swings[-1] if swings else None,
            state if state is not StructureState.UNDETERMINED else None,
        )
    )
    return StructureReport(
        timeframe=timeframe,
        state=state,
        sequence=sequence,
        latest_candle=latest_facts,
        swings=promoted_swings,
        protected_high=_find_promoted(promoted_swings, protected_high),
        protected_low=_find_promoted(promoted_swings, protected_low),
        events=events,
        bull_evidence=bull,
        bear_evidence=bear,
        coverage=available / 3.0,
    )


def _confirmed_swings(
    candles: tuple[Candle, ...],
    atr: tuple[float | None, ...],
    cfg: StructureConfig,
) -> tuple[SwingPoint, ...]:
    valid_index = next((index for index, value in enumerate(atr) if value is not None), None)
    if valid_index is None or valid_index + 1 >= len(candles):
        return ()

    next_index = valid_index + 1
    seeking = (
        SwingSide.HIGH
        if candles[next_index].close >= candles[valid_index].close
        else SwingSide.LOW
    )
    candidate_index = valid_index
    candidate_price = (
        candles[candidate_index].high if seeking is SwingSide.HIGH else candles[candidate_index].low
    )
    opposite_anchor = (
        candles[candidate_index].low if seeking is SwingSide.HIGH else candles[candidate_index].high
    )
    output: list[SwingPoint] = []

    for index in range(next_index, len(candles)):
        candle = candles[index]
        current_atr = atr[index]
        if current_atr is None or current_atr <= 0:
            continue
        threshold = current_atr * cfg.swing_reversal_atr

        if seeking is SwingSide.HIGH:
            if candle.high >= candidate_price:
                candidate_price = candle.high
                candidate_index = index
            opposite_anchor = min(opposite_anchor, candle.low)
            if candidate_price - candle.close >= threshold and index > candidate_index:
                excursion = max(candidate_price - opposite_anchor, threshold)
                output.append(
                    SwingPoint(
                        side=SwingSide.HIGH,
                        price=candidate_price,
                        pivot_time=candles[candidate_index].time_utc,
                        confirmed_at=candle.time_utc,
                        role=SwingRole.CONFIRMED,
                        significance_atr=excursion / current_atr,
                    )
                )
                seeking = SwingSide.LOW
                candidate_index = index
                candidate_price = candle.low
                opposite_anchor = candle.high
        else:
            if candle.low <= candidate_price:
                candidate_price = candle.low
                candidate_index = index
            opposite_anchor = max(opposite_anchor, candle.high)
            if candle.close - candidate_price >= threshold and index > candidate_index:
                excursion = max(opposite_anchor - candidate_price, threshold)
                output.append(
                    SwingPoint(
                        side=SwingSide.LOW,
                        price=candidate_price,
                        pivot_time=candles[candidate_index].time_utc,
                        confirmed_at=candle.time_utc,
                        role=SwingRole.CONFIRMED,
                        significance_atr=excursion / current_atr,
                    )
                )
                seeking = SwingSide.HIGH
                candidate_index = index
                candidate_price = candle.high
                opposite_anchor = candle.low

    return tuple(output)


def _state_from_available_swings(swings: list[SwingPoint]) -> StructureState:
    highs = [swing for swing in swings if swing.side is SwingSide.HIGH]
    lows = [swing for swing in swings if swing.side is SwingSide.LOW]
    if len(highs) < 2 or len(lows) < 2:
        return StructureState.UNDETERMINED

    high_delta = highs[-1].price - highs[-2].price
    low_delta = lows[-1].price - lows[-2].price
    if high_delta > 0 and low_delta > 0:
        return StructureState.BULLISH
    if high_delta < 0 and low_delta < 0:
        return StructureState.BEARISH
    if (high_delta > 0 > low_delta) or (high_delta < 0 < low_delta):
        return StructureState.TRANSITION
    return StructureState.RANGE


def _break_events(
    candles: tuple[Candle, ...],
    atr: tuple[float | None, ...],
    swings: tuple[SwingPoint, ...],
    cfg: StructureConfig,
) -> tuple[tuple[BreakEvent, ...], SwingPoint | None, SwingPoint | None, StructureState]:
    available: list[SwingPoint] = []
    events: list[BreakEvent] = []
    consumed: set[tuple[SwingSide, datetime]] = set()
    pending: tuple[SwingPoint, Direction, BreakState] | None = None
    protected_high: SwingPoint | None = None
    protected_low: SwingPoint | None = None
    state = StructureState.UNDETERMINED

    by_confirmation = sorted(swings, key=lambda swing: swing.confirmed_at)
    swing_cursor = 0

    for index, candle in enumerate(candles):
        while swing_cursor < len(by_confirmation) and by_confirmation[swing_cursor].confirmed_at <= candle.time_utc:
            available.append(by_confirmation[swing_cursor])
            swing_cursor += 1
        state = _state_from_available_swings(available)
        current_atr = atr[index]
        if current_atr is None or current_atr <= 0:
            continue

        if pending is not None:
            level_swing, direction, pending_state = pending
            follow = current_atr * cfg.followthrough_atr
            accepted = (
                candle.close >= level_swing.price + follow
                if direction is Direction.BUY
                else candle.close <= level_swing.price - follow
            )
            failed = (
                candle.close < level_swing.price
                if direction is Direction.BUY
                else candle.close > level_swing.price
            )
            if accepted:
                final_state = (
                    BreakState.CONFIRMED_MSS
                    if pending_state is BreakState.MSS_CANDIDATE
                    else BreakState.CONFIRMED_BOS
                )
                events.append(
                    BreakEvent(
                        state=final_state,
                        direction=direction,
                        level=level_swing.price,
                        level_pivot_time=level_swing.pivot_time,
                        event_time=candle.time_utc,
                    )
                )
                consumed.add((level_swing.side, level_swing.pivot_time))
                if direction is Direction.BUY:
                    lows = [swing for swing in available if swing.side is SwingSide.LOW]
                    protected_low = lows[-1] if lows else protected_low
                else:
                    highs = [swing for swing in available if swing.side is SwingSide.HIGH]
                    protected_high = highs[-1] if highs else protected_high
                pending = None
            elif failed:
                events.append(
                    BreakEvent(
                        state=BreakState.FAILED_BREAK,
                        direction=direction,
                        level=level_swing.price,
                        level_pivot_time=level_swing.pivot_time,
                        event_time=candle.time_utc,
                    )
                )
                consumed.add((level_swing.side, level_swing.pivot_time))
                pending = None
            else:
                continue

        latest_high = next(
            (
                swing
                for swing in reversed(available)
                if swing.side is SwingSide.HIGH
                and (swing.side, swing.pivot_time) not in consumed
                and swing.confirmed_at < candle.time_utc
            ),
            None,
        )
        latest_low = next(
            (
                swing
                for swing in reversed(available)
                if swing.side is SwingSide.LOW
                and (swing.side, swing.pivot_time) not in consumed
                and swing.confirmed_at < candle.time_utc
            ),
            None,
        )

        for level_swing, direction in ((latest_high, Direction.BUY), (latest_low, Direction.SELL)):
            if level_swing is None:
                continue
            penetration = current_atr * cfg.qualified_break_atr
            if direction is Direction.BUY:
                probed = candle.high > level_swing.price and candle.close <= level_swing.price
                qualified = candle.close >= level_swing.price + penetration
            else:
                probed = candle.low < level_swing.price and candle.close >= level_swing.price
                qualified = candle.close <= level_swing.price - penetration

            if probed:
                events.append(
                    BreakEvent(
                        state=BreakState.PROBE,
                        direction=direction,
                        level=level_swing.price,
                        level_pivot_time=level_swing.pivot_time,
                        event_time=candle.time_utc,
                    )
                )
            if qualified:
                against_state = (
                    direction is Direction.BUY and state is StructureState.BEARISH
                ) or (
                    direction is Direction.SELL and state is StructureState.BULLISH
                )
                event_state = BreakState.MSS_CANDIDATE if against_state else BreakState.QUALIFIED_BREAK
                events.append(
                    BreakEvent(
                        state=event_state,
                        direction=direction,
                        level=level_swing.price,
                        level_pivot_time=level_swing.pivot_time,
                        event_time=candle.time_utc,
                    )
                )
                pending = (level_swing, direction, event_state)
                break

    if events:
        latest_mss = next(
            (event for event in reversed(events) if event.state is BreakState.CONFIRMED_MSS),
            None,
        )
        latest_bos = next(
            (event for event in reversed(events) if event.state is BreakState.CONFIRMED_BOS),
            None,
        )
        if latest_mss is not None and (latest_bos is None or latest_mss.event_time >= latest_bos.event_time):
            state = StructureState.TRANSITION

    return tuple(events), protected_high, protected_low, state


def _promote_protected(
    swings: tuple[SwingPoint, ...],
    protected_high: SwingPoint | None,
    protected_low: SwingPoint | None,
) -> tuple[SwingPoint, ...]:
    promoted: list[SwingPoint] = []
    protected_keys = {
        (swing.side, swing.pivot_time)
        for swing in (protected_high, protected_low)
        if swing is not None
    }
    for swing in swings:
        if (swing.side, swing.pivot_time) in protected_keys:
            promoted.append(replace(swing, role=SwingRole.PROTECTED))
        else:
            promoted.append(swing)
    return tuple(promoted)


def _find_promoted(
    swings: tuple[SwingPoint, ...],
    original: SwingPoint | None,
) -> SwingPoint | None:
    if original is None:
        return None
    return next(
        (
            swing
            for swing in swings
            if swing.side is original.side and swing.pivot_time == original.pivot_time
        ),
        None,
    )


def _sequence_state(
    candles: tuple[Candle, ...],
    atr: tuple[float | None, ...],
    cfg: StructureConfig,
) -> CandleSequenceState:
    window = candles[-cfg.sequence_lookback :]
    latest_atr = atr[-1] if atr else None
    latest = candle_facts(window[-1], latest_atr)

    if latest.range_atr is not None and latest.range_atr >= cfg.expansion_range_atr and latest.body_ratio >= 0.60:
        if latest.direction is Direction.BUY and latest.close_position >= 0.70:
            return CandleSequenceState.BULL_EXPANSION
        if latest.direction is Direction.SELL and latest.close_position <= 0.30:
            return CandleSequenceState.BEAR_EXPANSION

    recent_ranges = [candle.high - candle.low for candle in window]
    if latest_atr is not None and latest_atr > 0 and median(recent_ranges) / latest_atr <= cfg.compression_range_atr:
        overlap_count = sum(
            min(left.high, right.high) > max(left.low, right.low)
            for left, right in zip(window, window[1:])
        )
        if overlap_count >= max(1, len(window) - 2):
            return CandleSequenceState.COMPRESSION

    body_floor = max(latest.body_size, latest.range_size * 0.10)
    if latest.lower_wick >= body_floor * cfg.rejection_wick_body and latest.close_position >= 0.60:
        return CandleSequenceState.BULL_REJECTION
    if latest.upper_wick >= body_floor * cfg.rejection_wick_body and latest.close_position <= 0.40:
        return CandleSequenceState.BEAR_REJECTION

    if len(window) >= 3:
        progress = window[-1].close - window[0].close
        positive = sum(right.close > left.close for left, right in zip(window, window[1:]))
        negative = sum(right.close < left.close for left, right in zip(window, window[1:]))
        if progress > 0 and positive > negative:
            return CandleSequenceState.BULL_CONTINUATION
        if progress < 0 and negative > positive:
            return CandleSequenceState.BEAR_CONTINUATION

    return CandleSequenceState.MIXED


def _directional_evidence(
    sequence: CandleSequenceState,
    state: StructureState,
    events: tuple[BreakEvent, ...],
) -> tuple[float, float]:
    bull = 50.0
    bear = 50.0

    if state is StructureState.BULLISH:
        bull += 20.0
        bear -= 15.0
    elif state is StructureState.BEARISH:
        bear += 20.0
        bull -= 15.0
    elif state is StructureState.TRANSITION:
        bull -= 5.0
        bear -= 5.0

    if sequence in {
        CandleSequenceState.BULL_CONTINUATION,
        CandleSequenceState.BULL_EXPANSION,
        CandleSequenceState.BULL_REJECTION,
    }:
        bull += 15.0
    elif sequence in {
        CandleSequenceState.BEAR_CONTINUATION,
        CandleSequenceState.BEAR_EXPANSION,
        CandleSequenceState.BEAR_REJECTION,
    }:
        bear += 15.0

    if events:
        latest = events[-1]
        weight = {
            BreakState.PROBE: 3.0,
            BreakState.QUALIFIED_BREAK: 8.0,
            BreakState.CONFIRMED_BOS: 15.0,
            BreakState.MSS_CANDIDATE: 10.0,
            BreakState.CONFIRMED_MSS: 18.0,
            BreakState.FAILED_BREAK: -8.0,
        }[latest.state]
        if latest.direction is Direction.BUY:
            bull += weight
        else:
            bear += weight

    return min(100.0, max(0.0, bull)), min(100.0, max(0.0, bear))
