from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from goldswingtraderai.decisions.opportunity import Opportunity
from goldswingtraderai.decisions.trade_plan import (
    PlanState,
    RRClass,
    StopQuality,
    TargetRole,
    build_trade_plan,
)
from goldswingtraderai.domain.enums import (
    AccountMode,
    CandleSequenceState,
    DataQuality,
    Direction,
    ExtensionState,
    MomentumPhase,
    OpportunityStage,
    StrategyFamily,
    StructureState,
    SwingRole,
    SwingSide,
    Timeframe,
    VolatilityState,
)
from goldswingtraderai.domain.ids import new_episode_id, new_opportunity_id, new_snapshot_id
from goldswingtraderai.domain.market import (
    AccountFacts,
    Candle,
    CandleSeries,
    MarketSnapshot,
    Quote,
    SymbolSpec,
)
from goldswingtraderai.domain.models import MarketSnapshotMeta
from goldswingtraderai.intelligence.candle_structure import CandleFacts, StructureReport, SwingPoint
from goldswingtraderai.intelligence.indicators import QuantReport
from goldswingtraderai.intelligence.liquidity import LiquidityPath, LiquidityReport
from goldswingtraderai.intelligence.session import SessionName, SessionReport
from goldswingtraderai.intelligence.snapshot import IntelligenceSnapshot, TimeframeIntelligence
from goldswingtraderai.intelligence.technical import LocationCategory, TechnicalReport
from goldswingtraderai.risk import (
    ClosedTradeOutcome,
    CooldownDecision,
    CooldownState,
    EpisodeRiskState,
    RiskBand,
    RiskContext,
    cooldown_decision,
    evaluate_risk,
    manual_reset_loss_lock,
    new_risk_day,
    record_closed_trade,
    record_episode_loss,
    record_non_trading_cash_flow,
    register_episode_entry,
    risk_day_metrics,
)


NOW = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
TIMEFRAMES = (Timeframe.H4, Timeframe.H1, Timeframe.M15, Timeframe.M5)


def _market(*, equity: float = 100.0, tick_value: float = 8.0) -> MarketSnapshot:
    candle = Candle(
        time_utc=NOW - timedelta(minutes=5),
        open=99.5,
        high=101.0,
        low=99.0,
        close=100.0,
        tick_volume=100,
    )
    series = tuple(CandleSeries(timeframe=tf, candles=(candle,)) for tf in TIMEFRAMES)
    return MarketSnapshot(
        meta=MarketSnapshotMeta(
            snapshot_id=new_snapshot_id(),
            symbol="XAUUSDm",
            as_of_utc=NOW,
            timeframes=TIMEFRAMES,
            data_complete=True,
        ),
        account=AccountFacts(
            login=123456,
            server="Broker-Demo",
            currency="USD",
            mode=AccountMode.DEMO,
            balance=100.0,
            equity=equity,
            margin=0.0,
            margin_free=max(1.0, equity),
            leverage=500,
        ),
        symbol_spec=SymbolSpec(
            symbol="XAUUSDm",
            digits=1,
            point=0.1,
            tick_size=0.1,
            tick_value=tick_value,
            contract_size=100.0,
            volume_min=0.01,
            volume_max=200.0,
            volume_step=0.01,
            stops_level_points=0,
            freeze_level_points=0,
        ),
        quote=Quote(symbol="XAUUSDm", bid=100.0, ask=100.2, time_utc=NOW),
        series=series,
        quality=DataQuality.HEALTHY,
    )


