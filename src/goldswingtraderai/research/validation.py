"""Chronological fixed-policy walk-forward validation.

This module partitions only historically eligible M5 decision events, carries the
production opportunity state through each development context, and scores only the
subsequent non-overlapping validation slice. It does not auto-tune parameters and
it does not consume the governed one-shot final holdout from ``promotion.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from goldswingtraderai.decisions.snapshot import DecisionConfig
from goldswingtraderai.decisions.trade_plan import TradePlanConfig
from goldswingtraderai.domain.enums import Timeframe
from goldswingtraderai.domain.market import CandleSeries
from goldswingtraderai.intelligence.snapshot import IntelligenceConfig
from goldswingtraderai.management.manager import TradeManagerConfig
from goldswingtraderai.research.ablation import (
    DecisionReplayMetrics,
    summarize_decision_replay,
)
from goldswingtraderai.research.management_replay import (
    ManagementReplayMetrics,
    run_trade_manager_replay,
    summarize_management_replay,
)
from goldswingtraderai.research.replay import (
    ReplayDataset,
    ReplayRun,
    run_decision_replay,
)
from goldswingtraderai.research.stress import (
    ExecutionStressReport,
    ExecutionStressScenario,
    run_execution_stress,
)


_PERIOD_SECONDS: dict[Timeframe, int] = {
    Timeframe.H4: 4 * 60 * 60,
    Timeframe.H1: 60 * 60,
    Timeframe.M15: 15 * 60,
    Timeframe.M5: 5 * 60,
    Timeframe.M1: 60,
}


class ValidationMode(StrEnum):
    FIXED_POLICY_WALK_FORWARD = "FIXED_POLICY_WALK_FORWARD"


@dataclass(frozen=True, slots=True)
class WalkForwardWindow:
    window_id: str
    development_start_utc: datetime
    development_end_utc: datetime
    validation_start_utc: datetime
    validation_end_utc: datetime
    development_events: int
    validation_events: int

    def __post_init__(self) -> None:
        for value in (
            self.development_start_utc,
            self.development_end_utc,
            self.validation_start_utc,
            self.validation_end_utc,
        ):
            _require_utc(value)
        if not (
            self.development_start_utc
            <= self.development_end_utc
            < self.validation_start_utc
            <= self.validation_end_utc
        ):
            raise ValueError("walk-forward window chronology is invalid")
        if self.development_events <= 0 or self.validation_events <= 0:
            raise ValueError("walk-forward windows require positive event counts")
        if not self.window_id.strip():
            raise ValueError("walk-forward window id cannot be empty")


@dataclass(frozen=True, slots=True)
class WalkForwardEvaluation:
    window: WalkForwardWindow
    decision_metrics: DecisionReplayMetrics
    management_metrics: ManagementReplayMetrics
    stress_report: ExecutionStressReport | None


@dataclass(frozen=True, slots=True)
class WalkForwardReport:
    mode: ValidationMode
    evaluations: tuple[WalkForwardEvaluation, ...]

    @property
    def validation_events(self) -> int:
        return sum(item.decision_metrics.events for item in self.evaluations)

    @property
    def enter_signals(self) -> int:
        return sum(item.management_metrics.enter_signals for item in self.evaluations)

    @property
    def resolved_management_net_r(self) -> float:
        return sum(item.management_metrics.resolved_net_r for item in self.evaluations)


def build_walk_forward_windows(
    dataset: ReplayDataset,
    *,
    development_events: int,
    validation_events: int,
    step_events: int | None = None,
    minimum_bars: dict[Timeframe, int] | None = None,
    start_utc: datetime | None = None,
    end_utc: datetime | None = None,
    max_windows: int | None = None,
) -> tuple[WalkForwardWindow, ...]:
    """Build non-overlapping validation windows from historically eligible events.

    Development slices may overlap. Validation slices may not. ``step_events``
    therefore defaults to ``validation_events`` and cannot be smaller than it.
    """

    if development_events <= 0 or validation_events <= 0:
        raise ValueError("walk-forward development/validation counts must be positive")
    step = validation_events if step_events is None else step_events
    if step < validation_events:
        raise ValueError("walk-forward validation slices may not overlap")
    if max_windows is not None and max_windows <= 0:
        raise ValueError("max_windows must be positive when configured")
    if start_utc is not None:
        _require_utc(start_utc)
    if end_utc is not None:
        _require_utc(end_utc)
    if start_utc is not None and end_utc is not None and end_utc < start_utc:
        raise ValueError("walk-forward end cannot precede start")

    events = _eligible_events(
        dataset,
        minimum_bars=minimum_bars,
        start_utc=start_utc,
        end_utc=end_utc,
    )
    needed = development_events + validation_events
    windows: list[WalkForwardWindow] = []
    start_index = 0
    while start_index + needed <= len(events):
        development = events[start_index : start_index + development_events]
        validation = events[
            start_index + development_events : start_index + needed
        ]
        windows.append(
            WalkForwardWindow(
                window_id=f"WF_{len(windows) + 1:04d}",
                development_start_utc=development[0],
                development_end_utc=development[-1],
                validation_start_utc=validation[0],
                validation_end_utc=validation[-1],
                development_events=len(development),
                validation_events=len(validation),
            )
        )
        if max_windows is not None and len(windows) >= max_windows:
            break
        start_index += step
    return tuple(windows)


def run_walk_forward_validation(
    dataset: ReplayDataset,
    windows: tuple[WalkForwardWindow, ...],
    *,
    minimum_bars: dict[Timeframe, int] | None = None,
    intelligence_config: IntelligenceConfig | None = None,
    decision_config: DecisionConfig | None = None,
    trade_plan_config: TradePlanConfig | None = None,
    manager_config: TradeManagerConfig | None = None,
    horizon_m5_bars: int = 96,
    include_stress: bool = True,
    stress_scenarios: tuple[ExecutionStressScenario, ...] | None = None,
) -> WalkForwardReport:
    """Evaluate fixed production semantics on each independent validation slice.

    Development history is used only to reconstruct chronological opportunity
    state before validation starts. This function performs no parameter search,
    candidate selection, or final-holdout consumption.
    """

    if not windows:
        raise ValueError("walk-forward validation requires at least one window")
    _assert_validation_non_overlap(windows)
    if horizon_m5_bars <= 0:
        raise ValueError("walk-forward management horizon must be positive")

    evaluations: list[WalkForwardEvaluation] = []
    for window in windows:
        truncated = _truncate_dataset(dataset, window.validation_end_utc)
        contextual_run = run_decision_replay(
            truncated,
            start_utc=window.development_start_utc,
            end_utc=window.validation_end_utc,
            minimum_bars=minimum_bars,
            intelligence_config=intelligence_config,
            decision_config=decision_config,
        )
        validation_run = _validation_slice(contextual_run, window)
        management_records = run_trade_manager_replay(
            truncated,
            validation_run,
            horizon_m5_bars=horizon_m5_bars,
            minimum_bars=minimum_bars,
            intelligence_config=intelligence_config,
            trade_plan_config=trade_plan_config,
            manager_config=manager_config,
        )
        stress_report = (
            run_execution_stress(
                truncated,
                validation_run,
                scenarios=stress_scenarios,
                horizon_m5_bars=horizon_m5_bars,
                minimum_bars=minimum_bars,
                intelligence_config=intelligence_config,
                trade_plan_config=trade_plan_config,
                manager_config=manager_config,
            )
            if include_stress
            else None
        )
        evaluations.append(
            WalkForwardEvaluation(
                window=window,
                decision_metrics=summarize_decision_replay(validation_run),
                management_metrics=summarize_management_replay(management_records),
                stress_report=stress_report,
            )
        )

    return WalkForwardReport(
        mode=ValidationMode.FIXED_POLICY_WALK_FORWARD,
        evaluations=tuple(evaluations),
    )


def _eligible_events(
    dataset: ReplayDataset,
    *,
    minimum_bars: dict[Timeframe, int] | None,
    start_utc: datetime | None,
    end_utc: datetime | None,
) -> tuple[datetime, ...]:
    output: list[datetime] = []
    for event_time in dataset.event_times():
        if start_utc is not None and event_time < start_utc:
            continue
        if end_utc is not None and event_time > end_utc:
            break
        if dataset.snapshot_at(event_time, minimum_bars=minimum_bars) is not None:
            output.append(event_time)
    return tuple(output)


def _validation_slice(run: ReplayRun, window: WalkForwardWindow) -> ReplayRun:
    decisions = tuple(
        item
        for item in run.decisions
        if window.validation_start_utc <= item.as_of_utc <= window.validation_end_utc
    )
    return ReplayRun(
        realism=run.realism,
        decisions=decisions,
        first_event_utc=decisions[0].as_of_utc if decisions else None,
        last_event_utc=decisions[-1].as_of_utc if decisions else None,
    )


def _truncate_dataset(dataset: ReplayDataset, end_utc: datetime) -> ReplayDataset:
    _require_utc(end_utc)
    series: list[CandleSeries] = []
    for item in dataset.series:
        period = timedelta(seconds=_PERIOD_SECONDS[item.timeframe])
        candles = tuple(
            candle for candle in item.candles if candle.time_utc + period <= end_utc
        )
        if not candles:
            raise ValueError("walk-forward truncation removed an entire timeframe")
        series.append(CandleSeries(timeframe=item.timeframe, candles=candles))
    return replace(dataset, series=tuple(series))


def _assert_validation_non_overlap(windows: tuple[WalkForwardWindow, ...]) -> None:
    ordered = tuple(sorted(windows, key=lambda item: item.validation_start_utc))
    for previous, current in zip(ordered, ordered[1:]):
        if current.validation_start_utc <= previous.validation_end_utc:
            raise ValueError("walk-forward validation windows must not overlap")


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("validation timestamp must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("validation timestamp must be UTC")
