from datetime import datetime, timedelta, timezone

import pytest

from goldswingtraderai.domain.enums import AccountMode, Timeframe
from goldswingtraderai.domain.market import AccountFacts, Candle, CandleSeries, SymbolSpec
from goldswingtraderai.research.replay import ReplayDataset
from goldswingtraderai.research.stress import ExecutionStressVariant
from goldswingtraderai.research.validation import (
    ValidationMode,
    build_walk_forward_windows,
    run_walk_forward_validation,
)


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


def test_walk_forward_builder_uses_non_overlapping_validation_slices() -> None:
    windows = build_walk_forward_windows(
        _dataset(),
        development_events=8,
        validation_events=4,
        minimum_bars=_MINIMUM_BARS,
        start_utc=END - timedelta(hours=2),
        end_utc=END,
        max_windows=2,
    )

    assert len(windows) == 2
    assert windows[0].development_events == 8
    assert windows[0].validation_events == 4
    assert windows[0].development_end_utc < windows[0].validation_start_utc
    assert windows[1].validation_start_utc > windows[0].validation_end_utc


def test_walk_forward_builder_rejects_overlapping_validation_steps() -> None:
    with pytest.raises(ValueError):
        build_walk_forward_windows(
            _dataset(),
            development_events=8,
            validation_events=4,
            step_events=3,
            minimum_bars=_MINIMUM_BARS,
        )


def test_walk_forward_scores_only_validation_after_development_context() -> None:
    dataset = _dataset()
    windows = build_walk_forward_windows(
        dataset,
        development_events=8,
        validation_events=4,
        minimum_bars=_MINIMUM_BARS,
        start_utc=END - timedelta(hours=2),
        end_utc=END,
        max_windows=1,
    )
    report = run_walk_forward_validation(
        dataset,
        windows,
        minimum_bars=_MINIMUM_BARS,
        horizon_m5_bars=8,
        include_stress=False,
    )

    assert report.mode is ValidationMode.FIXED_POLICY_WALK_FORWARD
    assert len(report.evaluations) == 1
    evaluation = report.evaluations[0]
    assert evaluation.decision_metrics.events == 4
    assert report.validation_events == 4
    assert evaluation.stress_report is None


def test_walk_forward_can_attach_declared_stress_to_validation_only() -> None:
    dataset = _dataset()
    windows = build_walk_forward_windows(
        dataset,
        development_events=8,
        validation_events=3,
        minimum_bars=_MINIMUM_BARS,
        start_utc=END - timedelta(hours=1),
        end_utc=END,
        max_windows=1,
    )
    report = run_walk_forward_validation(
        dataset,
        windows,
        minimum_bars=_MINIMUM_BARS,
        horizon_m5_bars=6,
        include_stress=True,
    )

    stress = report.evaluations[0].stress_report
    assert stress is not None
    base = stress.row(ExecutionStressVariant.BASE)
    combined = stress.row(ExecutionStressVariant.COMBINED)
    assert base.metrics.enter_signals == combined.metrics.enter_signals
