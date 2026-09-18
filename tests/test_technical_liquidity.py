from __future__ import annotations

from datetime import datetime, timedelta, timezone

from goldswingtraderai.domain.enums import (
    CandleSequenceState,
    Direction,
    ExtensionState,
    MomentumPhase,
    StructureState,
    SwingRole,
    SwingSide,
    Timeframe,
    VolatilityState,
)
from goldswingtraderai.domain.market import Candle
from goldswingtraderai.intelligence.candle_structure import (
    CandleFacts,
    StructureReport,
    SwingPoint,
)
from goldswingtraderai.intelligence.indicators import QuantReport
from goldswingtraderai.intelligence.liquidity import (
    FVGState,
    LiquidityEventType,
    LiquiditySide,
    analyze_liquidity,
)
from goldswingtraderai.intelligence.technical import (
    LocationCategory,
    ZoneSide,
    analyze_technical,
)


_START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _candle(index: int, open_price: float, high: float, low: float, close: float) -> Candle:
    return Candle(
        time_utc=_START + timedelta(minutes=5 * index),
        open=open_price,
        high=high,
        low=low,
        close=close,
        tick_volume=100,
        spread_points=20,
    )


def _swing(
    side: SwingSide,
    price: float,
    pivot_index: int,
    confirm_index: int,
    *,
    role: SwingRole = SwingRole.CONFIRMED,
) -> SwingPoint:
    return SwingPoint(
        side=side,
        price=price,
        pivot_time=_START + timedelta(minutes=5 * pivot_index),
        confirmed_at=_START + timedelta(minutes=5 * confirm_index),
        role=role,
        significance_atr=1.5,
    )


def _structure(swings: tuple[SwingPoint, ...]) -> StructureReport:
    latest = CandleFacts(
        time_utc=_START + timedelta(minutes=100),
        direction=Direction.BUY,
        range_size=2.0,
        body_size=1.0,
        body_ratio=0.5,
        upper_wick=0.5,
        lower_wick=0.5,
        close_position=0.75,
        range_atr=1.0,
    )
    return StructureReport(
        timeframe=Timeframe.M15,
        state=StructureState.BULLISH,
        sequence=CandleSequenceState.BULL_CONTINUATION,
        latest_candle=latest,
        swings=swings,
        protected_high=None,
        protected_low=None,
        events=(),
        bull_evidence=70.0,
        bear_evidence=35.0,
        coverage=1.0,
    )


def _quant() -> QuantReport:
    return QuantReport(
        timeframe=Timeframe.M15,
        ema_fast=100.0,
        ema_slow=98.0,
        rsi=60.0,
        atr=2.0,
        trend_support=Direction.BUY,
        volatility_state=VolatilityState.NORMAL,
        volatility_ratio=1.0,
        momentum_phase=MomentumPhase.BUILDING,
        extension_state=ExtensionState.NORMAL,
        extension_atr=0.5,
        coverage=1.0,
    )


def test_technical_zones_merge_nearby_same_side_swings() -> None:
    swings = (
        _swing(SwingSide.LOW, 98.00, 1, 3),
        _swing(SwingSide.LOW, 98.08, 5, 7, role=SwingRole.PROTECTED),
        _swing(SwingSide.HIGH, 104.0, 8, 10),
    )
    report = analyze_technical(
        _structure(swings),
        _quant(),
        current_price=100.0,
        tick_size=0.01,
    )

    supports = [zone for zone in report.zones if zone.side is ZoneSide.SUPPORT]
    assert len(supports) == 1
    assert supports[0].source_count == 2
    assert supports[0].protected_source is True
    assert report.nearest_resistance is not None
    assert report.buy_target_room is not None and report.buy_target_room > 0


def test_location_near_support_is_positive_soft_context() -> None:
    swings = (
        _swing(SwingSide.LOW, 99.5, 1, 3, role=SwingRole.PROTECTED),
        _swing(SwingSide.HIGH, 105.0, 5, 7),
    )
    report = analyze_technical(
        _structure(swings),
        _quant(),
        current_price=99.7,
        tick_size=0.01,
    )

    assert report.buy_location in {LocationCategory.EXCELLENT, LocationCategory.GOOD}


def test_liquidity_clusters_equal_highs_and_classifies_sweep() -> None:
    swings = (
        _swing(SwingSide.HIGH, 105.00, 1, 3),
        _swing(SwingSide.HIGH, 105.08, 5, 7),
        _swing(SwingSide.LOW, 98.0, 2, 4),
    )
    candles = (
        _candle(0, 100, 101, 99, 100.5),
        _candle(1, 103, 105.0, 102, 104),
        _candle(2, 100, 101, 98, 99),
        _candle(3, 104, 104.5, 103, 103.5),
        _candle(4, 99, 101, 98.5, 100),
        _candle(5, 104, 105.08, 103, 104.5),
        _candle(6, 103, 104, 102, 103),
        _candle(7, 104, 104.5, 103, 104),
        _candle(8, 104.5, 105.5, 103.8, 104.7),
    )
    report = analyze_liquidity(
        candles,
        _structure(swings),
        _quant(),
        current_price=104.7,
        tick_size=0.01,
    )

    buy_pools = [pool for pool in report.pools if pool.side is LiquiditySide.BUY_SIDE]
    assert len(buy_pools) == 1
    assert buy_pools[0].source_count == 2
    assert any(
        event.event_type is LiquidityEventType.CONFIRMED_SWEEP
        and event.direction is Direction.SELL
        for event in report.events
    )


def test_three_candle_fvg_creation_is_known_on_third_candle() -> None:
    candles = (
        _candle(0, 100.0, 101.0, 99.0, 100.5),
        _candle(1, 100.5, 104.0, 100.4, 103.8),
        _candle(2, 103.9, 105.0, 102.0, 104.5),
        _candle(3, 104.5, 105.5, 103.0, 104.0),
    )
    report = analyze_liquidity(
        candles,
        _structure((_swing(SwingSide.LOW, 99.0, 0, 1),)),
        _quant(),
        current_price=104.0,
        tick_size=0.01,
    )

    bullish = [gap for gap in report.fvgs if gap.direction is Direction.BUY]
    assert bullish
    assert bullish[0].created_at == candles[2].time_utc
    assert bullish[0].lower == 101.0
    assert bullish[0].upper == 102.0
    assert bullish[0].state in {FVGState.FRESH, FVGState.PARTIAL, FVGState.MITIGATED}
