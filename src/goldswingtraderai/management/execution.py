"""Pure bridge from Trade Manager actions into the governed execution boundary."""

from __future__ import annotations

from datetime import datetime

from goldswingtraderai.domain.ids import EntityId, new_execution_intent_id
from goldswingtraderai.execution import ExecutionAction, ExecutionIntent, IntentState
from goldswingtraderai.management.models import (
    ManagedTrade,
    TradeManagementDecision,
    apply_management_decision,
)
from goldswingtraderai.management.store import ManagedTradeRepository
from goldswingtraderai.domain.enums import TradeManagerAction


def management_intent_from_decision(
    trade: ManagedTrade,
    decision: TradeManagementDecision,
    *,
    account_login: int,
    account_server: str,
    controller_id: EntityId,
    fencing_epoch: int,
    created_at_utc: datetime,
    filling_mode: int | None,
) -> ExecutionIntent | None:
    """Translate a broker-write management action without bypassing ExecutionService."""

    if decision.action is TradeManagerAction.HOLD:
        return None

    if decision.action is TradeManagerAction.EXIT:
        action = ExecutionAction.CLOSE
        stop_loss = None
        take_profit = None
        required_filling = filling_mode
    else:
        action = ExecutionAction.MODIFY
        stop_loss = decision.proposed_stop if decision.proposed_stop is not None else trade.current_stop
        take_profit = decision.proposed_tp if decision.proposed_tp is not None else trade.broker_tp
        required_filling = None
        if decision.action in {TradeManagerAction.PROTECT, TradeManagerAction.TRAIL} and decision.proposed_stop is None:
            raise ValueError("PROTECT/TRAIL decision requires a proposed structural stop")
        if decision.action is TradeManagerAction.RUNNER and decision.proposed_tp is None:
            raise ValueError("RUNNER decision requires a proposed objective")

    return ExecutionIntent(
        intent_id=new_execution_intent_id(),
        action=action,
        account_login=account_login,
        account_server=account_server,
        symbol=trade.symbol,
        direction=trade.direction,
        volume=trade.volume,
        approved_entry_reference=trade.entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        opportunity_id=trade.opportunity_id,
        episode_id=trade.episode_id,
        trade_plan_id=trade.plan_id,
        controller_id=controller_id,
        fencing_epoch=fencing_epoch,
        created_at_utc=created_at_utc,
        position_ticket=trade.position_ticket,
        filling_mode=required_filling,
    )


def apply_verified_management_result(
    repository: ManagedTradeRepository,
    trade: ManagedTrade,
    decision: TradeManagementDecision,
    intent: ExecutionIntent,
    *,
    verified_at_utc: datetime,
) -> ManagedTrade | None:
    """Mutate durable trade lifecycle only after broker truth verifies the write."""

    if intent.state is not IntentState.ACCEPTED_VERIFIED:
        raise PermissionError("management state cannot update before broker verification")

    if decision.action is TradeManagerAction.EXIT:
        repository.clear_verified_closed()
        return None

    updated = apply_management_decision(trade, decision, verified_at_utc)
    repository.save(updated, event_type=f"MANAGED_TRADE_{decision.action.value}_VERIFIED")
    return updated
