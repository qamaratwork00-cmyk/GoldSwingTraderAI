from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from goldswingtraderai.decisions.trade_plan import (
    PlanState,
    PlanTarget,
    RRClass,
    StopQuality,
    TargetRole,
    TradePlan,
)
from goldswingtraderai.domain.enums import Direction, HardDecision, StrategyFamily
from goldswingtraderai.domain.ids import (
    new_controller_id,
    new_episode_id,
    new_execution_intent_id,
    new_opportunity_id,
    new_trade_plan_id,
)
from goldswingtraderai.domain.market import Quote
from goldswingtraderai.execution import (
    AuthorityTrace,
    ControllerLeaseManager,
    ExecutionAction,
    ExecutionIntent,
    ExecutionIntentRepository,
    ExecutionPermission,
    ExecutionService,
    GateInputs,
    InMemoryCoordinationStore,
    IntentState,
    MT5Reconciler,
    MT5WriteConfig,
    MT5Writer,
    ReconciliationStatus,
    evaluate_execution_checks,
    evaluate_execution_permission,
)
from goldswingtraderai.persistence import StateStore


NOW = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
SYMBOL = "XAUUSDm"
WRITE_CONFIG = MT5WriteConfig(magic=26091801, deviation_points=20)


class FakeMT5:
    TRADE_ACTION_DEAL = 1
    TRADE_ACTION_SLTP = 6
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    POSITION_TYPE_BUY = 0
    POSITION_TYPE_SELL = 1
    ORDER_TIME_GTC = 0
    TRADE_RETCODE_PLACED = 10008
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_DONE_PARTIAL = 10010

    def __init__(self) -> None:
        self.check_retcode = 0
        self.check_comment = "Done"
        self.send_result = SimpleNamespace(
            retcode=self.TRADE_RETCODE_DONE,
            order=777,
            deal=888,
            comment="Done",
        )
        self.send_exception: Exception | None = None
        self.check_calls = 0
        self.send_calls = 0
        self.last_request: dict[str, object] | None = None
        self.positions: tuple[object, ...] = ()
        self.orders: tuple[object, ...] = ()
        self.deals: tuple[object, ...] = ()

    def order_calc_margin(self, order_type, symbol, volume, price):
        assert order_type in {self.ORDER_TYPE_BUY, self.ORDER_TYPE_SELL}
        assert symbol == SYMBOL
        assert volume > 0 and price > 0
        return 2.5

    def order_check(self, request):
        self.check_calls += 1
        return SimpleNamespace(retcode=self.check_retcode, comment=self.check_comment)

    def order_send(self, request):
        self.send_calls += 1
        self.last_request = dict(request)
        if self.send_exception is not None:
            raise self.send_exception
        return self.send_result

    def positions_get(self, *, symbol):
        assert symbol == SYMBOL
        return self.positions

    def orders_get(self, *, symbol):
        assert symbol == SYMBOL
        return self.orders

    def history_deals_get(self, start, end):
        assert start.tzinfo is not None and end.tzinfo is not None
        return self.deals


def _plan(direction: Direction = Direction.BUY) -> TradePlan:
    primary = PlanTarget(TargetRole.PRIMARY, 115.0, 80.0, "H1:SWING", 1.5)
    expansion = PlanTarget(TargetRole.EXPANSION, 125.0, 90.0, "H4:SWING", 2.5)
    return TradePlan(
        plan_id=new_trade_plan_id(),
        opportunity_id=new_opportunity_id(),
        episode_id=new_episode_id(),
        family=StrategyFamily.TREND_PULLBACK_CONTINUATION,
        direction=direction,
        state=PlanState.READY,
        signal_price=99.8,
        approved_entry_reference=100.0,
        invalidation_level=91.0 if direction is Direction.BUY else 109.0,
        invalidation_source="M15:PROTECTED_SWING",
        initial_stop=90.0 if direction is Direction.BUY else 110.0,
        stop_buffer=1.0,
        stop_quality=StopQuality.ROBUST,
        original_r_price=10.0,
        immediate_obstacle=None,
        primary_target=primary,
        expansion_target=expansion,
        runner_target=None,
        broker_tp_target=expansion,
        rr_class=RRClass.GOOD,
        path_quality=80.0,
        plan_quality=85.0,
        created_at_utc=NOW,
        reason="PLAN_READY",
    )


def _quote(*, bid: float = 99.8, ask: float = 100.0) -> Quote:
    return Quote(symbol=SYMBOL, bid=bid, ask=ask, time_utc=NOW)


