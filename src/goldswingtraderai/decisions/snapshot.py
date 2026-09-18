"""Coherent read-only Phase-4 decision pipeline.

This is the single orchestration path from IntelligenceSnapshot to strategy floor,
BUY/SELL fusion, Opportunity lifecycle and M5 entry timing. It has no risk or
broker-write authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from goldswingtraderai.decisions.fusion import DecisionBoard, FusionConfig, fuse_decision
from goldswingtraderai.decisions.opportunity import (
    Opportunity,
    OpportunityConfig,
    update_opportunity,
)
from goldswingtraderai.decisions.timing import (
    EntryTimingConfig,
    EntryTimingResult,
    evaluate_entry_timing,
)
from goldswingtraderai.domain.enums import OpportunityStage
from goldswingtraderai.intelligence.snapshot import IntelligenceSnapshot
from goldswingtraderai.strategies.confluence import (
    ConfluenceBonusConfig,
    apply_optional_confluence,
)
from goldswingtraderai.strategies.floor import (
    StrategyFloorConfig,
    StrategyFloorReport,
    evaluate_strategy_floor,
)


@dataclass(frozen=True, slots=True)
class DecisionConfig:
    strategies: StrategyFloorConfig = StrategyFloorConfig()
    confluence: ConfluenceBonusConfig = ConfluenceBonusConfig()
    fusion: FusionConfig = FusionConfig()
    opportunity: OpportunityConfig = OpportunityConfig()
    timing: EntryTimingConfig = EntryTimingConfig()


@dataclass(frozen=True, slots=True)
class DecisionSnapshot:
    strategies: StrategyFloorReport
    board: DecisionBoard
    opportunity: Opportunity | None
    timing: EntryTimingResult | None


def build_decision_snapshot(
    intelligence: IntelligenceSnapshot,
    now_utc: datetime,
    *,
    previous_opportunity: Opportunity | None = None,
    config: DecisionConfig | None = None,
) -> DecisionSnapshot:
    """Build one deterministic analytical decision state from shared intelligence."""

    _require_utc(now_utc)
    cfg = config or DecisionConfig()
    strategies = evaluate_strategy_floor(intelligence, cfg.strategies)
    # Optional technical confluence is positive-only. Research may disable an
    # individual source for ablation, but production defaults keep all sources on.
    strategies = apply_optional_confluence(strategies, intelligence, cfg.confluence)
    board = fuse_decision(strategies, intelligence, cfg.fusion)
    opportunity = update_opportunity(
        board,
        now_utc,
        previous=previous_opportunity,
        config=cfg.opportunity,
    )

    timing: EntryTimingResult | None = None
    if opportunity is not None and opportunity.stage not in {
        OpportunityStage.TRIGGERED,
        OpportunityStage.MISSED,
        OpportunityStage.STALE,
        OpportunityStage.INVALIDATED,
    }:
        timing = evaluate_entry_timing(
            opportunity,
            board,
            intelligence,
            now_utc,
            cfg.timing,
        )
        opportunity = timing.opportunity

    return DecisionSnapshot(
        strategies=strategies,
        board=board,
        opportunity=opportunity,
        timing=timing,
    )


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("decision timestamp must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("decision timestamp must be UTC")
