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
from goldswingtraderai.domain.enums import Direction, StrategyFamily
from goldswingtraderai.domain.ids import (
    new_episode_id,
    new_opportunity_id,
    new_trade_plan_id,
)
from goldswingtraderai.domain.market import Candle
from goldswingtraderai.research.outcomes import (
    BarrierOutcome,
    EnterPlanOutcomeRecord,
    PlanPathOutcome,
    evaluate_plan_path,
    summarize_enter_plan_outcomes,
)


NOW = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)


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


def _bar(index: int, *, high: float, low: float, close: float) -> Candle:
    return Candle(
        time_utc=NOW + timedelta(minutes=5 * index),
        open=close,
        high=high,
        low=low,
        close=close,
        tick_volume=100,
    )


def test_buy_plan_target_first_tracks_r_excursions() -> None:
    outcome = evaluate_plan_path(
        _plan(Direction.BUY),
        (
            _bar(0, high=101.4, low=99.6, close=101.0),
            _bar(1, high=102.2, low=100.5, close=102.0),
        ),
    )

    assert outcome.outcome is BarrierOutcome.TARGET_FIRST
    assert outcome.bars_observed == 2
    assert outcome.realized_r == pytest.approx(2.0)
    assert outcome.mfe_r == pytest.approx(2.2)
    assert outcome.mae_r == pytest.approx(0.4)
    assert outcome.reached_2r is True
    assert outcome.reached_3r is False


def test_sell_plan_stop_first_is_symmetric() -> None:
    outcome = evaluate_plan_path(
        _plan(Direction.SELL),
        (
            _bar(0, high=100.6, low=99.0, close=99.4),
            _bar(1, high=101.2, low=99.2, close=100.8),
        ),
    )

    assert outcome.outcome is BarrierOutcome.STOP_FIRST
    assert outcome.bars_observed == 2
    assert outcome.realized_r == pytest.approx(-1.0)
    assert outcome.mfe_r == pytest.approx(1.0)
    assert outcome.mae_r == pytest.approx(1.2)


def test_same_bar_stop_and_target_is_ambiguous_not_favorably_guessed() -> None:
    outcome = evaluate_plan_path(
        _plan(Direction.BUY),
        (_bar(0, high=102.3, low=98.7, close=100.5),),
    )

    assert outcome.outcome is BarrierOutcome.BOTH_TOUCHED_AMBIGUOUS
    assert outcome.realized_r is None
    assert outcome.mfe_r == pytest.approx(2.3)
    assert outcome.mae_r == pytest.approx(1.3)


def test_empty_future_path_remains_unresolved() -> None:
    outcome = evaluate_plan_path(_plan(Direction.BUY), ())

    assert outcome.outcome is BarrierOutcome.HORIZON_UNRESOLVED
    assert outcome.bars_observed == 0
    assert outcome.realized_r is None


def test_summary_keeps_ambiguous_and_unresolved_out_of_resolved_net_r() -> None:
    def record(path: PlanPathOutcome) -> EnterPlanOutcomeRecord:
        return EnterPlanOutcomeRecord(
            as_of_utc=NOW,
            direction=Direction.BUY,
            plan_state=PlanState.READY,
            plan_reason="PLAN_READY",
            target_rr=2.0,
            path=path,
        )

    records = (
        record(
            PlanPathOutcome(
                outcome=BarrierOutcome.TARGET_FIRST,
                bars_observed=2,
                mfe_r=2.2,
                mae_r=0.4,
                end_r=2.0,
                realized_r=2.0,
                reached_2r=True,
                reached_3r=False,
                reached_4r=False,
            )
        ),
        record(
            PlanPathOutcome(
                outcome=BarrierOutcome.STOP_FIRST,
                bars_observed=1,
                mfe_r=0.3,
                mae_r=1.1,
                end_r=-1.0,
                realized_r=-1.0,
                reached_2r=False,
                reached_3r=False,
                reached_4r=False,
            )
        ),
        record(
            PlanPathOutcome(
                outcome=BarrierOutcome.BOTH_TOUCHED_AMBIGUOUS,
                bars_observed=1,
                mfe_r=2.3,
                mae_r=1.3,
                end_r=0.2,
                realized_r=None,
                reached_2r=True,
                reached_3r=False,
                reached_4r=False,
            )
        ),
        record(
            PlanPathOutcome(
                outcome=BarrierOutcome.HORIZON_UNRESOLVED,
                bars_observed=48,
                mfe_r=1.8,
                mae_r=0.8,
                end_r=0.6,
                realized_r=None,
                reached_2r=False,
                reached_3r=False,
                reached_4r=False,
            )
        ),
    )

    metrics = summarize_enter_plan_outcomes(records)

    assert metrics.enter_signals == 4
    assert metrics.ready_plans == 4
    assert metrics.target_first == 1
    assert metrics.stop_first == 1
    assert metrics.ambiguous == 1
    assert metrics.unresolved == 1
    assert metrics.resolved_coverage == pytest.approx(0.5)
    assert metrics.resolved_target_rate == pytest.approx(0.5)
    assert metrics.resolved_bracket_net_r == pytest.approx(1.0)
    assert metrics.resolved_bracket_average_r == pytest.approx(0.5)
    assert metrics.resolved_bracket_profit_factor == pytest.approx(2.0)
    assert metrics.resolved_bracket_max_drawdown_r == pytest.approx(1.0)
