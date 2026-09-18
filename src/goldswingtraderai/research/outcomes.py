"""Post-hoc Trade Plan outcome labeling for chronological research.

Outcome labels may inspect candles that occur *after* a historical decision, but
those future candles never feed back into the original decision. The bar-high/low
model is explicit about same-bar stop/target ambiguity and does not pretend to be
tick-perfect execution or full Trade Manager replay.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from goldswingtraderai.decisions.timing import TimingAction
from goldswingtraderai.decisions.trade_plan import (
    PlanState,
    TradePlan,
    TradePlanConfig,
    build_trade_plan,
)
from goldswingtraderai.domain.enums import Direction, OpportunityStage, Timeframe
from goldswingtraderai.domain.market import Candle
from goldswingtraderai.intelligence.snapshot import IntelligenceConfig, build_intelligence_snapshot
from goldswingtraderai.research.replay import ReplayDataset, ReplayRun


class OutcomeRealism(StrEnum):
    BAR_HIGH_LOW = "BAR_HIGH_LOW"


class BarrierOutcome(StrEnum):
    TARGET_FIRST = "TARGET_FIRST"
    STOP_FIRST = "STOP_FIRST"
    BOTH_TOUCHED_AMBIGUOUS = "BOTH_TOUCHED_AMBIGUOUS"
    HORIZON_UNRESOLVED = "HORIZON_UNRESOLVED"


@dataclass(frozen=True, slots=True)
class PlanPathOutcome:
    outcome: BarrierOutcome
    bars_observed: int
    mfe_r: float
    mae_r: float
    end_r: float
    realized_r: float | None
    reached_2r: bool
    reached_3r: bool
    reached_4r: bool


@dataclass(frozen=True, slots=True)
class EnterPlanOutcomeRecord:
    as_of_utc: datetime
    direction: Direction
    plan_state: PlanState
    plan_reason: str
    target_rr: float | None
    path: PlanPathOutcome | None


@dataclass(frozen=True, slots=True)
class EnterPlanOutcomeMetrics:
    enter_signals: int
    ready_plans: int
    non_ready_plans: int
    target_first: int
    stop_first: int
    ambiguous: int
    unresolved: int
    resolved_coverage: float
    resolved_target_rate: float | None
    resolved_bracket_net_r: float
    resolved_bracket_average_r: float
    resolved_bracket_profit_factor: float | None
    resolved_bracket_max_drawdown_r: float
    average_mfe_r: float
    average_mae_r: float
    reach_2r_rate: float
    reach_3r_rate: float
    reach_4r_rate: float


def label_enter_plan_outcomes(
    dataset: ReplayDataset,
    run: ReplayRun,
    *,
    horizon_m5_bars: int = 48,
    minimum_bars: dict[Timeframe, int] | None = None,
    intelligence_config: IntelligenceConfig | None = None,
    trade_plan_config: TradePlanConfig | None = None,
) -> tuple[EnterPlanOutcomeRecord, ...]:
    """Label analytical ENTER events using the production structural Trade Plan.

    The current research layer stops at initial stop/initial broker target path
    evidence. It intentionally does not claim Trade Manager, slippage or broker-fill
    parity. A same-M5 stop+target touch is marked ambiguous instead of choosing the
    favorable ordering.
    """

    if horizon_m5_bars <= 0:
        raise ValueError("outcome horizon must contain at least one M5 bar")

    records: list[EnterPlanOutcomeRecord] = []
    for item in run.decisions:
        timing = item.decision.timing
        if timing is None or timing.action not in {
            TimingAction.ENTER_BUY,
            TimingAction.ENTER_SELL,
        }:
            continue

        opportunity = item.decision.opportunity
        if opportunity is None or opportunity.stage is not OpportunityStage.READY:
            raise ValueError("ENTER replay decision must retain a READY opportunity")

        market = dataset.snapshot_at(item.as_of_utc, minimum_bars=minimum_bars)
        if market is None:
            raise ValueError("replay outcome cannot rebuild the original market snapshot")
        intelligence = build_intelligence_snapshot(market, config=intelligence_config)
        plan = build_trade_plan(
            opportunity,
            intelligence,
            market,
            item.as_of_utc,
            config=trade_plan_config,
        )

        if not plan.entry_ready:
            records.append(
                EnterPlanOutcomeRecord(
                    as_of_utc=item.as_of_utc,
                    direction=plan.direction,
                    plan_state=plan.state,
                    plan_reason=plan.reason,
                    target_rr=None,
                    path=None,
                )
            )
            continue

        target = plan.broker_tp_target
        if target is None:
            raise ValueError("READY Trade Plan must have a broker target")
        future = _future_m5_bars(dataset, item.as_of_utc, horizon_m5_bars)
        path = evaluate_plan_path(plan, future)
        records.append(
            EnterPlanOutcomeRecord(
                as_of_utc=item.as_of_utc,
                direction=plan.direction,
                plan_state=plan.state,
                plan_reason=plan.reason,
                target_rr=target.rr,
                path=path,
            )
        )

    return tuple(records)


def evaluate_plan_path(
    plan: TradePlan,
    future_bars: tuple[Candle, ...],
) -> PlanPathOutcome:
    """Evaluate initial stop/TP chronology without guessing intrabar order."""

    if not plan.entry_ready:
        raise ValueError("path evaluation requires a READY Trade Plan")
    if plan.initial_stop is None or plan.original_r_price is None:
        raise ValueError("READY Trade Plan requires stop/original-R geometry")
    target = plan.broker_tp_target
    if target is None:
        raise ValueError("READY Trade Plan requires broker target")
    if not future_bars:
        return PlanPathOutcome(
            outcome=BarrierOutcome.HORIZON_UNRESOLVED,
            bars_observed=0,
            mfe_r=0.0,
            mae_r=0.0,
            end_r=0.0,
            realized_r=None,
            reached_2r=False,
            reached_3r=False,
            reached_4r=False,
        )

    entry = plan.approved_entry_reference
    stop = plan.initial_stop
    risk = plan.original_r_price
    mfe_r = 0.0
    mae_r = 0.0

    for index, candle in enumerate(future_bars, start=1):
        favorable, adverse = _excursions_r(plan.direction, entry, risk, candle)
        mfe_r = max(mfe_r, favorable)
        mae_r = max(mae_r, adverse)
        stop_hit = _stop_touched(plan.direction, stop, candle)
        target_hit = _target_touched(plan.direction, target.price, candle)
        end_r = _signed_r(plan.direction, entry, risk, candle.close)

        if stop_hit and target_hit:
            return _path_result(
                BarrierOutcome.BOTH_TOUCHED_AMBIGUOUS,
                index,
                mfe_r,
                mae_r,
                end_r,
                None,
            )
        if stop_hit:
            return _path_result(
                BarrierOutcome.STOP_FIRST,
                index,
                mfe_r,
                mae_r,
                end_r,
                -1.0,
            )
        if target_hit:
            return _path_result(
                BarrierOutcome.TARGET_FIRST,
                index,
                mfe_r,
                mae_r,
                end_r,
                target.rr,
            )

    return _path_result(
        BarrierOutcome.HORIZON_UNRESOLVED,
        len(future_bars),
        mfe_r,
        mae_r,
        _signed_r(plan.direction, entry, risk, future_bars[-1].close),
        None,
    )


def summarize_enter_plan_outcomes(
    records: tuple[EnterPlanOutcomeRecord, ...],
) -> EnterPlanOutcomeMetrics:
    """Summarize explicit initial-bracket evidence without hiding uncertainty."""

    paths = tuple(record.path for record in records if record.path is not None)
    target_first = sum(path.outcome is BarrierOutcome.TARGET_FIRST for path in paths)
    stop_first = sum(path.outcome is BarrierOutcome.STOP_FIRST for path in paths)
    ambiguous = sum(
        path.outcome is BarrierOutcome.BOTH_TOUCHED_AMBIGUOUS for path in paths
    )
    unresolved = sum(path.outcome is BarrierOutcome.HORIZON_UNRESOLVED for path in paths)
    resolved_values = tuple(
        path.realized_r for path in paths if path.realized_r is not None
    )
    resolved = len(resolved_values)
    gross_profit = sum(value for value in resolved_values if value > 0)
    gross_loss = -sum(value for value in resolved_values if value < 0)

    return EnterPlanOutcomeMetrics(
        enter_signals=len(records),
        ready_plans=len(paths),
        non_ready_plans=len(records) - len(paths),
        target_first=target_first,
        stop_first=stop_first,
        ambiguous=ambiguous,
        unresolved=unresolved,
        resolved_coverage=(resolved / len(paths) if paths else 0.0),
        resolved_target_rate=(target_first / resolved if resolved else None),
        resolved_bracket_net_r=sum(resolved_values),
        resolved_bracket_average_r=_average(resolved_values),
        resolved_bracket_profit_factor=(
            gross_profit / gross_loss if gross_loss > 0 else None
        ),
        resolved_bracket_max_drawdown_r=_max_drawdown(resolved_values),
        average_mfe_r=_average(tuple(path.mfe_r for path in paths)),
        average_mae_r=_average(tuple(path.mae_r for path in paths)),
        reach_2r_rate=_rate(tuple(path.reached_2r for path in paths)),
        reach_3r_rate=_rate(tuple(path.reached_3r for path in paths)),
        reach_4r_rate=_rate(tuple(path.reached_4r for path in paths)),
    )


def _future_m5_bars(
    dataset: ReplayDataset,
    as_of_utc: datetime,
    horizon: int,
) -> tuple[Candle, ...]:
    m5 = next(item for item in dataset.series if item.timeframe is Timeframe.M5)
    return tuple(candle for candle in m5.candles if candle.time_utc >= as_of_utc)[:horizon]


def _excursions_r(
    direction: Direction,
    entry: float,
    risk: float,
    candle: Candle,
) -> tuple[float, float]:
    if direction is Direction.BUY:
        favorable = max(0.0, candle.high - entry) / risk
        adverse = max(0.0, entry - candle.low) / risk
    elif direction is Direction.SELL:
        favorable = max(0.0, entry - candle.low) / risk
        adverse = max(0.0, candle.high - entry) / risk
    else:
        raise ValueError("Trade Plan direction must be BUY or SELL")
    return favorable, adverse


def _stop_touched(direction: Direction, stop: float, candle: Candle) -> bool:
    if direction is Direction.BUY:
        return candle.low <= stop
    if direction is Direction.SELL:
        return candle.high >= stop
    raise ValueError("Trade Plan direction must be BUY or SELL")


def _target_touched(direction: Direction, target: float, candle: Candle) -> bool:
    if direction is Direction.BUY:
        return candle.high >= target
    if direction is Direction.SELL:
        return candle.low <= target
    raise ValueError("Trade Plan direction must be BUY or SELL")


def _signed_r(direction: Direction, entry: float, risk: float, price: float) -> float:
    if direction is Direction.BUY:
        return (price - entry) / risk
    if direction is Direction.SELL:
        return (entry - price) / risk
    raise ValueError("Trade Plan direction must be BUY or SELL")


def _path_result(
    outcome: BarrierOutcome,
    bars_observed: int,
    mfe_r: float,
    mae_r: float,
    end_r: float,
    realized_r: float | None,
) -> PlanPathOutcome:
    return PlanPathOutcome(
        outcome=outcome,
        bars_observed=bars_observed,
        mfe_r=mfe_r,
        mae_r=mae_r,
        end_r=end_r,
        realized_r=realized_r,
        reached_2r=mfe_r >= 2.0,
        reached_3r=mfe_r >= 3.0,
        reached_4r=mfe_r >= 4.0,
    )


def _average(values: tuple[float, ...]) -> float:
    return sum(values) / len(values) if values else 0.0


def _rate(values: tuple[bool, ...]) -> float:
    return sum(values) / len(values) if values else 0.0


def _max_drawdown(values: tuple[float, ...]) -> float:
    equity = 0.0
    peak = 0.0
    maximum = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        maximum = max(maximum, peak - equity)
    return maximum
