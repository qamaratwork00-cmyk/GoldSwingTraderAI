from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from goldswingtraderai.app.recovery_mt5 import build_mt5_recovery_truth
from goldswingtraderai.diagnostics.reasons import ReasonCode
from goldswingtraderai.domain.enums import Direction
from goldswingtraderai.market_data import MT5Reader, MarketDataError


NOW = datetime(2026, 9, 18, 18, 45, tzinfo=timezone.utc)


class FakeMT5:
    ACCOUNT_TRADE_MODE_DEMO = 0
    POSITION_TYPE_BUY = 0
    POSITION_TYPE_SELL = 1

    def __init__(self) -> None:
        self.positions_result: tuple[object, ...] | None = ()
        self.initialized = False
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

    def account_info(self):
        return SimpleNamespace(
            login=123456,
            server="Broker-Demo",
            currency="USD",
            trade_mode=self.ACCOUNT_TRADE_MODE_DEMO,
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

    def positions_get(self, *, symbol: str):
        assert symbol == "XAUUSD"
        return self.positions_result


def _reader(fake: FakeMT5) -> MT5Reader:
    reader = MT5Reader(fake)
    reader.initialize()
    return reader


def _position(
    *,
    ticket: int,
    position_type: int,
    volume: float = 0.01,
    price_open: float = 3650.0,
    sl: float = 3640.0,
    tp: float = 3675.0,
):
    return SimpleNamespace(
        ticket=ticket,
        symbol="XAUUSD",
        type=position_type,
        volume=volume,
        price_open=price_open,
        sl=sl,
        tp=tp,
        magic=26091801,
        comment="GSTAI:test",
    )


def test_open_positions_normalizes_buy_sell_and_sorts_by_ticket() -> None:
    fake = FakeMT5()
    fake.positions_result = (
        _position(ticket=20, position_type=fake.POSITION_TYPE_SELL, sl=3660.0, tp=3620.0),
        _position(ticket=10, position_type=fake.POSITION_TYPE_BUY),
    )
    positions = _reader(fake).open_positions("XAUUSD")

    assert [position.ticket for position in positions] == [10, 20]
    assert positions[0].direction is Direction.BUY
    assert positions[1].direction is Direction.SELL
    assert positions[0].magic == 26091801
    assert positions[0].comment == "GSTAI:test"


def test_zero_mt5_sl_tp_become_explicit_none() -> None:
    fake = FakeMT5()
    fake.positions_result = (
        _position(ticket=10, position_type=fake.POSITION_TYPE_BUY, sl=0.0, tp=0.0),
    )

    position = _reader(fake).open_positions("XAUUSD")[0]

    assert position.stop_loss is None
    assert position.take_profit is None


def test_positive_empty_positions_is_complete_empty_truth() -> None:
    fake = FakeMT5()
    truth = build_mt5_recovery_truth(
        _reader(fake),
        preferred_symbol="XAUUSDm",
        symbol_aliases=("XAUUSDm", "XAUUSD"),
        captured_at_utc=NOW,
    )

    assert truth.snapshot.symbol == "XAUUSD"
    assert truth.snapshot.positions == ()
    assert truth.snapshot.positions_complete
    assert truth.snapshot.account.login == 123456
    assert truth.price_tolerance == pytest.approx(0.01)


def test_live_recovery_truth_maps_current_position_and_broker_tick() -> None:
    fake = FakeMT5()
    fake.positions_result = (
        _position(ticket=9001, position_type=fake.POSITION_TYPE_BUY),
    )

    truth = build_mt5_recovery_truth(
        _reader(fake),
        preferred_symbol="XAUUSD",
        symbol_aliases=("XAUUSD",),
        captured_at_utc=NOW,
    )

    assert truth.symbol_spec.symbol == "XAUUSD"
    assert truth.price_tolerance == truth.symbol_spec.tick_size
    assert truth.snapshot.captured_at_utc == NOW
    assert truth.snapshot.positions[0].ticket == 9001
    assert truth.snapshot.positions[0].direction is Direction.BUY
    assert truth.snapshot.positions[0].stop_loss == pytest.approx(3640.0)
    assert truth.snapshot.positions[0].take_profit == pytest.approx(3675.0)


def test_unknown_positions_read_is_not_converted_to_zero_exposure() -> None:
    fake = FakeMT5()
    fake.positions_result = None

    with pytest.raises(MarketDataError) as exc_info:
        build_mt5_recovery_truth(
            _reader(fake),
            preferred_symbol="XAUUSD",
            symbol_aliases=("XAUUSD",),
            captured_at_utc=NOW,
        )

    assert exc_info.value.reason is ReasonCode.DATA_UNAVAILABLE


def test_invalid_position_direction_fails_as_corrupt_broker_truth() -> None:
    fake = FakeMT5()
    fake.positions_result = (_position(ticket=10, position_type=99),)

    with pytest.raises(MarketDataError) as exc_info:
        _reader(fake).open_positions("XAUUSD")

    assert exc_info.value.reason is ReasonCode.DATA_CORRUPT


def test_duplicate_position_ticket_fails_closed() -> None:
    fake = FakeMT5()
    fake.positions_result = (
        _position(ticket=10, position_type=fake.POSITION_TYPE_BUY),
        _position(ticket=10, position_type=fake.POSITION_TYPE_BUY),
    )

    with pytest.raises(MarketDataError) as exc_info:
        _reader(fake).open_positions("XAUUSD")

    assert exc_info.value.reason is ReasonCode.DATA_CORRUPT
