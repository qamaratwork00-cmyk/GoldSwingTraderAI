"""Lightweight EMA/RSI/ATR and normalized quantitative market context.

The functions are pure and depend only on completed candles. Thresholds are
explicit configuration baselines so research can calibrate them without hiding
magic values inside strategy code.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from statistics import median

from goldswingtraderai.domain.enums import (
    Direction,
    ExtensionState,
    MomentumPhase,
    Timeframe,
    VolatilityState,
)
from goldswingtraderai.domain.market import Candle


def _require_period(period: int) -> None:
    if period <= 0:
        raise ValueError("period must be positive")


def ema_series(values: tuple[float, ...], period: int) -> tuple[float | None, ...]:
    """Return a chronological EMA series with `None` before the seed is knowable."""

    _require_period(period)
    if not values:
        return ()
    output: list[float | None] = [None] * len(values)
    if len(values) < period:
        return tuple(output)
    seed = sum(values[:period]) / period
    output[period - 1] = seed
    multiplier = 2.0 / (period + 1.0)
    previous = seed
    for index in range(period, len(values)):
        previous = (values[index] - previous) * multiplier + previous
        output[index] = previous
    return tuple(output)


def rsi_series(values: tuple[float, ...], period: int = 14) -> tuple[float | None, ...]:
    """Return Wilder RSI using only values available at each chronological step."""

    _require_period(period)
    output: list[float | None] = [None] * len(values)
    if len(values) <= period:
        return tuple(output)
    changes = [values[index] - values[index - 1] for index in range(1, len(values))]
    gains = [max(change, 0.0) for change in changes]
    losses = [max(-change, 0.0) for change in changes]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    output[period] = _rsi_value(avg_gain, avg_loss)
    for change_index in range(period, len(changes)):
        avg_gain = ((avg_gain * (period - 1)) + gains[change_index]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[change_index]) / period
        output[change_index + 1] = _rsi_value(avg_gain, avg_loss)
    return tuple(output)


def _rsi_value(avg_gain: float, avg_loss: float) -> float:
    if avg_gain == 0.0 and avg_loss == 0.0:
        return 50.0
    if avg_loss == 0.0:
        return 100.0
    relative_strength = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + relative_strength))


def true_ranges(candles: tuple[Candle, ...]) -> tuple[float, ...]:
    if not candles:
        return ()
    output = [candles[0].high - candles[0].low]
    for previous, current in zip(candles, candles[1:]):
        output.append(
            max(
                current.high - current.low,
                abs(current.high - previous.close),
                abs(current.low - previous.close),
            )
        )
    return tuple(output)


def atr_series(candles: tuple[Candle, ...], period: int = 14) -> tuple[float | None, ...]:
    """Return chronological Wilder ATR from completed candles."""

    _require_period(period)
    ranges = true_ranges(candles)
    output: list[float | None] = [None] * len(ranges)
    if len(ranges) < period:
        return tuple(output)
    atr = sum(ranges[:period]) / period
    output[period - 1] = atr
    for index in range(period, len(ranges)):
        atr = ((atr * (period - 1)) + ranges[index]) / period
        output[index] = atr
    return tuple(output)


@dataclass(frozen=True, slots=True)
class QuantConfig:
    ema_fast_period: int = 20
    ema_slow_period: int = 50
    rsi_period: int = 14
    atr_period: int = 14
    volatility_lookback: int = 50
    quiet_ratio: float = 0.75
    building_ratio: float = 1.10
    expanding_ratio: float = 1.35
    extreme_ratio: float = 1.80
    dislocated_ratio: float = 2.50
    fresh_extension_atr: float = 0.35
    extended_atr: float = 1.00
    severe_extension_atr: float = 1.75

    def __post_init__(self) -> None:
        for period in (
            self.ema_fast_period,
            self.ema_slow_period,
            self.rsi_period,
            self.atr_period,
            self.volatility_lookback,
        ):
            _require_period(period)
        if self.ema_fast_period >= self.ema_slow_period:
            raise ValueError("fast EMA period must be below slow EMA period")
        ratios = (
            self.quiet_ratio,
            self.building_ratio,
            self.expanding_ratio,
            self.extreme_ratio,
            self.dislocated_ratio,
        )
        if any(not isfinite(value) for value in ratios):
            raise ValueError("volatility ratios must be finite")
        if tuple(sorted(ratios)) != ratios or ratios[0] <= 0:
            raise ValueError("volatility ratios must be positive and increasing")
        extensions = (self.fresh_extension_atr, self.extended_atr, self.severe_extension_atr)
        if any(not isfinite(value) for value in extensions):
            raise ValueError("extension thresholds must be finite")
        if tuple(sorted(extensions)) != extensions or extensions[0] < 0:
            raise ValueError("extension thresholds must be non-negative and increasing")


@dataclass(frozen=True, slots=True)
class IndicatorSeries:
    """Chronological indicator arrays computed once and shareable by intelligence desks."""

    ema_fast: tuple[float | None, ...]
    ema_slow: tuple[float | None, ...]
    rsi: tuple[float | None, ...]
    atr: tuple[float | None, ...]

    def __post_init__(self) -> None:
        lengths = {len(self.ema_fast), len(self.ema_slow), len(self.rsi), len(self.atr)}
        if len(lengths) != 1:
            raise ValueError("indicator series lengths must match")


@dataclass(frozen=True, slots=True)
class QuantReport:
    timeframe: Timeframe
    ema_fast: float | None
    ema_slow: float | None
    rsi: float | None
    atr: float | None
    trend_support: Direction
    volatility_state: VolatilityState
    volatility_ratio: float | None
    momentum_phase: MomentumPhase
    extension_state: ExtensionState
    extension_atr: float | None
    coverage: float


def compute_indicator_series(
    candles: tuple[Candle, ...],
    config: QuantConfig | None = None,
) -> IndicatorSeries:
    cfg = config or QuantConfig()
    closes = tuple(candle.close for candle in candles)
    return IndicatorSeries(
        ema_fast=ema_series(closes, cfg.ema_fast_period),
        ema_slow=ema_series(closes, cfg.ema_slow_period),
        rsi=rsi_series(closes, cfg.rsi_period),
        atr=atr_series(candles, cfg.atr_period),
    )


def analyze_quant(
    candles: tuple[Candle, ...],
    timeframe: Timeframe,
    config: QuantConfig | None = None,
    *,
    series: IndicatorSeries | None = None,
) -> QuantReport:
    """Summarize non-authoritative quantitative evidence for one timeframe."""

    cfg = config or QuantConfig()
    values = series or compute_indicator_series(candles, cfg)
    if values.atr and len(values.atr) != len(candles):
        raise ValueError("precomputed indicator series must match candle count")

    latest_fast = values.ema_fast[-1] if values.ema_fast else None
    latest_slow = values.ema_slow[-1] if values.ema_slow else None
    latest_rsi = values.rsi[-1] if values.rsi else None
    latest_atr = values.atr[-1] if values.atr else None

    if latest_fast is None or latest_slow is None:
        trend = Direction.NONE
    elif latest_fast > latest_slow:
        trend = Direction.BUY
    elif latest_fast < latest_slow:
        trend = Direction.SELL
    else:
        trend = Direction.NONE

    volatility_ratio = _volatility_ratio(values.atr, cfg.volatility_lookback)
    volatility_state = _volatility_state(volatility_ratio, cfg)

    extension_atr: float | None = None
    extension_state = ExtensionState.UNKNOWN
    if candles and latest_fast is not None and latest_atr is not None and latest_atr > 0:
        extension_atr = abs(candles[-1].close - latest_fast) / latest_atr
        extension_state = _extension_state(extension_atr, cfg)

    momentum_phase = _momentum_phase(
        candles,
        latest_fast,
        latest_slow,
        latest_rsi,
        latest_atr,
        extension_state,
    )
    present = sum(
        item is not None
        for item in (latest_fast, latest_slow, latest_rsi, latest_atr, volatility_ratio)
    )
    return QuantReport(
        timeframe=timeframe,
        ema_fast=latest_fast,
        ema_slow=latest_slow,
        rsi=latest_rsi,
        atr=latest_atr,
        trend_support=trend,
        volatility_state=volatility_state,
        volatility_ratio=volatility_ratio,
        momentum_phase=momentum_phase,
        extension_state=extension_state,
        extension_atr=extension_atr,
        coverage=present / 5.0,
    )


def _volatility_ratio(atr: tuple[float | None, ...], lookback: int) -> float | None:
    valid = [value for value in atr if value is not None and value > 0]
    if not valid:
        return None
    recent = valid[-lookback:]
    baseline = median(recent)
    if baseline <= 0:
        return None
    return recent[-1] / baseline


def _volatility_state(ratio: float | None, cfg: QuantConfig) -> VolatilityState:
    if ratio is None:
        return VolatilityState.UNKNOWN
    if ratio < cfg.quiet_ratio:
        return VolatilityState.QUIET
    if ratio < cfg.building_ratio:
        return VolatilityState.NORMAL
    if ratio < cfg.expanding_ratio:
        return VolatilityState.BUILDING
    if ratio < cfg.extreme_ratio:
        return VolatilityState.EXPANDING
    if ratio < cfg.dislocated_ratio:
        return VolatilityState.EXTREME
    return VolatilityState.DISLOCATED


def _extension_state(value: float, cfg: QuantConfig) -> ExtensionState:
    if value < cfg.fresh_extension_atr:
        return ExtensionState.FRESH
    if value < cfg.extended_atr:
        return ExtensionState.NORMAL
    if value < cfg.severe_extension_atr:
        return ExtensionState.EXTENDED
    return ExtensionState.SEVERELY_EXTENDED


def _momentum_phase(
    candles: tuple[Candle, ...],
    fast: float | None,
    slow: float | None,
    rsi: float | None,
    atr: float | None,
    extension: ExtensionState,
) -> MomentumPhase:
    if len(candles) < 3 or fast is None or slow is None or rsi is None or atr is None or atr <= 0:
        return MomentumPhase.UNKNOWN
    latest = candles[-1]
    previous = candles[-2]
    body = abs(latest.close - latest.open)
    directional_progress = latest.close - previous.close
    normalized_body = body / atr
    trend_up = fast > slow
    trend_down = fast < slow
    if trend_up and directional_progress < 0 and rsi < 50:
        return MomentumPhase.REVERSING
    if trend_down and directional_progress > 0 and rsi > 50:
        return MomentumPhase.REVERSING
    if extension is ExtensionState.SEVERELY_EXTENDED and normalized_body < 0.45:
        return MomentumPhase.EXHAUSTING
    if normalized_body >= 0.75 and (
        (trend_up and directional_progress > 0) or (trend_down and directional_progress < 0)
    ):
        return MomentumPhase.EXPANDING
    if (trend_up and rsi >= 55) or (trend_down and rsi <= 45):
        return MomentumPhase.BUILDING
    return MomentumPhase.MATURE
