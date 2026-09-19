"""Independent BUY/SELL thesis fusion with bounded family synergy and Red Team.

Safety/risk are intentionally absent. This module only fuses analytical strategy
evidence and keeps strong opposing evidence visible as conflict.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from goldswingtraderai.domain.enums import Direction, ExtensionState, StrategyFamily, Timeframe
from goldswingtraderai.intelligence.snapshot import IntelligenceSnapshot
from goldswingtraderai.strategies.floor import FamilyReport, StrategyFloorReport


@dataclass(frozen=True, slots=True)
class ThesisReport:
    direction: Direction
    score: float
    coverage: float
    leading_families: tuple[StrategyFamily, ...]
    supporting_evidence: tuple[str, ...]
    conflicting_evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DecisionBoard:
    buy: ThesisReport
    sell: ThesisReport
    leading_direction: Direction
    directional_edge: float
    conflict_score: float
    opportunity_score: float
    evidence_coverage: float
    confidence: float
    red_team_objections: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FusionConfig:
    primary_family_weight: float = 0.65
    secondary_family_weight: float = 0.25
    tertiary_family_weight: float = 0.10
    strong_family_score: float = 72.0
    max_synergy_bonus: float = 4.0
    conflict_start: float = 60.0
    max_conflict_penalty: float = 10.0

    def __post_init__(self) -> None:
        weights = (
            self.primary_family_weight,
            self.secondary_family_weight,
            self.tertiary_family_weight,
        )
        if any(weight < 0 for weight in weights) or abs(sum(weights) - 1.0) > 1e-9:
            raise ValueError("family fusion weights must be non-negative and sum to one")
        if not 0 <= self.strong_family_score <= 100:
            raise ValueError("strong family score must be between 0 and 100")
        if self.max_synergy_bonus < 0 or self.max_conflict_penalty < 0:
            raise ValueError("fusion bonuses/penalties cannot be negative")


def fuse_decision(
    floor: StrategyFloorReport,
    intelligence: IntelligenceSnapshot,
    config: FusionConfig | None = None,
) -> DecisionBoard:
    """Fuse family hypotheses without converting safety into a weighted score."""

    cfg = config or FusionConfig()
    buy = _thesis(Direction.BUY, floor, cfg)
    sell = _thesis(Direction.SELL, floor, cfg)

    edge = buy.score - sell.score
    if edge > 0:
        leading = Direction.BUY
        lead, opposition = buy, sell
    elif edge < 0:
        leading = Direction.SELL
        lead, opposition = sell, buy
    else:
        leading = Direction.NONE
        lead, opposition = buy, sell

    conflict = min(buy.score, sell.score)
    penalty = 0.0
    if conflict > cfg.conflict_start:
        span = max(1.0, 100.0 - cfg.conflict_start)
        penalty = min(
            cfg.max_conflict_penalty,
            ((conflict - cfg.conflict_start) / span) * cfg.max_conflict_penalty,
        )
    opportunity = _clip(lead.score - penalty) if leading is not Direction.NONE else 0.0
    coverage = min(buy.coverage, sell.coverage)
    clarity = min(1.0, abs(edge) / 40.0)
    confidence = _clip((lead.coverage * 70.0) + (clarity * 30.0))
    objections = _red_team(leading, lead, opposition, intelligence, floor, cfg)

    return DecisionBoard(
        buy=buy,
        sell=sell,
        leading_direction=leading,
        directional_edge=edge,
        conflict_score=conflict,
        opportunity_score=opportunity,
        evidence_coverage=coverage,
        confidence=confidence,
        red_team_objections=objections,
    )


def _thesis(
    direction: Direction,
    floor: StrategyFloorReport,
    cfg: FusionConfig,
) -> ThesisReport:
    ranked: list[tuple[FamilyReport, float, float, tuple[str, ...], tuple[str, ...]]] = []
    for report in floor.families:
        case = report.buy if direction is Direction.BUY else report.sell
        ranked.append((report, case.score, case.coverage, case.evidence, case.conflicts))
    ranked.sort(key=lambda item: item[1], reverse=True)

    selected = ranked[:3]
    weights = (
        cfg.primary_family_weight,
        cfg.secondary_family_weight,
        cfg.tertiary_family_weight,
    )
    score = sum(item[1] * weight for item, weight in zip(selected, weights))
    coverage = sum(item[2] * weight for item, weight in zip(selected, weights))

    strong_count = sum(item[1] >= cfg.strong_family_score for item in selected[:2])
    if strong_count >= 2:
        overlap = set(selected[0][3]).intersection(selected[1][3])
        correlation_factor = 0.5 if overlap else 1.0
        score += cfg.max_synergy_bonus * correlation_factor

    evidence = _unique(
        item
        for report, _, _, support, _ in selected
        for item in (f"{report.family}:{name}" for name in support)
    )
    conflicts = _unique(
        item
        for report, _, _, _, conflict in selected
        for item in (f"{report.family}:{name}" for name in conflict)
    )
    return ThesisReport(
        direction=direction,
        score=_clip(score),
        coverage=min(1.0, max(0.0, coverage)),
        leading_families=tuple(item[0].family for item in selected),
        supporting_evidence=evidence,
        conflicting_evidence=conflicts,
    )


def _red_team(
    leading: Direction,
    lead: ThesisReport,
    opposition: ThesisReport,
    intelligence: IntelligenceSnapshot,
    floor: StrategyFloorReport,
    cfg: FusionConfig,
) -> tuple[str, ...]:
    if leading is Direction.NONE:
        return ("NO_DIRECTIONAL_EDGE",)

    objections: list[str] = []
    if opposition.score >= cfg.strong_family_score:
        objections.append("STRONG_OPPOSING_THESIS")
    if lead.coverage < 0.60:
        objections.append("LOW_EVIDENCE_COVERAGE")
    if lead.conflicting_evidence:
        objections.append("LEADING_FAMILY_CONFLICTS")

    m5 = intelligence.for_timeframe(Timeframe.M5)
    if m5.quant.extension_state is ExtensionState.SEVERELY_EXTENDED:
        objections.append("ENTRY_EXTENDED")

    ranked = sorted(
        floor.families,
        key=lambda report: (report.buy.score if leading is Direction.BUY else report.sell.score),
        reverse=True,
    )
    if len(ranked) >= 2:
        first_case = ranked[0].buy if leading is Direction.BUY else ranked[0].sell
        second_case = ranked[1].buy if leading is Direction.BUY else ranked[1].sell
        shared = set(first_case.evidence).intersection(second_case.evidence)
        if len(shared) >= 2:
            objections.append("CORRELATED_FAMILY_SUPPORT")

    return tuple(objections)


def _unique(items: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(items))


def _clip(value: float) -> float:
    return min(100.0, max(0.0, value))
