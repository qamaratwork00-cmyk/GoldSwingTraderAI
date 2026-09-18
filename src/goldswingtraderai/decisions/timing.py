"""M5 entry timing kept separate from opportunity quality and hard safety."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from goldswingtraderai.decisions.fusion import DecisionBoard
from goldswingtraderai.decisions.opportunity import Opportunity, transition_opportunity
from goldswingtraderai.domain.enums import (
    CandleSequenceState,
    Direction,
    ExtensionState,
    MomentumPhase,
    OpportunityStage,
    Timeframe,
)
from goldswingtraderai.intelligence.snapshot import IntelligenceSnapshot
from goldswingtraderai.intelligence.technical import LocationCategory


class TimingAction(StrEnum):
    ENTER_BUY = "ENTER_BUY"
    ENTER_SELL = "ENTER_SELL"
    WAIT = "WAIT"
    MISSED = "MISSED"
    INVALID = "INVALID"


@dataclass(frozen=True, slots=True)
class EntryTimingResult:
    action: TimingAction
    score: float
    coverage: float
    reasons: tuple[str, ...]
    opportunity: Opportunity


@dataclass(frozen=True, slots=True)
class EntryTimingConfig:
    enter_score: float = 62.0
    minimum_opportunity_score: float = 60.0
    invalidate_score: float = 45.0
    missed_after_minutes: int = 60

    def __post_init__(self) -> None:
        if not 0 <= self.invalidate_score < self.minimum_opportunity_score <= 100:
            raise ValueError("timing opportunity thresholds are invalid")
        if not 0 <= self.enter_score <= 100:
            raise ValueError("entry score must be between 0 and 100")
        if self.missed_after_minutes <= 0:
            raise ValueError("missed-after window must be positive")


def evaluate_entry_timing(
    opportunity: Opportunity,
    board: DecisionBoard,
    intelligence: IntelligenceSnapshot,
    now_utc: datetime,
    config: EntryTimingConfig | None = None,
) -> EntryTimingResult:
    """Return ENTER/WAIT/MISSED/INVALID without applying hard broker safety."""

    cfg = config or EntryTimingConfig()
    if opportunity.stage in {
        OpportunityStage.TRIGGERED,
        OpportunityStage.MISSED,
        OpportunityStage.STALE,
        OpportunityStage.INVALIDATED,
    }:
        raise ValueError("terminal opportunity cannot be re-timed")

    if (
        board.leading_direction is not opportunity.direction
        or board.opportunity_score < cfg.invalidate_score
    ):
        invalid = transition_opportunity(opportunity, OpportunityStage.INVALIDATED, now_utc)
        return EntryTimingResult(
            action=TimingAction.INVALID,
            score=0.0,
            coverage=1.0,
            reasons=("OPPORTUNITY_THESIS_NO_LONGER_SURVIVES",),
            opportunity=invalid,
        )

    m5 = intelligence.for_timeframe(Timeframe.M5)
    m15 = intelligence.for_timeframe(Timeframe.M15)
    direction = opportunity.direction
    features = (
        ("M5_STRUCTURE", _structure(m5, direction), 0.24),
        ("M5_CANDLE_SEQUENCE", _sequence(m5, direction), 0.22),
        ("M5_MOMENTUM", _momentum(m5, direction), 0.18),
        ("M5_LOCATION", _location(m5, direction), 0.12),
        ("M15_TARGET_ROOM", _target_room(m15, direction), 0.14),
        ("M5_LIQUIDITY", _liquidity(m5, direction), 0.10),
    )
    available = [(name, value, weight) for name, value, weight in features if value is not None]
    available_weight = sum(weight for _, _, weight in available)
    score = (
        sum(float(value) * weight for _, value, weight in available) / available_weight
        if available_weight > 0
        else 50.0
    )
    coverage = available_weight / sum(weight for _, _, weight in features)
    reasons = [name for name, value, _ in available if float(value) >= 65.0]

    age_minutes = (now_utc - opportunity.created_at_utc).total_seconds() / 60.0
    severe_extension = m5.quant.extension_state is ExtensionState.SEVERELY_EXTENDED
    can_miss = opportunity.stage in {
        OpportunityStage.ARMED,
        OpportunityStage.WAITING,
        OpportunityStage.READY,
        OpportunityStage.RE_ARMED,
    }

    if severe_extension:
        if can_miss and age_minutes >= cfg.missed_after_minutes:
            missed = transition_opportunity(opportunity, OpportunityStage.MISSED, now_utc)
            return EntryTimingResult(
                action=TimingAction.MISSED,
                score=_clip(score),
                coverage=coverage,
                reasons=(*reasons, "ENTRY_SEVERELY_EXTENDED_WINDOW_PASSED"),
                opportunity=missed,
            )
        waited = _wait_stage(opportunity, now_utc)
        return EntryTimingResult(
            action=TimingAction.WAIT,
            score=_clip(score),
            coverage=coverage,
            reasons=(*reasons, "ENTRY_SEVERELY_EXTENDED"),
            opportunity=waited,
        )

    if (
        board.opportunity_score >= cfg.minimum_opportunity_score
        and score >= cfg.enter_score
        and opportunity.stage is not OpportunityStage.DISCOVERED
    ):
        ready = transition_opportunity(opportunity, OpportunityStage.READY, now_utc)
        action = TimingAction.ENTER_BUY if direction is Direction.BUY else TimingAction.ENTER_SELL
        return EntryTimingResult(
            action=action,
            score=_clip(score),
            coverage=coverage,
            reasons=tuple(reasons) or ("ENTRY_TIMING_ACCEPTABLE",),
            opportunity=ready,
        )

    waited = _wait_stage(opportunity, now_utc)
    wait_reasons = list(reasons)
    if board.opportunity_score < cfg.minimum_opportunity_score:
        wait_reasons.append("OPPORTUNITY_NOT_ARMED_FOR_ENTRY")
    if score < cfg.enter_score:
        wait_reasons.append("ENTRY_NOT_READY")
    return EntryTimingResult(
        action=TimingAction.WAIT,
        score=_clip(score),
        coverage=coverage,
        reasons=tuple(wait_reasons),
        opportunity=waited,
    )


def _wait_stage(opportunity: Opportunity, now_utc: datetime) -> Opportunity:
    if opportunity.stage is OpportunityStage.DISCOVERED:
        return opportunity
    if opportunity.stage is OpportunityStage.WAITING:
        return transition_opportunity(opportunity, OpportunityStage.WAITING, now_utc)
    return transition_opportunity(opportunity, OpportunityStage.WAITING, now_utc)


def _structure(frame, direction: Direction) -> float:
    return frame.structure.bull_evidence if direction is Direction.BUY else frame.structure.bear_evidence


def _sequence(frame, direction: Direction) -> float:
    state = frame.structure.sequence
    ideal = {
        Direction.BUY: {
            CandleSequenceState.BULL_REJECTION: 90.0,
            CandleSequenceState.BULL_CONTINUATION: 84.0,
            CandleSequenceState.BULL_EXPANSION: 80.0,
        },
        Direction.SELL: {
            CandleSequenceState.BEAR_REJECTION: 90.0,
            CandleSequenceState.BEAR_CONTINUATION: 84.0,
            CandleSequenceState.BEAR_EXPANSION: 80.0,
        },
    }[direction]
    if state in ideal:
        return ideal[state]
    opposing = {
        Direction.BUY: {
            CandleSequenceState.BEAR_REJECTION,
            CandleSequenceState.BEAR_CONTINUATION,
            CandleSequenceState.BEAR_EXPANSION,
        },
        Direction.SELL: {
            CandleSequenceState.BULL_REJECTION,
            CandleSequenceState.BULL_CONTINUATION,
            CandleSequenceState.BULL_EXPANSION,
        },
    }[direction]
    if state in opposing:
        return 20.0
    if state is CandleSequenceState.COMPRESSION:
        return 48.0
    return 52.0


def _momentum(frame, direction: Direction) -> float | None:
    phase = frame.quant.momentum_phase
    if phase is MomentumPhase.UNKNOWN:
        return None
    aligned = frame.quant.trend_support is direction
    if phase is MomentumPhase.BUILDING:
        return 86.0 if aligned else 50.0
    if phase is MomentumPhase.EXPANDING:
        return 82.0 if aligned else 52.0
    if phase is MomentumPhase.MATURE:
        return 62.0 if aligned else 45.0
    if phase is MomentumPhase.EXHAUSTING:
        return 32.0 if aligned else 42.0
    if phase is MomentumPhase.REVERSING:
        return 25.0 if aligned else 72.0
    return 50.0


def _location(frame, direction: Direction) -> float | None:
    category = frame.technical.buy_location if direction is Direction.BUY else frame.technical.sell_location
    return {
        LocationCategory.EXCELLENT: 95.0,
        LocationCategory.GOOD: 82.0,
        LocationCategory.NEUTRAL: 58.0,
        LocationCategory.POOR: 35.0,
        LocationCategory.DANGEROUS: 15.0,
        LocationCategory.UNKNOWN: None,
    }[category]


def _target_room(frame, direction: Direction) -> float | None:
    room = frame.technical.buy_target_room if direction is Direction.BUY else frame.technical.sell_target_room
    atr = frame.quant.atr
    if room is None or atr is None or atr <= 0:
        return None
    ratio = room / atr
    if ratio < 0.25:
        return 10.0
    if ratio < 0.75:
        return 35.0
    if ratio < 1.50:
        return 62.0
    if ratio < 2.50:
        return 82.0
    return 95.0


def _liquidity(frame, direction: Direction) -> float:
    return frame.liquidity.buy_evidence if direction is Direction.BUY else frame.liquidity.sell_evidence


def _clip(value: float) -> float:
    return min(100.0, max(0.0, value))
