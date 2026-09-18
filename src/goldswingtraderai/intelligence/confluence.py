"""Causal technical confluence: trendlines, Fibonacci geometry and broker-volume POC.

These facts are soft market intelligence only. They never grant trading permission and
never require every confluence source to be present. Trendline/Fibonacci anchors use
only already-confirmed swings; POC is explicitly broker-local volume context.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import floor

from goldswingtraderai.domain.enums import Direction, SwingRole, SwingSide, Timeframe
from goldswingtraderai.domain.market import Candle
from goldswingtraderai.intelligence.candle_structure import StructureReport, SwingPoint
from goldswingtraderai.intelligence.indicators import QuantReport


class TrendlineSide(StrEnum):
    SUPPORT = "SUPPORT"
    RESISTANCE = "RESISTANCE"


class TrendlineSlope(StrEnum):
    ASCENDING = "ASCENDING"
    DESCENDING = "DESCENDING"
    FLAT = "FLAT"


class LineEvent(StrEnum):
    NONE = "NONE"
    TOUCH = "TOUCH"
    BREAK = "BREAK"
    RECLAIM = "RECLAIM"


class FibLevelKind(StrEnum):
    RETRACEMENT = "RETRACEMENT"
    EXTENSION = "EXTENSION"


class VolumeSource(StrEnum):
    REAL_VOLUME = "REAL_VOLUME"
    TICK_VOLUME = "TICK_VOLUME"


class PocRelation(StrEnum):
    ABOVE = "ABOVE"
    BELOW = "BELOW"
    NEAR = "NEAR"


@dataclass(frozen=True, slots=True)
class ConfluenceConfig:
    trendline_near_atr: float = 0.20
    trendline_break_buffer_atr: float = 0.05
    min_fib_leg_atr: float = 0.80
    profile_lookback: int = 96
    profile_bins: int = 24
    poc_near_atr: float = 0.15

    def __post_init__(self) -> None:
        if self.trendline_near_atr <= 0 or self.trendline_break_buffer_atr < 0:
            raise ValueError("trendline thresholds are invalid")
        if self.min_fib_leg_atr < 0:
            raise ValueError("minimum Fibonacci leg cannot be negative")
        if self.profile_lookback < 10 or self.profile_bins < 4:
            raise ValueError("volume profile dimensions are too small")
        if self.poc_near_atr < 0:
            raise ValueError("POC proximity threshold cannot be negative")


@dataclass(frozen=True, slots=True)
class Trendline:
    side: TrendlineSide
    timeframe: Timeframe
    first_pivot: SwingPoint
    second_pivot: SwingPoint
    slope_per_bar: float
    slope: TrendlineSlope
    projected_price: float
    distance_atr: float | None
    event: LineEvent


@dataclass(frozen=True, slots=True)
class FibLevel:
    ratio: float
    price: float
    kind: FibLevelKind


@dataclass(frozen=True, slots=True)
class FibonacciContext:
    direction: Direction
    anchor_from: SwingPoint
    anchor_to: SwingPoint
    leg_size: float
    levels: tuple[FibLevel, ...]
    nearest_ratio: float
    nearest_price: float
    in_core_retracement: bool
    in_deep_retracement: bool


@dataclass(frozen=True, slots=True)
class VolumeProfileContext:
    source: VolumeSource
    lookback_bars: int
    bins: int
    poc_price: float
    total_volume: float
    relation: PocRelation
    distance_atr: float | None


@dataclass(frozen=True, slots=True)
class ConfluenceReport:
    timeframe: Timeframe
    support_trendline: Trendline | None
    resistance_trendline: Trendline | None
    fibonacci: FibonacciContext | None
    volume_profile: VolumeProfileContext | None
    buy_bonus: float | None
    sell_bonus: float | None
    evidence: tuple[str, ...]


def analyze_confluence(
    candles: tuple[Candle, ...],
    structure: StructureReport,
    quant: QuantReport,
    *,
    current_price: float,
    tick_size: float,
    config: ConfluenceConfig | None = None,
) -> ConfluenceReport:
    """Build optional confluence facts without turning them into hard filters."""

    if not candles:
        raise ValueError("confluence analysis requires completed candles")
    if current_price <= 0 or tick_size <= 0:
        raise ValueError("price and tick size must be positive")
    if structure.timeframe is not quant.timeframe:
        raise ValueError("structure and quant timeframes must match")

    cfg = config or ConfluenceConfig()
    atr = quant.atr
    support = _trendline(
        candles,
        structure,
        SwingSide.LOW,
        TrendlineSide.SUPPORT,
        atr,
        tick_size,
        cfg,
    )
    resistance = _trendline(
        candles,
        structure,
        SwingSide.HIGH,
        TrendlineSide.RESISTANCE,
        atr,
        tick_size,
        cfg,
    )
    fib = _fibonacci(structure, current_price, atr, cfg)
    profile = _volume_profile(candles, current_price, atr, cfg)

    buy_parts: list[float] = []
    sell_parts: list[float] = []
    evidence: list[str] = []

    if support is not None:
        if support.event is LineEvent.RECLAIM:
            buy_parts.append(92.0)
            evidence.append("TRENDLINE_SUPPORT_RECLAIM")
        elif support.event is LineEvent.TOUCH:
            buy_parts.append(80.0)
            evidence.append("TRENDLINE_SUPPORT_TOUCH")
    if resistance is not None:
        if resistance.event is LineEvent.RECLAIM:
            sell_parts.append(92.0)
            evidence.append("TRENDLINE_RESISTANCE_RECLAIM")
        elif resistance.event is LineEvent.TOUCH:
            sell_parts.append(80.0)
            evidence.append("TRENDLINE_RESISTANCE_TOUCH")

    if fib is not None:
        if fib.in_core_retracement:
            score = 82.0
            evidence.append(f"FIB_CORE_{fib.direction.value}")
        elif fib.in_deep_retracement:
            score = 72.0
            evidence.append(f"FIB_DEEP_{fib.direction.value}")
        else:
            score = 0.0
        if score > 0:
            (buy_parts if fib.direction is Direction.BUY else sell_parts).append(score)

    if profile is not None and profile.relation is PocRelation.NEAR:
        evidence.append("POC_NEAR")

    return ConfluenceReport(
        timeframe=structure.timeframe,
        support_trendline=support,
        resistance_trendline=resistance,
        fibonacci=fib,
        volume_profile=profile,
        buy_bonus=_average_or_none(buy_parts),
        sell_bonus=_average_or_none(sell_parts),
        evidence=tuple(evidence),
    )


def _trendline(
    candles: tuple[Candle, ...],
    structure: StructureReport,
    swing_side: SwingSide,
    line_side: TrendlineSide,
    atr: float | None,
    tick_size: float,
    cfg: ConfluenceConfig,
) -> Trendline | None:
    index_by_time = {candle.time_utc: index for index, candle in enumerate(candles)}
    eligible = [
        swing
        for swing in structure.swings
        if swing.side is swing_side
        and swing.role is not SwingRole.CANDIDATE
        and swing.pivot_time in index_by_time
        and swing.confirmed_at <= candles[-1].time_utc
    ]
    if len(eligible) < 2:
        return None
    first, second = eligible[-2:]
    first_index = index_by_time[first.pivot_time]
    second_index = index_by_time[second.pivot_time]
    if second_index <= first_index:
        return None

    slope_per_bar = (second.price - first.price) / (second_index - first_index)
    last_index = len(candles) - 1
    projected = first.price + slope_per_bar * (last_index - first_index)
    previous_projected = first.price + slope_per_bar * (max(0, last_index - 1) - first_index)
    current_close = candles[-1].close
    previous_close = candles[-2].close if len(candles) > 1 else current_close
    buffer = max(tick_size * 2.0, (atr or 0.0) * cfg.trendline_break_buffer_atr)
    near_distance = max(tick_size * 2.0, (atr or 0.0) * cfg.trendline_near_atr)

    if line_side is TrendlineSide.SUPPORT:
        broke = previous_close >= previous_projected - buffer and current_close < projected - buffer
        reclaimed = previous_close < previous_projected - buffer and current_close >= projected + buffer
    else:
        broke = previous_close <= previous_projected + buffer and current_close > projected + buffer
        reclaimed = previous_close > previous_projected + buffer and current_close <= projected - buffer

    if broke:
        event = LineEvent.BREAK
    elif reclaimed:
        event = LineEvent.RECLAIM
    elif abs(current_close - projected) <= near_distance:
        event = LineEvent.TOUCH
    else:
        event = LineEvent.NONE

    if abs(slope_per_bar) <= tick_size * 0.25:
        slope = TrendlineSlope.FLAT
    elif slope_per_bar > 0:
        slope = TrendlineSlope.ASCENDING
    else:
        slope = TrendlineSlope.DESCENDING

    return Trendline(
        side=line_side,
        timeframe=structure.timeframe,
        first_pivot=first,
        second_pivot=second,
        slope_per_bar=slope_per_bar,
        slope=slope,
        projected_price=projected,
        distance_atr=(abs(current_price - projected) / atr) if atr is not None and atr > 0 else None,
        event=event,
    )


def _fibonacci(
    structure: StructureReport,
    current_price: float,
    atr: float | None,
    cfg: ConfluenceConfig,
) -> FibonacciContext | None:
    swings = [swing for swing in structure.swings if swing.role is not SwingRole.CANDIDATE]
    pair: tuple[SwingPoint, SwingPoint] | None = None
    for first, second in zip(reversed(swings[:-1]), reversed(swings[1:])):
        if first.side is second.side or second.pivot_time <= first.pivot_time:
            continue
        leg = abs(second.price - first.price)
        if atr is not None and atr > 0 and leg / atr < cfg.min_fib_leg_atr:
            continue
        pair = (first, second)
        break
    if pair is None:
        return None

    first, second = pair
    if first.side is SwingSide.LOW and second.side is SwingSide.HIGH:
        direction = Direction.BUY
    elif first.side is SwingSide.HIGH and second.side is SwingSide.LOW:
        direction = Direction.SELL
    else:
        return None

    leg = abs(second.price - first.price)
    retracement_ratios = (0.382, 0.500, 0.618, 0.786)
    extension_ratios = (1.272, 1.618, 2.000)
    levels: list[FibLevel] = []
    for ratio in retracement_ratios:
        price = (
            second.price - leg * ratio
            if direction is Direction.BUY
            else second.price + leg * ratio
        )
        levels.append(FibLevel(ratio=ratio, price=price, kind=FibLevelKind.RETRACEMENT))
    for ratio in extension_ratios:
        extension = leg * (ratio - 1.0)
        price = (
            second.price + extension
            if direction is Direction.BUY
            else second.price - extension
        )
        levels.append(FibLevel(ratio=ratio, price=price, kind=FibLevelKind.EXTENSION))

    nearest = min(levels, key=lambda level: abs(level.price - current_price))
    r382 = next(level.price for level in levels if level.ratio == 0.382)
    r618 = next(level.price for level in levels if level.ratio == 0.618)
    r786 = next(level.price for level in levels if level.ratio == 0.786)
    core_low, core_high = sorted((r382, r618))
    deep_low, deep_high = sorted((r618, r786))
    return FibonacciContext(
        direction=direction,
        anchor_from=first,
        anchor_to=second,
        leg_size=leg,
        levels=tuple(levels),
        nearest_ratio=nearest.ratio,
        nearest_price=nearest.price,
        in_core_retracement=core_low <= current_price <= core_high,
        in_deep_retracement=deep_low <= current_price <= deep_high,
    )


def _volume_profile(
    candles: tuple[Candle, ...],
    current_price: float,
    atr: float | None,
    cfg: ConfluenceConfig,
) -> VolumeProfileContext | None:
    sample = candles[-cfg.profile_lookback :]
    use_real = sum(candle.real_volume for candle in sample) > 0
    volumes = tuple(
        float(candle.real_volume if use_real else candle.tick_volume)
        for candle in sample
    )
    total_volume = sum(volumes)
    if total_volume <= 0:
        return None

    low = min(candle.low for candle in sample)
    high = max(candle.high for candle in sample)
    span = high - low
    if span <= 0:
        return None
    bin_width = span / cfg.profile_bins
    buckets = [0.0] * cfg.profile_bins

    for candle, volume in zip(sample, volumes):
        if volume <= 0:
            continue
        start = min(cfg.profile_bins - 1, max(0, floor((candle.low - low) / bin_width)))
        end = min(cfg.profile_bins - 1, max(0, floor((candle.high - low) / bin_width)))
        count = max(1, end - start + 1)
        share = volume / count
        for index in range(start, end + 1):
            buckets[index] += share

    poc_index = max(range(cfg.profile_bins), key=buckets.__getitem__)
    poc_price = low + (poc_index + 0.5) * bin_width
    distance = abs(current_price - poc_price)
    near = max(bin_width, (atr or 0.0) * cfg.poc_near_atr)
    if distance <= near:
        relation = PocRelation.NEAR
    elif current_price > poc_price:
        relation = PocRelation.ABOVE
    else:
        relation = PocRelation.BELOW

    return VolumeProfileContext(
        source=VolumeSource.REAL_VOLUME if use_real else VolumeSource.TICK_VOLUME,
        lookback_bars=len(sample),
        bins=cfg.profile_bins,
        poc_price=poc_price,
        total_volume=total_volume,
        relation=relation,
        distance_atr=(distance / atr) if atr is not None and atr > 0 else None,
    )


def _average_or_none(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None
