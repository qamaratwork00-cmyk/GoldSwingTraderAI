"""Pure post-entry evidence derivation and HOLD/PROTECT/TRAIL/RUNNER/EXIT decisions."""

from __future__ import annotations

from dataclasses import dataclass

from goldswingtraderai.domain.enums import (
    CandleSequenceState,
    Direction,
    MomentumPhase,
    StructureState,
    Timeframe,
    TradeManagerAction,
)
from goldswingtraderai.domain.market import MarketSnapshot
from goldswingtraderai.intelligence.liquidity import LiquidityPath
from goldswingtraderai.intelligence.snapshot import IntelligenceSnapshot, TimeframeIntelligence
from goldswingtraderai.management.models import (
    ManagedTrade,
    ManagementEvidence,
    ObjectiveStage,
    StructuralStopReference,
    TradeManagementDecision,
)


@dataclass(frozen=True, slots=True)
class TradeManagerConfig:
    """Research-calibratable management baselines; structure remains the authority."""

    protect_min_r: float = 0.65
    trail_min_r: float = 1.20
    protect_structure_min: float = 50.0
    exit_reversal_score: float = 72.0
    exit_continuation_ceiling: float = 38.0
    target_exhaustion_reversal: float = 60.0
    target_exhaustion_continuation_ceiling: float = 45.0
    runner_activation_distance_r: float = 0.20
    runner_continuation_min: float = 68.0
    runner_reversal_max: float = 38.0
    runner_structure_min: float = 60.0
    runner_path_min: float = 55.0
    trail_buffer_atr: float = 0.12

    def __post_init__(self) -> None:
        if self.protect_min_r < 0 or self.trail_min_r <= self.protect_min_r:
            raise ValueError("management R thresholds are invalid")
        if self.runner_activation_distance_r < 0 or self.trail_buffer_atr <= 0:
            raise ValueError("runner/trailing normalization must be positive")
        for value in (
            self.protect_structure_min,
            self.exit_reversal_score,
            self.exit_continuation_ceiling,
            self.target_exhaustion_reversal,
            self.target_exhaustion_continuation_ceiling,
            self.runner_continuation_min,
            self.runner_reversal_max,
            self.runner_structure_min,
            self.runner_path_min,
        ):
            if not 0 <= value <= 100:
                raise ValueError("management score thresholds must be between 0 and 100")


def derive_management_evidence(
    intelligence: IntelligenceSnapshot,
    direction: Direction,
) -> ManagementEvidence:
    """Summarize continuation/reversal evidence without creating broker authority."""

    if direction is Direction.NONE:
        raise ValueError("management direction must be BUY or SELL")
    opposite = Direction.SELL if direction is Direction.BUY else Direction.BUY

    structure = _multi_frame_score(
        intelligence,
        direction,
        _structure_score,
        ((Timeframe.H4, 0.15), (Timeframe.H1, 0.30), (Timeframe.M15, 0.35), (Timeframe.M5, 0.20)),
    )
    opposing_structure = _multi_frame_score(
        intelligence,
        opposite,
        _structure_score,
        ((Timeframe.H4, 0.15), (Timeframe.H1, 0.30), (Timeframe.M15, 0.35), (Timeframe.M5, 0.20)),
    )
    momentum = _multi_frame_score(
        intelligence,
        direction,
        _momentum_score,
        ((Timeframe.H1, 0.30), (Timeframe.M15, 0.40), (Timeframe.M5, 0.30)),
    )
    opposing_momentum = _multi_frame_score(
        intelligence,
        opposite,
        _momentum_score,
        ((Timeframe.H1, 0.30), (Timeframe.M15, 0.40), (Timeframe.M5, 0.30)),
    )
    candle = _multi_frame_score(
        intelligence,
        direction,
        _candle_score,
        ((Timeframe.M15, 0.40), (Timeframe.M5, 0.60)),
    )
    opposing_candle = _multi_frame_score(
        intelligence,
        opposite,
        _candle_score,
        ((Timeframe.M15, 0.40), (Timeframe.M5, 0.60)),
    )
    path = _multi_frame_score(
        intelligence,
        direction,
        _path_score,
        ((Timeframe.H1, 0.40), (Timeframe.M15, 0.60)),
    )
    opposing_path = _multi_frame_score(
        intelligence,
        opposite,
        _path_score,
        ((Timeframe.H1, 0.40), (Timeframe.M15, 0.60)),
    )

    continuation = _weighted_mean(
        ((structure, 0.40), (momentum, 0.25), (candle, 0.15), (path, 0.20)),
        fallback=50.0,
    )
    reversal = _weighted_mean(
        (
            (opposing_structure, 0.45),
            (opposing_momentum, 0.25),
            (opposing_candle, 0.20),
            (opposing_path, 0.10),
        ),
        fallback=50.0,
    )

    return ManagementEvidence(
        continuation_score=continuation,
        reversal_score=reversal,
        structure_integrity=structure if structure is not None else 50.0,
        candle_health=candle if candle is not None else 50.0,
        momentum_health=momentum if momentum is not None else 50.0,
        path_quality=path if path is not None else 50.0,
        stop_references=_stop_references(intelligence, direction),
    )


