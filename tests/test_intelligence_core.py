from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from goldswingtraderai.domain.enums import (
    CandleSequenceState,
    Direction,
    Timeframe,
)
from goldswingtraderai.domain.market import Candle
from goldswingtraderai.intelligence.candle_structure import StructureConfig, analyze_structure
from goldswingtraderai.intelligence.indicators import (
    QuantConfig,
    analyze_quant,
    atr_series,
    ema_series,
    rsi_series,
)


_START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _candles(closes: list[float], *, step_minutes: int = 5) -> tuple[Candle, ...]:
    candles: list[Candle] = []
    previous = closes[0]
    for index, close in enumerate(closes):
        open_price = previous if index else close
        high = max(open_price, close) + 0.5
        low = min(open_price, close) - 0.5
        candles.append(
            Candle(
                time_utc=_START + timedelta(minutes=step_minutes * index),
                open=open_price,
                high=high,
                low=low,
                close=close,
                tick_volume=100,
                spread_points=20,
            )
        )
        previous = close
    return tuple(candles)


def test_ema_does_not_exist_before_seed_period() -> None:
    values = tuple(float(value) for value in range(1, 7))
    result = ema_series(values, 3)

    assert result[:2] == (None, None)
    assert result[2] == pytest.approx(2.0)
    assert result[-1] is not None


def test_rsi_and_atr_are_chronological() -> None:
    candles = _candles([100, 101, 102, 101, 103, 104, 103, 105])
    closes = tuple(candle.close for candle in candles)

    rsi = rsi_series(closes, 3)
    atr = atr_series(candles, 3)

    assert rsi[:3] == (None, None, None)
    assert atr[:2] == (None, None)
    assert rsi[-1] is not None
    assert atr[-1] is not None
    assert 0 <= rsi[-1] <= 100
    assert atr[-1] > 0


def test_quant_report_uses_soft_support_not_trade_signal() -> None:
    candles = _candles([100 + index * 0.5 for index in range(60)])
    report = analyze_quant(candles, Timeframe.M5, QuantConfig())

    assert report.trend_support is Direction.BUY
    assert report.ema_fast is not None
    assert report.ema_slow is not None
    assert report.atr is not None
    assert report.coverage == 1.0


def test_confirmed_swings_have_later_confirmation_time() -> None:
    closes = [
        100,
        101,
        102,
        103,
        104,
        105,
        106,
        107,
        108,
        109,
        110,
        111,
        112,
        113,
        114,
        116,
        118,
        120,
        117,
        114,
        111,
        108,
        110,
        113,
        116,
        119,
        121,
        118,
        115,
    ]
    report = analyze_structure(
        _candles(closes),
        Timeframe.M5,
        StructureConfig(atr_period=3, swing_reversal_atr=0.8),
    )

    assert report.swings
    assert all(swing.confirmed_at > swing.pivot_time for swing in report.swings)


def test_prefix_replay_cannot_see_future_confirmed_swing() -> None:
    candles = _candles(
        [100, 101, 102, 103, 104, 105, 106, 108, 111, 114, 118, 120, 118, 115, 112, 109, 111, 114, 118, 121, 119, 116]
    )
    cfg = StructureConfig(atr_period=3, swing_reversal_atr=0.8)
    prefix = candles[:15]

    prefix_report = analyze_structure(prefix, Timeframe.M5, cfg)
    full_report = analyze_structure(candles, Timeframe.M5, cfg)
    visible_in_full = tuple(
        swing for swing in full_report.swings if swing.confirmed_at <= prefix[-1].time_utc
    )

    assert prefix_report.swings == visible_in_full


def test_large_directional_candle_is_expansion_evidence() -> None:
    candles = list(_candles([100 + index * 0.2 for index in range(20)]))
    last = candles[-1]
    candles[-1] = Candle(
        time_utc=last.time_utc,
        open=last.open,
        high=last.open + 5.2,
        low=last.open - 0.1,
        close=last.open + 5.0,
        tick_volume=500,
        spread_points=20,
    )
    report = analyze_structure(
        tuple(candles),
        Timeframe.M5,
        StructureConfig(atr_period=5, expansion_range_atr=1.2),
    )

    assert report.sequence is CandleSequenceState.BULL_EXPANSION
    assert report.bull_evidence >= report.bear_evidence
