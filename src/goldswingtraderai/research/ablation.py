"""Confluence ablation over the production chronological replay path.

Decision-level reports measure opportunity/entry coverage without inventing P/L.
Bracket-outcome reports may additionally attach the explicit initial Trade Plan
stop/target bar model from ``research.outcomes``. That second layer reports only
resolved bar-level outcomes and keeps ambiguous/unresolved cases visible.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from goldswingtraderai.decisions.snapshot import DecisionConfig
from goldswingtraderai.decisions.timing import TimingAction
from goldswingtraderai.decisions.trade_plan import TradePlanConfig
from goldswingtraderai.domain.enums import Direction, Timeframe
from goldswingtraderai.intelligence.snapshot import IntelligenceConfig
from goldswingtraderai.research.outcomes import (
    EnterPlanOutcomeMetrics,
    label_enter_plan_outcomes,
    summarize_enter_plan_outcomes,
)
from goldswingtraderai.research.replay import ReplayDataset, ReplayRun, run_decision_replay
from goldswingtraderai.strategies.confluence import ConfluenceBonusConfig


class ConfluenceAblationVariant(StrEnum):
    BASE = "BASE"
    TRENDLINE = "TRENDLINE"
    FIBONACCI = "FIBONACCI"
    DIRECTIONAL_COMBINED = "DIRECTIONAL_COMBINED"
    ALL = "ALL"


_VARIANTS = (
    ConfluenceAblationVariant.BASE,
    ConfluenceAblationVariant.TRENDLINE,
    ConfluenceAblationVariant.FIBONACCI,
    ConfluenceAblationVariant.DIRECTIONAL_COMBINED,
    ConfluenceAblationVariant.ALL,
)


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


@dataclass(frozen=True, slots=True)
class ConfluenceBracketAblationRow:
    variant: ConfluenceAblationVariant
    decision_metrics: DecisionReplayMetrics
    outcome_metrics: EnterPlanOutcomeMetrics
    ready_plan_delta_vs_base: int
    resolved_coverage_delta_vs_base: float
    resolved_bracket_net_r_delta_vs_base: float
    average_mfe_r_delta_vs_base: float


@dataclass(frozen=True, slots=True)
class ConfluenceBracketAblationReport:
    rows: tuple[ConfluenceBracketAblationRow, ...]

    def row(self, variant: ConfluenceAblationVariant) -> ConfluenceBracketAblationRow:
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
    """Replay identical chronology with controlled optional-confluence variants.

    POC is direction-neutral, so its marginal analytical effect is measured by
    comparing ALL against DIRECTIONAL_COMBINED (Trendline + Fibonacci, no POC).
    These are decision-frequency/score metrics only, not profitability evidence.
    """

    runs = _run_variants(
        dataset,
        start_utc=start_utc,
        end_utc=end_utc,
        minimum_bars=minimum_bars,
        intelligence_config=intelligence_config,
        decision_config=decision_config,
    )
    metrics = {variant: summarize_decision_replay(run) for variant, run in runs.items()}
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
        for variant in _VARIANTS
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


def run_confluence_bracket_ablation(
    dataset: ReplayDataset,
    *,
    start_utc: datetime | None = None,
    end_utc: datetime | None = None,
    horizon_m5_bars: int = 48,
    minimum_bars: dict[Timeframe, int] | None = None,
    intelligence_config: IntelligenceConfig | None = None,
    decision_config: DecisionConfig | None = None,
    trade_plan_config: TradePlanConfig | None = None,
) -> ConfluenceBracketAblationReport:
    """Compare initial Trade Plan path evidence across confluence variants.

    ``resolved_bracket_net_r`` is not a claim about full production P/L. It covers
    only unambiguous initial stop/initial broker-target outcomes under the declared
    bar-high/low model. Ambiguous same-bar touches and horizon-unresolved cases stay
    outside resolved Net R and remain visible through coverage metrics.
    """

    runs = _run_variants(
        dataset,
        start_utc=start_utc,
        end_utc=end_utc,
        minimum_bars=minimum_bars,
        intelligence_config=intelligence_config,
        decision_config=decision_config,
    )
    decision_metrics = {
        variant: summarize_decision_replay(run) for variant, run in runs.items()
    }
    outcomes = {
        variant: summarize_enter_plan_outcomes(
            label_enter_plan_outcomes(
                dataset,
                run,
                horizon_m5_bars=horizon_m5_bars,
                minimum_bars=minimum_bars,
                intelligence_config=intelligence_config,
                trade_plan_config=trade_plan_config,
            )
        )
        for variant, run in runs.items()
    }
    base = outcomes[ConfluenceAblationVariant.BASE]

    return ConfluenceBracketAblationReport(
        rows=tuple(
            ConfluenceBracketAblationRow(
                variant=variant,
                decision_metrics=decision_metrics[variant],
                outcome_metrics=outcomes[variant],
                ready_plan_delta_vs_base=(
                    outcomes[variant].ready_plans - base.ready_plans
                ),
                resolved_coverage_delta_vs_base=(
                    outcomes[variant].resolved_coverage - base.resolved_coverage
                ),
                resolved_bracket_net_r_delta_vs_base=(
                    outcomes[variant].resolved_bracket_net_r
                    - base.resolved_bracket_net_r
                ),
                average_mfe_r_delta_vs_base=(
                    outcomes[variant].average_mfe_r - base.average_mfe_r
                ),
            )
            for variant in _VARIANTS
        )
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


def _run_variants(
    dataset: ReplayDataset,
    *,
    start_utc: datetime | None,
    end_utc: datetime | None,
    minimum_bars: dict[Timeframe, int] | None,
    intelligence_config: IntelligenceConfig | None,
    decision_config: DecisionConfig | None,
) -> dict[ConfluenceAblationVariant, ReplayRun]:
    base_config = decision_config or DecisionConfig()
    runs: dict[ConfluenceAblationVariant, ReplayRun] = {}
    for variant in _VARIANTS:
        config = replace(base_config, confluence=_confluence_config(variant))
        runs[variant] = run_decision_replay(
            dataset,
            start_utc=start_utc,
            end_utc=end_utc,
            minimum_bars=minimum_bars,
            intelligence_config=intelligence_config,
            decision_config=config,
        )
    _assert_same_chronology(tuple(runs.values()))
    return runs


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
