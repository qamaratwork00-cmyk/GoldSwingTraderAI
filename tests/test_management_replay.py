from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

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
    StrategyFamily,
    Timeframe,
    TradeManagerAction,
)
from goldswingtraderai.domain.ids import (
    new_episode_id,
    new_opportunity_id,
    new_trade_plan_id,
)
from goldswingtraderai.domain.market import AccountFacts, Candle, CandleSeries, SymbolSpec
from goldswingtraderai.management.models import managed_trade_from_fill
from goldswingtraderai.research.management_replay import (
    ActiveBarrierTouch,
    ManagementOutcome,
    ManagementReplayRecord,
    evaluate_active_barriers,
    run_trade_manager_replay,
    summarize_management_replay,
)
from goldswingtraderai.research.replay import ReplayDataset, run_decision_replay


NOW = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
END = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
_PERIODS = {
    Timeframe.H4: timedelta(hours=4),
    Timeframe.H1: timedelta(hours=1),
    Timeframe.M15: timedelta(minutes=15),
    Timeframe.M5: timedelta(minutes=5),
}
_MINIMUM_BARS = {
    Timeframe.H4: 50,
    Timeframe.H1: 55,
    Timeframe.M15: 60,
    Timeframe.M5: 70,
}


def _plan(direction: Direction = Direction.BUY) -> TradePlan:
    entry = 100.0
    stop = 99.0 if direction is Direction.BUY else 101.0
    target_price = 102.0 if direction is Direction.BUY else 98.0
    target = PlanTarget(
        role=TargetRole.EXPANSION,
        price=target_price,
        quality=80.0,
        source="TEST_TARGET",
        rr=2.0,
    )
    return TradePlan(
        plan_id=new_trade_plan_id(),
        opportunity_id=new_opportunity_id(),
        episode_id=new_episode_id(),
        family=StrategyFamily.TREND_PULLBACK_CONTINUATION,
        direction=direction,
        state=PlanState.READY,
        signal_price=100.0,
        approved_entry_reference=entry,
        invalidation_level=99.2 if direction is Direction.BUY else 100.8,
        invalidation_source="TEST_STRUCTURE",
        initial_stop=stop,
        stop_buffer=0.2,
        stop_quality=StopQuality.ACCEPTABLE,
        original_r_price=1.0,
        immediate_obstacle=None,
        primary_target=target,
        expansion_target=target,
        runner_target=None,
        broker_tp_target=target,
        rr_class=RRClass.STRONG,
        path_quality=80.0,
        plan_quality=80.0,
        created_at_utc=NOW,
        reason="PLAN_READY",
    )


def _trade(direction: Direction = Direction.BUY):
    return managed_trade_from_fill(
        _plan(direction),
        position_ticket=1,
        volume=0.01,
        fill_price=100.0,
        opened_at_utc=NOW,
        symbol="XAUUSDm",
    )


def _candle(*, high: float, low: float, close: float) -> Candle:
    return Candle(
        time_utc=NOW,
        open=close,
        high=high,
        low=low,
        close=close,
        tick_volume=100,
    )


def test_active_barrier_uses_current_trailing_stop_r() -> None:
    trade = replace(_trade(Direction.BUY), current_stop=100.5)
    result = evaluate_active_barriers(
        trade,
        _candle(high=101.4, low=100.4, close=101.0),
    )

    assert result.touch is ActiveBarrierTouch.STOP
    assert result.realized_r == pytest.approx(0.5)


def test_active_stop_and_target_same_bar_remains_ambiguous() -> None:
    result = evaluate_active_barriers(
        _trade(Direction.BUY),
        _candle(high=102.2, low=98.8, close=100.5),
    )

    assert result.touch is ActiveBarrierTouch.BOTH_AMBIGUOUS
    assert result.realized_r is None


