"""Typed post-entry management state for bot-owned Gold positions."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum
from math import isfinite

from goldswingtraderai.decisions.trade_plan import PlanTarget, PlanState, TradePlan
from goldswingtraderai.domain.enums import Direction, Timeframe, TradeManagerAction
from goldswingtraderai.domain.ids import EntityId, new_trade_id


class ObjectiveStage(StrEnum):
    PRIMARY = "PRIMARY"
    EXPANSION = "EXPANSION"
    RUNNER = "RUNNER"


@dataclass(frozen=True, slots=True)
class StructuralStopReference:
    timeframe: Timeframe
    price: float
    atr: float

    def __post_init__(self) -> None:
        if not isfinite(self.price) or not isfinite(self.atr):
            raise ValueError("structural stop reference values must be finite")
        if self.price <= 0 or self.atr <= 0:
            raise ValueError("structural stop reference price/ATR must be positive")


@dataclass(frozen=True, slots=True)
class ManagementEvidence:
    continuation_score: float
    reversal_score: float
    structure_integrity: float
    candle_health: float
    momentum_health: float
    path_quality: float
    stop_references: tuple[StructuralStopReference, ...] = ()

    def __post_init__(self) -> None:
        for value in (
            self.continuation_score,
            self.reversal_score,
            self.structure_integrity,
            self.candle_health,
            self.momentum_health,
            self.path_quality,
        ):
            if not isfinite(value) or not 0 <= value <= 100:
                raise ValueError("management evidence scores must be between 0 and 100")


@dataclass(frozen=True, slots=True)
class ManagedTrade:
    trade_id: EntityId
    position_ticket: int
    plan_id: EntityId
    opportunity_id: EntityId
    episode_id: EntityId
    symbol: str
    direction: Direction
    volume: float
    entry_price: float
    original_stop: float
    original_r_price: float
    current_stop: float
    broker_tp: float | None
    primary_target: PlanTarget | None
    expansion_target: PlanTarget | None
    runner_candidate: PlanTarget | None
    active_runner_target: PlanTarget | None
    objective_stage: ObjectiveStage
    opened_at_utc: datetime
    updated_at_utc: datetime

    def __post_init__(self) -> None:
        _require_utc(self.opened_at_utc)
        _require_utc(self.updated_at_utc)
        if self.updated_at_utc < self.opened_at_utc:
            raise ValueError("managed-trade update cannot precede open time")
        if self.position_ticket <= 0:
            raise ValueError("managed trade requires positive broker position ticket")
        if not self.symbol.strip():
            raise ValueError("managed trade symbol cannot be empty")
        if self.direction is Direction.NONE:
            raise ValueError("managed trade direction must be BUY or SELL")
        monetary_values = (
            self.volume,
            self.entry_price,
            self.original_stop,
            self.original_r_price,
            self.current_stop,
        )
        if any(not isfinite(value) for value in monetary_values):
            raise ValueError("managed-trade monetary values must be finite")
        if min(monetary_values) <= 0:
            raise ValueError("managed-trade volume/prices must be positive")
        if self.direction is Direction.BUY:
            if self.original_stop >= self.entry_price:
                raise ValueError("BUY original stop must be below entry")
            if self.current_stop < self.original_stop:
                raise ValueError("BUY stop may not widen below original approved stop")
        else:
            if self.original_stop <= self.entry_price:
                raise ValueError("SELL original stop must be above entry")
            if self.current_stop > self.original_stop:
                raise ValueError("SELL stop may not widen above original approved stop")
        if self.broker_tp is not None and (
            not isfinite(self.broker_tp) or self.broker_tp <= 0
        ):
            raise ValueError("broker TP must be positive when present")
        if self.objective_stage is ObjectiveStage.RUNNER and self.active_runner_target is None:
            raise ValueError("RUNNER stage requires an active runner objective")


@dataclass(frozen=True, slots=True)
class TradeManagementDecision:
    action: TradeManagerAction
    current_r: float
    continuation_score: float
    reversal_score: float
    structure_integrity: float
    path_quality: float
    objective_stage: ObjectiveStage
    proposed_stop: float | None
    proposed_tp: float | None
    reason: str

    def __post_init__(self) -> None:
        values = (
            self.current_r,
            self.continuation_score,
            self.reversal_score,
            self.structure_integrity,
            self.path_quality,
        )
        if not all(isfinite(value) for value in values):
            raise ValueError("trade-management decision values must be finite")
        if not all(0 <= value <= 100 for value in values[1:]):
            raise ValueError("trade-management decision scores must be between 0 and 100")
        for value in (self.proposed_stop, self.proposed_tp):
            if value is not None and (not isfinite(value) or value <= 0):
                raise ValueError("proposed management prices must be positive and finite")
        if not self.reason.strip():
            raise ValueError("trade-management decision reason cannot be empty")

    @property
    def requires_broker_write(self) -> bool:
        return self.action in {
            TradeManagerAction.PROTECT,
            TradeManagerAction.TRAIL,
            TradeManagerAction.RUNNER,
            TradeManagerAction.EXIT,
        }


def managed_trade_from_fill(
    plan: TradePlan,
    *,
    position_ticket: int,
    volume: float,
    fill_price: float,
    opened_at_utc: datetime,
    symbol: str,
) -> ManagedTrade:
    """Create durable bot-owned trade state from one verified broker fill."""

    _require_utc(opened_at_utc)
    if plan.state is not PlanState.READY:
        raise ValueError("managed trade requires READY Trade Plan")
    if plan.initial_stop is None or plan.original_r_price is None:
        raise ValueError("READY Trade Plan lacks required risk geometry")

    if plan.expansion_target is not None:
        stage = ObjectiveStage.EXPANSION
    else:
        stage = ObjectiveStage.PRIMARY
    broker_tp = plan.broker_tp_target.price if plan.broker_tp_target is not None else None
    return ManagedTrade(
        trade_id=new_trade_id(),
        position_ticket=position_ticket,
        plan_id=plan.plan_id,
        opportunity_id=plan.opportunity_id,
        episode_id=plan.episode_id,
        symbol=symbol,
        direction=plan.direction,
        volume=volume,
        entry_price=fill_price,
        original_stop=plan.initial_stop,
        original_r_price=plan.original_r_price,
        current_stop=plan.initial_stop,
        broker_tp=broker_tp,
        primary_target=plan.primary_target,
        expansion_target=plan.expansion_target,
        runner_candidate=plan.runner_target,
        active_runner_target=None,
        objective_stage=stage,
        opened_at_utc=opened_at_utc,
        updated_at_utc=opened_at_utc,
    )


def apply_management_decision(
    trade: ManagedTrade,
    decision: TradeManagementDecision,
    updated_at_utc: datetime,
) -> ManagedTrade:
    """Update local lifecycle only after the corresponding broker write is verified."""

    _require_utc(updated_at_utc)
    current_stop = trade.current_stop
    broker_tp = trade.broker_tp
    stage = trade.objective_stage
    active_runner = trade.active_runner_target

    if decision.proposed_stop is not None:
        if trade.direction is Direction.BUY:
            current_stop = max(current_stop, decision.proposed_stop)
        else:
            current_stop = min(current_stop, decision.proposed_stop)
    if decision.action is TradeManagerAction.RUNNER and decision.proposed_tp is not None:
        broker_tp = decision.proposed_tp
        stage = ObjectiveStage.RUNNER
        active_runner = trade.runner_candidate

    return replace(
        trade,
        current_stop=current_stop,
        broker_tp=broker_tp,
        objective_stage=stage,
        active_runner_target=active_runner,
        updated_at_utc=updated_at_utc,
    )


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("managed-trade timestamp must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("managed-trade timestamp must be UTC")
