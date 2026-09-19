"""Six parallel production strategy-family hypotheses over one IntelligenceSnapshot.

Family scores are soft analytical evidence only. This module has no MT5, risk or
execution authority and deliberately avoids a sequential filter pipeline.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from goldswingtraderai.domain.enums import (
    BreakState,
    CandleSequenceState,
    Direction,
    MomentumPhase,
    StrategyFamily,
    StructureState,
    Timeframe,
    VolatilityState,
)
from goldswingtraderai.intelligence.liquidity import LiquidityEventType, LiquidityPath
from goldswingtraderai.intelligence.snapshot import IntelligenceSnapshot, TimeframeIntelligence
from goldswingtraderai.intelligence.technical import LocationCategory


@dataclass(frozen=True, slots=True)
class DirectionalFamilyCase:
    score: float
    coverage: float
    evidence: tuple[str, ...]
    conflicts: tuple[str, ...]
    structural_target: float | None
    expansion_potential: float | None


@dataclass(frozen=True, slots=True)
class FamilyReport:
    family: StrategyFamily
    buy: DirectionalFamilyCase
    sell: DirectionalFamilyCase
    preferred_timing_profile: str

    @property
    def direction(self) -> Direction:
        if self.buy.score > self.sell.score:
            return Direction.BUY
        if self.sell.score > self.buy.score:
            return Direction.SELL
        return Direction.NONE

    @property
    def quality(self) -> float:
        return max(self.buy.score, self.sell.score)


@dataclass(frozen=True, slots=True)
class StrategyFloorReport:
    families: tuple[FamilyReport, ...]

    def by_family(self, family: StrategyFamily) -> FamilyReport:
        for report in self.families:
            if report.family is family:
                return report
        raise KeyError(f"strategy family not present: {family}")


@dataclass(frozen=True, slots=True)
class StrategyFloorConfig:
    evidence_floor: float = 65.0
    conflict_ceiling: float = 35.0

    def __post_init__(self) -> None:
        if not 0 <= self.conflict_ceiling < self.evidence_floor <= 100:
            raise ValueError("strategy evidence thresholds are invalid")


def evaluate_strategy_floor(
    intelligence: IntelligenceSnapshot,
    config: StrategyFloorConfig | None = None,
) -> StrategyFloorReport:
    """Evaluate all six families independently against the same snapshot."""

    cfg = config or StrategyFloorConfig()
    h4 = intelligence.for_timeframe(Timeframe.H4)
    h1 = intelligence.for_timeframe(Timeframe.H1)
    m15 = intelligence.for_timeframe(Timeframe.M15)
    m5 = intelligence.for_timeframe(Timeframe.M5)

    families = (
        _trend_pullback(h4, h1, m15, m5, cfg),
        _breakout_expansion(h1, m15, m5, cfg),
        _breakout_retest(h1, m15, m5, cfg),
        _liquidity_sweep(h1, m15, m5, cfg),
        _failed_breakout(h1, m15, m5, cfg),
        _compression_expansion(h1, m15, m5, cfg),
    )
    return StrategyFloorReport(families=families)


def _trend_pullback(
    h4: TimeframeIntelligence,
    h1: TimeframeIntelligence,
    m15: TimeframeIntelligence,
    m5: TimeframeIntelligence,
    cfg: StrategyFloorConfig,
) -> FamilyReport:
    return _family(
        StrategyFamily.TREND_PULLBACK_CONTINUATION,
        "PULLBACK_RECLAIM",
        lambda direction: (
            ("H4_CONTEXT", _structure(h4, direction), 0.10),
            ("H1_STRUCTURE", _structure(h1, direction), 0.22),
            ("M15_STRUCTURE", _structure(m15, direction), 0.18),
            ("M15_LOCATION", _location(m15, direction), 0.18),
            ("M5_RESUMPTION", _sequence(m5, direction), 0.15),
            ("EMA_FLOW", _trend_flow(m15, direction), 0.07),
            ("TARGET_ROOM", _target_room(m15, direction), 0.10),
        ),
        m15,
        cfg,
    )


def _breakout_expansion(
    h1: TimeframeIntelligence,
    m15: TimeframeIntelligence,
    m5: TimeframeIntelligence,
    cfg: StrategyFloorConfig,
) -> FamilyReport:
    return _family(
        StrategyFamily.BREAKOUT_EXPANSION,
        "BREAK_ACCEPTANCE",
        lambda direction: (
            ("H1_CONTEXT", _structure(h1, direction), 0.10),
            ("M15_BREAK", _break_support(m15, direction), 0.25),
            ("M15_EXPANSION", _sequence(m15, direction), 0.15),
            ("M5_ACCEPTANCE", _sequence(m5, direction), 0.12),
            ("MOMENTUM", _momentum(m5, direction), 0.12),
            ("VOLATILITY", _volatility(m15), 0.08),
            ("LIQUIDITY_ACCEPTANCE", _accepted_break(m15, direction), 0.08),
            ("TARGET_ROOM", _target_room(m15, direction), 0.10),
        ),
        m15,
        cfg,
    )


def _breakout_retest(
    h1: TimeframeIntelligence,
    m15: TimeframeIntelligence,
    m5: TimeframeIntelligence,
    cfg: StrategyFloorConfig,
) -> FamilyReport:
    return _family(
        StrategyFamily.BREAKOUT_RETEST_CONTINUATION,
        "BREAK_RETEST_CONTINUATION",
        lambda direction: (
            ("H1_CONTEXT", _structure(h1, direction), 0.10),
            ("M15_PRIOR_BREAK", _break_support(m15, direction), 0.25),
            ("M15_LOCATION", _location(m15, direction), 0.15),
            ("M5_REJECTION_CONTINUATION", _sequence(m5, direction), 0.20),
            ("M5_STRUCTURE", _structure(m5, direction), 0.10),
            ("LIQUIDITY_ACCEPTANCE", _accepted_break(m15, direction), 0.08),
            ("TARGET_ROOM", _target_room(m15, direction), 0.12),
        ),
        m15,
        cfg,
    )


def _liquidity_sweep(
    h1: TimeframeIntelligence,
    m15: TimeframeIntelligence,
    m5: TimeframeIntelligence,
    cfg: StrategyFloorConfig,
) -> FamilyReport:
    return _family(
        StrategyFamily.LIQUIDITY_SWEEP_REVERSAL,
        "SWEEP_RECLAIM_REVERSAL",
        lambda direction: (
            ("M15_SWEEP", _sweep(m15, direction), 0.30),
            ("M5_SWEEP", _sweep(m5, direction), 0.15),
            ("M5_REJECTION", _sequence(m5, direction), 0.15),
            ("M5_STRUCTURE_SHIFT", _mss_support(m5, direction), 0.15),
            ("M15_LOCATION", _location(m15, direction), 0.10),
            ("H1_NOT_HOSTILE", _not_hostile(h1, direction), 0.05),
            ("TARGET_ROOM", _target_room(m15, direction), 0.10),
        ),
        m15,
        cfg,
    )


def _failed_breakout(
    h1: TimeframeIntelligence,
    m15: TimeframeIntelligence,
    m5: TimeframeIntelligence,
    cfg: StrategyFloorConfig,
) -> FamilyReport:
    return _family(
        StrategyFamily.FAILED_BREAKOUT_REVERSAL,
        "FAILED_ACCEPTANCE_REVERSAL",
        lambda direction: (
            ("M15_FAILED_BREAK", _failed_break(m15, direction), 0.30),
            ("M5_FAILED_BREAK", _failed_break(m5, direction), 0.15),
            ("M5_OPPOSING_RESPONSE", _sequence(m5, direction), 0.16),
            ("M5_MSS", _mss_support(m5, direction), 0.14),
            ("M15_LOCATION", _location(m15, direction), 0.10),
            ("H1_NOT_HOSTILE", _not_hostile(h1, direction), 0.05),
            ("TARGET_ROOM", _target_room(m15, direction), 0.10),
        ),
        m15,
        cfg,
    )


def _compression_expansion(
    h1: TimeframeIntelligence,
    m15: TimeframeIntelligence,
    m5: TimeframeIntelligence,
    cfg: StrategyFloorConfig,
) -> FamilyReport:
    compression = 90.0 if m15.structure.sequence is CandleSequenceState.COMPRESSION else 45.0
    return _family(
        StrategyFamily.COMPRESSION_EXPANSION,
        "COMPRESSION_RELEASE",
        lambda direction: (
            ("M15_COMPRESSION", compression, 0.20),
            ("M5_DIRECTIONAL_RELEASE", _sequence(m5, direction), 0.23),
            ("M15_BREAK", _break_support(m15, direction), 0.17),
            ("MOMENTUM", _momentum(m5, direction), 0.12),
            ("VOLATILITY_BUILD", _volatility(m5), 0.08),
            ("H1_CONTEXT", _not_hostile(h1, direction), 0.07),
            ("LIQUIDITY_PATH", _path(m15, direction), 0.05),
            ("TARGET_ROOM", _target_room(m15, direction), 0.08),
        ),
        m15,
        cfg,
    )


def _family(
    family: StrategyFamily,
    timing_profile: str,
    features: Callable[[Direction], tuple[tuple[str, float | None, float], ...]],
    target_frame: TimeframeIntelligence,
    cfg: StrategyFloorConfig,
) -> FamilyReport:
    buy = _case(Direction.BUY, features(Direction.BUY), target_frame, cfg)
    sell = _case(Direction.SELL, features(Direction.SELL), target_frame, cfg)
    return FamilyReport(
        family=family,
        buy=buy,
        sell=sell,
        preferred_timing_profile=timing_profile,
    )


def _case(
    direction: Direction,
    features: tuple[tuple[str, float | None, float], ...],
    target_frame: TimeframeIntelligence,
    cfg: StrategyFloorConfig,
) -> DirectionalFamilyCase:
    available = [(name, value, weight) for name, value, weight in features if value is not None]
    total_weight = sum(weight for _, _, weight in features)
    available_weight = sum(weight for _, _, weight in available)
    score = (
        sum(float(value) * weight for _, value, weight in available) / available_weight
        if available_weight > 0
        else 50.0
    )
    evidence = tuple(name for name, value, _ in available if float(value) >= cfg.evidence_floor)
    conflicts = tuple(name for name, value, _ in available if float(value) <= cfg.conflict_ceiling)
    target = _structural_target(target_frame, direction)
    room_score = _target_room(target_frame, direction)
    return DirectionalFamilyCase(
        score=_clip(score),
        coverage=available_weight / total_weight if total_weight > 0 else 0.0,
        evidence=evidence,
        conflicts=conflicts,
        structural_target=target,
        expansion_potential=(room_score / 100.0) if room_score is not None else None,
    )


def _structure(frame: TimeframeIntelligence, direction: Direction) -> float:
    return frame.structure.bull_evidence if direction is Direction.BUY else frame.structure.bear_evidence


def _not_hostile(frame: TimeframeIntelligence, direction: Direction) -> float:
    state = frame.structure.state
    desired = StructureState.BULLISH if direction is Direction.BUY else StructureState.BEARISH
    opposite = StructureState.BEARISH if direction is Direction.BUY else StructureState.BULLISH
    if state is desired:
        return 90.0
    if state is opposite:
        return 25.0
    if state is StructureState.TRANSITION:
        return 55.0
    return 60.0


def _trend_flow(frame: TimeframeIntelligence, direction: Direction) -> float:
    flow = frame.quant.trend_support
    if flow is direction:
        return 85.0
    if flow is Direction.NONE:
        return 50.0
    return 20.0


def _location(frame: TimeframeIntelligence, direction: Direction) -> float | None:
    category = frame.technical.buy_location if direction is Direction.BUY else frame.technical.sell_location
    return {
        LocationCategory.EXCELLENT: 95.0,
        LocationCategory.GOOD: 78.0,
        LocationCategory.NEUTRAL: 55.0,
        LocationCategory.POOR: 35.0,
        LocationCategory.DANGEROUS: 15.0,
        LocationCategory.UNKNOWN: None,
    }[category]


def _target_room(frame: TimeframeIntelligence, direction: Direction) -> float | None:
    room = frame.technical.buy_target_room if direction is Direction.BUY else frame.technical.sell_target_room
    atr = frame.quant.atr
    if room is None or atr is None or atr <= 0:
        return None
    normalized = room / atr
    if normalized < 0.25:
        return 10.0
    if normalized < 0.75:
        return 35.0
    if normalized < 1.50:
        return 60.0
    if normalized < 2.50:
        return 80.0
    return 95.0


def _sequence(frame: TimeframeIntelligence, direction: Direction) -> float:
    sequence = frame.structure.sequence
    strong = (
        CandleSequenceState.BULL_EXPANSION
        if direction is Direction.BUY
        else CandleSequenceState.BEAR_EXPANSION
    )
    continuation = (
        CandleSequenceState.BULL_CONTINUATION
        if direction is Direction.BUY
        else CandleSequenceState.BEAR_CONTINUATION
    )
    rejection = (
        CandleSequenceState.BULL_REJECTION
        if direction is Direction.BUY
        else CandleSequenceState.BEAR_REJECTION
    )
    opposite = {
        CandleSequenceState.BEAR_EXPANSION,
        CandleSequenceState.BEAR_CONTINUATION,
        CandleSequenceState.BEAR_REJECTION,
    } if direction is Direction.BUY else {
        CandleSequenceState.BULL_EXPANSION,
        CandleSequenceState.BULL_CONTINUATION,
        CandleSequenceState.BULL_REJECTION,
    }
    if sequence is strong:
        return 92.0
    if sequence is continuation:
        return 80.0
    if sequence is rejection:
        return 76.0
    if sequence in opposite:
        return 20.0
    if sequence is CandleSequenceState.COMPRESSION:
        return 50.0
    return 52.0


def _break_support(frame: TimeframeIntelligence, direction: Direction) -> float:
    relevant = [event for event in frame.structure.events if event.direction is direction]
    if not relevant:
        return 40.0
    state = relevant[-1].state
    return {
        BreakState.PROBE: 45.0,
        BreakState.QUALIFIED_BREAK: 78.0,
        BreakState.CONFIRMED_BOS: 95.0,
        BreakState.MSS_CANDIDATE: 72.0,
        BreakState.CONFIRMED_MSS: 88.0,
        BreakState.FAILED_BREAK: 20.0,
    }[state]


def _mss_support(frame: TimeframeIntelligence, direction: Direction) -> float:
    relevant = [event for event in frame.structure.events if event.direction is direction]
    if not relevant:
        return 45.0
    state = relevant[-1].state
    if state is BreakState.CONFIRMED_MSS:
        return 95.0
    if state is BreakState.MSS_CANDIDATE:
        return 78.0
    if state in {BreakState.QUALIFIED_BREAK, BreakState.CONFIRMED_BOS}:
        return 65.0
    return 40.0


def _failed_break(frame: TimeframeIntelligence, direction: Direction) -> float:
    attempted = Direction.SELL if direction is Direction.BUY else Direction.BUY
    relevant = [
        event
        for event in frame.structure.events
        if event.direction is attempted and event.state is BreakState.FAILED_BREAK
    ]
    return 95.0 if relevant else 35.0


def _accepted_break(frame: TimeframeIntelligence, direction: Direction) -> float:
    relevant = [
        event
        for event in frame.liquidity.events
        if event.direction is direction and event.event_type is LiquidityEventType.ACCEPTED_BREAK
    ]
    return 92.0 if relevant else 45.0


def _sweep(frame: TimeframeIntelligence, direction: Direction) -> float:
    relevant = [
        event
        for event in frame.liquidity.events
        if event.direction is direction and event.event_type is LiquidityEventType.CONFIRMED_SWEEP
    ]
    return 95.0 if relevant else 35.0


def _momentum(frame: TimeframeIntelligence, direction: Direction) -> float | None:
    phase = frame.quant.momentum_phase
    if phase is MomentumPhase.UNKNOWN:
        return None
    aligned = frame.quant.trend_support is direction
    if phase is MomentumPhase.EXPANDING:
        return 92.0 if aligned else 55.0
    if phase is MomentumPhase.BUILDING:
        return 82.0 if aligned else 50.0
    if phase is MomentumPhase.MATURE:
        return 65.0 if aligned else 45.0
    if phase is MomentumPhase.EXHAUSTING:
        return 38.0 if aligned else 42.0
    if phase is MomentumPhase.REVERSING:
        return 30.0 if aligned else 70.0
    return 50.0


def _volatility(frame: TimeframeIntelligence) -> float | None:
    return {
        VolatilityState.QUIET: 45.0,
        VolatilityState.NORMAL: 65.0,
        VolatilityState.BUILDING: 82.0,
        VolatilityState.EXPANDING: 92.0,
        VolatilityState.EXTREME: 65.0,
        VolatilityState.DISLOCATED: 25.0,
        VolatilityState.UNKNOWN: None,
    }[frame.quant.volatility_state]


def _path(frame: TimeframeIntelligence, direction: Direction) -> float | None:
    path = frame.liquidity.path_up if direction is Direction.BUY else frame.liquidity.path_down
    return {
        LiquidityPath.OPEN: 90.0,
        LiquidityPath.MIXED: 60.0,
        LiquidityPath.CROWDED: 30.0,
        LiquidityPath.UNKNOWN: None,
    }[path]


def _structural_target(frame: TimeframeIntelligence, direction: Direction) -> float | None:
    zone = frame.technical.nearest_resistance if direction is Direction.BUY else frame.technical.nearest_support
    return zone.midpoint if zone is not None else None


def _clip(value: float) -> float:
    return min(100.0, max(0.0, value))
