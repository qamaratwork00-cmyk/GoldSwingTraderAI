from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from goldswingtraderai.domain.enums import AccountMode, Timeframe
from goldswingtraderai.domain.market import AccountFacts, Candle, CandleSeries, SymbolSpec
from goldswingtraderai.research.acquisition import (
    HistoricalAcquisitionError,
    HistoricalAcquisitionRequest,
    HistoricalSpreadSource,
    acquire_and_export_mt5_bundle,
    acquire_mt5_replay_dataset,
)
from goldswingtraderai.research.datasets import import_replay_dataset_bundle


START = datetime(2026, 1, 5, 0, 0, tzinfo=timezone.utc)
_PERIODS = {
    Timeframe.H4: timedelta(hours=4),
    Timeframe.H1: timedelta(hours=1),
    Timeframe.M15: timedelta(minutes=15),
    Timeframe.M5: timedelta(minutes=5),
    Timeframe.M1: timedelta(minutes=1),
}


def _series(timeframe: Timeframe, count: int, *, spread_points: int = 20) -> CandleSeries:
    candles = []
    for index in range(count):
        base = 2300.0 + index * 0.1
        candles.append(
            Candle(
                time_utc=START + _PERIODS[timeframe] * index,
                open=base,
                high=base + 0.5,
                low=base - 0.4,
                close=base + 0.1,
                tick_volume=100 + index,
                spread_points=spread_points + index,
                real_volume=0,
            )
        )
    return CandleSeries(timeframe=timeframe, candles=tuple(candles))


class FakeReader:
    def __init__(self, *, short_timeframe: Timeframe | None = None, zero_spread: bool = False) -> None:
        self.short_timeframe = short_timeframe
        self.zero_spread = zero_spread
        self.calls: list[tuple[str, Timeframe, int]] = []

    def resolve_symbol(self, preferred: str, aliases: tuple[str, ...]) -> str:
        assert preferred == "XAUUSDm"
        assert aliases == ("XAUUSD",)
        return "XAUUSDm"

    def account_facts(self) -> AccountFacts:
        return AccountFacts(
            login=7654321,
            server="Private-Demo-Endpoint",
            currency="USD",
            mode=AccountMode.DEMO,
            balance=100.0,
            equity=100.0,
            margin=0.0,
            margin_free=100.0,
            leverage=500,
        )

    def symbol_spec(self, symbol: str) -> SymbolSpec:
        assert symbol == "XAUUSDm"
        return SymbolSpec(
            symbol=symbol,
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
        )

    def completed_candles(self, symbol: str, timeframe: Timeframe, count: int) -> CandleSeries:
        self.calls.append((symbol, timeframe, count))
        actual = count - 1 if timeframe is self.short_timeframe else count
        spread = 0 if self.zero_spread else 20
        return _series(timeframe, actual, spread_points=spread)


def _request(**changes) -> HistoricalAcquisitionRequest:
    base = HistoricalAcquisitionRequest(
        preferred_symbol="XAUUSDm",
        aliases=("XAUUSD",),
        counts={
            Timeframe.H4: 4,
            Timeframe.H1: 5,
            Timeframe.M15: 6,
            Timeframe.M5: 5,
            Timeframe.M1: 7,
        },
        source_label="mt5-history",
        source_version="2026-09-18-export-1",
    )
    return replace(base, **changes)


def test_mt5_acquisition_reads_exact_completed_series_and_uses_m5_median_spread() -> None:
    reader = FakeReader()
    acquired = acquire_mt5_replay_dataset(reader, _request())

    assert acquired.symbol == "XAUUSDm"
    assert acquired.spread_source is HistoricalSpreadSource.M5_MEDIAN_SPREAD_POINTS
    # M5 spreads are 20,21,22,23,24 points; median = 22 points at 0.001.
    assert acquired.dataset.spread_price == pytest.approx(0.022)
    assert {item.timeframe for item in acquired.dataset.series} == {
        Timeframe.H4,
        Timeframe.H1,
        Timeframe.M15,
        Timeframe.M5,
        Timeframe.M1,
    }
    assert len(reader.calls) == 5


def test_mt5_acquisition_rejects_partial_history_instead_of_silently_shrinking_sample() -> None:
    reader = FakeReader(short_timeframe=Timeframe.H1)

    with pytest.raises(HistoricalAcquisitionError, match="H1 count mismatch"):
        acquire_mt5_replay_dataset(reader, _request())


def test_mt5_acquisition_requires_declared_spread_when_history_has_no_spread_points() -> None:
    reader = FakeReader(zero_spread=True)

    with pytest.raises(HistoricalAcquisitionError, match="spread_points unavailable"):
        acquire_mt5_replay_dataset(reader, _request())


def test_mt5_acquisition_allows_explicit_nonnegative_spread_override() -> None:
    reader = FakeReader(zero_spread=True)
    acquired = acquire_mt5_replay_dataset(
        reader,
        _request(spread_price_override=0.35),
    )

    assert acquired.dataset.spread_price == pytest.approx(0.35)
    assert acquired.spread_source is HistoricalSpreadSource.EXPLICIT_OVERRIDE


def test_acquire_and_export_bundle_is_reimportable_without_broker_endpoint_identity(tmp_path) -> None:
    reader = FakeReader()
    result = acquire_and_export_mt5_bundle(reader, _request(), tmp_path / "bundle")
    imported = import_replay_dataset_bundle(result.bundle.path)

    assert imported.dataset_sha256 == result.bundle.dataset_sha256
    assert imported.dataset.account.login == 1
    assert imported.dataset.account.server == "RESEARCH_DATASET"
