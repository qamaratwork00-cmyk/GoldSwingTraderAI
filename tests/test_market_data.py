from __future__ import annotations

import inspect
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from goldswingtraderai.diagnostics.reasons import ReasonCode
from goldswingtraderai.domain.enums import AccountMode, DataQuality, HardDecision, Timeframe
from goldswingtraderai.market_data import MT5Reader, MarketDataError, MarketSnapshotBuilder


_NOW = datetime(2026, 9, 18, 10, 0, tzinfo=timezone.utc)
_NOW_TS = int(_NOW.timestamp())


class FakeMT5:
    ACCOUNT_TRADE_MODE_DEMO = 0
    SYMBOL_FILLING_FOK = 1
    SYMBOL_FILLING_IOC = 2
    SYMBOL_TRADE_EXECUTION_MARKET = 2
    ORDER_FILLING_FOK = 0
    ORDER_FILLING_IOC = 1
    ORDER_FILLING_RETURN = 2
    TIMEFRAME_H4 = 14_400
    TIMEFRAME_H1 = 3_600
    TIMEFRAME_M15 = 900
    TIMEFRAME_M5 = 300
    TIMEFRAME_M1 = 60

    def __init__(self, *, trade_mode: int = 0, quote_age_seconds: int = 0) -> None:
        self.trade_mode = trade_mode
        self.quote_age_seconds = quote_age_seconds
        self.initialized = False
        self.copy_calls: list[tuple[str, int, int, int]] = []
        self.symbols = {
            "XAUUSD": SimpleNamespace(
                visible=True,
                digits=2,
                point=0.01,
                trade_tick_size=0.01,
                trade_tick_value=1.0,
                trade_tick_value_profit=1.0,
                trade_tick_value_loss=1.0,
                trade_contract_size=100.0,
                volume_min=0.01,
                volume_max=200.0,
                volume_step=0.01,
                trade_stops_level=0,
                trade_freeze_level=0,
            )
        }

    def initialize(self) -> bool:
        self.initialized = True
        return True

    def shutdown(self) -> None:
        self.initialized = False

    def last_error(self):
        return (0, "ok")

    def account_info(self):
        return SimpleNamespace(
            login=123456,
            server="Broker-Demo",
            currency="USD",
            trade_mode=self.trade_mode,
            balance=100.0,
            equity=101.0,
            margin=5.0,
            margin_free=96.0,
            leverage=500,
        )

    def symbol_info(self, symbol: str):
        return self.symbols.get(symbol)

    def symbol_select(self, symbol: str, selected: bool) -> bool:
        return selected and symbol in self.symbols

    def symbol_info_tick(self, symbol: str):
        if symbol not in self.symbols:
            return None
        timestamp = _NOW_TS - self.quote_age_seconds
        return SimpleNamespace(bid=3650.10, ask=3650.30, time=timestamp, time_msc=timestamp * 1000)

    def copy_rates_from_pos(self, symbol: str, timeframe: int, start_pos: int, count: int):
        self.copy_calls.append((symbol, timeframe, start_pos, count))
        if symbol not in self.symbols:
            return None
        rows = []
        for index in range(count, 0, -1):
            timestamp = _NOW_TS - timeframe * index
            price = 3600.0 + index
            rows.append(
                {
                    "time": timestamp,
                    "open": price,
                    "high": price + 2.0,
                    "low": price - 2.0,
                    "close": price + 0.5,
                    "tick_volume": 100,
                    "spread": 20,
                    "real_volume": 0,
                }
            )
        return rows


def _reader(fake: FakeMT5) -> MT5Reader:
    reader = MT5Reader(fake)
    reader.initialize()
    return reader


def test_reader_requires_initialization() -> None:
    reader = MT5Reader(FakeMT5())
    with pytest.raises(MarketDataError) as exc_info:
        reader.account_facts()
    assert exc_info.value.reason is ReasonCode.MT5_NOT_INITIALIZED


def test_sdk_read_exception_becomes_typed_unavailable_failure() -> None:
    fake = FakeMT5()

    def failing_account_info():
        raise RuntimeError("terminal read failed")

    fake.account_info = failing_account_info
    reader = _reader(fake)

    with pytest.raises(MarketDataError) as exc_info:
        reader.account_facts()

    assert exc_info.value.reason is ReasonCode.DATA_UNAVAILABLE


