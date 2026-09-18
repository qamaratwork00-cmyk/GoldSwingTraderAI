"""Deterministic execution-friction stress around chronological management replay.

This module does not create a second trading strategy. It freezes the analytical
ReplayRun and rebuilds the production Trade Plan/Trade Manager under explicitly
declared execution assumptions. The goal is to measure fragility to plausible
friction without pretending those assumptions are historical broker truth.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from goldswingtraderai.decisions.trade_plan import TradePlanConfig
from goldswingtraderai.domain.enums import Timeframe
from goldswingtraderai.intelligence.snapshot import IntelligenceConfig
from goldswingtraderai.management.manager import TradeManagerConfig
from goldswingtraderai.research.management_replay import (
    ManagementReplayAssumptions,
    ManagementReplayMetrics,
    run_trade_manager_replay,
    summarize_management_replay,
)
from goldswingtraderai.research.replay import ReplayDataset, ReplayRun


class ExecutionStressVariant(StrEnum):
    BASE = "BASE"
    WIDER_SPREAD = "WIDER_SPREAD"
    ADVERSE_ENTRY = "ADVERSE_ENTRY"
    MODIFY_DELAY = "MODIFY_DELAY"
    MODIFY_REJECTION = "MODIFY_REJECTION"
    COMBINED = "COMBINED"


@dataclass(frozen=True, slots=True)
class ExecutionStressScenario:
    variant: ExecutionStressVariant
    spread_multiplier: float = 1.0
    adverse_entry_slippage_r: float = 0.0
    modify_delay_bars: int = 0
    reject_every_nth_modify: int | None = None

    def __post_init__(self) -> None:
        if self.spread_multiplier <= 0:
            raise ValueError("stress spread multiplier must be positive")
        if not 0.0 <= self.adverse_entry_slippage_r < 1.0:
            raise ValueError("stress entry slippage must be in [0, 1) original R")
        if self.modify_delay_bars < 0:
            raise ValueError("stress modify delay cannot be negative")
        if self.reject_every_nth_modify is not None and self.reject_every_nth_modify <= 0:
            raise ValueError("stress modify rejection cadence must be positive")


@dataclass(frozen=True, slots=True)
class ExecutionStressRow:
    scenario: ExecutionStressScenario
    stressed_spread_price: float
    metrics: ManagementReplayMetrics
    managed_trade_delta_vs_base: int
    plan_not_ready_delta_vs_base: int
    resolved_coverage_delta_vs_base: float
    resolved_net_r_delta_vs_base: float
    resolved_average_r_delta_vs_base: float
    resolved_max_drawdown_r_delta_vs_base: float
    average_capture_efficiency_delta_vs_base: float
    average_profit_giveback_r_delta_vs_base: float


@dataclass(frozen=True, slots=True)
class ExecutionStressReport:
    rows: tuple[ExecutionStressRow, ...]

    def row(self, variant: ExecutionStressVariant) -> ExecutionStressRow:
        for item in self.rows:
            if item.scenario.variant is variant:
                return item
        raise KeyError(variant)


_DEFAULT_SCENARIOS = (
    ExecutionStressScenario(ExecutionStressVariant.BASE),
    ExecutionStressScenario(
        ExecutionStressVariant.WIDER_SPREAD,
        spread_multiplier=1.50,
    ),
    ExecutionStressScenario(
        ExecutionStressVariant.ADVERSE_ENTRY,
        adverse_entry_slippage_r=0.10,
    ),
    ExecutionStressScenario(
        ExecutionStressVariant.MODIFY_DELAY,
        modify_delay_bars=1,
    ),
    ExecutionStressScenario(
        ExecutionStressVariant.MODIFY_REJECTION,
        reject_every_nth_modify=2,
    ),
    ExecutionStressScenario(
        ExecutionStressVariant.COMBINED,
        spread_multiplier=1.50,
        adverse_entry_slippage_r=0.10,
        modify_delay_bars=1,
        reject_every_nth_modify=2,
    ),
)


def default_execution_stress_scenarios() -> tuple[ExecutionStressScenario, ...]:
    """Return transparent V1 research baselines; callers may supply alternatives.

    These values are deliberately modest deterministic probes, not frozen broker
    assumptions and not production risk thresholds. Calibration belongs to
    chronological historical/DEMO evidence.
    """

    return _DEFAULT_SCENARIOS


def run_execution_stress(
    dataset: ReplayDataset,
    run: ReplayRun,
    *,
    scenarios: tuple[ExecutionStressScenario, ...] | None = None,
    horizon_m5_bars: int = 96,
    minimum_bars: dict[Timeframe, int] | None = None,
    intelligence_config: IntelligenceConfig | None = None,
    trade_plan_config: TradePlanConfig | None = None,
    manager_config: TradeManagerConfig | None = None,
) -> ExecutionStressReport:
    """Compare fixed analytical decisions under declared execution friction.

    The analytical ``ReplayRun`` is intentionally held constant so the report
    isolates Trade Plan / fill / exit-side spread / management-write sensitivity.
    This function does **not** claim full Execution Permission Gate, margin,
    order-book, variable intrabar spread, or tick-ordering parity.
    """

    selected = scenarios or _DEFAULT_SCENARIOS
    _validate_scenarios(selected)

    raw: list[tuple[ExecutionStressScenario, float, ManagementReplayMetrics]] = []
    for scenario in selected:
        stressed_spread = dataset.spread_price * scenario.spread_multiplier
        stressed_dataset = replace(dataset, spread_price=stressed_spread)
        assumptions = ManagementReplayAssumptions(
            adverse_entry_slippage_r=scenario.adverse_entry_slippage_r,
            barrier_spread_price=stressed_spread,
            modify_delay_bars=scenario.modify_delay_bars,
            reject_every_nth_modify=scenario.reject_every_nth_modify,
        )
        metrics = summarize_management_replay(
            run_trade_manager_replay(
                stressed_dataset,
                run,
                horizon_m5_bars=horizon_m5_bars,
                minimum_bars=minimum_bars,
                intelligence_config=intelligence_config,
                trade_plan_config=trade_plan_config,
                manager_config=manager_config,
                assumptions=assumptions,
            )
        )
        raw.append((scenario, stressed_spread, metrics))

    base = next(
        metrics
        for scenario, _spread, metrics in raw
        if scenario.variant is ExecutionStressVariant.BASE
    )
    return ExecutionStressReport(
        rows=tuple(
            ExecutionStressRow(
                scenario=scenario,
                stressed_spread_price=spread,
                metrics=metrics,
                managed_trade_delta_vs_base=metrics.managed_trades - base.managed_trades,
                plan_not_ready_delta_vs_base=metrics.plan_not_ready - base.plan_not_ready,
                resolved_coverage_delta_vs_base=(
                    metrics.resolved_coverage - base.resolved_coverage
                ),
                resolved_net_r_delta_vs_base=(
                    metrics.resolved_net_r - base.resolved_net_r
                ),
                resolved_average_r_delta_vs_base=(
                    metrics.resolved_average_r - base.resolved_average_r
                ),
                resolved_max_drawdown_r_delta_vs_base=(
                    metrics.resolved_max_drawdown_r - base.resolved_max_drawdown_r
                ),
                average_capture_efficiency_delta_vs_base=(
                    metrics.average_capture_efficiency - base.average_capture_efficiency
                ),
                average_profit_giveback_r_delta_vs_base=(
                    metrics.average_profit_giveback_r - base.average_profit_giveback_r
                ),
            )
            for scenario, spread, metrics in raw
        )
    )


def _validate_scenarios(scenarios: tuple[ExecutionStressScenario, ...]) -> None:
    if not scenarios:
        raise ValueError("execution stress requires at least one scenario")
    variants = tuple(item.variant for item in scenarios)
    if len(variants) != len(set(variants)):
        raise ValueError("execution stress scenarios cannot repeat a variant")
    if variants.count(ExecutionStressVariant.BASE) != 1:
        raise ValueError("execution stress requires exactly one BASE scenario")
    base = next(item for item in scenarios if item.variant is ExecutionStressVariant.BASE)
    if base != ExecutionStressScenario(ExecutionStressVariant.BASE):
        raise ValueError("BASE execution stress scenario must contain zero added friction")