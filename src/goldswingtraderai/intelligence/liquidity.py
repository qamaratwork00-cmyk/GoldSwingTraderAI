"""Auditable liquidity/SMC primitives built from existing structure facts.

The desk treats SMC labels as observable geometry. Related evidence is kept in one
report and bounded rather than counted as independent certainty by strategies.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from math import isfinite

from goldswingtraderai.domain.enums import BreakState, Direction, SwingRole, SwingSide, Timeframe
from goldswingtraderai.domain.market import Candle
from goldswingtraderai.intelligence.candle_structure import StructureReport, SwingPoint
from goldswingtraderai.intelligence.indicators import QuantReport


class LiquiditySide(StrEnum):
    BUY_SIDE = "BUY_SIDE"
    SELL_SIDE = "SELL_SIDE"


class LiquidityScope(StrEnum):
    INTERNAL = "INTERNAL"
    STRUCTURAL = "STRUCTURAL"


class LiquidityState(StrEnum):
    UNTOUCHED = "UNTOUCHED"
    APPROACHED = "APPROACHED"
    PROBED = "PROBED"
    SWEPT = "SWEPT"
    RECLAIMED = "RECLAIMED"
    ACCEPTED_BEYOND = "ACCEPTED_BEYOND"


class LiquidityEventType(StrEnum):
    PROBE = "PROBE"
    CONFIRMED_SWEEP = "CONFIRMED_SWEEP"
    ACCEPTED_BREAK = "ACCEPTED_BREAK"


class FVGState(StrEnum):
    FRESH = "FRESH"
    PARTIAL = "PARTIAL"
    MITIGATED = "MITIGATED"


class OrderBlockState(StrEnum):
    FRESH = "FRESH"
    TESTED = "TESTED"
    INVALIDATED = "INVALIDATED"


class LiquidityPath(StrEnum):
    OPEN = "OPEN"
    MIXED = "MIXED"
    CROWDED = "CROWDED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class LiquidityConfig:
    cluster_atr_fraction: float = 0.10
    min_cluster_ticks: int = 4
    approach_atr_fraction: float = 0.15
    max_source_swings: int = 20
    max_fvgs: int = 12
    ob_lookback: int = 6
    path_horizon_atr: float = 2.0

    def __post_init__(self) -> None:
        fractions = (
            self.cluster_atr_fraction,
            self.approach_atr_fraction,
            self.path_horizon_atr,
        )
        if any(not isfinite(value) for value in fractions):
            raise ValueError("liquidity thresholds must be finite")
        if self.cluster_atr_fraction <= 0 or self.approach_atr_fraction <= 0:
            raise ValueError("liquidity normalization must be positive")
        if self.min_cluster_ticks <= 0 or self.max_source_swings <= 0:
            raise ValueError("liquidity counts must be positive")
        if self.max_fvgs <= 0 or self.ob_lookback <= 0 or self.path_horizon_atr <= 0:
            raise ValueError("liquidity lookbacks/horizons must be positive")


@dataclass(frozen=True, slots=True)
class LiquidityPool:
    side: LiquiditySide
    scope: LiquidityScope
    timeframe: Timeframe
    lower: float
    upper: float
    created_at: datetime
    source_count: int
    significance: float
    state: LiquidityState

    @property
    def midpoint(self) -> float:
        return (self.lower + self.upper) / 2.0


@dataclass(frozen=True, slots=True)
class LiquidityEvent:
    event_type: LiquidityEventType
    pool_side: LiquiditySide
    direction: Direction
    level: float
    event_time: datetime


@dataclass(frozen=True, slots=True)
class FairValueGap:
    direction: Direction
    timeframe: Timeframe
    lower: float
    upper: float
    created_at: datetime
    fill_fraction: float
    state: FVGState


@dataclass(frozen=True, slots=True)
class OrderBlock:
    direction: Direction
    timeframe: Timeframe
    lower: float
    upper: float
    origin_time: datetime
    qualified_at: datetime
    source_break: BreakState
    state: OrderBlockState


@dataclass(frozen=True, slots=True)
class LiquidityReport:
    timeframe: Timeframe
    pools: tuple[LiquidityPool, ...]
    events: tuple[LiquidityEvent, ...]
    fvgs: tuple[FairValueGap, ...]
    order_blocks: tuple[OrderBlock, ...]
    nearest_buy_side: LiquidityPool | None
    nearest_sell_side: LiquidityPool | None
    path_up: LiquidityPath
    path_down: LiquidityPath
    buy_evidence: float
    sell_evidence: float
    coverage: float


def analyze_liquidity(
    candles: tuple[Candle, ...],
    structure: StructureReport,
    quant: QuantReport,
    *,
    current_price: float,
    tick_size: float,
    config: LiquidityConfig | None = None,
) -> LiquidityReport:
    """Build pools/events/FVG/qualified-OB facts without creating trade authority."""

    if not candles:
        raise ValueError("liquidity analysis requires completed candles")
    if structure.timeframe is not quant.timeframe:
        raise ValueError("structure and quant timeframes must match")
    if current_price <= 0 or tick_size <= 0:
        raise ValueError("price and tick size must be positive")

    cfg = config or LiquidityConfig()
    atr = quant.atr
    tolerance = max(tick_size * cfg.min_cluster_ticks, (atr or tick_size) * cfg.cluster_atr_fraction)
    pools = _build_pools(
        structure.swings[-cfg.max_source_swings :],
        candles,
        structure.timeframe,
        tolerance,
        atr,
        cfg,
    )
    events = _pool_events(pools, candles)
    fvgs = _fair_value_gaps(candles, structure.timeframe, cfg.max_fvgs)
    order_blocks = _order_blocks(candles, structure, cfg)

    buy_side = min(
        (pool for pool in pools if pool.side is LiquiditySide.BUY_SIDE and pool.upper >= current_price),
        key=lambda pool: pool.midpoint,
        default=None,
    )
    sell_side = max(
        (pool for pool in pools if pool.side is LiquiditySide.SELL_SIDE and pool.lower <= current_price),
        key=lambda pool: pool.midpoint,
        default=None,
    )
    path_up = _path_quality(pools, current_price, atr, cfg, upward=True)
    path_down = _path_quality(pools, current_price, atr, cfg, upward=False)
    buy_evidence, sell_evidence = _directional_evidence(events, fvgs, order_blocks)

    coverage_parts = (bool(pools), atr is not None, bool(fvgs) or bool(order_blocks) or bool(events))
    return LiquidityReport(
        timeframe=structure.timeframe,
        pools=pools,
        events=events,
        fvgs=fvgs,
        order_blocks=order_blocks,
        nearest_buy_side=buy_side,
        nearest_sell_side=sell_side,
        path_up=path_up,
        path_down=path_down,
        buy_evidence=buy_evidence,
        sell_evidence=sell_evidence,
        coverage=sum(coverage_parts) / len(coverage_parts),
    )


def _build_pools(
    swings: tuple[SwingPoint, ...],
    candles: tuple[Candle, ...],
    timeframe: Timeframe,
    tolerance: float,
    atr: float | None,
    cfg: LiquidityConfig,
) -> tuple[LiquidityPool, ...]:
    groups: list[list[SwingPoint]] = []
    for side in (SwingSide.LOW, SwingSide.HIGH):
        ordered = sorted((swing for swing in swings if swing.side is side), key=lambda item: item.price)
        for swing in ordered:
            if groups and groups[-1][0].side is side:
                center = sum(item.price for item in groups[-1]) / len(groups[-1])
                if abs(swing.price - center) <= tolerance:
                    groups[-1].append(swing)
                    continue
            groups.append([swing])

    pools: list[LiquidityPool] = []
    for group in groups:
        lower = min(item.price for item in group) - tolerance / 2.0
        upper = max(item.price for item in group) + tolerance / 2.0
        created_at = max(item.confirmed_at for item in group)
        scope = (
            LiquidityScope.STRUCTURAL
            if any(item.role is SwingRole.PROTECTED for item in group)
            else LiquidityScope.INTERNAL
        )
        base = LiquidityPool(
            side=LiquiditySide.BUY_SIDE if group[0].side is SwingSide.HIGH else LiquiditySide.SELL_SIDE,
            scope=scope,
            timeframe=timeframe,
            lower=lower,
            upper=upper,
            created_at=created_at,
            source_count=len(group),
            significance=max(item.significance_atr for item in group),
            state=LiquidityState.UNTOUCHED,
        )
        pools.append(_with_pool_state(base, candles, atr, cfg))
    return tuple(sorted(pools, key=lambda pool: pool.midpoint))


def _with_pool_state(
    pool: LiquidityPool,
    candles: tuple[Candle, ...],
    atr: float | None,
    cfg: LiquidityConfig,
) -> LiquidityPool:
    state = LiquidityState.UNTOUCHED
    approach = (atr or (pool.upper - pool.lower)) * cfg.approach_atr_fraction
    for candle in candles:
        if candle.time_utc <= pool.created_at:
            continue
        if pool.side is LiquiditySide.BUY_SIDE:
            if candle.close > pool.upper:
                state = LiquidityState.ACCEPTED_BEYOND
            elif candle.high > pool.upper:
                state = LiquidityState.RECLAIMED
            elif candle.high >= pool.lower:
                state = LiquidityState.PROBED
            elif pool.lower - candle.high <= approach and state is LiquidityState.UNTOUCHED:
                state = LiquidityState.APPROACHED
        else:
            if candle.close < pool.lower:
                state = LiquidityState.ACCEPTED_BEYOND
            elif candle.low < pool.lower:
                state = LiquidityState.RECLAIMED
            elif candle.low <= pool.upper:
                state = LiquidityState.PROBED
            elif candle.low - pool.upper <= approach and state is LiquidityState.UNTOUCHED:
                state = LiquidityState.APPROACHED
    return LiquidityPool(
        side=pool.side,
        scope=pool.scope,
        timeframe=pool.timeframe,
        lower=pool.lower,
        upper=pool.upper,
        created_at=pool.created_at,
        source_count=pool.source_count,
        significance=pool.significance,
        state=state,
    )


def _pool_events(
    pools: tuple[LiquidityPool, ...],
    candles: tuple[Candle, ...],
) -> tuple[LiquidityEvent, ...]:
    events: list[LiquidityEvent] = []
    for pool in pools:
        for candle in candles:
            if candle.time_utc <= pool.created_at:
                continue
            if pool.side is LiquiditySide.BUY_SIDE:
                if candle.close > pool.upper:
                    events.append(
                        LiquidityEvent(
                            event_type=LiquidityEventType.ACCEPTED_BREAK,
                            pool_side=pool.side,
                            direction=Direction.BUY,
                            level=pool.midpoint,
                            event_time=candle.time_utc,
                        )
                    )
                    break
                if candle.high > pool.upper and candle.close <= pool.upper:
                    events.append(
                        LiquidityEvent(
                            event_type=LiquidityEventType.CONFIRMED_SWEEP,
                            pool_side=pool.side,
                            direction=Direction.SELL,
                            level=pool.midpoint,
                            event_time=candle.time_utc,
                        )
                    )
                    break
                if candle.high >= pool.lower:
                    events.append(
                        LiquidityEvent(
                            event_type=LiquidityEventType.PROBE,
                            pool_side=pool.side,
                            direction=Direction.NONE,
                            level=pool.midpoint,
                            event_time=candle.time_utc,
                        )
                    )
                    break
            else:
                if candle.close < pool.lower:
                    events.append(
                        LiquidityEvent(
                            event_type=LiquidityEventType.ACCEPTED_BREAK,
                            pool_side=pool.side,
                            direction=Direction.SELL,
                            level=pool.midpoint,
                            event_time=candle.time_utc,
                        )
                    )
                    break
                if candle.low < pool.lower and candle.close >= pool.lower:
                    events.append(
                        LiquidityEvent(
                            event_type=LiquidityEventType.CONFIRMED_SWEEP,
                            pool_side=pool.side,
                            direction=Direction.BUY,
                            level=pool.midpoint,
                            event_time=candle.time_utc,
                        )
                    )
                    break
                if candle.low <= pool.upper:
                    events.append(
                        LiquidityEvent(
                            event_type=LiquidityEventType.PROBE,
                            pool_side=pool.side,
                            direction=Direction.NONE,
                            level=pool.midpoint,
                            event_time=candle.time_utc,
                        )
                    )
                    break
    return tuple(sorted(events, key=lambda event: event.event_time))


def _fair_value_gaps(
    candles: tuple[Candle, ...],
    timeframe: Timeframe,
    max_count: int,
) -> tuple[FairValueGap, ...]:
    gaps: list[FairValueGap] = []
    for index in range(2, len(candles)):
        first = candles[index - 2]
        third = candles[index]
        if third.low > first.high:
            gaps.append(
                _fvg_with_fill(
                    Direction.BUY,
                    timeframe,
                    first.high,
                    third.low,
                    third.time_utc,
                    candles[index + 1 :],
                )
            )
        elif third.high < first.low:
            gaps.append(
                _fvg_with_fill(
                    Direction.SELL,
                    timeframe,
                    third.high,
                    first.low,
                    third.time_utc,
                    candles[index + 1 :],
                )
            )
    return tuple(gaps[-max_count:])


def _fvg_with_fill(
    direction: Direction,
    timeframe: Timeframe,
    lower: float,
    upper: float,
    created_at: datetime,
    later: tuple[Candle, ...],
) -> FairValueGap:
    width = upper - lower
    if direction is Direction.BUY:
        deepest = min((candle.low for candle in later), default=upper)
        fill = (upper - min(upper, deepest)) / width
    else:
        highest = max((candle.high for candle in later), default=lower)
        fill = (max(lower, highest) - lower) / width
    fill = min(1.0, max(0.0, fill))
    state = FVGState.FRESH if fill == 0 else FVGState.MITIGATED if fill >= 1 else FVGState.PARTIAL
    return FairValueGap(
        direction=direction,
        timeframe=timeframe,
        lower=lower,
        upper=upper,
        created_at=created_at,
        fill_fraction=fill,
        state=state,
    )


def _order_blocks(
    candles: tuple[Candle, ...],
    structure: StructureReport,
    cfg: LiquidityConfig,
) -> tuple[OrderBlock, ...]:
    candidates: dict[tuple[Direction, datetime], OrderBlock] = {}
    eligible = {
        BreakState.QUALIFIED_BREAK,
        BreakState.CONFIRMED_BOS,
        BreakState.MSS_CANDIDATE,
        BreakState.CONFIRMED_MSS,
    }
    time_to_index = {candle.time_utc: index for index, candle in enumerate(candles)}

    for event in structure.events:
        if event.state not in eligible or event.direction is Direction.NONE:
            continue
        event_index = time_to_index.get(event.event_time)
        if event_index is None:
            continue
        start = max(0, event_index - cfg.ob_lookback)
        opposite = Direction.SELL if event.direction is Direction.BUY else Direction.BUY
        origin_index = next(
            (
                index
                for index in range(event_index - 1, start - 1, -1)
                if _candle_direction(candles[index]) is opposite
            ),
            None,
        )
        if origin_index is None:
            continue
        origin = candles[origin_index]
        state = _order_block_state(
            event.direction,
            origin.low,
            origin.high,
            candles[event_index + 1 :],
        )
        candidates[(event.direction, origin.time_utc)] = OrderBlock(
            direction=event.direction,
            timeframe=structure.timeframe,
            lower=origin.low,
            upper=origin.high,
            origin_time=origin.time_utc,
            qualified_at=event.event_time,
            source_break=event.state,
            state=state,
        )
    return tuple(sorted(candidates.values(), key=lambda block: block.qualified_at))


def _order_block_state(
    direction: Direction,
    lower: float,
    upper: float,
    later: tuple[Candle, ...],
) -> OrderBlockState:
    tested = False
    for candle in later:
        if direction is Direction.BUY:
            if candle.close < lower:
                return OrderBlockState.INVALIDATED
            tested = tested or candle.low <= upper
        else:
            if candle.close > upper:
                return OrderBlockState.INVALIDATED
            tested = tested or candle.high >= lower
    return OrderBlockState.TESTED if tested else OrderBlockState.FRESH


def _candle_direction(candle: Candle) -> Direction:
    if candle.close > candle.open:
        return Direction.BUY
    if candle.close < candle.open:
        return Direction.SELL
    return Direction.NONE


def _path_quality(
    pools: tuple[LiquidityPool, ...],
    price: float,
    atr: float | None,
    cfg: LiquidityConfig,
    *,
    upward: bool,
) -> LiquidityPath:
    if atr is None or atr <= 0:
        return LiquidityPath.UNKNOWN
    horizon = atr * cfg.path_horizon_atr
    if upward:
        count = sum(price < pool.midpoint <= price + horizon for pool in pools)
    else:
        count = sum(price - horizon <= pool.midpoint < price for pool in pools)
    if count <= 1:
        return LiquidityPath.OPEN
    if count <= 3:
        return LiquidityPath.MIXED
    return LiquidityPath.CROWDED


def _directional_evidence(
    events: tuple[LiquidityEvent, ...],
    fvgs: tuple[FairValueGap, ...],
    order_blocks: tuple[OrderBlock, ...],
) -> tuple[float, float]:
    bull_components: list[float] = []
    bear_components: list[float] = []

    for event in events[-4:]:
        if event.direction is Direction.BUY:
            bull_components.append(20.0 if event.event_type is LiquidityEventType.CONFIRMED_SWEEP else 12.0)
        elif event.direction is Direction.SELL:
            bear_components.append(20.0 if event.event_type is LiquidityEventType.CONFIRMED_SWEEP else 12.0)

    if any(gap.direction is Direction.BUY and gap.state is not FVGState.MITIGATED for gap in fvgs[-4:]):
        bull_components.append(8.0)
    if any(gap.direction is Direction.SELL and gap.state is not FVGState.MITIGATED for gap in fvgs[-4:]):
        bear_components.append(8.0)
    if any(block.direction is Direction.BUY and block.state is not OrderBlockState.INVALIDATED for block in order_blocks[-4:]):
        bull_components.append(8.0)
    if any(block.direction is Direction.SELL and block.state is not OrderBlockState.INVALIDATED for block in order_blocks[-4:]):
        bear_components.append(8.0)

    # Correlated liquidity primitives are deliberately capped so one episode cannot
    # masquerade as several independent proofs.
    bull = 50.0 + min(30.0, sum(bull_components))
    bear = 50.0 + min(30.0, sum(bear_components))
    return bull, bear