def _all_pass_permission() -> ExecutionPermission:
    def trace(name: str) -> AuthorityTrace:
        return AuthorityTrace(name, HardDecision.PASS, f"{name.upper()}_PASS")

    return evaluate_execution_permission(
        GateInputs(
            demo_guard=trace("demo"),
            account_identity=trace("account"),
            market_data_quote=trace("data"),
            session_news=trace("session_news"),
            risk=trace("risk"),
            position_capacity=trace("position"),
            order_lifecycle=trace("lifecycle"),
            controller=trace("controller"),
            execution_checks=trace("execution"),
        )
    )


def _controller(clock: list[datetime]):
    store = InMemoryCoordinationStore(lambda: clock[0])
    controller_id = new_controller_id()
    manager = ControllerLeaseManager(store, "123456:XAUUSDm", controller_id)
    status = manager.acquire()
    assert status.decision is HardDecision.PASS and status.lease is not None
    return store, manager, controller_id, status.lease.epoch


def _intent(controller_id, epoch: int, *, action: ExecutionAction = ExecutionAction.OPEN):
    position_ticket = 9001 if action in {ExecutionAction.MODIFY, ExecutionAction.CLOSE} else None
    return ExecutionIntent(
        intent_id=new_execution_intent_id(),
        action=action,
        account_login=123456,
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
        created_at_utc=NOW,
        position_ticket=position_ticket,
        filling_mode=1 if action in {ExecutionAction.OPEN, ExecutionAction.CLOSE} else None,
    )


def _service(tmp_path, fake: FakeMT5, controller: ControllerLeaseManager):
    repository = ExecutionIntentRepository(StateStore(tmp_path / "state.db"), "scope")
    writer = MT5Writer(fake, WRITE_CONFIG)
    reconciler = MT5Reconciler(fake, WRITE_CONFIG)
    service = ExecutionService(repository, writer, controller, reconciler)
    return repository, writer, reconciler, service


def test_gate_requires_every_hard_authority_without_weighting() -> None:
    permission = _all_pass_permission()
    assert permission.allowed

    pass_trace = AuthorityTrace("pass", HardDecision.PASS, "PASS")
    blocked = evaluate_execution_permission(
        GateInputs(
            demo_guard=pass_trace,
            account_identity=AuthorityTrace("account", HardDecision.BLOCK, "ACCOUNT_MISMATCH"),
            market_data_quote=pass_trace,
            session_news=AuthorityTrace("news", HardDecision.UNKNOWN, "NEWS_UNKNOWN"),
            risk=pass_trace,
            position_capacity=pass_trace,
            order_lifecycle=pass_trace,
            controller=pass_trace,
            execution_checks=pass_trace,
        )
    )
    assert blocked.decision is HardDecision.BLOCK
    assert blocked.primary_reason == "ACCOUNT_MISMATCH"
    assert "NEWS_UNKNOWN" in blocked.secondary_reasons


def test_elevated_spread_and_drift_pass_after_full_revalidation() -> None:
    plan = _plan()
    spread_elevated = evaluate_execution_checks(
        plan,
        _quote(bid=99.65, ask=100.0),
        healthy_spread_baseline=0.20,
        quote_fresh=True,
        full_revalidation_passed=True,
    )
    drift_elevated = evaluate_execution_checks(
        plan,
        _quote(bid=101.3, ask=101.5),
        healthy_spread_baseline=0.20,
        quote_fresh=True,
        full_revalidation_passed=True,
    )

    assert spread_elevated.decision is HardDecision.PASS
    assert spread_elevated.elevated
    assert drift_elevated.decision is HardDecision.PASS
    assert drift_elevated.elevated


def test_execution_hard_spread_and_drift_limits_block_current_intent() -> None:
    plan = _plan()
    geometry_spread = evaluate_execution_checks(
        plan,
        _quote(bid=97.4, ask=100.0),
        healthy_spread_baseline=2.0,
        quote_fresh=True,
        full_revalidation_passed=True,
    )
    drift = evaluate_execution_checks(
        plan,
        _quote(bid=101.9, ask=102.1),
        healthy_spread_baseline=0.20,
        quote_fresh=True,
        full_revalidation_passed=True,
    )

    assert geometry_spread.decision is HardDecision.BLOCK
    assert geometry_spread.reason == "SPREAD_TOO_HIGH"
    assert drift.decision is HardDecision.BLOCK
    assert drift.reason == "PRICE_DRIFT"


