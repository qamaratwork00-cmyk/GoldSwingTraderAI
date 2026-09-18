"""Decision-level ablation over the production replay path.

This module measures how optional confluence changes analytical opportunity/entry
coverage. It deliberately does not invent P/L from decision events; profitability
requires separately labelled trade/outcome evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from goldswingtraderai.decisions.snapshot import DecisionConfig
from goldswingtraderai.decisions.timing import TimingAction
from goldswingtraderai.domain.enums import Direction, Timeframe
from goldswingtraderai.intelligence.snapshot import IntelligenceConfig
from goldswingtraderai.research.replay import ReplayDataset, ReplayRun, run_decision_replay
from goldswingtraderai.strategies.confluence import ConfluenceBonusConfig


class ConfluenceAblationVariant(StrEnum):
    BASE = "BASE"
    TRENDLINE = "TRENDLINE"
    FIBONACCI = "FIBONACCI"
    DIRECTIONAL_COMBINED = "DIRECTIONAL_COMBINED"
    ALL = "ALL"


@dataclass(frozen=True, slots=True)
class DecisionReplayMetrics:
    events: int
    opportunity_events: int
    enter_events: int
    wait_events: int
    missed_events: int
    invalid_events: int
    buy_leading_events: int
    sell_leading_events: int
    average_opportunity_score: float
    average_conflict_score: float


@dataclass(frozen=True, slots=True)
class ConfluenceAblationRow:
    variant: ConfluenceAblationVariant
    metrics: DecisionReplayMetrics
    opportunity_event_delta_vs_base: int
    enter_event_delta_vs_base: int
    average_opportunity_score_delta_vs_base: float


@dataclass(frozen=True, slots=True)
class ConfluenceAblationReport:
    rows: tuple[ConfluenceAblationRow, ...]
    poc_marginal_opportunity_event_delta: int
    poc_marginal_enter_event_delta: int
    poc_marginal_average_opportunity_score_delta: float

    def row(self, variant: ConfluenceAblationVariant) -> ConfluenceAblationRow:
        for item in self.rows:
            if item.variant is variant:
                return item
        raise KeyError(variant)


def run_confluence_ablation(
    dataset: ReplayDataset,
    *,
    start_utc: datetime | None = None,
    end_utc: datetime | None = None,
    minimum_bars: dict[Timeframe, int] | None = None,
    intelligence_config: IntelligenceConfig | None = None,
    decision_config: DecisionConfig | None = None,
) -> ConfluenceAblationReport:
    """Replay the same chronology with controlled optional-confluence variants.

    POC is direction-neutral, so its marginal analytical effect is measured by
    comparing ALL against DIRECTIONAL_COMBINED (Trendline + Fibonacci, no POC).
    These are decision-frequency/score metrics only, not profitability evidence.
    """

    base_config = decision_config or DecisionConfig()
    variants = (
        ConfluenceAblationVariant.BASE,
        ConfluenceAblationVariant.TRENDLINE,
        ConfluenceAblationVariant.FIBONACCI,
        ConfluenceAblationVariant.DIRECTIONAL_COMBINED,
        ConfluenceAblationVariant.ALL,
    )
    runs: dict[ConfluenceAblationVariant, ReplayRun] = {}
    metrics: dict[ConfluenceAblationVariant, DecisionReplayMetrics] = {}

    for variant in variants:
        config = replace(base_config, confluence=_confluence_config(variant))
        run = run_decision_replay(
            dataset,
            start_utc=start_utc,
            end_utc=end_utc,
            minimum_bars=minimum_bars,
            intelligence_config=intelligence_config,
            decision_config=config,
        )
        runs[variant] = run
        metrics[variant] = summarize_decision_replay(run)

    _assert_same_chronology(tuple(runs.values()))
    base = metrics[ConfluenceAblationVariant.BASE]
    rows = tuple(
        ConfluenceAblationRow(
            variant=variant,
            metrics=metrics[variant],
            opportunity_event_delta_vs_base=(
                metrics[variant].opportunity_events - base.opportunity_events
            ),
            enter_event_delta_vs_base=metrics[variant].enter_events - base.enter_events,
            average_opportunity_score_delta_vs_base=(
                metrics[variant].average_opportunity_score - base.average_opportunity_score
            ),
        )
        for variant in variants
    )

    directional = metrics[ConfluenceAblationVariant.DIRECTIONAL_COMBINED]
    all_sources = metrics[ConfluenceAblationVariant.ALL]
    return ConfluenceAblationReport(
        rows=rows,
        poc_marginal_opportunity_event_delta=(
            all_sources.opportunity_events - directional.opportunity_events
        ),
        poc_marginal_enter_event_delta=all_sources.enter_events - directional.enter_events,
        poc_marginal_average_opportunity_score_delta=(
            all_sources.average_opportunity_score - directional.average_opportunity_score
        ),
    )


def summarize_decision_replay(run: ReplayRun) -> DecisionReplayMetrics:
    """Summarize analytical replay without pretending ENTER events are broker trades."""

    decisions = tuple(item.decision for item in run.decisions)
    actions = tuple(item.timing.action for item in decisions if item.timing is not None)
    boards = tuple(item.board for item in decisions)
    return DecisionReplayMetrics(
        events=len(decisions),
        opportunity_events=sum(item.opportunity is not None for item in decisions),
        enter_events=sum(
            action in {TimingAction.ENTER_BUY, TimingAction.ENTER_SELL} for action in actions
        ),
        wait_events=sum(action is TimingAction.WAIT for action in actions),
        missed_events=sum(action is TimingAction.MISSED for action in actions),
        invalid_events=sum(action is TimingAction.INVALID for action in actions),
        buy_leading_events=sum(board.leading_direction is Direction.BUY for board in boards),
        sell_leading_events=sum(board.leading_direction is Direction.SELL for board in boards),
        average_opportunity_score=_average(tuple(board.opportunity_score for board in boards)),
        average_conflict_score=_average(tuple(board.conflict_score for board in boards)),
    )


def _confluence_config(variant: ConfluenceAblationVariant) -> ConfluenceBonusConfig:
    if variant is ConfluenceAblationVariant.BASE:
        return ConfluenceBonusConfig(trendline=False, fibonacci=False, poc=False)
    if variant is ConfluenceAblationVariant.TRENDLINE:
        return ConfluenceBonusConfig(trendline=True, fibonacci=False, poc=False)
    if variant is ConfluenceAblationVariant.FIBONACCI:
        return ConfluenceBonusConfig(trendline=False, fibonacci=True, poc=False)
    if variant is ConfluenceAblationVariant.DIRECTIONAL_COMBINED:
        return ConfluenceBonusConfig(trendline=True, fibonacci=True, poc=False)
    if variant is ConfluenceAblationVariant.ALL:
        return ConfluenceBonusConfig()
    raise ValueError(f"unsupported confluence ablation variant: {variant}")


def _assert_same_chronology(runs: tuple[ReplayRun, ...]) -> None:
    if not runs:
        return
    reference = tuple(item.as_of_utc for item in runs[0].decisions)
    for run in runs[1:]:
        if tuple(item.as_of_utc for item in run.decisions) != reference:
            raise ValueError("ablation variants must replay identical event chronology")


def _average(values: tuple[float, ...]) -> float:
    return sum(values) / len(values) if values else 0.0
