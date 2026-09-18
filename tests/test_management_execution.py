from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from goldswingtraderai.decisions.trade_plan import PlanTarget, TargetRole
from goldswingtraderai.domain.enums import Direction, TradeManagerAction
from goldswingtraderai.domain.ids import (
    new_controller_id,
    new_episode_id,
    new_opportunity_id,
    new_trade_id,
    new_trade_plan_id,
)
from goldswingtraderai.execution import ExecutionAction, IntentState
from goldswingtraderai.management import (
    ManagedTrade,
    ManagedTradeRepository,
    ObjectiveStage,
    TradeManagementDecision,
    apply_verified_management_result,
    management_intent_from_decision,
)
from goldswingtraderai.persistence import StateStore


NOW = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)


def _target(role: TargetRole, price: float, rr: float) -> PlanTarget:
    return PlanTarget(role, price, 80.0, f"TEST:{role.value}", rr)


def _trade() -> ManagedTrade:
    return ManagedTrade(
        trade_id=new_trade_id(),
        position_ticket=7001,
        plan_id=new_trade_plan_id(),
        opportunity_id=new_opportunity_id(),
        episode_id=new_episode_id(),
        symbol="XAUUSDm",
        direction=Direction.BUY,
        volume=0.01,
        entry_price=100.0,
        original_stop=90.0,
        original_r_price=10.0,
        current_stop=90.0,
        broker_tp=120.0,
        primary_target=_target(TargetRole.PRIMARY, 110.0, 1.0),
        expansion_target=_target(TargetRole.EXPANSION, 120.0, 2.0),
        runner_candidate=_target(TargetRole.RUNNER, 130.0, 3.0),
        active_runner_target=None,
        objective_stage=ObjectiveStage.EXPANSION,
        opened_at_utc=NOW,
        updated_at_utc=NOW,
    )


def _decision(action: TradeManagerAction) -> TradeManagementDecision:
    return TradeManagementDecision(
        action=action,
        current_r=1.8,
        continuation_score=80.0,
        reversal_score=20.0,
        structure_integrity=80.0,
        path_quality=80.0,
        objective_stage=ObjectiveStage.RUNNER if action is TradeManagerAction.RUNNER else ObjectiveStage.EXPANSION,
        proposed_stop=105.0 if action in {TradeManagerAction.PROTECT, TradeManagerAction.TRAIL, TradeManagerAction.RUNNER} else None,
        proposed_tp=130.0 if action is TradeManagerAction.RUNNER else None,
        reason="TEST",
    )


def test_hold_creates_no_broker_intent() -> None:
    intent = management_intent_from_decision(
        _trade(),
        _decision(TradeManagerAction.HOLD),
        account_login=123456,
        account_server="Broker-Demo",
        controller_id=new_controller_id(),
        fencing_epoch=1,
        created_at_utc=NOW,
        filling_mode=1,
    )
    assert intent is None


def test_runner_maps_to_modify_and_exit_maps_to_close() -> None:
    trade = _trade()
    controller = new_controller_id()
    runner = management_intent_from_decision(
        trade,
        _decision(TradeManagerAction.RUNNER),
        account_login=123456,
        account_server="Broker-Demo",
        controller_id=controller,
        fencing_epoch=3,
        created_at_utc=NOW,
        filling_mode=1,
    )
    exit_intent = management_intent_from_decision(
        trade,
        _decision(TradeManagerAction.EXIT),
        account_login=123456,
        account_server="Broker-Demo",
        controller_id=controller,
        fencing_epoch=3,
        created_at_utc=NOW,
        filling_mode=2,
    )

    assert runner is not None and runner.action is ExecutionAction.MODIFY
    assert runner.position_ticket == trade.position_ticket
    assert runner.stop_loss == pytest.approx(105.0)
    assert runner.take_profit == pytest.approx(130.0)
    assert runner.filling_mode is None
    assert exit_intent is not None and exit_intent.action is ExecutionAction.CLOSE
    assert exit_intent.position_ticket == trade.position_ticket
    assert exit_intent.filling_mode == 2


def test_local_trade_state_changes_only_after_verified_broker_result(tmp_path) -> None:
    trade = _trade()
    repository = ManagedTradeRepository(StateStore(tmp_path / "state.db"), "scope")
    repository.save(trade)
    decision = _decision(TradeManagerAction.RUNNER)
    intent = management_intent_from_decision(
        trade,
        decision,
        account_login=123456,
        account_server="Broker-Demo",
        controller_id=new_controller_id(),
        fencing_epoch=1,
        created_at_utc=NOW,
        filling_mode=1,
    )
    assert intent is not None

    unknown = replace(intent, state=IntentState.ACCEPTED_UNKNOWN, submit_attempts=1)
    with pytest.raises(PermissionError, match="before broker verification"):
        apply_verified_management_result(
            repository,
            trade,
            decision,
            unknown,
            verified_at_utc=NOW,
        )
    assert repository.load() == trade

    verified = replace(intent, state=IntentState.ACCEPTED_VERIFIED, submit_attempts=1)
    updated = apply_verified_management_result(
        repository,
        trade,
        decision,
        verified,
        verified_at_utc=NOW,
    )
    assert updated is not None
    assert updated.objective_stage is ObjectiveStage.RUNNER
    assert updated.current_stop == pytest.approx(105.0)
    assert updated.broker_tp == pytest.approx(130.0)


def test_verified_exit_clears_managed_trade(tmp_path) -> None:
    trade = _trade()
    repository = ManagedTradeRepository(StateStore(tmp_path / "state.db"), "scope")
    repository.save(trade)
    decision = _decision(TradeManagerAction.EXIT)
    intent = management_intent_from_decision(
        trade,
        decision,
        account_login=123456,
        account_server="Broker-Demo",
        controller_id=new_controller_id(),
        fencing_epoch=1,
        created_at_utc=NOW,
        filling_mode=1,
    )
    assert intent is not None
    verified = replace(intent, state=IntentState.ACCEPTED_VERIFIED, submit_attempts=1)

    result = apply_verified_management_result(
        repository,
        trade,
        decision,
        verified,
        verified_at_utc=NOW,
    )
    assert result is None
    assert repository.load() is None