def _frame(
    timeframe: Timeframe,
    direction: Direction,
    *,
    target_price: float,
    target_significance: float,
    protected_price: float,
) -> TimeframeIntelligence:
    swing_side = SwingSide.HIGH if direction is Direction.BUY else SwingSide.LOW
    protected_side = SwingSide.LOW if direction is Direction.BUY else SwingSide.HIGH
    protected = SwingPoint(
        side=protected_side,
        price=protected_price,
        pivot_time=NOW - timedelta(hours=2),
        confirmed_at=NOW - timedelta(hours=1),
        role=SwingRole.PROTECTED,
        significance_atr=1.5,
    )
    target = SwingPoint(
        side=swing_side,
        price=target_price,
        pivot_time=NOW - timedelta(hours=1),
        confirmed_at=NOW - timedelta(minutes=30),
        role=SwingRole.CONFIRMED,
        significance_atr=target_significance,
    )
    candle_direction = Direction.BUY if direction is Direction.BUY else Direction.SELL
    latest = CandleFacts(
        time_utc=NOW - timedelta(minutes=5),
        direction=candle_direction,
        range_size=2.0,
        body_size=1.0,
        body_ratio=0.5,
        upper_wick=0.5,
        lower_wick=0.5,
        close_position=0.7 if direction is Direction.BUY else 0.3,
        range_atr=0.4,
    )
    state = StructureState.BULLISH if direction is Direction.BUY else StructureState.BEARISH
    sequence = (
        CandleSequenceState.BULL_CONTINUATION
        if direction is Direction.BUY
        else CandleSequenceState.BEAR_CONTINUATION
    )
    structure = StructureReport(
        timeframe=timeframe,
        state=state,
        sequence=sequence,
        latest_candle=latest,
        swings=(protected, target),
        protected_high=protected if protected_side is SwingSide.HIGH else None,
        protected_low=protected if protected_side is SwingSide.LOW else None,
        events=(),
        bull_evidence=80.0 if direction is Direction.BUY else 25.0,
        bear_evidence=80.0 if direction is Direction.SELL else 25.0,
        coverage=1.0,
    )
    quant = QuantReport(
        timeframe=timeframe,
        ema_fast=100.0,
        ema_slow=99.0,
        rsi=60.0 if direction is Direction.BUY else 40.0,
        atr=5.0,
        trend_support=direction,
        volatility_state=VolatilityState.NORMAL,
        volatility_ratio=1.0,
        momentum_phase=MomentumPhase.BUILDING,
        extension_state=ExtensionState.NORMAL,
        extension_atr=0.4,
        coverage=1.0,
    )
    technical = TechnicalReport(
        timeframe=timeframe,
        zones=(),
        nearest_support=None,
        nearest_resistance=None,
        buy_location=LocationCategory.GOOD,
        sell_location=LocationCategory.GOOD,
        buy_target_room=8.0,
        sell_target_room=8.0,
        equilibrium=100.0,
        conflict=False,
        coverage=1.0,
    )
    liquidity = LiquidityReport(
        timeframe=timeframe,
        pools=(),
        events=(),
        fvgs=(),
        order_blocks=(),
        nearest_buy_side=None,
        nearest_sell_side=None,
        path_up=LiquidityPath.OPEN,
        path_down=LiquidityPath.OPEN,
        buy_evidence=60.0,
        sell_evidence=60.0,
        coverage=1.0,
    )
    return TimeframeIntelligence(
        timeframe=timeframe,
        quant=quant,
        structure=structure,
        technical=technical,
        liquidity=liquidity,
    )


def _intelligence(
    direction: Direction = Direction.BUY,
    *,
    primary_price: float | None = None,
    expansion_price: float | None = None,
) -> IntelligenceSnapshot:
    if direction is Direction.BUY:
        prices = {
            Timeframe.M5: (103.0, 0.20, 96.0),
            Timeframe.M15: (primary_price or 109.0, 1.50, 95.0),
            Timeframe.H1: (expansion_price or 113.0, 1.50, 94.0),
            Timeframe.H4: (120.0, 1.50, 90.0),
        }
    else:
        prices = {
            Timeframe.M5: (97.0, 0.20, 104.0),
            Timeframe.M15: (primary_price or 91.0, 1.50, 105.0),
            Timeframe.H1: (expansion_price or 87.0, 1.50, 106.0),
            Timeframe.H4: (80.0, 1.50, 110.0),
        }
    frames = tuple(
        _frame(
            timeframe,
            direction,
            target_price=prices[timeframe][0],
            target_significance=prices[timeframe][1],
            protected_price=prices[timeframe][2],
        )
        for timeframe in TIMEFRAMES
    )
    session = SessionReport(
        current=SessionName.NEW_YORK,
        current_high=101.0,
        current_low=99.0,
        current_range=2.0,
        previous=SessionName.LONDON,
        previous_high=102.0,
        previous_low=98.0,
        overlap=False,
        holiday_context=False,
        coverage=1.0,
    )
    return IntelligenceSnapshot(
        market_snapshot_id=new_snapshot_id(),
        frames=frames,
        session=session,
        news=None,
    )