def evaluate_trade_manager(
    trade: ManagedTrade,
    market: MarketSnapshot,
    intelligence: IntelligenceSnapshot,
    *,
    pre_close_flatten: bool = False,
    config: TradeManagerConfig | None = None,
) -> TradeManagementDecision:
    """Choose one post-entry action from fresh completed-candle intelligence."""

    if market.meta.symbol != trade.symbol:
        raise ValueError("managed trade symbol does not match market snapshot")
    cfg = config or TradeManagerConfig()
    evidence = derive_management_evidence(intelligence, trade.direction)
    exit_price = market.quote.bid if trade.direction is Direction.BUY else market.quote.ask
    current_r = _current_r(trade, exit_price)

    if pre_close_flatten:
        return _decision(
            trade,
            evidence,
            current_r,
            TradeManagerAction.EXIT,
            reason="PRE_CLOSE_FLATTEN",
        )

    # Exit needs a meaningful combination of opposing evidence and collapsed
    # continuation. A single RSI/candle signal cannot satisfy this condition alone.
    if (
        evidence.reversal_score >= cfg.exit_reversal_score
        and evidence.continuation_score <= cfg.exit_continuation_ceiling
    ):
        return _decision(
            trade,
            evidence,
            current_r,
            TradeManagerAction.EXIT,
            reason="THESIS_REVERSAL_CONFIRMED",
        )

    primary_reached = _target_reached(trade, trade.primary_target, exit_price)
    expansion_reached = _target_reached(trade, trade.expansion_target, exit_price)

    if _runner_eligible(trade, evidence, exit_price, cfg):
        proposed_stop = _structural_stop_candidate(trade, evidence, exit_price, current_r, primary_reached, cfg)
        return _decision(
            trade,
            evidence,
            current_r,
            TradeManagerAction.RUNNER,
            proposed_stop=proposed_stop,
            proposed_tp=trade.runner_candidate.price if trade.runner_candidate is not None else None,
            stage=ObjectiveStage.RUNNER,
            reason="RUNNER_EARNED_BY_CONTINUATION",
        )

    # If the main expansion objective has already been consumed and continuation
    # has materially weakened, there is no reason to invent an endless target.
    if expansion_reached and trade.objective_stage is not ObjectiveStage.RUNNER:
        if (
            evidence.reversal_score >= cfg.target_exhaustion_reversal
            or evidence.continuation_score <= cfg.target_exhaustion_continuation_ceiling
        ):
            return _decision(
                trade,
                evidence,
                current_r,
                TradeManagerAction.EXIT,
                reason="EXPANSION_TARGET_EXHAUSTED",
            )

    proposed_stop = _structural_stop_candidate(
        trade,
        evidence,
        exit_price,
        current_r,
        primary_reached,
        cfg,
    )
    if proposed_stop is not None and current_r >= cfg.protect_min_r:
        if current_r >= cfg.trail_min_r or primary_reached or trade.objective_stage is ObjectiveStage.RUNNER:
            return _decision(
                trade,
                evidence,
                current_r,
                TradeManagerAction.TRAIL,
                proposed_stop=proposed_stop,
                reason="STRUCTURAL_TRAIL_EARNED",
            )
        return _decision(
            trade,
            evidence,
            current_r,
            TradeManagerAction.PROTECT,
            proposed_stop=proposed_stop,
            reason="STRUCTURAL_PROTECTION_EARNED",
        )

    reason = "PRIMARY_CHECKPOINT_CONTINUATION" if primary_reached else "THESIS_HEALTHY_HOLD"
    return _decision(
        trade,
        evidence,
        current_r,
        TradeManagerAction.HOLD,
        reason=reason,
    )


