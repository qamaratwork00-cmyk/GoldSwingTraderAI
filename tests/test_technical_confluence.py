from datetime import datetime, timedelta, timezone

import pytest

from goldswingtraderai.domain.enums import (
    CandleSequenceState,
    Direction,
    ExtensionState,
    MomentumPhase,
    StrategyFamily,
    StructureState,
    SwingRole,
    SwingSide,
    Timeframe,
    VolatilityState,
)
from goldswingtraderai.domain.ids import new_snapshot_id
from goldswingtraderai.domain.market import Candle
from goldswingtraderai.intelligence.candle_structure import CandleFacts, StructureReport, SwingPoint
from goldswingtraderai.intelligence.confluence import (
    ConfluenceReport,
    FibLevel,
    FibLevelKind,
    FibonacciContext,
    LineEvent,
    PocRelation,
    Trendline,
    TrendlineSide,
    TrendlineSlope,
    VolumeProfileContext,
    VolumeSource,
    analyze_confluence,
)
from goldswingtraderai.intelligence.indicators import QuantReport
from goldswingtraderai.intelligence.snapshot import IntelligenceSnapshot, TimeframeIntelligence
from goldswingtraderai.strategies.confluence import apply_optional_confluence
from goldswingtraderai.strategies.floor import (
    DirectionalFamilyCase,
    FamilyReport,
    StrategyFloorReport,
)


START = datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc)


def _candles() -> tuple[Candle, ...]:
    closes = (101.0, 102.0, 104.0, 106.0, 104.0, 103.0, 105.0, 108.0, 110.0, 108.0, 107.0, 108.0)
    return tuple(
        Candle(
            time_utc=START + timedelta(minutes=15 * index),
            open=close - 0.4,
            high=close + 0.8,
            low=close - 0.8,
            close=close,
            tick_volume=100 + index * 10,
        )
        for index, close in enumerate(closes)
    )


def _swing(side: SwingSide, price: float, index: int) -> SwingPoint:
    pivot = START + timedelta(minutes=15 * index)
    return SwingPoint(
        side=side,
        price=price,
        pivot_time=pivot,
        confirmed_at=pivot + timedelta(minutes=15),
        role=SwingRole.CONFIRMED,
        significance_atr=1.2,
    )


def _structure() -> StructureReport:
    candles = _candles()
    swings = (
        _swing(SwingSide.LOW, 100.0, 0),
        _swing(SwingSide.HIGH, 106.8, 3),
        _swing(SwingSide.LOW, 102.0, 5),
        _swing(SwingSide.HIGH, 110.8, 8),
    )
    return StructureReport(
        timeframe=Timeframe.M15,
        state=StructureState.BULLISH,
        sequence=CandleSequenceState.BULL_CONTINUATION,
        latest_candle=CandleFacts(
            time_utc=candles[-1].time_utc,
            direction=Direction.BUY,
            range_size=1.6,
            body_size=0.4,
            body_ratio=0.25,
            upper_wick=0.8,
            lower_wick=0.4,
            close_position=0.5,
            range_atr=0.8,
        ),
        swings=swings,
        protected_high=None,
        protected_low=None,
        events=(),
        bull_evidence=80.0,
        bear_evidence=20.0,
        coverage=1.0,
    )


def _quant() -> QuantReport:
    return QuantReport(
        timeframe=Timeframe.M15,
        ema_fast=107.0,
        ema_slow=104.0,
        rsi=58.0,
        atr=2.0,
        trend_support=Direction.BUY,
        volatility_state=VolatilityState.NORMAL,
        volatility_ratio=1.0,
        momentum_phase=MomentumPhase.BUILDING,
        extension_state=ExtensionState.NORMAL,
        extension_atr=0.4,
        coverage=1.0,
    )


def test_confluence_builds_causal_trendline_fib_and_tick_volume_poc() -> None:
    report = analyze_confluence(
        _candles(),
        _structure(),
        _quant(),
        current_price=108.0,
        tick_size=0.01,
    )

    assert report.support_trendline is not None
    assert report.resistance_trendline is not None
    assert report.fibonacci is not None
    assert report.volume_profile is not None
    assert report.volume_profile.source is VolumeSource.TICK_VOLUME
    assert report.fibonacci.anchor_from.confirmed_at <= _candles()[-1].time_utc
    assert report.fibonacci.anchor_to.confirmed_at <= _candles()[-1].time_utc