def _opportunity(direction: Direction = Direction.BUY) -> Opportunity:
    return Opportunity(
        opportunity_id=new_opportunity_id(),
        episode_id=new_episode_id(),
        direction=direction,
        stage=OpportunityStage.READY,
        created_at_utc=NOW - timedelta(minutes=10),
        updated_at_utc=NOW,
        opportunity_score=82.0,
        thesis_score=84.0,
        source_families=(StrategyFamily.TREND_PULLBACK_CONTINUATION,),
    )


def _risk_context(plan, *, day_equity: float = 100.0) -> RiskContext:
    return RiskContext(
        risk_day=new_risk_day(NOW, day_equity),
        cooldown=CooldownDecision.CLEAR,
        episode=EpisodeRiskState(episode_id=plan.episode_id),
        fresh_structural_event=True,
    )


def test_trade_plan_ignores_small_internal_obstacle_as_primary_target() -> None:
    plan = build_trade_plan(_opportunity(), _intelligence(), _market(), NOW)

    assert plan.state is PlanState.READY
    assert plan.stop_quality is StopQuality.ROBUST
    assert plan.immediate_obstacle is not None
    assert plan.immediate_obstacle.role is TargetRole.IMMEDIATE
    assert plan.immediate_obstacle.price == pytest.approx(103.0)
    assert plan.primary_target is not None
    assert plan.primary_target.price == pytest.approx(109.0)
    assert plan.primary_target.rr >= 1.5
    assert plan.rr_class is RRClass.GOOD
    assert plan.expansion_target is not None
    assert plan.broker_tp_target == plan.expansion_target


def test_marginal_rr_can_pass_with_credible_two_r_expansion() -> None:
    intel = _intelligence(primary_price=107.5, expansion_price=112.0)
    plan = build_trade_plan(_opportunity(), intel, _market(), NOW)

    assert plan.primary_target is not None
    assert 1.2 <= plan.primary_target.rr < 1.5
    assert plan.expansion_target is not None
    assert plan.expansion_target.rr >= 2.0
    assert plan.state is PlanState.READY
    assert plan.rr_class is RRClass.MARGINAL


def test_poor_primary_rr_degrades_entry_without_changing_structural_stop() -> None:
    intel = _intelligence(primary_price=106.5, expansion_price=112.0)
    plan = build_trade_plan(_opportunity(), intel, _market(), NOW)

    assert plan.primary_target is not None
    assert plan.primary_target.rr < 1.2
    assert plan.state is PlanState.DEGRADED
    assert plan.reason == "TARGET_ROOM_POOR"
    assert plan.invalidation_level == pytest.approx(95.0)
    assert plan.initial_stop == pytest.approx(94.4)


def test_sell_plan_has_structural_stop_above_and_targets_below() -> None:
    plan = build_trade_plan(
        _opportunity(Direction.SELL),
        _intelligence(Direction.SELL),
        _market(),
        NOW,
    )

    assert plan.state is PlanState.READY
    assert plan.initial_stop > plan.approved_entry_reference
    assert plan.primary_target is not None
    assert plan.primary_target.price < plan.approved_entry_reference
    assert plan.broker_tp_target is not None
    assert plan.broker_tp_target.price < plan.approved_entry_reference


def test_small_account_minimum_lot_can_pass_in_elevated_band() -> None:
    market = _market(equity=100.0, tick_value=8.0)
    plan = build_trade_plan(_opportunity(), _intelligence(), market, NOW)
    result = evaluate_risk(plan, market, _risk_context(plan))

    assert result.passed
    assert result.volume == pytest.approx(0.01)
    assert result.risk_band is RiskBand.ELEVATED
    assert result.all_in_risk_pct is not None
    assert 4.5 < result.all_in_risk_pct <= 6.5


def test_spread_is_diagnostic_not_double_counted_in_all_in_risk() -> None:
    market = _market(equity=100.0, tick_value=8.0)
    plan = build_trade_plan(_opportunity(), _intelligence(), market, NOW)
    result = evaluate_risk(plan, market, _risk_context(plan))

    assert result.structural_risk_money == pytest.approx(4.64)
    assert result.friction_risk_money == pytest.approx(0.16)
    assert result.all_in_risk_money == pytest.approx(4.80)
    assert result.spread_money_diagnostic == pytest.approx(0.16)


def test_minimum_lot_above_hard_ceiling_is_blocked_without_tightening_stop() -> None:
    market = _market(equity=100.0, tick_value=12.0)
    plan = build_trade_plan(_opportunity(), _intelligence(), market, NOW)
    original_stop = plan.initial_stop
    result = evaluate_risk(plan, market, _risk_context(plan))

    assert not result.passed
    assert result.reason == "MIN_LOT_UNAFFORDABLE"
    assert plan.initial_stop == original_stop


