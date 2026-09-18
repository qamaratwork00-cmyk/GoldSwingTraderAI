from datetime import datetime, timedelta, timezone

from goldswingtraderai.decisions.snapshot import DecisionConfig
from goldswingtraderai.domain.enums import AccountMode, Timeframe
from goldswingtraderai.domain.market import AccountFacts, Candle, CandleSeries, SymbolSpec
from goldswingtraderai.research.ablation import (
    ConfluenceAblationVariant,
    run_confluence_ablation,
)
from goldswingtraderai.research.replay import ReplayDataset
from goldswingtraderai.strategies.confluence import ConfluenceBonusConfig


END = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
_PERIODS = {
    Timeframe.H4: timedelta(hours=4),
    Timeframe.H1: timedelta(hours=1),
    Timeframe.M15: timedelta(minutes=15),
    Timeframe.M5: timedelta(minutes=5),
}


def _series(timeframe: Timeframe, count: int) -> CandleSeries:
    period = _PERIODS[timeframe]
    start = END - period * count
    candles = []
    for index in range(count):
        # Smooth trend + repeating pullbacks gives structure enough variation for
        # the real production intelligence path without hand-building reports.
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


def test_production_decision_defaults_keep_all_confluence_enabled() -> None:
    assert DecisionConfig().confluence == ConfluenceBonusConfig(
        trendline=True,
        fibonacci=True,
        poc=True,
    )


def test_ablation_replays_same_chronology_and_reports_frequency_deltas() -> None:
    dataset = _dataset()
    start = END - timedelta(minutes=45)
    report = run_confluence_ablation(
        dataset,
        start_utc=start,
        end_utc=END,
        minimum_bars={
            Timeframe.H4: 50,
            Timeframe.H1: 55,
            Timeframe.M15: 60,
            Timeframe.M5: 70,
        },
    )

    assert tuple(row.variant for row in report.rows) == (
        ConfluenceAblationVariant.BASE,
        ConfluenceAblationVariant.TRENDLINE,
        ConfluenceAblationVariant.FIBONACCI,
        ConfluenceAblationVariant.DIRECTIONAL_COMBINED,
        ConfluenceAblationVariant.ALL,
    )

    base = report.row(ConfluenceAblationVariant.BASE)
    all_sources = report.row(ConfluenceAblationVariant.ALL)
    directional = report.row(ConfluenceAblationVariant.DIRECTIONAL_COMBINED)

    assert base.metrics.events > 0
    assert all(row.metrics.events == base.metrics.events for row in report.rows)

    # Confluence is positive-only at the family-evidence layer, but it can support
    # both BUY and SELL theses at the same event. That can increase conflict and
    # therefore legitimately reduce the fused Opportunity Score. The ablation
    # report must measure the signed final effect rather than assuming monotonic
    # improvement.
    assert all_sources.average_opportunity_score_delta_vs_base == (
        all_sources.metrics.average_opportunity_score
        - base.metrics.average_opportunity_score
    )
    assert all_sources.opportunity_event_delta_vs_base == (
        all_sources.metrics.opportunity_events - base.metrics.opportunity_events
    )
    assert report.poc_marginal_enter_event_delta == (
        all_sources.metrics.enter_events - directional.metrics.enter_events
    )
    assert report.poc_marginal_opportunity_event_delta == (
        all_sources.metrics.opportunity_events - directional.metrics.opportunity_events
    )
    assert report.poc_marginal_average_opportunity_score_delta == (
        all_sources.metrics.average_opportunity_score
        - directional.metrics.average_opportunity_score
    )


def test_decision_ablation_does_not_invent_profitability_fields() -> None:
    report = run_confluence_ablation(
        _dataset(),
        start_utc=END - timedelta(minutes=20),
        end_utc=END,
        minimum_bars={
            Timeframe.H4: 50,
            Timeframe.H1: 55,
            Timeframe.M15: 60,
            Timeframe.M5: 70,
        },
    )

    base_metrics = report.row(ConfluenceAblationVariant.BASE).metrics
    assert not hasattr(base_metrics, "net_r")
    assert not hasattr(base_metrics, "profit_factor")
    assert not hasattr(base_metrics, "win_rate")