def test_real_volume_is_preferred_when_available() -> None:
    candles = tuple(
        Candle(
            time_utc=item.time_utc,
            open=item.open,
            high=item.high,
            low=item.low,
            close=item.close,
            tick_volume=item.tick_volume,
            real_volume=50 + index,
        )
        for index, item in enumerate(_candles())
    )
    report = analyze_confluence(
        candles,
        _structure(),
        _quant(),
        current_price=108.0,
        tick_size=0.01,
    )
    assert report.volume_profile is not None
    assert report.volume_profile.source is VolumeSource.REAL_VOLUME


def _supportive_confluence(timeframe: Timeframe) -> ConfluenceReport:
    first = _swing(SwingSide.LOW, 100.0, 0)
    second = _swing(SwingSide.LOW, 102.0, 5)
    fib_from = _swing(SwingSide.LOW, 100.0, 0)
    fib_to = _swing(SwingSide.HIGH, 110.0, 8)
    return ConfluenceReport(
        timeframe=timeframe,
        support_trendline=Trendline(
            side=TrendlineSide.SUPPORT,
            timeframe=timeframe,
            first_pivot=first,
            second_pivot=second,
            slope_per_bar=0.4,
            slope=TrendlineSlope.ASCENDING,
            projected_price=107.8,
            distance_atr=0.1,
            event=LineEvent.TOUCH,
        ),
        resistance_trendline=None,
        fibonacci=FibonacciContext(
            direction=Direction.BUY,
            anchor_from=fib_from,
            anchor_to=fib_to,
            leg_size=10.0,
            levels=(FibLevel(0.618, 103.82, FibLevelKind.RETRACEMENT),),
            nearest_ratio=0.618,
            nearest_price=103.82,
            in_core_retracement=True,
            in_deep_retracement=False,
        ),
        volume_profile=VolumeProfileContext(
            source=VolumeSource.TICK_VOLUME,
            lookback_bars=48,
            bins=24,
            poc_price=107.9,
            total_volume=5000.0,
            relation=PocRelation.NEAR,
            distance_atr=0.05,
        ),
        buy_bonus=85.0,
        sell_bonus=None,
        evidence=("TRENDLINE_SUPPORT_TOUCH", "FIB_CORE_BUY", "POC_NEAR"),
    )


def _frame(timeframe: Timeframe, confluence: ConfluenceReport | None) -> TimeframeIntelligence:
    structure = _structure()
    quant = _quant()
    return TimeframeIntelligence(
        timeframe=timeframe,
        quant=quant,
        structure=structure,
        technical=None,  # unused by the confluence booster
        liquidity=None,  # unused by the confluence booster
        confluence=confluence,
    )


def _base_floor() -> StrategyFloorReport:
    case = DirectionalFamilyCase(
        score=60.0,
        coverage=0.8,
        evidence=("BASE",),
        conflicts=(),
        structural_target=120.0,
        expansion_potential=0.8,
    )
    opposite = DirectionalFamilyCase(
        score=40.0,
        coverage=0.8,
        evidence=(),
        conflicts=(),
        structural_target=90.0,
        expansion_potential=0.4,
    )
    return StrategyFloorReport(
        families=(
            FamilyReport(
                family=StrategyFamily.TREND_PULLBACK_CONTINUATION,
                buy=case,
                sell=opposite,
                preferred_timing_profile="PULLBACK_RECLAIM",
            ),
        )
    )


def test_missing_confluence_never_penalizes_base_strategy_score() -> None:
    intelligence = IntelligenceSnapshot(
        market_snapshot_id=new_snapshot_id(),
        frames=(_frame(Timeframe.M15, None), _frame(Timeframe.M5, None)),
        session=None,
        news=None,
    )
    base = _base_floor()
    adjusted = apply_optional_confluence(base, intelligence)
    assert adjusted.families[0].buy.score == pytest.approx(base.families[0].buy.score)
    assert adjusted.families[0].sell.score == pytest.approx(base.families[0].sell.score)


def test_supportive_confluence_is_bounded_positive_only_bonus() -> None:
    intelligence = IntelligenceSnapshot(
        market_snapshot_id=new_snapshot_id(),
        frames=(
            _frame(Timeframe.M15, _supportive_confluence(Timeframe.M15)),
            _frame(Timeframe.M5, _supportive_confluence(Timeframe.M5)),
        ),
        session=None,
        news=None,
    )
    base = _base_floor()
    adjusted = apply_optional_confluence(base, intelligence)
    buy = adjusted.families[0].buy
    sell = adjusted.families[0].sell

    assert base.families[0].buy.score < buy.score <= base.families[0].buy.score + 6.0
    assert sell.score == pytest.approx(base.families[0].sell.score)
    assert "TRENDLINE_PULLBACK_SUPPORT" in buy.evidence
    assert "FIB_CORE_RETRACEMENT" in buy.evidence
    assert "POC_LOCATION_CONFLUENCE" in buy.evidence
