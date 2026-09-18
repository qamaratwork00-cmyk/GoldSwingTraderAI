"""Typed market/account facts shared by the read layer and downstream desks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import isfinite

from goldswingtraderai.domain.enums import AccountMode, DataQuality, Direction, Timeframe
from goldswingtraderai.domain.ids import EntityId
from goldswingtraderai.domain.models import MarketSnapshotMeta


def _require_utc(name: str, value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(f"{name} must be UTC")


def _require_finite(name: str, *values: float) -> None:
    if not all(isfinite(value) for value in values):
        raise ValueError(f"{name} must contain finite numeric values")


@dataclass(frozen=True, slots=True)
class AccountFacts:
    login: int
    server: str
    currency: str
    mode: AccountMode
    balance: float
    equity: float
    margin: float
    margin_free: float
    leverage: int

    def __post_init__(self) -> None:
        if self.login <= 0:
            raise ValueError("account login must be positive")
        if not self.server.strip():
            raise ValueError("account server cannot be empty")
        if not self.currency.strip():
            raise ValueError("account currency cannot be empty")
        _require_finite("account monetary facts", self.balance, self.equity, self.margin, self.margin_free)
        if self.leverage <= 0:
            raise ValueError("account leverage must be positive")


@dataclass(frozen=True, slots=True)
class SymbolSpec:
    symbol: str
    digits: int
    point: float
    tick_size: float
    tick_value: float
    contract_size: float
    volume_min: float
    volume_max: float
    volume_step: float
    stops_level_points: int
    freeze_level_points: int

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol cannot be empty")
        if self.digits < 0:
            raise ValueError("digits cannot be negative")
        _require_finite(
            "symbol specification",
            self.point,
            self.tick_size,
            self.tick_value,
            self.contract_size,
            self.volume_min,
            self.volume_max,
            self.volume_step,
        )
        if self.point <= 0 or self.tick_size <= 0:
            raise ValueError("point and tick size must be positive")
        if self.tick_value < 0:
            raise ValueError("tick value cannot be negative")
        if self.contract_size <= 0:
            raise ValueError("contract size must be positive")
        if self.volume_min <= 0 or self.volume_step <= 0:
            raise ValueError("minimum volume and step must be positive")
        if self.volume_max < self.volume_min:
            raise ValueError("maximum volume cannot be below minimum volume")
        if self.stops_level_points < 0 or self.freeze_level_points < 0:
            raise ValueError("broker stop/freeze levels cannot be negative")


@dataclass(frozen=True, slots=True)
class OpenPositionFacts:
    """Normalized read-only broker position facts; never ownership by themselves."""

    ticket: int
    symbol: str
    direction: Direction
    volume: float
    price_open: float
    stop_loss: float | None
    take_profit: float | None
    magic: int | None = None
    comment: str | None = None

    def __post_init__(self) -> None:
        if self.ticket <= 0:
            raise ValueError("position ticket must be positive")
        if not self.symbol.strip():
            raise ValueError("position symbol cannot be empty")
        if self.direction is Direction.NONE:
            raise ValueError("position direction must be BUY or SELL")
        _require_finite("position facts", self.volume, self.price_open)
        if self.volume <= 0 or self.price_open <= 0:
            raise ValueError("position volume/open price must be positive")
        if self.stop_loss is not None:
            _require_finite("position stop", self.stop_loss)
            if self.stop_loss <= 0:
                raise ValueError("position stop must be positive when present")
        if self.take_profit is not None:
            _require_finite("position target", self.take_profit)
            if self.take_profit <= 0:
                raise ValueError("position target must be positive when present")


@dataclass(frozen=True, slots=True)
class Quote:
    symbol: str
    bid: float
    ask: float
    time_utc: datetime

    def __post_init__(self) -> None:
        _require_utc("quote time", self.time_utc)
        if not self.symbol.strip():
            raise ValueError("quote symbol cannot be empty")
        _require_finite("quote", self.bid, self.ask)
        if self.bid <= 0 or self.ask <= 0:
            raise ValueError("bid and ask must be positive")
        if self.ask < self.bid:
            raise ValueError("ask cannot be below bid")

    @property
    def spread_price(self) -> float:
        return self.ask - self.bid

    def age_seconds(self, now_utc: datetime) -> float:
        _require_utc("now_utc", now_utc)
        return max(0.0, (now_utc - self.time_utc).total_seconds())


@dataclass(frozen=True, slots=True)
class Candle:
    time_utc: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: int = 0
    spread_points: int = 0
    real_volume: int = 0

    def __post_init__(self) -> None:
        _require_utc("candle time", self.time_utc)
        _require_finite("OHLC", self.open, self.high, self.low, self.close)
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("OHLC prices must be positive")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("OHLC geometry is invalid")
        if self.high < self.low:
            raise ValueError("candle high cannot be below low")
        if self.tick_volume < 0 or self.real_volume < 0 or self.spread_points < 0:
            raise ValueError("volume/spread fields cannot be negative")


@dataclass(frozen=True, slots=True)
class CandleSeries:
    timeframe: Timeframe
    candles: tuple[Candle, ...]

    def __post_init__(self) -> None:
        if not self.candles:
            raise ValueError("candle series cannot be empty")
        times = tuple(candle.time_utc for candle in self.candles)
        if times != tuple(sorted(times)):
            raise ValueError("candles must be chronological")
        if len(times) != len(set(times)):
            raise ValueError("candle timestamps must be unique")

    @property
    def latest(self) -> Candle:
        return self.candles[-1]


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    meta: MarketSnapshotMeta
    account: AccountFacts
    symbol_spec: SymbolSpec
    quote: Quote
    series: tuple[CandleSeries, ...]
    quality: DataQuality
    issues: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.meta.symbol != self.symbol_spec.symbol or self.quote.symbol != self.symbol_spec.symbol:
            raise ValueError("snapshot symbol facts must agree")
        actual = tuple(item.timeframe for item in self.series)
        if actual != self.meta.timeframes:
            raise ValueError("snapshot timeframe metadata must match series order")

    def candles(self, timeframe: Timeframe) -> tuple[Candle, ...]:
        for item in self.series:
            if item.timeframe is timeframe:
                return item.candles
        raise KeyError(f"timeframe not present: {timeframe}")

    @property
    def snapshot_id(self) -> EntityId:
        return self.meta.snapshot_id
