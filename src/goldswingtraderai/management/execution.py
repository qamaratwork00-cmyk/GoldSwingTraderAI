"""Pure bridge from Trade Manager actions into the governed execution boundary."""

from __future__ import annotations

from datetime import datetime
from math import isclose

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

    _validate_verified_management_identity(trade, decision, intent, verified_at_utc)

    if decision.action is TradeManagerAction.EXIT:
        repository.clear_verified_closed()
        return None

    updated = apply_management_decision(trade, decision, verified_at_utc)
    repository.save(updated, event_type=f"MANAGED_TRADE_{decision.action.value}_VERIFIED")
    return updated


def _validate_verified_management_identity(
    trade: ManagedTrade,
    decision: TradeManagementDecision,
    intent: ExecutionIntent,
    verified_at_utc: datetime,
) -> None:
    """Reject a verified result that does not belong to this trade/action."""

    if verified_at_utc < intent.created_at_utc:
        raise ValueError("management verification cannot precede intent creation")
    if decision.action is TradeManagerAction.HOLD:
        raise ValueError("HOLD decision cannot have a broker-write intent")
    expected_action = (
        ExecutionAction.CLOSE
        if decision.action is TradeManagerAction.EXIT
        else ExecutionAction.MODIFY
    )
    if intent.action is not expected_action:
        raise ValueError("management intent action does not match decision")
    if (
        intent.symbol != trade.symbol
        or intent.direction is not trade.direction
        or intent.position_ticket != trade.position_ticket
        or not isclose(intent.volume, trade.volume, rel_tol=0.0, abs_tol=1e-12)
        or intent.trade_plan_id != trade.plan_id
        or intent.opportunity_id != trade.opportunity_id
        or intent.episode_id != trade.episode_id
    ):
        raise ValueError("management intent identity does not match managed trade")

    if decision.action is TradeManagerAction.EXIT:
        return

    expected_stop = decision.proposed_stop if decision.proposed_stop is not None else trade.current_stop
    expected_tp = decision.proposed_tp if decision.action is TradeManagerAction.RUNNER else trade.broker_tp
    if intent.stop_loss is None or not isclose(
        intent.stop_loss,
        expected_stop,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError("management intent stop does not match decision")
    if (intent.take_profit is None) != (expected_tp is None):
        raise ValueError("management intent target does not match decision")
    if expected_tp is not None and not isclose(
        intent.take_profit or 0.0,
        expected_tp,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError("management intent target does not match decision")
