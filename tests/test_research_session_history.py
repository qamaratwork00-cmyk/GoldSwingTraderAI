from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from goldswingtraderai.decisions.timing import TimingAction
from goldswingtraderai.decisions.trade_plan import (
    PlanState,
    PlanTarget,
    RRClass,
    StopQuality,
    TargetRole,
    TradePlan,
)
from goldswingtraderai.domain.enums import (
    AccountMode,
    Direction,
    MarketState,
    StrategyFamily,
    Timeframe,
)
from goldswingtraderai.domain.ids import (
    new_episode_id,
    new_opportunity_id,
    new_trade_plan_id,
)
from goldswingtraderai.domain.market import AccountFacts, Candle, CandleSeries, SymbolSpec
from goldswingtraderai.research.management_replay import (
    ManagementOutcome,
    run_trade_manager_replay,
    summarize_management_replay,
)
from goldswingtraderai.research.replay import ReplayDataset
from goldswingtraderai.research.session_history import (
    HistoricalSessionCoverageError,
    HistoricalSessionSchedule,
    HistoricalTradingInterval,
)
from goldswingtraderai.risk.permissions import ClosureKind


DAY = datetime(2026, 9, 18, 0, 0, tzinfo=timezone.utc)
AS_OF = DAY + timedelta(minutes=110)
_PERIODS = {
    Timeframe.H4: timedelta(hours=4),
    Timeframe.H1: timedelta(hours=1),
    Timeframe.M15: timedelta(minutes=15),
    Timeframe.M5: timedelta(minutes=5),
}


def _schedule(kind: ClosureKind, close_minute: int = 120) -> HistoricalSessionSchedule:
    return HistoricalSessionSchedule(
        source_label="verified-broker-schedule",
        source_version="2026-09-v1",
        coverage_start_utc=DAY,
        coverage_end_utc=DAY + timedelta(hours=4),
        intervals=(
            HistoricalTradingInterval(
                open_utc=DAY,
                close_utc=DAY + timedelta(minutes=close_minute),
                closure_kind=kind,
            ),
        ),
    )


def test_daily_schedule_reuses_frozen_preclose_thresholds() -> None:
    schedule = _schedule(ClosureKind.DAILY)
    no_entry = schedule.market_permission_at(DAY + timedelta(minutes=105))  # T-15
    flatten = schedule.market_permission_at(DAY + timedelta(minutes=115))  # T-5

    assert no_entry.state is MarketState.PRE_CLOSE
    assert not no_entry.new_entries_allowed
    assert not no_entry.flatten_required
    assert flatten.state is MarketState.PRE_CLOSE
    assert flatten.flatten_required


def test_weekend_schedule_reuses_wider_frozen_thresholds() -> None:
    schedule = _schedule(ClosureKind.WEEKEND)
    no_entry = schedule.market_permission_at(DAY + timedelta(minutes=75))  # T-45
    flatten = schedule.market_permission_at(DAY + timedelta(minutes=105))  # T-15

    assert no_entry.state is MarketState.PRE_CLOSE
    assert not no_entry.flatten_required
    assert flatten.flatten_required


def test_time_outside_tradeable_interval_is_closed_within_verified_coverage() -> None:
    schedule = _schedule(ClosureKind.DAILY)
    permission = schedule.market_permission_at(DAY + timedelta(minutes=150))

    assert permission.state is MarketState.CLOSED
    assert not permission.new_entries_allowed
    assert not permission.flatten_required
    with pytest.raises(HistoricalSessionCoverageError, match="outside declared tradeable"):
        schedule.flatten_required_at(DAY + timedelta(minutes=150))


def test_schedule_refuses_unverified_time_outside_coverage() -> None:
    with pytest.raises(HistoricalSessionCoverageError):
        _schedule(ClosureKind.DAILY).market_permission_at(DAY - timedelta(minutes=1))


