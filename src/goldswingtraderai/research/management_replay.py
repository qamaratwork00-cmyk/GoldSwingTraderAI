"""Chronological bar-close replay of the production Trade Manager.

The replay starts from a historical production Trade Plan, models the currently
active broker stop/TP against each later M5 bar, then (only if still open) feeds
the completed bar into the real Trade Manager. Manager state changes are applied
only after the research execution model says the corresponding modify is verified.

The default assumptions preserve the earlier idealized model. Research may opt in
to explicit adverse entry slippage, executable-side spread, modify latency and a
deterministic modify-rejection pattern. These are declared stress assumptions,
not claims of tick-perfect broker parity. Same-bar stop+TP ambiguity therefore
remains unresolved rather than guessed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from goldswingtraderai.decisions.timing import TimingAction
from goldswingtraderai.decisions.trade_plan import PlanState, TradePlan, TradePlanConfig
from goldswingtraderai.domain.enums import Direction, Timeframe, TradeManagerAction
from goldswingtraderai.domain.market import Candle
from goldswingtraderai.intelligence.snapshot import IntelligenceConfig, build_intelligence_snapshot
from goldswingtraderai.management.manager import TradeManagerConfig, evaluate_trade_manager
from goldswingtraderai.management.models import (
    ManagedTrade,
    TradeManagementDecision,
    apply_management_decision,
    managed_trade_from_fill,
)
from goldswingtraderai.research.outcomes import build_historical_trade_plan
from goldswingtraderai.research.replay import ReplayDataset, ReplayRun


_M5 = timedelta(minutes=5)


class ManagementReplayRealism(StrEnum):
    BAR_CLOSE_IDEALIZED = "BAR_CLOSE_IDEALIZED"
    BAR_CLOSE_EXECUTION_STRESS = "BAR_CLOSE_EXECUTION_STRESS"


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
class ManagementReplayAssumptions:
    """Explicit research-only execution assumptions for one management replay.

    ``adverse_entry_slippage_r`` is measured in the production plan's immutable
    original-R units. The structural stop/targets are not moved to hide slippage.

    ``barrier_spread_price`` treats historical candle OHLC as a mid-price proxy and
    shifts BUY exits to Bid / SELL exits to Ask by half the declared spread.

    ``modify_delay_bars`` delays PROTECT/TRAIL/RUNNER verification by completed M5
    bars. While one modify is unresolved, later manager modify requests are not
    submitted, matching the production principle that ambiguous lifecycle state
    must reconcile before another irreversible write.

    ``reject_every_nth_modify`` is deterministic. For example, ``2`` rejects every
    second submitted modify. ``None`` means no synthetic rejection.
    """

    adverse_entry_slippage_r: float = 0.0
    barrier_spread_price: float = 0.0
    modify_delay_bars: int = 0
    reject_every_nth_modify: int | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.adverse_entry_slippage_r < 1.0:
            raise ValueError("adverse entry slippage must be in [0, 1) original R")
        if self.barrier_spread_price < 0:
            raise ValueError("barrier spread cannot be negative")
        if self.modify_delay_bars < 0:
            raise ValueError("modify delay cannot be negative")
        if self.reject_every_nth_modify is not None and self.reject_every_nth_modify <= 0:
            raise ValueError("modify rejection cadence must be positive when configured")


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
    entry_slippage_r: float = 0.0
    modify_requests: int = 0
    modify_applied: int = 0
    modify_rejected: int = 0
    modify_suppressed_pending: int = 0
    modify_pending_at_end: int = 0


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
    modify_requests: int = 0
    modify_applied: int = 0
    modify_rejected: int = 0
    modify_suppressed_pending: int = 0
    modify_pending_at_end: int = 0


@dataclass(frozen=True, slots=True)
class _PendingModification:
    decision: TradeManagementDecision
    due_bar: int
    reject: bool


def run_trade_manager_replay(
    dataset: ReplayDataset,
    run: ReplayRun,
    *,
    horizon_m5_bars: int = 96,
    minimum_bars: dict[Timeframe, int] | None = None,
    intelligence_config: IntelligenceConfig | None = None,
    trade_plan_config: TradePlanConfig | None = None,
    manager_config: TradeManagerConfig | None = None,
    assumptions: ManagementReplayAssumptions | None = None,
) -> tuple[ManagementReplayRecord, ...]:
    """Replay production management for every analytical ENTER in ``run``."""

    if horizon_m5_bars <= 0:
        raise ValueError("management replay horizon must contain at least one M5 bar")
    execution = assumptions or ManagementReplayAssumptions()

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
                    entry_slippage_r=execution.adverse_entry_slippage_r,
                )
            )
            continue

        trade = managed_trade_from_fill(
            plan,
            position_ticket=ticket,
            volume=dataset.symbol_spec.volume_min,
            fill_price=_stressed_fill_price(plan, execution),
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
                assumptions=execution,
            )
        )

    return tuple(records)


def evaluate_active_barriers(
    trade: ManagedTrade,
    candle: Candle,
    *,
    spread_price: float = 0.0,
) -> ActiveBarrierResult:
    """Evaluate stop/active broker TP without inventing same-bar ordering.

    With a positive ``spread_price``, candle OHLC is treated as a mid-price proxy.
    BUY exits are evaluated on Bid and SELL exits on Ask.
    """

    if spread_price < 0:
        raise ValueError("active-barrier spread cannot be negative")
    low, high = _executable_extremes(trade.direction, candle, spread_price)
    stop_hit = _stop_touched(trade.direction, trade.current_stop, low=low, high=high)
    target_hit = (
        trade.broker_tp is not None
        and _target_touched(trade.direction, trade.broker_tp, low=low, high=high)
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
        modify_requests=sum(record.modify_requests for record in managed),
        modify_applied=sum(record.modify_applied for record in managed),
        modify_rejected=sum(record.modify_rejected for record in managed),
        modify_suppressed_pending=sum(
            record.modify_suppressed_pending for record in managed
        ),
        modify_pending_at_end=sum(record.modify_pending_at_end for record in managed),
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
    assumptions: ManagementReplayAssumptions,
) -> ManagementReplayRecord:
    future = _future_m5_bars(dataset, as_of_utc, horizon_m5_bars)
    mfe_r = 0.0
    mae_r = 0.0
    actions: list[TradeManagerAction] = []
    final_r = 0.0
    pending: _PendingModification | None = None
    modify_requests = 0
    modify_applied = 0
    modify_rejected = 0
    modify_suppressed_pending = 0

    for index, candle in enumerate(future, start=1):
        favorable, adverse = _excursions_r(
            trade,
            candle,
            assumptions.barrier_spread_price,
        )
        mfe_r = max(mfe_r, favorable)
        mae_r = max(mae_r, adverse)
        barrier = evaluate_active_barriers(
            trade,
            candle,
            spread_price=assumptions.barrier_spread_price,
        )
        close_price = _executable_close(
            trade.direction,
            candle.close,
            assumptions.barrier_spread_price,
        )
        final_r = _signed_r(
            trade.direction,
            trade.entry_price,
            trade.original_r_price,
            close_price,
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
                assumptions,
                modify_requests,
                modify_applied,
                modify_rejected,
                modify_suppressed_pending,
                pending,
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
                assumptions,
                modify_requests,
                modify_applied,
                modify_rejected,
                modify_suppressed_pending,
                pending,
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
                assumptions,
                modify_requests,
                modify_applied,
                modify_rejected,
                modify_suppressed_pending,
                pending,
            )

        event_time = candle.time_utc + _M5
        if pending is not None and index >= pending.due_bar:
            if pending.reject:
                modify_rejected += 1
            else:
                trade = apply_management_decision(trade, pending.decision, event_time)
                modify_applied += 1
            pending = None

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
                assumptions,
                modify_requests,
                modify_applied,
                modify_rejected,
                modify_suppressed_pending,
                pending,
            )
        if decision.requires_broker_write:
            if pending is not None:
                modify_suppressed_pending += 1
                continue
            modify_requests += 1
            reject = _should_reject_modify(
                modify_requests,
                assumptions.reject_every_nth_modify,
            )
            if assumptions.modify_delay_bars == 0:
                if reject:
                    modify_rejected += 1
                else:
                    trade = apply_management_decision(trade, decision, event_time)
                    modify_applied += 1
            else:
                pending = _PendingModification(
                    decision=decision,
                    due_bar=index + assumptions.modify_delay_bars,
                    reject=reject,
                )

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
        assumptions,
        modify_requests,
        modify_applied,
        modify_rejected,
        modify_suppressed_pending,
        pending,
    )


def _stressed_fill_price(
    plan: TradePlan,
    assumptions: ManagementReplayAssumptions,
) -> float:
    if plan.original_r_price is None:
        raise ValueError("READY Trade Plan requires original R before fill modeling")
    slip = plan.original_r_price * assumptions.adverse_entry_slippage_r
    fill = (
        plan.approved_entry_reference + slip
        if plan.direction is Direction.BUY
        else plan.approved_entry_reference - slip
    )
    if fill <= 0:
        raise ValueError("stressed fill must remain positive")
    return fill


def _should_reject_modify(request_number: int, cadence: int | None) -> bool:
    return cadence is not None and request_number % cadence == 0


def _future_m5_bars(
    dataset: ReplayDataset,
    as_of_utc: datetime,
    horizon: int,
) -> tuple[Candle, ...]:
    m5 = next(item for item in dataset.series if item.timeframe is Timeframe.M5)
    return tuple(candle for candle in m5.candles if candle.time_utc >= as_of_utc)[:horizon]


def _excursions_r(
    trade: ManagedTrade,
    candle: Candle,
    spread_price: float,
) -> tuple[float, float]:
    low, high = _executable_extremes(trade.direction, candle, spread_price)
    if trade.direction is Direction.BUY:
        favorable = max(0.0, high - trade.entry_price) / trade.original_r_price
        adverse = max(0.0, trade.entry_price - low) / trade.original_r_price
    else:
        favorable = max(0.0, trade.entry_price - low) / trade.original_r_price
        adverse = max(0.0, high - trade.entry_price) / trade.original_r_price
    return favorable, adverse


def _executable_extremes(
    direction: Direction,
    candle: Candle,
    spread_price: float,
) -> tuple[float, float]:
    half_spread = spread_price / 2.0
    if direction is Direction.BUY:
        return candle.low - half_spread, candle.high - half_spread
    return candle.low + half_spread, candle.high + half_spread


def _executable_close(direction: Direction, close: float, spread_price: float) -> float:
    half_spread = spread_price / 2.0
    return close - half_spread if direction is Direction.BUY else close + half_spread


def _stop_touched(
    direction: Direction,
    stop: float,
    *,
    low: float,
    high: float,
) -> bool:
    return low <= stop if direction is Direction.BUY else high >= stop


def _target_touched(
    direction: Direction,
    target: float,
    *,
    low: float,
    high: float,
) -> bool:
    return high >= target if direction is Direction.BUY else low <= target


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
    assumptions: ManagementReplayAssumptions,
    modify_requests: int,
    modify_applied: int,
    modify_rejected: int,
    modify_suppressed_pending: int,
    pending: _PendingModification | None,
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
        entry_slippage_r=assumptions.adverse_entry_slippage_r,
        modify_requests=modify_requests,
        modify_applied=modify_applied,
        modify_rejected=modify_rejected,
        modify_suppressed_pending=modify_suppressed_pending,
        modify_pending_at_end=1 if pending is not None else 0,
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