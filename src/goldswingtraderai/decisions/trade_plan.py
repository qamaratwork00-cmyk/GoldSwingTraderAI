"""Structural Trade Plan built before monetary sizing.

The planner converts a READY opportunity into deterministic entry, invalidation,
stop and objective geometry. It does not size lots or place orders. Nearby noisy
obstacles stay visible without automatically becoming the Primary objective.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from math import ceil, floor, isfinite

from goldswingtraderai.decisions.opportunity import Opportunity
from goldswingtraderai.domain.enums import (
    Direction,
    OpportunityStage,
    StrategyFamily,
    SwingSide,
    Timeframe,
)
from goldswingtraderai.domain.ids import EntityId, new_trade_plan_id
from goldswingtraderai.domain.market import MarketSnapshot
from goldswingtraderai.intelligence.liquidity import LiquidityPath, LiquiditySide
from goldswingtraderai.intelligence.snapshot import IntelligenceSnapshot, TimeframeIntelligence
from goldswingtraderai.intelligence.technical import LocationCategory, ZoneSide


class PlanState(StrEnum):
    DRAFT = "DRAFT"
    VALID = "VALID"
    READY = "READY"
    DEGRADED = "DEGRADED"
    EXPIRED = "EXPIRED"
    INVALID = "INVALID"
    EXECUTED = "EXECUTED"


class StopQuality(StrEnum):
    ROBUST = "ROBUST"
    ACCEPTABLE = "ACCEPTABLE"
    FRAGILE = "FRAGILE"
    INVALID = "INVALID"


class RRClass(StrEnum):
    POOR = "POOR"
    MARGINAL = "MARGINAL"
    GOOD = "GOOD"
    STRONG = "STRONG"


class TargetRole(StrEnum):
    IMMEDIATE = "IMMEDIATE"
    PRIMARY = "PRIMARY"
    EXPANSION = "EXPANSION"
    RUNNER = "RUNNER"


@dataclass(frozen=True, slots=True)
class PlanTarget:
    role: TargetRole
    price: float
    quality: float
    source: str
    rr: float

    def __post_init__(self) -> None:
        if not isfinite(self.price) or not isfinite(self.quality) or not isfinite(self.rr):
            raise ValueError("target price/quality/RR must be finite")
        if self.price <= 0 or self.rr <= 0:
            raise ValueError("target price/RR must be positive")
        if not 0 <= self.quality <= 100:
            raise ValueError("target quality must be between 0 and 100")
        if not self.source.strip():
            raise ValueError("target source cannot be empty")


@dataclass(frozen=True, slots=True)
class TradePlanConfig:
    # Research-calibratable baselines. Frozen RR thresholds below are policy.
    atr_buffer_fraction: float = 0.12
    minimum_buffer_ticks: int = 4
    fragile_risk_atr: float = 0.20
    acceptable_risk_atr: float = 0.45
    fragile_buffer_atr: float = 0.06
    robust_buffer_atr: float = 0.10
    meaningful_target_quality: float = 55.0
    target_merge_atr: float = 0.06
    expansion_min_extra_r: float = 0.45
    runner_min_extra_r: float = 0.60
    marginal_rr_floor: float = 1.20
    good_rr_floor: float = 1.50
    strong_rr_floor: float = 2.00
    marginal_expansion_rr: float = 2.00
    marginal_min_path_quality: float = 55.0

    def __post_init__(self) -> None:
        positive = (
            self.atr_buffer_fraction,
            self.fragile_risk_atr,
            self.acceptable_risk_atr,
            self.fragile_buffer_atr,
            self.robust_buffer_atr,
            self.target_merge_atr,
            self.expansion_min_extra_r,
            self.runner_min_extra_r,
            self.marginal_rr_floor,
            self.good_rr_floor,
            self.strong_rr_floor,
            self.marginal_expansion_rr,
        )
        if any(not isfinite(value) or value <= 0 for value in positive):
            raise ValueError("Trade Plan thresholds must be positive")
        if self.minimum_buffer_ticks <= 0:
            raise ValueError("minimum buffer ticks must be positive")
        if not self.fragile_risk_atr < self.acceptable_risk_atr:
            raise ValueError("stop-risk ATR thresholds are invalid")
        if not self.fragile_buffer_atr < self.robust_buffer_atr:
            raise ValueError("stop-buffer ATR thresholds are invalid")
        if not self.marginal_rr_floor < self.good_rr_floor < self.strong_rr_floor:
            raise ValueError("RR thresholds must increase")
        if not 0 <= self.meaningful_target_quality <= 100:
            raise ValueError("meaningful target quality must be between 0 and 100")
        if not 0 <= self.marginal_min_path_quality <= 100:
            raise ValueError("path quality must be between 0 and 100")


@dataclass(frozen=True, slots=True)
class TradePlan:
    plan_id: EntityId
    opportunity_id: EntityId
    episode_id: EntityId
    family: StrategyFamily
    direction: Direction
    state: PlanState
    signal_price: float
    approved_entry_reference: float
    invalidation_level: float | None
    invalidation_source: str
    initial_stop: float | None
    stop_buffer: float | None
    stop_quality: StopQuality
    original_r_price: float | None
    immediate_obstacle: PlanTarget | None
    primary_target: PlanTarget | None
    expansion_target: PlanTarget | None
    runner_target: PlanTarget | None
    broker_tp_target: PlanTarget | None
    rr_class: RRClass
    path_quality: float
    plan_quality: float
    created_at_utc: datetime
    reason: str

    def __post_init__(self) -> None:
        _require_utc(self.created_at_utc)
        if self.direction is Direction.NONE:
            raise ValueError("Trade Plan direction must be BUY or SELL")
        if (
            not isfinite(self.signal_price)
            or not isfinite(self.approved_entry_reference)
            or self.signal_price <= 0
            or self.approved_entry_reference <= 0
        ):
            raise ValueError("signal/entry prices must be positive")
        for value in (
            self.invalidation_level,
            self.initial_stop,
            self.stop_buffer,
            self.original_r_price,
        ):
            if value is not None and (not isfinite(value) or value <= 0):
                raise ValueError("Trade Plan geometry must be positive when present")
        if self.state is not PlanState.INVALID and None in (
            self.invalidation_level,
            self.initial_stop,
            self.stop_buffer,
            self.original_r_price,
        ):
            raise ValueError("non-INVALID Trade Plan requires complete stop geometry")
        if self.state is PlanState.READY and self.broker_tp_target is None:
            raise ValueError("READY Trade Plan requires a broker target")
        if (
            not isfinite(self.path_quality)
            or not isfinite(self.plan_quality)
            or not 0 <= self.path_quality <= 100
            or not 0 <= self.plan_quality <= 100
        ):
            raise ValueError("plan/path quality must be between 0 and 100")

    @property
    def entry_ready(self) -> bool:
        return self.state is PlanState.READY


@dataclass(frozen=True, slots=True)
class _TargetCandidate:
    price: float
    quality: float
    source: str


def build_trade_plan(
    opportunity: Opportunity,
    intelligence: IntelligenceSnapshot,
    market: MarketSnapshot,
    now_utc: datetime,
    config: TradePlanConfig | None = None,
) -> TradePlan:
    """Build structural geometry for one analytically READY opportunity.

    Snapshot Bid/Ask is the approved plan reference. Phase 7 still performs fresh
    executable-quote, margin and broker-rule revalidation before a write.
    """

    _require_utc(now_utc)
    if opportunity.stage is not OpportunityStage.READY:
        raise ValueError("Trade Plan requires a READY opportunity")

    cfg = config or TradePlanConfig()
    direction = opportunity.direction
    family = opportunity.source_families[0]
    entry = market.quote.ask if direction is Direction.BUY else market.quote.bid
    signal = market.candles(Timeframe.M5)[-1].close
    tick = market.symbol_spec.tick_size

    invalidation = _find_invalidation(family, direction, entry, intelligence)
    if invalidation is None:
        return _invalid_plan(
            opportunity,
            family,
            signal,
            entry,
            now_utc,
            "NO_STRUCTURAL_INVALIDATION",
        )

    invalidation_level, invalidation_source, reference_frame = invalidation
    atr = reference_frame.quant.atr or intelligence.for_timeframe(Timeframe.M5).quant.atr
    if atr is None or atr <= 0:
        return _invalid_plan(
            opportunity,
            family,
            signal,
            entry,
            now_utc,
            "ATR_UNAVAILABLE_FOR_STOP_BUFFER",
            invalidation_level,
            invalidation_source,
        )

    buffer = max(tick * cfg.minimum_buffer_ticks, atr * cfg.atr_buffer_fraction)
    raw_stop = invalidation_level - buffer if direction is Direction.BUY else invalidation_level + buffer
    stop = _outward_tick(raw_stop, tick, direction)
    original_r = abs(entry - stop)
    if original_r <= 0 or not _stop_is_correct_side(entry, stop, direction):
        return _invalid_plan(
            opportunity,
            family,
            signal,
            entry,
            now_utc,
            "INVALID_STOP_GEOMETRY",
            invalidation_level,
            invalidation_source,
        )

    broker_min_distance = market.symbol_spec.stops_level_points * market.symbol_spec.point
    if broker_min_distance > 0 and original_r < broker_min_distance:
        # Do not widen a market-derived stop merely to satisfy broker geometry.
        return _invalid_plan(
            opportunity,
            family,
            signal,
            entry,
            now_utc,
            "BROKER_STOP_DISTANCE_DISTORTS_PLAN",
            invalidation_level,
            invalidation_source,
        )

    stop_quality = _stop_quality(original_r, buffer, atr, cfg)
    candidates = _target_candidates(direction, entry, intelligence, atr, tick, cfg)
    immediate, primary, expansion, runner = _select_targets(
        candidates,
        direction,
        entry,
        original_r,
        cfg,
    )
    path_quality = _path_quality(direction, intelligence)

    if primary is None:
        return _complete_plan(
            opportunity,
            family,
            signal,
            entry,
            invalidation_level,
            invalidation_source,
            stop,
            buffer,
            stop_quality,
            original_r,
            immediate,
            None,
            None,
            None,
            None,
            RRClass.POOR,
            path_quality,
            20.0,
            now_utc,
            PlanState.DEGRADED,
            "NO_CREDIBLE_PRIMARY_TARGET",
        )

    rr_class = _rr_class(primary.rr, cfg)
    state = PlanState.READY
    reason = "PLAN_READY"
    if stop_quality is StopQuality.FRAGILE:
        state = PlanState.DEGRADED
        reason = "STOP_FRAGILE_WAIT_FOR_BETTER_GEOMETRY"
    elif primary.rr < cfg.marginal_rr_floor:
        state = PlanState.DEGRADED
        reason = "TARGET_ROOM_POOR"
    elif primary.rr < cfg.good_rr_floor:
        marginal_ok = (
            expansion is not None
            and expansion.rr >= cfg.marginal_expansion_rr
            and path_quality >= cfg.marginal_min_path_quality
        )
        if not marginal_ok:
            state = PlanState.DEGRADED
            reason = "MARGINAL_RR_NEEDS_CREDIBLE_EXPANSION"

    broker_tp = (expansion or primary) if state is PlanState.READY else None
    plan_quality = _plan_quality(
        stop_quality,
        primary,
        expansion,
        path_quality,
        intelligence,
        direction,
    )
    return _complete_plan(
        opportunity,
        family,
        signal,
        entry,
        invalidation_level,
        invalidation_source,
        stop,
        buffer,
        stop_quality,
        original_r,
        immediate,
        primary,
        expansion,
        runner,
        broker_tp,
        rr_class,
        path_quality,
        plan_quality,
        now_utc,
        state,
        reason,
    )


def _find_invalidation(
    family: StrategyFamily,
    direction: Direction,
    entry: float,
    intelligence: IntelligenceSnapshot,
) -> tuple[float, str, TimeframeIntelligence] | None:
    reversal_families = {
        StrategyFamily.LIQUIDITY_SWEEP_REVERSAL,
        StrategyFamily.FAILED_BREAKOUT_REVERSAL,
    }
    order = (
        (Timeframe.M5, Timeframe.M15, Timeframe.H1)
        if family in reversal_families
        else (Timeframe.M15, Timeframe.M5, Timeframe.H1)
    )
    wanted_side = SwingSide.LOW if direction is Direction.BUY else SwingSide.HIGH

    for timeframe in order:
        frame = intelligence.for_timeframe(timeframe)
        protected = frame.structure.protected_low if direction is Direction.BUY else frame.structure.protected_high
        if protected is not None and _level_is_beyond_entry(protected.price, entry, direction):
            return protected.price, f"{timeframe}:PROTECTED_{wanted_side.value}", frame

        swing = next(
            (
                item
                for item in reversed(frame.structure.swings)
                if item.side is wanted_side and _level_is_beyond_entry(item.price, entry, direction)
            ),
            None,
        )
        if swing is not None:
            return swing.price, f"{timeframe}:CONFIRMED_{wanted_side.value}", frame

        zone = frame.technical.nearest_support if direction is Direction.BUY else frame.technical.nearest_resistance
        if zone is not None:
            level = zone.lower if direction is Direction.BUY else zone.upper
            if _level_is_beyond_entry(level, entry, direction):
                return level, f"{timeframe}:TECHNICAL_ZONE", frame
    return None


def _target_candidates(
    direction: Direction,
    entry: float,
    intelligence: IntelligenceSnapshot,
    atr: float,
    tick: float,
    cfg: TradePlanConfig,
) -> tuple[_TargetCandidate, ...]:
    raw: list[_TargetCandidate] = []
    target_side = ZoneSide.RESISTANCE if direction is Direction.BUY else ZoneSide.SUPPORT
    pool_side = LiquiditySide.BUY_SIDE if direction is Direction.BUY else LiquiditySide.SELL_SIDE
    swing_side = SwingSide.HIGH if direction is Direction.BUY else SwingSide.LOW
    tf_bonus = {
        Timeframe.M5: 0.0,
        Timeframe.M15: 5.0,
        Timeframe.H1: 10.0,
        Timeframe.H4: 15.0,
    }

    for timeframe in (Timeframe.M5, Timeframe.M15, Timeframe.H1, Timeframe.H4):
        frame = intelligence.for_timeframe(timeframe)
        bonus = tf_bonus[timeframe]
        for zone in frame.technical.zones:
            if zone.side is target_side and _target_is_ahead(zone.midpoint, entry, direction):
                raw.append(
                    _TargetCandidate(
                        price=zone.midpoint,
                        quality=min(100.0, zone.quality + bonus),
                        source=f"{timeframe}:ZONE",
                    )
                )
        for pool in frame.liquidity.pools:
            if pool.side is pool_side and _target_is_ahead(pool.midpoint, entry, direction):
                raw.append(
                    _TargetCandidate(
                        price=pool.midpoint,
                        quality=min(100.0, 40.0 + pool.significance * 15.0 + bonus),
                        source=f"{timeframe}:LIQUIDITY",
                    )
                )
        for swing in frame.structure.swings:
            if swing.side is swing_side and _target_is_ahead(swing.price, entry, direction):
                raw.append(
                    _TargetCandidate(
                        price=swing.price,
                        quality=min(100.0, 35.0 + swing.significance_atr * 15.0 + bonus),
                        source=f"{timeframe}:SWING",
                    )
                )

    tolerance = max(tick * 4, atr * cfg.target_merge_atr)
    ordered = sorted(
        raw,
        key=lambda item: (
            -item.price if direction is Direction.SELL else item.price,
            -item.quality,
            item.source,
        ),
    )
    merged: list[_TargetCandidate] = []
    for candidate in ordered:
        if merged and abs(candidate.price - merged[-1].price) <= tolerance:
            if candidate.quality > merged[-1].quality:
                merged[-1] = candidate
            continue
        merged.append(candidate)
    return tuple(merged)


def _select_targets(
    candidates: tuple[_TargetCandidate, ...],
    direction: Direction,
    entry: float,
    original_r: float,
    cfg: TradePlanConfig,
) -> tuple[PlanTarget | None, PlanTarget | None, PlanTarget | None, PlanTarget | None]:
    if not candidates:
        return None, None, None, None

    immediate = _as_target(TargetRole.IMMEDIATE, candidates[0], direction, entry, original_r)
    meaningful = [item for item in candidates if item.quality >= cfg.meaningful_target_quality]
    if not meaningful:
        return immediate, None, None, None

    primary_c = meaningful[0]
    primary = _as_target(TargetRole.PRIMARY, primary_c, direction, entry, original_r)
    expansion_c = next(
        (
            item
            for item in meaningful[1:]
            if _directional_distance(primary_c.price, item.price, direction)
            >= original_r * cfg.expansion_min_extra_r
        ),
        None,
    )
    expansion = (
        _as_target(TargetRole.EXPANSION, expansion_c, direction, entry, original_r)
        if expansion_c is not None
        else None
    )

    anchor = expansion_c or primary_c
    remaining = meaningful[meaningful.index(anchor) + 1 :]
    runner_c = next(
        (
            item
            for item in remaining
            if _directional_distance(anchor.price, item.price, direction)
            >= original_r * cfg.runner_min_extra_r
        ),
        None,
    )
    runner = (
        _as_target(TargetRole.RUNNER, runner_c, direction, entry, original_r)
        if runner_c is not None
        else None
    )
    return immediate, primary, expansion, runner


def _as_target(
    role: TargetRole,
    candidate: _TargetCandidate,
    direction: Direction,
    entry: float,
    original_r: float,
) -> PlanTarget:
    return PlanTarget(
        role=role,
        price=candidate.price,
        quality=candidate.quality,
        source=candidate.source,
        rr=_directional_distance(entry, candidate.price, direction) / original_r,
    )


def _path_quality(direction: Direction, intelligence: IntelligenceSnapshot) -> float:
    values: list[float] = []
    mapping = {
        LiquidityPath.OPEN: 90.0,
        LiquidityPath.MIXED: 62.0,
        LiquidityPath.CROWDED: 35.0,
        LiquidityPath.UNKNOWN: 50.0,
    }
    for timeframe, weight in ((Timeframe.M15, 0.65), (Timeframe.H1, 0.35)):
        frame = intelligence.for_timeframe(timeframe)
        path = frame.liquidity.path_up if direction is Direction.BUY else frame.liquidity.path_down
        values.append(mapping[path] * weight)
    return sum(values)


def _plan_quality(
    stop_quality: StopQuality,
    primary: PlanTarget,
    expansion: PlanTarget | None,
    path_quality: float,
    intelligence: IntelligenceSnapshot,
    direction: Direction,
) -> float:
    stop_score = {
        StopQuality.ROBUST: 92.0,
        StopQuality.ACCEPTABLE: 75.0,
        StopQuality.FRAGILE: 38.0,
        StopQuality.INVALID: 0.0,
    }[stop_quality]
    rr_score = min(100.0, primary.rr / 2.0 * 85.0)
    if expansion is not None and expansion.rr >= 2.0:
        rr_score = min(100.0, rr_score + 10.0)

    m15 = intelligence.for_timeframe(Timeframe.M15)
    location = m15.technical.buy_location if direction is Direction.BUY else m15.technical.sell_location
    location_score = {
        LocationCategory.EXCELLENT: 95.0,
        LocationCategory.GOOD: 82.0,
        LocationCategory.NEUTRAL: 60.0,
        LocationCategory.POOR: 38.0,
        LocationCategory.DANGEROUS: 20.0,
        LocationCategory.UNKNOWN: 50.0,
    }[location]
    return min(
        100.0,
        stop_score * 0.28
        + primary.quality * 0.22
        + rr_score * 0.22
        + path_quality * 0.18
        + location_score * 0.10,
    )


def _rr_class(rr: float, cfg: TradePlanConfig) -> RRClass:
    if rr < cfg.marginal_rr_floor:
        return RRClass.POOR
    if rr < cfg.good_rr_floor:
        return RRClass.MARGINAL
    if rr < cfg.strong_rr_floor:
        return RRClass.GOOD
    return RRClass.STRONG


def _stop_quality(
    risk_distance: float,
    buffer: float,
    atr: float,
    cfg: TradePlanConfig,
) -> StopQuality:
    risk_atr = risk_distance / atr
    buffer_atr = buffer / atr
    if risk_atr < cfg.fragile_risk_atr or buffer_atr < cfg.fragile_buffer_atr:
        return StopQuality.FRAGILE
    if risk_atr < cfg.acceptable_risk_atr or buffer_atr < cfg.robust_buffer_atr:
        return StopQuality.ACCEPTABLE
    return StopQuality.ROBUST


def _outward_tick(price: float, tick: float, direction: Direction) -> float:
    steps = price / tick
    normalized = floor(steps) * tick if direction is Direction.BUY else ceil(steps) * tick
    return round(normalized, 10)


def _level_is_beyond_entry(level: float, entry: float, direction: Direction) -> bool:
    return level < entry if direction is Direction.BUY else level > entry


def _target_is_ahead(price: float, entry: float, direction: Direction) -> bool:
    return price > entry if direction is Direction.BUY else price < entry


def _stop_is_correct_side(entry: float, stop: float, direction: Direction) -> bool:
    return stop < entry if direction is Direction.BUY else stop > entry


def _directional_distance(start: float, end: float, direction: Direction) -> float:
    return end - start if direction is Direction.BUY else start - end


def _complete_plan(
    opportunity: Opportunity,
    family: StrategyFamily,
    signal: float,
    entry: float,
    invalidation_level: float,
    invalidation_source: str,
    stop: float,
    buffer: float,
    stop_quality: StopQuality,
    original_r: float,
    immediate: PlanTarget | None,
    primary: PlanTarget | None,
    expansion: PlanTarget | None,
    runner: PlanTarget | None,
    broker_tp: PlanTarget | None,
    rr_class: RRClass,
    path_quality: float,
    plan_quality: float,
    now_utc: datetime,
    state: PlanState,
    reason: str,
) -> TradePlan:
    return TradePlan(
        plan_id=new_trade_plan_id(),
        opportunity_id=opportunity.opportunity_id,
        episode_id=opportunity.episode_id,
        family=family,
        direction=opportunity.direction,
        state=state,
        signal_price=signal,
        approved_entry_reference=entry,
        invalidation_level=invalidation_level,
        invalidation_source=invalidation_source,
        initial_stop=stop,
        stop_buffer=buffer,
        stop_quality=stop_quality,
        original_r_price=original_r,
        immediate_obstacle=immediate,
        primary_target=primary,
        expansion_target=expansion,
        runner_target=runner,
        broker_tp_target=broker_tp,
        rr_class=rr_class,
        path_quality=path_quality,
        plan_quality=plan_quality,
        created_at_utc=now_utc,
        reason=reason,
    )


def _invalid_plan(
    opportunity: Opportunity,
    family: StrategyFamily,
    signal: float,
    entry: float,
    now_utc: datetime,
    reason: str,
    invalidation_level: float | None = None,
    invalidation_source: str = "UNAVAILABLE",
) -> TradePlan:
    return TradePlan(
        plan_id=new_trade_plan_id(),
        opportunity_id=opportunity.opportunity_id,
        episode_id=opportunity.episode_id,
        family=family,
        direction=opportunity.direction,
        state=PlanState.INVALID,
        signal_price=signal,
        approved_entry_reference=entry,
        invalidation_level=invalidation_level,
        invalidation_source=invalidation_source,
        initial_stop=None,
        stop_buffer=None,
        stop_quality=StopQuality.INVALID,
        original_r_price=None,
        immediate_obstacle=None,
        primary_target=None,
        expansion_target=None,
        runner_target=None,
        broker_tp_target=None,
        rr_class=RRClass.POOR,
        path_quality=0.0,
        plan_quality=0.0,
        created_at_utc=now_utc,
        reason=reason,
    )


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Trade Plan timestamp must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("Trade Plan timestamp must be UTC")