def test_schedule_rejects_overlapping_intervals() -> None:
    with pytest.raises(ValueError, match="cannot overlap"):
        HistoricalSessionSchedule(
            source_label="verified",
            source_version="v1",
            coverage_start_utc=DAY,
            coverage_end_utc=DAY + timedelta(hours=4),
            intervals=(
                HistoricalTradingInterval(
                    open_utc=DAY,
                    close_utc=DAY + timedelta(hours=2),
                    closure_kind=ClosureKind.DAILY,
                ),
                HistoricalTradingInterval(
                    open_utc=DAY + timedelta(hours=1),
                    close_utc=DAY + timedelta(hours=3),
                    closure_kind=ClosureKind.DAILY,
                ),
            ),
        )


def _series(timeframe: Timeframe, count: int = 120) -> CandleSeries:
    period = _PERIODS[timeframe]
    start = AS_OF - period * (count - 1)
    candles = tuple(
        Candle(
            time_utc=start + period * index,
            open=100.0,
            high=100.2,
            low=99.8,
            close=100.0,
            tick_volume=200,
            spread_points=20,
        )
        for index in range(count)
    )
    return CandleSeries(timeframe=timeframe, candles=candles)


def _dataset() -> ReplayDataset:
    return ReplayDataset(
        account=AccountFacts(
            login=123456,
            server="Demo-Server",
            currency="USD",
            mode=AccountMode.DEMO,
            balance=100.0,
            equity=100.0,
            margin=0.0,
            margin_free=100.0,
            leverage=500,
        ),
        symbol_spec=SymbolSpec(
            symbol="XAUUSDm",
            digits=3,
            point=0.001,
            tick_size=0.001,
            tick_value=0.01,
            contract_size=100.0,
            volume_min=0.01,
            volume_max=200.0,
            volume_step=0.01,
            stops_level_points=0,
            freeze_level_points=0,
        ),
        series=tuple(_series(frame) for frame in _PERIODS),
        spread_price=0.20,
    )


def _ready_plan() -> TradePlan:
    primary = PlanTarget(
        role=TargetRole.PRIMARY,
        price=105.0,
        quality=80.0,
        source="TEST_PRIMARY",
        rr=1.0,
    )
    expansion = PlanTarget(
        role=TargetRole.EXPANSION,
        price=110.0,
        quality=80.0,
        source="TEST_EXPANSION",
        rr=2.0,
    )
    return TradePlan(
        plan_id=new_trade_plan_id(),
        opportunity_id=new_opportunity_id(),
        episode_id=new_episode_id(),
        family=StrategyFamily.TREND_PULLBACK_CONTINUATION,
        direction=Direction.BUY,
        state=PlanState.READY,
        signal_price=100.0,
        approved_entry_reference=100.0,
        invalidation_level=95.5,
        invalidation_source="TEST_STRUCTURE",
        initial_stop=95.0,
        stop_buffer=0.5,
        stop_quality=StopQuality.ACCEPTABLE,
        original_r_price=5.0,
        immediate_obstacle=None,
        primary_target=primary,
        expansion_target=expansion,
        runner_target=None,
        broker_tp_target=expansion,
        rr_class=RRClass.STRONG,
        path_quality=80.0,
        plan_quality=80.0,
        created_at_utc=AS_OF,
        reason="PLAN_READY",
    )


def test_manager_replay_uses_verified_schedule_to_force_preclose_exit(monkeypatch) -> None:
    import goldswingtraderai.research.management_replay as replay_module

    monkeypatch.setattr(
        replay_module,
        "build_historical_trade_plan",
        lambda *args, **kwargs: _ready_plan(),
    )
    replay_decision = SimpleNamespace(
        as_of_utc=AS_OF,
        decision=SimpleNamespace(timing=SimpleNamespace(action=TimingAction.ENTER_BUY)),
    )
    run = SimpleNamespace(decisions=(replay_decision,))

    records = run_trade_manager_replay(
        _dataset(),
        run,
        horizon_m5_bars=1,
        session_schedule=_schedule(ClosureKind.DAILY),
    )

    assert len(records) == 1
    assert records[0].outcome is ManagementOutcome.MANAGER_EXIT
    assert records[0].exit_reason == "PRE_CLOSE_FLATTEN"
    assert summarize_management_replay(records).pre_close_exits == 1
