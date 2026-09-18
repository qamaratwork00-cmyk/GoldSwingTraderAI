from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from goldswingtraderai.app.recovery import (
    BrokerRecoveryPosition,
    BrokerRecoverySnapshot,
    RecoveryAuthorities,
    RecoveryState,
    StartupRecoveryCoordinator,
)
from goldswingtraderai.domain.enums import AccountMode, Direction, HardDecision
from goldswingtraderai.domain.ids import (
    new_controller_id,
    new_episode_id,
    new_execution_intent_id,
    new_opportunity_id,
    new_trade_id,
    new_trade_plan_id,
)
from goldswingtraderai.domain.market import AccountFacts
from goldswingtraderai.execution import (
    AuthorityTrace,
    ControllerLeaseManager,
    ExecutionAction,
    ExecutionIntent,
    ExecutionIntentRepository,
    InMemoryCoordinationStore,
    IntentState,
    MT5Reconciler,
    MT5WriteConfig,
)
from goldswingtraderai.management import ManagedTrade, ManagedTradeRepository, ObjectiveStage
from goldswingtraderai.persistence import RuntimeStateRepository, StateStore


NOW = datetime(2026, 9, 18, 18, 30, tzinfo=timezone.utc)
SYMBOL = "XAUUSDm"
SCOPE = "123456:XAUUSDm"
WRITE_CONFIG = MT5WriteConfig(magic=26091801, deviation_points=20)


class FakeBroker:
    POSITION_TYPE_BUY = 0
    POSITION_TYPE_SELL = 1
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1

    def __init__(self) -> None:
        self.positions: tuple[object, ...] = ()
        self.orders: tuple[object, ...] = ()
        self.deals: tuple[object, ...] = ()

    def positions_get(self, *, symbol):
        assert symbol == SYMBOL
        return self.positions

    def orders_get(self, *, symbol):
        assert symbol == SYMBOL
        return self.orders

    def history_deals_get(self, start, end):
        assert start.tzinfo is not None and end.tzinfo is not None
        return self.deals


def _account(*, login: int = 123456, mode: AccountMode = AccountMode.DEMO) -> AccountFacts:
    return AccountFacts(
        login=login,
        server="Broker-Demo",
        currency="USD",
        mode=mode,
        balance=100.0,
        equity=100.0,
        margin=0.0,
        margin_free=100.0,
        leverage=500,
    )


def _snapshot(
    *,
    account: AccountFacts | None = None,
    positions: tuple[BrokerRecoveryPosition, ...] = (),
    positions_complete: bool = True,
) -> BrokerRecoverySnapshot:
    return BrokerRecoverySnapshot(
        account=account or _account(),
        symbol=SYMBOL,
        positions=positions,
        captured_at_utc=NOW,
        positions_complete=positions_complete,
    )


def _trace(name: str, decision: HardDecision = HardDecision.PASS) -> AuthorityTrace:
    return AuthorityTrace(name, decision, f"{name.upper()}_{decision.value}")


def _authorities(**overrides: HardDecision) -> RecoveryAuthorities:
    return RecoveryAuthorities(
        account_identity=_trace("account_identity", overrides.get("account_identity", HardDecision.PASS)),
        market_data=_trace("market_data", overrides.get("market_data", HardDecision.PASS)),
        session_news=_trace("session_news", overrides.get("session_news", HardDecision.PASS)),
        risk=_trace("risk", overrides.get("risk", HardDecision.PASS)),
        position_capacity=_trace(
            "position_capacity", overrides.get("position_capacity", HardDecision.PASS)
        ),
        execution_environment=_trace(
            "execution_environment", overrides.get("execution_environment", HardDecision.PASS)
        ),
    )


def _intent(
    controller_id,
    epoch: int,
    *,
    state: IntentState,
    account_login: int = 123456,
    action: ExecutionAction = ExecutionAction.OPEN,
    broker_ticket: int | None = None,
) -> ExecutionIntent:
    submit_attempts = 1 if state in {
        IntentState.SUBMITTING,
        IntentState.ACCEPTED_UNKNOWN,
        IntentState.ACCEPTED_VERIFIED,
    } else 0
    return ExecutionIntent(
        intent_id=new_execution_intent_id(),
        action=action,
        account_login=account_login,
        account_server="Broker-Demo",
        symbol=SYMBOL,
        direction=Direction.BUY,
        volume=0.01,
        approved_entry_reference=100.0,
        stop_loss=90.0 if action is not ExecutionAction.CLOSE else None,
        take_profit=125.0 if action is not ExecutionAction.CLOSE else None,
        opportunity_id=new_opportunity_id(),
        episode_id=new_episode_id(),
        trade_plan_id=new_trade_plan_id(),
        controller_id=controller_id,
        fencing_epoch=epoch,
        created_at_utc=NOW - timedelta(minutes=1),
        state=state,
        submit_attempts=submit_attempts,
        broker_ticket=broker_ticket,
        position_ticket=9001 if action in {ExecutionAction.MODIFY, ExecutionAction.CLOSE} else None,
        filling_mode=1 if action in {ExecutionAction.OPEN, ExecutionAction.CLOSE} else None,
    )


