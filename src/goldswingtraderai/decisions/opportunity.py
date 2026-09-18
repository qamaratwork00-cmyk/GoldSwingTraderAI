"""Opportunity lifecycle separate from immediate entry timing."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone

from goldswingtraderai.decisions.fusion import DecisionBoard
from goldswingtraderai.domain.enums import Direction, OpportunityStage, StrategyFamily
from goldswingtraderai.domain.ids import EntityId, new_episode_id, new_opportunity_id


_TERMINAL_STAGES = {
    OpportunityStage.TRIGGERED,
    OpportunityStage.MISSED,
    OpportunityStage.STALE,
    OpportunityStage.INVALIDATED,
}

_ALLOWED_TRANSITIONS: dict[OpportunityStage, set[OpportunityStage]] = {
    OpportunityStage.DISCOVERED: {
        OpportunityStage.ARMED,
        OpportunityStage.STALE,
        OpportunityStage.INVALIDATED,
    },
    OpportunityStage.ARMED: {
        OpportunityStage.WAITING,
        OpportunityStage.READY,
        OpportunityStage.MISSED,
        OpportunityStage.STALE,
        OpportunityStage.INVALIDATED,
    },
    OpportunityStage.WAITING: {
        OpportunityStage.WAITING,
        OpportunityStage.READY,
        OpportunityStage.MISSED,
        OpportunityStage.STALE,
        OpportunityStage.INVALIDATED,
    },
    OpportunityStage.READY: {
        OpportunityStage.READY,
        OpportunityStage.WAITING,
        OpportunityStage.TRIGGERED,
        OpportunityStage.MISSED,
        OpportunityStage.INVALIDATED,
    },
    OpportunityStage.MISSED: {OpportunityStage.RE_ARMED},
    OpportunityStage.RE_ARMED: {
        OpportunityStage.WAITING,
        OpportunityStage.READY,
        OpportunityStage.MISSED,
        OpportunityStage.STALE,
        OpportunityStage.INVALIDATED,
    },
    OpportunityStage.TRIGGERED: set(),
    OpportunityStage.STALE: set(),
    OpportunityStage.INVALIDATED: set(),
}


@dataclass(frozen=True, slots=True)
class Opportunity:
    opportunity_id: EntityId
    episode_id: EntityId
    direction: Direction
    stage: OpportunityStage
    created_at_utc: datetime
    updated_at_utc: datetime
    opportunity_score: float
    thesis_score: float
    source_families: tuple[StrategyFamily, ...]

    def __post_init__(self) -> None:
        _require_utc(self.created_at_utc)
        _require_utc(self.updated_at_utc)
        if self.direction is Direction.NONE:
            raise ValueError("opportunity direction must be BUY or SELL")
        if not 0 <= self.opportunity_score <= 100 or not 0 <= self.thesis_score <= 100:
            raise ValueError("opportunity/thesis scores must be between 0 and 100")
        if not self.source_families:
            raise ValueError("opportunity requires at least one source family")
        if self.updated_at_utc < self.created_at_utc:
            raise ValueError("opportunity update cannot precede creation")


@dataclass(frozen=True, slots=True)
class OpportunityConfig:
    discover_score: float = 55.0
    arm_score: float = 62.0
    maintain_score: float = 48.0
    minimum_directional_edge: float = 6.0

    def __post_init__(self) -> None:
        if not 0 <= self.maintain_score <= self.discover_score <= self.arm_score <= 100:
            raise ValueError("opportunity score thresholds are invalid")
        if not 0 <= self.minimum_directional_edge <= 100:
            raise ValueError("minimum directional edge is invalid")


def update_opportunity(
    board: DecisionBoard,
    now_utc: datetime,
    previous: Opportunity | None = None,
    config: OpportunityConfig | None = None,
) -> Opportunity | None:
    """Create/maintain one directional opportunity without timing it yet."""

    _require_utc(now_utc)
    cfg = config or OpportunityConfig()
    direction = board.leading_direction
    thesis = board.buy if direction is Direction.BUY else board.sell

    if previous is not None and previous.stage in _TERMINAL_STAGES:
        return previous

    if previous is not None:
        survives = (
            direction is previous.direction
            and board.opportunity_score >= cfg.maintain_score
            and thesis.score >= cfg.maintain_score
        )
        if not survives:
            return transition_opportunity(
                replace(
                    previous,
                    opportunity_score=min(100.0, max(0.0, board.opportunity_score)),
                    thesis_score=min(100.0, max(0.0, thesis.score)),
                ),
                OpportunityStage.INVALIDATED,
                now_utc,
            )

        stage = previous.stage
        if stage is OpportunityStage.DISCOVERED and _armable(board, cfg):
            stage = OpportunityStage.ARMED
        return replace(
            previous,
            stage=stage,
            updated_at_utc=now_utc,
            opportunity_score=board.opportunity_score,
            thesis_score=thesis.score,
            source_families=thesis.leading_families,
        )

    if direction is Direction.NONE:
        return None
    if board.opportunity_score < cfg.discover_score:
        return None
    if abs(board.directional_edge) < cfg.minimum_directional_edge:
        return None

    stage = OpportunityStage.ARMED if _armable(board, cfg) else OpportunityStage.DISCOVERED
    return Opportunity(
        opportunity_id=new_opportunity_id(),
        episode_id=new_episode_id(),
        direction=direction,
        stage=stage,
        created_at_utc=now_utc,
        updated_at_utc=now_utc,
        opportunity_score=board.opportunity_score,
        thesis_score=thesis.score,
        source_families=thesis.leading_families,
    )


def transition_opportunity(
    opportunity: Opportunity,
    stage: OpportunityStage,
    now_utc: datetime,
) -> Opportunity:
    """Apply one explicit lifecycle transition while preserving identity."""

    _require_utc(now_utc)
    if stage is opportunity.stage:
        return replace(opportunity, updated_at_utc=now_utc)
    allowed = _ALLOWED_TRANSITIONS[opportunity.stage]
    if stage not in allowed:
        raise ValueError(f"invalid opportunity transition: {opportunity.stage} -> {stage}")
    return replace(opportunity, stage=stage, updated_at_utc=now_utc)


def rearm_missed_opportunity(
    opportunity: Opportunity,
    now_utc: datetime,
    *,
    fresh_structural_event: bool,
) -> Opportunity:
    """Re-arm only when a caller proves a genuinely fresh structural/timing event."""

    if opportunity.stage is not OpportunityStage.MISSED:
        raise ValueError("only MISSED opportunities can be re-armed")
    if not fresh_structural_event:
        raise ValueError("re-arm requires a genuinely fresh structural/timing event")
    return transition_opportunity(opportunity, OpportunityStage.RE_ARMED, now_utc)


def _armable(board: DecisionBoard, cfg: OpportunityConfig) -> bool:
    return (
        board.opportunity_score >= cfg.arm_score
        and abs(board.directional_edge) >= cfg.minimum_directional_edge
    )


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("opportunity timestamps must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("opportunity timestamps must be UTC")