def _runner_eligible(
    trade: ManagedTrade,
    evidence: ManagementEvidence,
    exit_price: float,
    cfg: TradeManagerConfig,
) -> bool:
    if trade.objective_stage is ObjectiveStage.RUNNER:
        return False
    expansion = trade.expansion_target
    runner = trade.runner_candidate
    if expansion is None or runner is None:
        return False
    distance_r = _directional_distance(trade.direction, exit_price, expansion.price) / trade.original_r_price
    if distance_r > cfg.runner_activation_distance_r:
        return False
    if not _target_beyond(trade.direction, runner.price, expansion.price):
        return False
    if not _target_beyond(trade.direction, runner.price, exit_price):
        return False
    return (
        evidence.continuation_score >= cfg.runner_continuation_min
        and evidence.reversal_score <= cfg.runner_reversal_max
        and evidence.structure_integrity >= cfg.runner_structure_min
        and evidence.path_quality >= cfg.runner_path_min
    )


def _structural_stop_candidate(
    trade: ManagedTrade,
    evidence: ManagementEvidence,
    exit_price: float,
    current_r: float,
    primary_reached: bool,
    cfg: TradeManagerConfig,
) -> float | None:
    if current_r < cfg.protect_min_r or evidence.structure_integrity < cfg.protect_structure_min:
        return None

    if trade.objective_stage is ObjectiveStage.RUNNER:
        preference = (Timeframe.H1, Timeframe.M15, Timeframe.M5)
    elif current_r >= cfg.trail_min_r or primary_reached:
        preference = (Timeframe.M15, Timeframe.M5)
    else:
        preference = (Timeframe.M5,)

    by_timeframe = {reference.timeframe: reference for reference in evidence.stop_references}
    for timeframe in preference:
        reference = by_timeframe.get(timeframe)
        if reference is None:
            continue
        buffer = reference.atr * cfg.trail_buffer_atr
        candidate = reference.price - buffer if trade.direction is Direction.BUY else reference.price + buffer
        if _valid_tightening_stop(trade, candidate, exit_price):
            return candidate
    return None


def _valid_tightening_stop(trade: ManagedTrade, candidate: float, exit_price: float) -> bool:
    if trade.direction is Direction.BUY:
        return trade.current_stop < candidate < exit_price
    return exit_price < candidate < trade.current_stop


def _current_r(trade: ManagedTrade, exit_price: float) -> float:
    if trade.direction is Direction.BUY:
        move = exit_price - trade.entry_price
    else:
        move = trade.entry_price - exit_price
    return move / trade.original_r_price


def _target_reached(trade: ManagedTrade, target, exit_price: float) -> bool:
    if target is None:
        return False
    return _directional_distance(trade.direction, exit_price, target.price) <= 0


def _directional_distance(direction: Direction, price: float, target: float) -> float:
    return target - price if direction is Direction.BUY else price - target


def _target_beyond(direction: Direction, candidate: float, reference: float) -> bool:
    return candidate > reference if direction is Direction.BUY else candidate < reference


def _stop_references(
    intelligence: IntelligenceSnapshot,
    direction: Direction,
) -> tuple[StructuralStopReference, ...]:
    references: list[StructuralStopReference] = []
    for timeframe in (Timeframe.M5, Timeframe.M15, Timeframe.H1):
        frame = _frame(intelligence, timeframe)
        if frame is None or frame.quant.atr is None:
            continue
        swing = frame.structure.protected_low if direction is Direction.BUY else frame.structure.protected_high
        if swing is None:
            continue
        references.append(
            StructuralStopReference(
                timeframe=timeframe,
                price=swing.price,
                atr=frame.quant.atr,
            )
        )
    return tuple(references)


def _multi_frame_score(
    intelligence: IntelligenceSnapshot,
    direction: Direction,
    scorer,
    weights: tuple[tuple[Timeframe, float], ...],
) -> float | None:
    parts: list[tuple[float | None, float]] = []
    for timeframe, weight in weights:
        frame = _frame(intelligence, timeframe)
        parts.append((None if frame is None else scorer(frame, direction), weight))
    return _weighted_mean(tuple(parts), fallback=None)


def _frame(
    intelligence: IntelligenceSnapshot,
    timeframe: Timeframe,
) -> TimeframeIntelligence | None:
    try:
        return intelligence.for_timeframe(timeframe)
    except KeyError:
        return None