def _managed_trade() -> ManagedTrade:
    return ManagedTrade(
        trade_id=new_trade_id(),
        position_ticket=9001,
        plan_id=new_trade_plan_id(),
        opportunity_id=new_opportunity_id(),
        episode_id=new_episode_id(),
        symbol=SYMBOL,
        direction=Direction.BUY,
        volume=0.01,
        entry_price=100.0,
        original_stop=90.0,
        original_r_price=10.0,
        current_stop=90.0,
        broker_tp=125.0,
        primary_target=None,
        expansion_target=None,
        runner_candidate=None,
        active_runner_target=None,
        objective_stage=ObjectiveStage.PRIMARY,
        opened_at_utc=NOW - timedelta(hours=1),
        updated_at_utc=NOW - timedelta(minutes=5),
    )


def _position(*, stop_loss: float = 90.0, take_profit: float | None = 125.0):
    return BrokerRecoveryPosition(
        ticket=9001,
        symbol=SYMBOL,
        direction=Direction.BUY,
        volume=0.01,
        stop_loss=stop_loss,
        take_profit=take_profit,
    )


def _coordinator(tmp_path, controller: ControllerLeaseManager, broker: FakeBroker):
    store = StateStore(tmp_path / "runtime.db")
    runtime = RuntimeStateRepository(store, SCOPE)
    intents = ExecutionIntentRepository(store, SCOPE)
    trades = ManagedTradeRepository(store, SCOPE)
    coordinator = StartupRecoveryCoordinator(
        store,
        runtime,
        intents,
        trades,
        controller,
        MT5Reconciler(broker, WRITE_CONFIG),
    )
    return coordinator, intents, trades


def _primary_controller(clock: list[datetime]):
    coordination = InMemoryCoordinationStore(lambda: clock[0])
    controller = ControllerLeaseManager(coordination, SCOPE, new_controller_id())
    status = controller.acquire()
    assert status.decision is HardDecision.PASS
    assert status.lease is not None
    return coordination, controller, status.lease.epoch


def test_clean_startup_recovery_becomes_ready(tmp_path) -> None:
    clock = [NOW]
    _, controller, _ = _primary_controller(clock)
    coordinator, _, _ = _coordinator(tmp_path, controller, FakeBroker())

    result = coordinator.recover(
        _snapshot(),
        _authorities(),
        NOW,
        price_tolerance=0.001,
    )

    assert result.state is RecoveryState.READY
    assert result.reason == "STARTUP_RECOVERY_READY"
    assert result.controller_status is not None
    assert result.controller_status.decision is HardDecision.PASS
    assert not result.takeover_completed


def test_expired_lease_takeover_completes_only_after_recovery_passes(tmp_path) -> None:
    clock = [NOW]
    coordination = InMemoryCoordinationStore(lambda: clock[0])
    first = ControllerLeaseManager(coordination, SCOPE, new_controller_id())
    second = ControllerLeaseManager(coordination, SCOPE, new_controller_id())
    assert first.acquire().decision is HardDecision.PASS

    clock[0] += timedelta(seconds=31)
    takeover = second.acquire()
    assert takeover.reason == "CONTROLLER_TAKEOVER_RECONCILIATION_REQUIRED"
    coordinator, _, _ = _coordinator(tmp_path, second, FakeBroker())

    result = coordinator.recover(
        _snapshot(),
        _authorities(),
        clock[0],
        price_tolerance=0.001,
    )

    assert result.state is RecoveryState.READY
    assert result.takeover_completed
    assert not second.takeover_reconciliation_required
    assert second.verify_write_authority(clock[0]).decision is HardDecision.PASS


def test_unresolved_execution_intent_keeps_takeover_blocked(tmp_path) -> None:
    clock = [NOW]
    coordination = InMemoryCoordinationStore(lambda: clock[0])
    first = ControllerLeaseManager(coordination, SCOPE, new_controller_id())
    first_status = first.acquire()
    assert first_status.lease is not None
    clock[0] += timedelta(seconds=31)
    second = ControllerLeaseManager(coordination, SCOPE, new_controller_id())
    assert second.acquire().reason == "CONTROLLER_TAKEOVER_RECONCILIATION_REQUIRED"

    broker = FakeBroker()
    coordinator, intents, _ = _coordinator(tmp_path, second, broker)
    intents.save(_intent(first.controller_id, first_status.lease.epoch, state=IntentState.SUBMITTING))

    result = coordinator.recover(
        _snapshot(),
        _authorities(),
        clock[0],
        price_tolerance=0.001,
    )

    assert result.state is RecoveryState.RECONCILING
    assert result.reason == "EXECUTION_INTENT_RECONCILIATION_UNRESOLVED"
    assert result.execution_intent is not None
    assert result.execution_intent.state is IntentState.ACCEPTED_UNKNOWN
    assert second.takeover_reconciliation_required