def test_malformed_mt5_numeric_constant_becomes_typed_corrupt_failure() -> None:
    fake = FakeMT5()
    fake.TIMEFRAME_M5 = float("inf")
    reader = _reader(fake)

    with pytest.raises(MarketDataError) as exc_info:
        reader.completed_candles("XAUUSD", Timeframe.M5, 3)

    assert exc_info.value.reason is ReasonCode.DATA_CORRUPT


def test_account_facts_and_positive_demo_guard() -> None:
    reader = _reader(FakeMT5())
    account = reader.account_facts()
    guard = reader.demo_guard(account)

    assert account.mode is AccountMode.DEMO
    assert account.server == "Broker-Demo"
    assert guard.decision is HardDecision.PASS


def test_non_demo_account_does_not_pass_positive_guard() -> None:
    reader = _reader(FakeMT5(trade_mode=2))
    guard = reader.demo_guard()

    assert guard.decision is HardDecision.BLOCK
    assert guard.account_mode is AccountMode.OTHER
    assert guard.reason is not None
    assert guard.reason.code is ReasonCode.DEMO_GUARD_NOT_VERIFIED


def test_symbol_alias_resolution_and_specs() -> None:
    reader = _reader(FakeMT5())
    symbol = reader.resolve_symbol("XAUUSDm", ("XAUUSDm", "XAUUSD"))
    spec = reader.symbol_spec(symbol)
    quote = reader.quote(symbol)

    assert symbol == "XAUUSD"
    assert spec.volume_min == 0.01
    assert spec.volume_step == 0.01
    assert quote.spread_price == pytest.approx(0.20)


def test_symbol_filling_flags_are_normalized_to_request_enum() -> None:
    fake = FakeMT5()
    info = fake.symbols["XAUUSD"]
    info.filling_mode = fake.SYMBOL_FILLING_FOK
    info.trade_exemode = fake.SYMBOL_TRADE_EXECUTION_MARKET
    reader = _reader(fake)

    market_spec = reader.symbol_spec("XAUUSD")

    assert market_spec.filling_mode == fake.ORDER_FILLING_FOK

    info.filling_mode = fake.SYMBOL_FILLING_IOC
    info.trade_exemode = 0  # non-market execution: RETURN is request-ready
    non_market_spec = reader.symbol_spec("XAUUSD")

    assert non_market_spec.filling_mode == fake.ORDER_FILLING_RETURN


def test_completed_candles_explicitly_exclude_forming_bar() -> None:
    fake = FakeMT5()
    reader = _reader(fake)
    series = reader.completed_candles("XAUUSD", Timeframe.M5, 3)

    assert fake.copy_calls[-1] == ("XAUUSD", fake.TIMEFRAME_M5, 1, 3)
    assert len(series.candles) == 3
    assert series.candles[0].time_utc < series.candles[-1].time_utc
    assert series.latest.time_utc == datetime.fromtimestamp(_NOW_TS - 300, tz=timezone.utc)


def test_snapshot_builder_creates_one_healthy_reusable_snapshot() -> None:
    reader = _reader(FakeMT5())
    history = {Timeframe.H4: 3, Timeframe.H1: 3, Timeframe.M15: 3, Timeframe.M5: 3}
    snapshot = MarketSnapshotBuilder(reader, history_bars=history).build(
        preferred_symbol="XAUUSDm",
        symbol_aliases=("XAUUSDm", "XAUUSD"),
        now_utc=_NOW,
    )

    assert snapshot.quality is DataQuality.HEALTHY
    assert snapshot.meta.data_complete is True
    assert snapshot.meta.symbol == "XAUUSD"
    assert snapshot.meta.timeframes == (Timeframe.H4, Timeframe.H1, Timeframe.M15, Timeframe.M5)
    assert len(snapshot.candles(Timeframe.M5)) == 3


def test_snapshot_marks_stale_quote() -> None:
    reader = _reader(FakeMT5(quote_age_seconds=30))
    history = {Timeframe.M5: 3}
    snapshot = MarketSnapshotBuilder(
        reader,
        history_bars=history,
        max_quote_age_seconds=10,
    ).build(
        preferred_symbol="XAUUSD",
        symbol_aliases=("XAUUSD",),
        now_utc=_NOW,
    )

    assert snapshot.quality is DataQuality.STALE
    assert snapshot.meta.data_complete is False
    assert any("quote age" in issue for issue in snapshot.issues)


def test_market_data_adapter_contains_no_irreversible_order_send() -> None:
    source = inspect.getsource(MT5Reader)
    assert "order_send" not in source