def test_two_controllers_have_one_winner_and_takeover_gets_new_epoch() -> None:
    clock = [NOW]
    store = InMemoryCoordinationStore(lambda: clock[0])
    first = ControllerLeaseManager(store, "scope", new_controller_id())
    second = ControllerLeaseManager(store, "scope", new_controller_id())

    first_status = first.acquire()
    assert first_status.decision is HardDecision.PASS
    assert second.acquire().reason == "ANOTHER_ACTIVE_CONTROLLER"

    first_epoch = first_status.lease.epoch
    clock[0] += timedelta(seconds=31)
    second_status = second.acquire()
    assert second_status.decision is HardDecision.PASS
    assert second_status.lease.epoch > first_epoch
    assert first.verify_write_authority(clock[0]).reason == "ANOTHER_ACTIVE_CONTROLLER"


def test_precheck_reject_causes_zero_order_send_attempts(tmp_path) -> None:
    clock = [NOW]
    _, controller, controller_id, epoch = _controller(clock)
    fake = FakeMT5()
    fake.check_retcode = 10013
    fake.check_comment = "Invalid request"
    _, _, _, service = _service(tmp_path, fake, controller)

    result = service.execute(_intent(controller_id, epoch), _all_pass_permission(), _quote(), NOW)

    assert result.state is IntentState.FAILED
    assert result.submit_attempts == 0
    assert fake.send_calls == 0


def test_success_retcode_without_broker_evidence_stays_unknown(tmp_path) -> None:
    clock = [NOW]
    _, controller, controller_id, epoch = _controller(clock)
    fake = FakeMT5()
    repository, _, _, service = _service(tmp_path, fake, controller)
    intent = _intent(controller_id, epoch)

    result = service.execute(intent, _all_pass_permission(), _quote(), NOW)

    assert result.state is IntentState.ACCEPTED_UNKNOWN
    assert result.submit_attempts == 1
    assert result.broker_ticket == 777
    assert fake.send_calls == 1
    assert repository.load() == result


def test_success_is_verified_only_after_matching_broker_truth(tmp_path) -> None:
    clock = [NOW]
    _, controller, controller_id, epoch = _controller(clock)
    fake = FakeMT5()
    repository, writer, _, service = _service(tmp_path, fake, controller)
    intent = _intent(controller_id, epoch)
    fake.positions = (
        SimpleNamespace(
            ticket=555,
            symbol=SYMBOL,
            magic=WRITE_CONFIG.magic,
            comment=writer.intent_comment(intent),
            volume=0.01,
            type=fake.POSITION_TYPE_BUY,
        ),
    )

    result = service.execute(intent, _all_pass_permission(), _quote(), NOW)

    assert result.state is IntentState.ACCEPTED_VERIFIED
    assert result.submit_attempts == 1
    assert result.broker_ticket == 555
    assert fake.send_calls == 1
    assert repository.load() == result


def test_reused_intent_id_can_never_send_again(tmp_path) -> None:
    clock = [NOW]
    _, controller, controller_id, epoch = _controller(clock)
    fake = FakeMT5()
    repository, writer, _, service = _service(tmp_path, fake, controller)
    intent = _intent(controller_id, epoch)
    fake.positions = (
        SimpleNamespace(
            ticket=555,
            symbol=SYMBOL,
            magic=WRITE_CONFIG.magic,
            comment=writer.intent_comment(intent),
            volume=0.01,
            type=fake.POSITION_TYPE_BUY,
        ),
    )
    assert service.execute(intent, _all_pass_permission(), _quote(), NOW).state is IntentState.ACCEPTED_VERIFIED

    with pytest.raises(PermissionError, match="already been used"):
        service.execute(intent, _all_pass_permission(), _quote(), NOW)
    assert fake.send_calls == 1
    assert repository.intent_id_seen(intent.intent_id)


def test_ambiguous_ack_is_persisted_and_never_blind_retried(tmp_path) -> None:
    clock = [NOW]
    _, controller, controller_id, epoch = _controller(clock)
    fake = FakeMT5()
    fake.send_result = None
    _, _, _, service = _service(tmp_path, fake, controller)
    intent = _intent(controller_id, epoch)

    result = service.execute(intent, _all_pass_permission(), _quote(), NOW)
    assert result.state is IntentState.ACCEPTED_UNKNOWN
    assert result.submit_attempts == 1
    assert fake.send_calls == 1

    fresh = _intent(controller_id, epoch)
    with pytest.raises(PermissionError, match="lifecycle is not clear"):
        service.execute(fresh, _all_pass_permission(), _quote(), NOW)
    assert fake.send_calls == 1