def test_plan_quality_does_not_leverage_monetary_risk() -> None:
    market = _market(equity=100.0, tick_value=8.0)
    plan = build_trade_plan(_opportunity(), _intelligence(), market, NOW)
    low_quality = replace(plan, plan_quality=55.0)
    high_quality = replace(plan, plan_quality=99.0)

    low = evaluate_risk(low_quality, market, _risk_context(low_quality))
    high = evaluate_risk(high_quality, market, _risk_context(high_quality))

    assert low.volume == high.volume
    assert low.all_in_risk_pct == high.all_in_risk_pct


def test_daily_loss_lock_uses_day_start_profile_even_after_equity_falls_below_100() -> None:
    market = _market(equity=88.0, tick_value=1.0)
    plan = build_trade_plan(_opportunity(), _intelligence(), market, NOW)
    context = _risk_context(plan, day_equity=100.0)
    result = evaluate_risk(plan, market, context)

    assert result.reason == "DAILY_LOSS_LIMIT_REACHED"
    assert result.day is not None
    assert result.day.cycle_loss_pct == pytest.approx(12.0)


def test_cash_flow_adjustment_and_one_manual_reset_preserve_cumulative_day_pl() -> None:
    state = new_risk_day(NOW, 100.0, manual_reset_enabled=True)
    deposited = record_non_trading_cash_flow(state, 50.0)
    neutral = risk_day_metrics(deposited, 150.0, 12.0)
    assert neutral.account_safety_pl == pytest.approx(0.0)

    locked = new_risk_day(NOW, 100.0, manual_reset_enabled=True)
    before = risk_day_metrics(locked, 88.0, 12.0)
    assert before.loss_locked
    reset = manual_reset_loss_lock(locked, 88.0, 12.0, double_confirmed=True)
    after = risk_day_metrics(reset, 88.0, 12.0)
    assert after.account_safety_pl == pytest.approx(-12.0)
    assert after.cycle_safety_pl == pytest.approx(0.0)
    assert reset.manual_reset_count == 1

    second_lock_equity = 77.44
    assert risk_day_metrics(reset, second_lock_equity, 12.0).loss_locked
    with pytest.raises(PermissionError):
        manual_reset_loss_lock(reset, second_lock_equity, 12.0, double_confirmed=True)


def test_three_losses_need_time_fresh_m15_and_fresh_opportunity_for_release() -> None:
    state = CooldownState()
    first = record_closed_trade(state, ClosedTradeOutcome.LOSS, NOW)
    second = record_closed_trade(first, ClosedTradeOutcome.LOSS, NOW + timedelta(minutes=5))
    third_time = NOW + timedelta(minutes=10)
    third = record_closed_trade(second, ClosedTradeOutcome.LOSS, third_time)

    assert first.cooldown_until_utc is None
    assert second.cooldown_until_utc is None
    assert third.cooldown_until_utc == third_time + timedelta(minutes=30)
    assert cooldown_decision(
        third,
        third_time + timedelta(minutes=31),
        latest_completed_m15_utc=third_time,
        unresolved_execution_fault=False,
        fresh_opportunity=True,
    ) is CooldownDecision.COOLDOWN
    assert cooldown_decision(
        third,
        third_time + timedelta(minutes=31),
        latest_completed_m15_utc=third_time + timedelta(minutes=15),
        unresolved_execution_fault=False,
        fresh_opportunity=True,
    ) is CooldownDecision.CLEAR

    won = record_closed_trade(third, ClosedTradeOutcome.WIN, third_time + timedelta(minutes=40))
    assert won.consecutive_losses == 0


def test_same_episode_allows_only_one_fresh_reentry_then_locks_after_second_loss() -> None:
    episode = EpisodeRiskState(episode_id=new_episode_id())
    first = register_episode_entry(episode, fresh_structural_event=False)
    first_loss = record_episode_loss(first)

    with pytest.raises(PermissionError):
        register_episode_entry(first_loss, fresh_structural_event=False)

    reentry = register_episode_entry(first_loss, fresh_structural_event=True)
    second_loss = record_episode_loss(reentry)
    assert second_loss.locked
    assert second_loss.entries_taken == 2
    assert second_loss.losses == 2
