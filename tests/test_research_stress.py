from datetime import datetime, timedelta, timezone

import pytest

from goldswingtraderai.domain.enums import AccountMode, Timeframe
from goldswingtraderai.domain.market import AccountFacts, Candle, CandleSeries, SymbolSpec
from goldswingtraderai.research.replay import ReplayDataset, run_decision_replay
from goldswingtraderai.research.stress import (
    ExecutionStressScenario,
    ExecutionStressVariant,
    default_execution_stress_scenarios,
    run_execution_stress,
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


def test_default_execution_stress_scenarios_are_explicit() -> None:
    scenarios = default_execution_stress_scenarios()

    assert tuple(item.variant for item in scenarios) == (
        ExecutionStressVariant.BASE,
        ExecutionStressVariant.WIDER_SPREAD,
        ExecutionStressVariant.ADVERSE_ENTRY,
        ExecutionStressVariant.MODIFY_DELAY,
        ExecutionStressVariant.MODIFY_REJECTION,
        ExecutionStressVariant.COMBINED,
    )
    assert scenarios[1].spread_multiplier == pytest.approx(1.50)
    assert scenarios[2].adverse_entry_slippage_r == pytest.approx(0.10)
    assert scenarios[3].modify_delay_bars == 1
    assert scenarios[4].reject_every_nth_modify == 2


def test_execution_stress_reuses_fixed_analytical_run_and_reports_deltas() -> None:
    dataset = _dataset()
    run = run_decision_replay(
        dataset,
        start_utc=END - timedelta(hours=3),
        end_utc=END,
        minimum_bars=_MINIMUM_BARS,
    )
    report = run_execution_stress(
        dataset,
        run,
        horizon_m5_bars=18,
        minimum_bars=_MINIMUM_BARS,
    )

    base = report.row(ExecutionStressVariant.BASE)
    wider = report.row(ExecutionStressVariant.WIDER_SPREAD)
    adverse = report.row(ExecutionStressVariant.ADVERSE_ENTRY)
    combined = report.row(ExecutionStressVariant.COMBINED)

    assert base.stressed_spread_price == pytest.approx(0.20)
    assert wider.stressed_spread_price == pytest.approx(0.30)
    assert combined.stressed_spread_price == pytest.approx(0.30)
    assert adverse.scenario.adverse_entry_slippage_r == pytest.approx(0.10)

    # Analytical ENTER events are frozen; only Trade Plan / execution-management
    # assumptions vary across the stress report.
    assert all(
        row.metrics.enter_signals == base.metrics.enter_signals for row in report.rows
    )
    assert combined.managed_trade_delta_vs_base == (
        combined.metrics.managed_trades - base.metrics.managed_trades
    )
    assert combined.plan_not_ready_delta_vs_base == (
        combined.metrics.plan_not_ready - base.metrics.plan_not_ready
    )
    assert combined.resolved_net_r_delta_vs_base == pytest.approx(
        combined.metrics.resolved_net_r - base.metrics.resolved_net_r
    )
    assert combined.resolved_max_drawdown_r_delta_vs_base == pytest.approx(
        combined.metrics.resolved_max_drawdown_r
        - base.metrics.resolved_max_drawdown_r
    )


def test_execution_stress_requires_clean_single_base_scenario() -> None:
    dataset = _dataset()
    run = run_decision_replay(
        dataset,
        start_utc=END - timedelta(minutes=20),
        end_utc=END,
        minimum_bars=_MINIMUM_BARS,
    )

    with pytest.raises(ValueError):
        run_execution_stress(
            dataset,
            run,
            scenarios=(ExecutionStressScenario(ExecutionStressVariant.WIDER_SPREAD),),
            minimum_bars=_MINIMUM_BARS,
        )

    with pytest.raises(ValueError):
        run_execution_stress(
            dataset,
            run,
            scenarios=(
                ExecutionStressScenario(
                    ExecutionStressVariant.BASE,
                    spread_multiplier=1.25,
                ),
            ),
            minimum_bars=_MINIMUM_BARS,
        )