def test_management_summary_excludes_open_and_ambiguous_from_net_r() -> None:
    records = (
        ManagementReplayRecord(
            as_of_utc=NOW,
            direction=Direction.BUY,
            plan_state=PlanState.READY,
            plan_reason="PLAN_READY",
            outcome=ManagementOutcome.TARGET_FILLED,
            bars_observed=3,
            realized_r=2.0,
            mfe_r=2.2,
            mae_r=0.3,
            final_r=2.0,
            action_history=(TradeManagerAction.HOLD, TradeManagerAction.TRAIL),
            final_stop=100.5,
            final_tp=102.0,
            exit_reason="ACTIVE_BROKER_TP_TOUCHED",
        ),
        ManagementReplayRecord(
            as_of_utc=NOW,
            direction=Direction.BUY,
            plan_state=PlanState.READY,
            plan_reason="PLAN_READY",
            outcome=ManagementOutcome.STOP_FILLED,
            bars_observed=2,
            realized_r=-1.0,
            mfe_r=0.5,
            mae_r=1.1,
            final_r=-1.0,
            action_history=(TradeManagerAction.HOLD,),
            final_stop=99.0,
            final_tp=102.0,
            exit_reason="ACTIVE_STOP_TOUCHED",
        ),
        ManagementReplayRecord(
            as_of_utc=NOW,
            direction=Direction.BUY,
            plan_state=PlanState.READY,
            plan_reason="PLAN_READY",
            outcome=ManagementOutcome.BOTH_TOUCHED_AMBIGUOUS,
            bars_observed=1,
            realized_r=None,
            mfe_r=2.3,
            mae_r=1.2,
            final_r=0.2,
            action_history=(),
            final_stop=99.0,
            final_tp=102.0,
            exit_reason="ACTIVE_STOP_AND_TP_TOUCHED_SAME_M5",
        ),
        ManagementReplayRecord(
            as_of_utc=NOW,
            direction=Direction.BUY,
            plan_state=PlanState.READY,
            plan_reason="PLAN_READY",
            outcome=ManagementOutcome.HORIZON_OPEN,
            bars_observed=20,
            realized_r=None,
            mfe_r=1.5,
            mae_r=0.6,
            final_r=0.8,
            action_history=(TradeManagerAction.PROTECT,),
            final_stop=100.1,
            final_tp=102.0,
            exit_reason="MANAGEMENT_HORIZON_ENDED_OPEN",
        ),
    )

    metrics = summarize_management_replay(records)

    assert metrics.managed_trades == 4
    assert metrics.target_exits == 1
    assert metrics.stop_exits == 1
    assert metrics.ambiguous == 1
    assert metrics.horizon_open == 1
    assert metrics.resolved_coverage == pytest.approx(0.5)
    assert metrics.resolved_net_r == pytest.approx(1.0)
    assert metrics.resolved_average_r == pytest.approx(0.5)
    assert metrics.resolved_profit_factor == pytest.approx(2.0)
    assert metrics.hold_actions == 2
    assert metrics.protect_actions == 1
    assert metrics.trail_actions == 1


def _series(timeframe: Timeframe, count: int) -> CandleSeries:
    period = _PERIODS[timeframe]
    start = END - period * count
    candles = []
    for index in range(count):
        wave = (index % 12) - 6
        close = 2300.0 + index * 0.35 + wave * 0.18
        open_price = close - (0.22 if index % 3 else -0.12)
        candles.append(
            Candle(
                time_utc=start + period * index,
                open=open_price,
                high=max(open_price, close) + 0.55,
                low=min(open_price, close) - 0.55,
                close=close,
                tick_volume=200 + (index % 17) * 9,
            )
        )
    return CandleSeries(timeframe=timeframe, candles=tuple(candles))


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
        series=(
            _series(Timeframe.H4, 70),
            _series(Timeframe.H1, 90),
            _series(Timeframe.M15, 120),
            _series(Timeframe.M5, 150),
        ),
        spread_price=0.20,
    )


def test_manager_replay_composes_with_real_decision_replay() -> None:
    dataset = _dataset()
    run = run_decision_replay(
        dataset,
        start_utc=END - timedelta(minutes=45),
        end_utc=END,
        minimum_bars=_MINIMUM_BARS,
    )
    records = run_trade_manager_replay(
        dataset,
        run,
        horizon_m5_bars=12,
        minimum_bars=_MINIMUM_BARS,
    )
    expected_enter = sum(
        item.decision.timing is not None
        and item.decision.timing.action
        in {TimingAction.ENTER_BUY, TimingAction.ENTER_SELL}
        for item in run.decisions
    )

    assert len(records) == expected_enter
    metrics = summarize_management_replay(records)
    assert metrics.enter_signals == expected_enter
    assert metrics.plan_not_ready + metrics.managed_trades == expected_enter