def _structure_score(frame: TimeframeIntelligence, direction: Direction) -> float | None:
    state = frame.structure.state
    if state is StructureState.UNDETERMINED:
        state_score = None
    elif state is StructureState.RANGE:
        state_score = 50.0
    elif state is StructureState.TRANSITION:
        state_score = 42.0
    elif (state is StructureState.BULLISH and direction is Direction.BUY) or (
        state is StructureState.BEARISH and direction is Direction.SELL
    ):
        state_score = 90.0
    else:
        state_score = 15.0
    evidence = (
        frame.structure.bull_evidence
        if direction is Direction.BUY
        else frame.structure.bear_evidence
    )
    return _weighted_mean(((state_score, 0.65), (_clamp(evidence), 0.35)), fallback=state_score)


def _momentum_score(frame: TimeframeIntelligence, direction: Direction) -> float | None:
    trend = frame.quant.trend_support
    if trend is Direction.NONE:
        trend_score = 50.0
    elif trend is direction:
        trend_score = 82.0
    else:
        trend_score = 20.0
    phase_score = {
        MomentumPhase.BUILDING: 72.0,
        MomentumPhase.EXPANDING: 90.0,
        MomentumPhase.MATURE: 64.0,
        MomentumPhase.EXHAUSTING: 42.0,
        MomentumPhase.REVERSING: 30.0,
        MomentumPhase.UNKNOWN: None,
    }[frame.quant.momentum_phase]
    return _weighted_mean(((trend_score, 0.60), (phase_score, 0.40)), fallback=trend_score)


def _candle_score(frame: TimeframeIntelligence, direction: Direction) -> float:
    sequence = frame.structure.sequence
    if direction is Direction.BUY:
        sequence_score = {
            CandleSequenceState.BULL_EXPANSION: 90.0,
            CandleSequenceState.BULL_CONTINUATION: 78.0,
            CandleSequenceState.BULL_REJECTION: 72.0,
            CandleSequenceState.COMPRESSION: 55.0,
            CandleSequenceState.MIXED: 50.0,
            CandleSequenceState.BEAR_REJECTION: 35.0,
            CandleSequenceState.BEAR_CONTINUATION: 25.0,
            CandleSequenceState.BEAR_EXPANSION: 15.0,
        }[sequence]
    else:
        sequence_score = {
            CandleSequenceState.BEAR_EXPANSION: 90.0,
            CandleSequenceState.BEAR_CONTINUATION: 78.0,
            CandleSequenceState.BEAR_REJECTION: 72.0,
            CandleSequenceState.COMPRESSION: 55.0,
            CandleSequenceState.MIXED: 50.0,
            CandleSequenceState.BULL_REJECTION: 35.0,
            CandleSequenceState.BULL_CONTINUATION: 25.0,
            CandleSequenceState.BULL_EXPANSION: 15.0,
        }[sequence]
    latest = frame.structure.latest_candle.direction
    latest_score = 50.0 if latest is Direction.NONE else (65.0 if latest is direction else 35.0)
    return _weighted_mean(((sequence_score, 0.75), (latest_score, 0.25)), fallback=50.0) or 50.0


def _path_score(frame: TimeframeIntelligence, direction: Direction) -> float | None:
    path = frame.liquidity.path_up if direction is Direction.BUY else frame.liquidity.path_down
    return {
        LiquidityPath.OPEN: 85.0,
        LiquidityPath.MIXED: 60.0,
        LiquidityPath.CROWDED: 30.0,
        LiquidityPath.UNKNOWN: None,
    }[path]


def _weighted_mean(
    parts: tuple[tuple[float | None, float], ...],
    *,
    fallback: float | None,
) -> float | None:
    available = tuple((value, weight) for value, weight in parts if value is not None and weight > 0)
    if not available:
        return fallback
    total_weight = sum(weight for _, weight in available)
    return _clamp(sum(value * weight for value, weight in available) / total_weight)


def _clamp(value: float) -> float:
    return min(100.0, max(0.0, value))


def _decision(
    trade: ManagedTrade,
    evidence: ManagementEvidence,
    current_r: float,
    action: TradeManagerAction,
    *,
    proposed_stop: float | None = None,
    proposed_tp: float | None = None,
    stage: ObjectiveStage | None = None,
    reason: str,
) -> TradeManagementDecision:
    return TradeManagementDecision(
        action=action,
        current_r=current_r,
        continuation_score=evidence.continuation_score,
        reversal_score=evidence.reversal_score,
        structure_integrity=evidence.structure_integrity,
        path_quality=evidence.path_quality,
        objective_stage=stage or trade.objective_stage,
        proposed_stop=proposed_stop,
        proposed_tp=proposed_tp,
        reason=reason,
    )
