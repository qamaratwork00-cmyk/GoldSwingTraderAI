from datetime import datetime, timedelta, timezone

from goldswingtraderai.decisions import (
    PlanState,
    PlanTarget,
    RRClass,
    StopQuality,
    TargetRole,
    TradePlan,
)
from goldswingtraderai.domain.enums import (
    AccountMode,
    DataQuality,
    Direction,
    StrategyFamily,
    Timeframe,
)
from goldswingtraderai.domain.ids import new_episode_id, new_opportunity_id, new_snapshot_id, new_trade_plan_id
from goldswingtraderai.domain.market import (
    AccountFacts,
    Candle,
    CandleSeries,
    MarketSnapshot,
    Quote,
    SymbolSpec,
)
from goldswingtraderai.domain.models import MarketSnapshotMeta
from goldswingtraderai.risk import (
    CooldownDecision,
    EpisodeRiskState,
    RiskContext,
    evaluate_risk,
    new_risk_day,
)


NOW = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)


def _plan():
    episode_id = new_episode_id()
    target = PlanTarget(
        role=TargetRole.PRIMARY,
        price=102.0,
        quality=80.0,
        source="M15:SWING",
        rr=3.33,
    )
    return TradePlan(
        plan_id=new_trade_plan_id(),
        opportunity_id=new_opportunity_id(),
        episode_id=episode_id,
        family=StrategyFamily.TREND_PULLBACK_CONTINUATION,
        direction=Direction.BUY,
        state=PlanState.READY,
        signal_price=100.0,
        approved_entry_reference=100.0,
        invalidation_level=99.5,
        invalidation_source="M15:PROTECTED_LOW",
        initial_stop=99.4,
        stop_buffer=0.1,
        stop_quality=StopQuality.ROBUST,
        original_r_price=0.6,
        immediate_obstacle=None,
        primary_target=target,
        expansion_target=None,
        runner_target=None,
        broker_tp_target=target,
        rr_class=RRClass.STRONG,
        path_quality=80.0,
        plan_quality=80.0,
        created_at_utc=NOW,
        reason="PLAN_READY",
    )


def _market() -> MarketSnapshot:
    candle = Candle(
        time_utc=NOW - timedelta(minutes=5),
        open=99.5,
        high=100.5,
        low=99.0,
        close=100.0,
    )
    series = CandleSeries(timeframe=Timeframe.M5, candles=(candle,))
    return MarketSnapshot(
        meta=MarketSnapshotMeta(
            snapshot_id=new_snapshot_id(),
            symbol="XAUUSDm",
            as_of_utc=NOW,
            timeframes=(Timeframe.M5,),
            data_complete=True,
        ),
        account=AccountFacts(
            login=123456,
            server="Broker-Demo",
            currency="USD",
            mode=AccountMode.DEMO,
            balance=100.0,
            equity=100.0,
            margin=0.0,
            margin_free=100.0,
            leverage=1,
        ),
        symbol_spec=SymbolSpec(
            symbol="XAUUSDm",
            digits=1,
            point=0.1,
            tick_size=0.1,
            tick_value=8.0,
            contract_size=100.0,
            volume_min=0.01,
            volume_max=200.0,
            volume_step=0.01,
            stops_level_points=0,
            freeze_level_points=0,
        ),
        quote=Quote(symbol="XAUUSDm", bid=99.8, ask=100.0, time_utc=NOW),
        series=(series,),
        quality=DataQuality.HEALTHY,
    )


def _context(plan, *, broker_required_margin=None) -> RiskContext:
    return RiskContext(
        risk_day=new_risk_day(NOW, 100.0),
        cooldown=CooldownDecision.CLEAR,
        episode=EpisodeRiskState(episode_id=plan.episode_id),
        fresh_structural_event=True,
        broker_required_margin=broker_required_margin,
    )


def test_heuristic_margin_is_diagnostic_not_a_hard_block() -> None:
    plan = _plan()
    result = evaluate_risk(plan, _market(), _context(plan))

    assert result.passed
    assert result.estimated_margin is not None
    assert result.estimated_margin > 100.0
    assert result.margin_verified is False
    assert result.broker_required_margin is None


def test_exact_broker_margin_can_block_when_free_margin_is_insufficient() -> None:
    plan = _plan()
    result = evaluate_risk(
        plan,
        _market(),
        _context(plan, broker_required_margin=120.0),
    )

    assert not result.passed
    assert result.reason == "MARGIN_INSUFFICIENT"
    assert result.margin_verified is True
    assert result.broker_required_margin == 120.0