def test_pre_submit_approved_intent_is_cancelled_without_send_and_recovery_continues(tmp_path) -> None:
    clock = [NOW]
    _, controller, epoch = _primary_controller(clock)
    coordinator, intents, _ = _coordinator(tmp_path, controller, FakeBroker())
    intents.save(_intent(controller.controller_id, epoch, state=IntentState.APPROVED))

    result = coordinator.recover(
        _snapshot(),
        _authorities(),
        NOW,
        price_tolerance=0.001,
    )

    assert result.state is RecoveryState.READY
    assert result.execution_intent is not None
    assert result.execution_intent.state is IntentState.FAILED
    assert result.execution_intent.submit_attempts == 0
    assert result.execution_intent.result_message == "RECOVERY_CANCELLED_PRE_SUBMIT_INTENT"


def test_verified_open_without_managed_trade_context_stays_reconciling(tmp_path) -> None:
    clock = [NOW]
    _, controller, epoch = _primary_controller(clock)
    coordinator, intents, _ = _coordinator(tmp_path, controller, FakeBroker())
    intents.save(
        _intent(
            controller.controller_id,
            epoch,
            state=IntentState.ACCEPTED_VERIFIED,
            broker_ticket=9001,
        )
    )

    result = coordinator.recover(
        _snapshot(positions=(_position(),)),
        _authorities(),
        NOW,
        price_tolerance=0.001,
    )

    assert result.state is RecoveryState.RECONCILING
    assert result.reason == "MANAGED_TRADE_CONTEXT_MISSING_FOR_VERIFIED_OPEN"


def test_managed_trade_must_match_current_broker_position(tmp_path) -> None:
    clock = [NOW]
    _, controller, _ = _primary_controller(clock)
    coordinator, _, trades = _coordinator(tmp_path, controller, FakeBroker())
    trades.save(_managed_trade())

    ready = coordinator.recover(
        _snapshot(positions=(_position(),)),
        _authorities(),
        NOW,
        price_tolerance=0.001,
    )
    assert ready.state is RecoveryState.READY


def test_managed_trade_level_mismatch_requires_reconciliation(tmp_path) -> None:
    clock = [NOW]
    _, controller, _ = _primary_controller(clock)
    coordinator, _, trades = _coordinator(tmp_path, controller, FakeBroker())
    trades.save(_managed_trade())

    result = coordinator.recover(
        _snapshot(positions=(_position(stop_loss=91.0),)),
        _authorities(),
        NOW,
        price_tolerance=0.001,
    )

    assert result.state is RecoveryState.RECONCILING
    assert result.reason == "MANAGED_TRADE_STOP_RECONCILIATION_REQUIRED"


def test_unknown_hard_authority_prevents_takeover_completion(tmp_path) -> None:
    clock = [NOW]
    coordination = InMemoryCoordinationStore(lambda: clock[0])
    first = ControllerLeaseManager(coordination, SCOPE, new_controller_id())
    assert first.acquire().decision is HardDecision.PASS
    clock[0] += timedelta(seconds=31)
    second = ControllerLeaseManager(coordination, SCOPE, new_controller_id())
    assert second.acquire().reason == "CONTROLLER_TAKEOVER_RECONCILIATION_REQUIRED"
    coordinator, _, _ = _coordinator(tmp_path, second, FakeBroker())

    result = coordinator.recover(
        _snapshot(),
        _authorities(risk=HardDecision.UNKNOWN),
        clock[0],
        price_tolerance=0.001,
    )

    assert result.state is RecoveryState.RECONCILING
    assert result.reason == "RISK_UNKNOWN"
    assert second.takeover_reconciliation_required


def test_persisted_intent_account_mismatch_blocks_recovery(tmp_path) -> None:
    clock = [NOW]
    _, controller, epoch = _primary_controller(clock)
    coordinator, intents, _ = _coordinator(tmp_path, controller, FakeBroker())
    intents.save(
        replace(
            _intent(controller.controller_id, epoch, state=IntentState.FAILED),
            account_login=999999,
        )
    )

    result = coordinator.recover(
        _snapshot(),
        _authorities(),
        NOW,
        price_tolerance=0.001,
    )

    assert result.state is RecoveryState.BLOCKED
    assert result.reason == "RECOVERY_ACCOUNT_LOGIN_MISMATCH"


def test_non_demo_account_blocks_recovery_ready(tmp_path) -> None:
    clock = [NOW]
    _, controller, _ = _primary_controller(clock)
    coordinator, _, _ = _coordinator(tmp_path, controller, FakeBroker())

    result = coordinator.recover(
        _snapshot(account=_account(mode=AccountMode.OTHER)),
        _authorities(),
        NOW,
        price_tolerance=0.001,
    )

    assert result.state is RecoveryState.BLOCKED
    assert result.reason == "DEMO_GUARD_NOT_VERIFIED"
