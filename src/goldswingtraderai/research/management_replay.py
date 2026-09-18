"""Chronological bar-close replay of the production Trade Manager.

The replay starts from a historical production Trade Plan, models the currently
active broker stop/TP against each later M5 bar, then (only if still open) feeds
the completed bar into the real Trade Manager. Verified-style manager state
changes are applied at bar close for the *next* bar.

This is an idealized research model: it does not simulate order latency, modify
rejection, slippage, PRE_CLOSE schedule data or tick-level intrabar ordering.
Same-bar stop+TP ambiguity therefore remains unresolved rather than guessed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from goldswingtraderai.decisions.timing import TimingAction
from goldswingtraderai.decisions.trade_plan import PlanState, TradePlanConfig
from goldswingtraderai.domain.enums import Direction, Timeframe, TradeManagerAction
from goldswingtraderai.domain.market import Candle
from goldswingtraderai.intelligence.snapshot import IntelligenceConfig, build_intelligence_snapshot
from goldswingtraderai.management.manager import TradeManagerConfig, evaluate_trade_manager
from goldswingtraderai.management.models import (
    ManagedTrade,
    apply_management_decision,
    managed_trade_from_fill,
)
from goldswingtraderai.research.outcomes import build_historical_trade_plan
from goldswingtraderai.research.replay import ReplayDataset, ReplayRun


_M5 = timedelta(minutes=5)


class ManagementReplayRealism(StrEnum):
    BAR_CLOSE_IDEALIZED = "BAR_CLOSE_IDEALIZED"


class ActiveBarrierTouch(StrEnum):
    NONE = "NONE"
    STOP = "STOP"
    TARGET = "TARGET"
    BOTH_AMBIGUOUS = "BOTH_AMBIGUOUS"


class ManagementOutcome(StrEnum):
    PLAN_NOT_READY = "PLAN_NOT_READY"
    STOP_FILLED = "STOP_FILLED"
    TARGET_FILLED = "TARGET_FILLED"
    MANAGER_EXIT = "MANAGER_EXIT"
    BOTH_TOUCHED_AMBIGUOUS = "BOTH_TOUCHED_AMBIGUOUS"
    HORIZON_OPEN = "HORIZON_OPEN"


@dataclass(frozen=True, slots=True)
class ActiveBarrierResult:
    touch: ActiveBarrierTouch
    realized_r: float | None


@dataclass(frozen=True, slots=True)
class ManagementReplayRecord:
    as_of_utc: datetime
    direction: Direction
    plan_state: PlanState
    plan_reason: str
    outcome: ManagementOutcome
    bars_observed: int
    realized_r: float | None
    mfe_r: float
    mae_r: float
    final_r: float
    action_history: tuple[TradeManagerAction, ...]
    final_stop: float | None
    final_tp: float | None
    exit_reason: str | None


@dataclass(frozen=True, slots=True)
class ManagementReplayMetrics:
    enter_signals: int
    managed_trades: int
    plan_not_ready: int
    stop_exits: int
    target_exits: int
    manager_exits: int
    ambiguous: int
    horizon_open: int
    resolved_coverage: float
    resolved_net_r: float
    resolved_average_r: float
    resolved_profit_factor: float | None
    resolved_max_drawdown_r: float
    average_mfe_r: float
    average_mae_r: float
    average_capture_efficiency: float
    average_profit_giveback_r: float
    hold_actions: int
    protect_actions: int
    trail_actions: int
    runner_actions: int
    exit_actions: int


def run_trade_manager_replay(
    dataset: ReplayDataset,
    run: ReplayRun,
    *,
    horizon_m5_bars: int = 96,
    minimum_bars: dict[Timeframe, int] | None = None,
    intelligence_config: IntelligenceConfig | None = None,
    trade_plan_config: TradePlanConfig | None = None,
    manager_config: TradeManagerConfig | None = None,
) -> tuple[ManagementReplayRecord, ...]:
    """Replay production management for every analytical ENTER in ``run``."""

    if horizon_m5_bars <= 0:
        raise ValueError("management replay horizon must contain at least one M5 bar")

    records: list[ManagementReplayRecord] = []
    ticket = 1
    for replay_decision in run.decisions:
        timing = replay_decision.decision.timing
        if timing is None or timing.action not in {
            TimingAction.ENTER_BUY,
            TimingAction.ENTER_SELL,
        }:
            continue

        plan = build_historical_trade_plan(
            dataset,
            replay_decision,
            minimum_bars=minimum_bars,
            intelligence_config=intelligence_config,
            trade_plan_config=trade_plan_config,
        )
        if not plan.entry_ready:
            records.append(
                ManagementReplayRecord(
                    as_of_utc=replay_decision.as_of_utc,
                    direction=plan.direction,
                    plan_state=plan.state,
                    plan_reason=plan.reason,
                    outcome=ManagementOutcome.PLAN_NOT_READY,
                    bars_observed=0,
                    realized_r=None,
                    mfe_r=0.0,
                    mae_r=0.0,
                    final_r=0.0,
                    action_history=(),
                    final_stop=plan.initial_stop,
                    final_tp=None,
                    exit_reason=plan.reason,
                )
            )
            continue

        trade = managed_trade_from_fill(
            plan,
            position_ticket=ticket,
            volume=dataset.symbol_spec.volume_min,
            fill_price=plan.approved_entry_reference,
            opened_at_utc=replay_decision.as_of_utc,
            symbol=dataset.symbol_spec.symbol,
        )
        ticket += 1
        records.append(
            _replay_one_trade(
                dataset,
                replay_decision.as_of_utc,
                trade,
                plan.state,
                plan.reason,
                horizon_m5_bars=horizon_m5_bars,
                minimum_bars=minimum_bars,
                intelligence_config=intelligence_config,
                manager_config=manager_config,
            )
        )

    return tuple(records)


def evaluate_active_barriers(
    trade: ManagedTrade,
    candle: Candle,
) -> ActiveBarrierResult:
    """Evaluate stop/active broker TP without inventing same-bar ordering."""

    stop_hit = _stop_touched(trade.direction, trade.current_stop, candle)
    target_hit = (
        trade.broker_tp is not None
        and _target_touched(trade.direction, trade.broker_tp, candle)
    )
    if stop_hit and target_hit:
        return ActiveBarrierResult(ActiveBarrierTouch.BOTH_AMBIGUOUS, None)
    if stop_hit:
        return ActiveBarrierResult(
            ActiveBarrierTouch.STOP,
            _signed_r(
                trade.direction,
                trade.entry_price,
                trade.original_r_price,
                trade.current_stop,
            ),
        )
    if target_hit:
        assert trade.broker_tp is not None
        return ActiveBarrierResult(
            ActiveBarrierTouch.TARGET,
            _signed_r(
                trade.direction,
                trade.entry_price,
                trade.original_r_price,
                trade.broker_tp,
            ),
        )
    return ActiveBarrierResult(ActiveBarrierTouch.NONE, None)


def summarize_management_replay(
    records: tuple[ManagementReplayRecord, ...],
) -> ManagementReplayMetrics:
    """Summarize manager replay while keeping unresolved trades out of Net R."""

    managed = tuple(
        record for record in records if record.outcome is not ManagementOutcome.PLAN_NOT_READY
    )
    resolved_values = tuple(
        record.realized_r for record in managed if record.realized_r is not None
    )
    gross_profit = sum(value for value in resolved_values if value > 0)
    gross_loss = -sum(value for value in resolved_values if value < 0)
    action_history = tuple(action for record in managed for action in record.action_history)
    capture = tuple(_capture_efficiency(record) for record in managed)
    giveback = tuple(
        max(0.0, record.mfe_r - record.realized_r)
        for record in managed
        if record.realized_r is not None
    )

    return ManagementReplayMetrics(
        enter_signals=len(records),
        managed_trades=len(managed),
        plan_not_ready=sum(
            record.outcome is ManagementOutcome.PLAN_NOT_READY for record in records
        ),
        stop_exits=sum(record.outcome is ManagementOutcome.STOP_FILLED for record in managed),
        target_exits=sum(
            record.outcome is ManagementOutcome.TARGET_FILLED for record in managed
        ),
        manager_exits=sum(
            record.outcome is ManagementOutcome.MANAGER_EXIT for record in managed
        ),
        ambiguous=sum(
            record.outcome is ManagementOutcome.BOTH_TOUCHED_AMBIGUOUS
            for record in managed
        ),
        horizon_open=sum(
            record.outcome is ManagementOutcome.HORIZON_OPEN for record in managed
        ),
        resolved_coverage=(len(resolved_values) / len(managed) if managed else 0.0),
        resolved_net_r=sum(resolved_values),
        resolved_average_r=_average(resolved_values),
        resolved_profit_factor=(
            gross_profit / gross_loss if gross_loss > 0 else None
        ),
        resolved_max_drawdown_r=_max_drawdown(resolved_values),
        average_mfe_r=_average(tuple(record.mfe_r for record in managed)),
        average_mae_r=_average(tuple(record.mae_r for record in managed)),
        average_capture_efficiency=_average(capture),
        average_profit_giveback_r=_average(giveback),
        hold_actions=sum(action is TradeManagerAction.HOLD for action in action_history),
        protect_actions=sum(action is TradeManagerAction.PROTECT for action in action_history),
        trail_actions=sum(action is TradeManagerAction.TRAIL for action in action_history),
        runner_actions=sum(action is TradeManagerAction.RUNNER for action in action_history),
        exit_actions=sum(action is TradeManagerAction.EXIT for action in action_history),
    )


def _replay_one_trade(
    dataset: ReplayDataset,
    as_of_utc: datetime,
    trade: ManagedTrade,
    plan_state: PlanState,
    plan_reason: str,
    *,
    horizon_m5_bars: int,
    minimum_bars: dict[Timeframe, int] | None,
    intelligence_config: IntelligenceConfig | None,
    manager_config: TradeManagerConfig | None,
) -> ManagementReplayRecord:
    future = _future_m5_bars(dataset, as_of_utc, horizon_m5_bars)
    mfe_r = 0.0
    mae_r = 0.0
    actions: list[TradeManagerAction] = []
    final_r = 0.0

    for index, candle in enumerate(future, start=1):
        favorable, adverse = _excursions_r(trade, candle)
        mfe_r = max(mfe_r, favorable)
        mae_r = max(mae_r, adverse)
        barrier = evaluate_active_barriers(trade, candle)
        final_r = _signed_r(
            trade.direction,
            trade.entry_price,
            trade.original_r_price,
            candle.close,
        )

        if barrier.touch is ActiveBarrierTouch.BOTH_AMBIGUOUS:
            return _record(
                as_of_utc,
                trade,
                plan_state,
                plan_reason,
                ManagementOutcome.BOTH_TOUCHED_AMBIGUOUS,
                index,
                None,
                mfe_r,
                mae_r,
                final_r,
                tuple(actions),
                "ACTIVE_STOP_AND_TP_TOUCHED_SAME_M5",
            )
        if barrier.touch is ActiveBarrierTouch.STOP:
            return _record(
                as_of_utc,
                trade,
                plan_state,
                plan_reason,
                ManagementOutcome.STOP_FILLED,
                index,
                barrier.realized_r,
                mfe_r,
                mae_r,
                final_r,
                tuple(actions),
                "ACTIVE_STOP_TOUCHED",
            )
        if barrier.touch is ActiveBarrierTouch.TARGET:
            return _record(
                as_of_utc,
                trade,
                plan_state,
                plan_reason,
                ManagementOutcome.TARGET_FILLED,
                index,
                barrier.realized_r,
                mfe_r,
                mae_r,
                final_r,
                tuple(actions),
                "ACTIVE_BROKER_TP_TOUCHED",
            )

        event_time = candle.time_utc + _M5
        market = dataset.snapshot_at(event_time, minimum_bars=minimum_bars)
        if market is None:
            break
        intelligence = build_intelligence_snapshot(market, config=intelligence_config)
        decision = evaluate_trade_manager(
            trade,
            market,
            intelligence,
            pre_close_flatten=False,
            config=manager_config,
        )
        actions.append(decision.action)

        if decision.action is TradeManagerAction.EXIT:
            return _record(
                as_of_utc,
                trade,
                plan_state,
                plan_reason,
                ManagementOutcome.MANAGER_EXIT,
                index,
                decision.current_r,
                mfe_r,
                mae_r,
                decision.current_r,
                tuple(actions),
                decision.reason,
            )
        if decision.requires_broker_write:
            # Research assumes the manager's requested modify is accepted at this
            # completed-bar boundary. Live broker rejection/latency belongs to a
            # separate execution-stress/DEMO evidence layer.
            trade = apply_management_decision(trade, decision, event_time)

    return _record(
        as_of_utc,
        trade,
        plan_state,
        plan_reason,
        ManagementOutcome.HORIZON_OPEN,
        len(future),
        None,
        mfe_r,
        mae_r,
        final_r,
        tuple(actions),
        "MANAGEMENT_HORIZON_ENDED_OPEN",
    )


def _future_m5_bars(
    dataset: ReplayDataset,
    as_of_utc: datetime,
    horizon: int,
) -> tuple[Candle, ...]:
    m5 = next(item for item in dataset.series if item.timeframe is Timeframe.M5)
    return tuple(candle for candle in m5.candles if candle.time_utc >= as_of_utc)[:horizon]


def _excursions_r(trade: ManagedTrade, candle: Candle) -> tuple[float, float]:
    if trade.direction is Direction.BUY:
        favorable = max(0.0, candle.high - trade.entry_price) / trade.original_r_price
        adverse = max(0.0, trade.entry_price - candle.low) / trade.original_r_price
    else:
        favorable = max(0.0, trade.entry_price - candle.low) / trade.original_r_price
        adverse = max(0.0, candle.high - trade.entry_price) / trade.original_r_price
    return favorable, adverse


def _stop_touched(direction: Direction, stop: float, candle: Candle) -> bool:
    return candle.low <= stop if direction is Direction.BUY else candle.high >= stop


def _target_touched(direction: Direction, target: float, candle: Candle) -> bool:
    return candle.high >= target if direction is Direction.BUY else candle.low <= target


def _signed_r(direction: Direction, entry: float, risk: float, price: float) -> float:
    return (price - entry) / risk if direction is Direction.BUY else (entry - price) / risk


def _record(
    as_of_utc: datetime,
    trade: ManagedTrade,
    plan_state: PlanState,
    plan_reason: str,
    outcome: ManagementOutcome,
    bars_observed: int,
    realized_r: float | None,
    mfe_r: float,
    mae_r: float,
    final_r: float,
    actions: tuple[TradeManagerAction, ...],
    exit_reason: str,
) -> ManagementReplayRecord:
    return ManagementReplayRecord(
        as_of_utc=as_of_utc,
        direction=trade.direction,
        plan_state=plan_state,
        plan_reason=plan_reason,
        outcome=outcome,
        bars_observed=bars_observed,
        realized_r=realized_r,
        mfe_r=mfe_r,
        mae_r=mae_r,
        final_r=final_r,
        action_history=actions,
        final_stop=trade.current_stop,
        final_tp=trade.broker_tp,
        exit_reason=exit_reason,
    )


def _capture_efficiency(record: ManagementReplayRecord) -> float:
    if record.realized_r is None or record.realized_r <= 0 or record.mfe_r <= 0:
        return 0.0
    return min(1.0, record.realized_r / record.mfe_r)


def _average(values: tuple[float, ...]) -> float:
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