def test_stale_fencing_epoch_blocks_before_order_send(tmp_path) -> None:
    clock = [NOW]
    _, controller, controller_id, epoch = _controller(clock)
    fake = FakeMT5()
    _, _, _, service = _service(tmp_path, fake, controller)

    result = service.execute(
        _intent(controller_id, epoch + 1),
        _all_pass_permission(),
        _quote(),
        NOW,
    )

    assert result.state is IntentState.FAILED
    assert result.submit_attempts == 0
    assert "fencing epoch" in (result.result_message or "")
    assert fake.send_calls == 0


def test_open_unknown_reconciles_from_tagged_position_later(tmp_path) -> None:
    clock = [NOW]
    _, controller, controller_id, epoch = _controller(clock)
    fake = FakeMT5()
    fake.send_result = None
    repository, writer, reconciler, service = _service(tmp_path, fake, controller)
    intent = _intent(controller_id, epoch)
    unknown = service.execute(intent, _all_pass_permission(), _quote(), NOW)

    fake.positions = (
        SimpleNamespace(
            ticket=555,
            symbol=SYMBOL,
            magic=WRITE_CONFIG.magic,
            comment=writer.intent_comment(intent),
            volume=0.01,
            type=fake.POSITION_TYPE_BUY,
        ),
    )
    evidence = reconciler.reconcile(unknown, NOW + timedelta(minutes=1))
    resolved = reconciler.apply(repository, unknown, evidence)

    assert evidence.status is ReconciliationStatus.VERIFIED_ACCEPTED
    assert resolved.state is IntentState.ACCEPTED_VERIFIED
    assert resolved.broker_ticket == 555


def test_complete_broker_truth_can_prove_unknown_open_not_created(tmp_path) -> None:
    clock = [NOW]
    _, controller, controller_id, epoch = _controller(clock)
    fake = FakeMT5()
    fake.send_result = None
    repository, _, reconciler, service = _service(tmp_path, fake, controller)
    unknown = service.execute(
        _intent(controller_id, epoch),
        _all_pass_permission(),
        _quote(),
        NOW,
    )

    evidence = reconciler.reconcile(
        unknown,
        NOW + timedelta(minutes=2),
        allow_verified_not_created=True,
    )
    resolved = reconciler.apply(repository, unknown, evidence)

    assert evidence.status is ReconciliationStatus.VERIFIED_NOT_CREATED
    assert resolved.state is IntentState.FAILED
    assert resolved.submit_attempts == 1


def test_modify_reconciliation_uses_actual_position_levels(tmp_path) -> None:
    controller_id = new_controller_id()
    intent = replace(
        _intent(controller_id, 1, action=ExecutionAction.MODIFY),
        state=IntentState.ACCEPTED_UNKNOWN,
        submit_attempts=1,
    )
    fake = FakeMT5()
    fake.positions = (
        SimpleNamespace(ticket=9001, symbol=SYMBOL, sl=90.0, tp=125.0, comment="old-open"),
    )
    repository = ExecutionIntentRepository(StateStore(tmp_path / "state.db"), "scope")
    repository.save(intent)
    reconciler = MT5Reconciler(fake, WRITE_CONFIG)

    evidence = reconciler.reconcile(intent, NOW + timedelta(minutes=1))
    resolved = reconciler.apply(repository, intent, evidence)

    assert evidence.status is ReconciliationStatus.VERIFIED_ACCEPTED
    assert resolved.state is IntentState.ACCEPTED_VERIFIED


def test_close_request_uses_opposite_side_and_position_ticket() -> None:
    fake = FakeMT5()
    writer = MT5Writer(fake, WRITE_CONFIG)
    intent = _intent(new_controller_id(), 1, action=ExecutionAction.CLOSE)
    request = writer.build_request(intent, _quote())

    assert request["type"] == fake.ORDER_TYPE_SELL
    assert request["price"] == pytest.approx(99.8)
    assert request["position"] == 9001


def test_raw_order_send_is_confined_to_mt5_writer() -> None:
    root = Path("src/goldswingtraderai")
    offenders = []
    for path in root.rglob("*.py"):
        if path.name == "mt5_writer.py":
            continue
        if "order_send(" in path.read_text(encoding="utf-8"):
            offenders.append(str(path))
    assert offenders == []
