"""Read-only MetaTrader 5 adapter.

The module deliberately exposes market/account/broker-truth reads only.
Irreversible broker writes belong to the execution package and must never be
added here.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from math import isfinite
from types import ModuleType
from typing import Any

from goldswingtraderai.diagnostics.reasons import ReasonCode
from goldswingtraderai.domain.enums import AccountMode, Direction, HardDecision, Timeframe
from goldswingtraderai.domain.market import (
    AccountFacts,
    Candle,
    CandleSeries,
    OpenPositionFacts,
    Quote,
    SymbolSpec,
)
from goldswingtraderai.domain.models import DemoGuardResult, Reason


class MarketDataError(RuntimeError):
    """A read-layer failure with a stable machine-readable reason."""

    def __init__(self, reason: ReasonCode, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def _field(row: Any, name: str, default: Any = None) -> Any:
    if isinstance(row, Mapping):
        return row.get(name, default)
    try:
        return row[name]
    except (KeyError, IndexError, TypeError, ValueError):
        return getattr(row, name, default)


def _utc_from_epoch(seconds: float | int) -> datetime:
    value = float(seconds)
    if not isfinite(value):
        raise ValueError("MT5 epoch timestamp must be finite")
    try:
        return datetime.fromtimestamp(value, tz=timezone.utc)
    except (OSError, OverflowError, ValueError) as exc:
        raise ValueError("MT5 epoch timestamp is outside the supported range") from exc


def _optional_positive_price(value: Any) -> float | None:
    number = 0.0 if value is None else float(value)
    if not isfinite(number):
        raise ValueError("optional broker price must be finite")
    return None if number <= 0 else number


class MT5Reader:
    """Small read-only boundary around the official MetaTrader5 module.

    A module can be injected for deterministic tests; production lazily imports
    `MetaTrader5` so normal CI does not require the Windows-only terminal package.
    """

    def __init__(self, mt5_module: ModuleType | Any | None = None) -> None:
        self._mt5 = mt5_module
        self._initialized = False

    def _module(self) -> Any:
        if self._mt5 is not None:
            return self._mt5
        try:
            self._mt5 = importlib.import_module("MetaTrader5")
        except ImportError as exc:
            raise MarketDataError(
                ReasonCode.MT5_UNAVAILABLE,
                "MetaTrader5 package is not available in this runtime",
            ) from exc
        return self._mt5

    def initialize(self) -> None:
        mt5 = self._module()
        try:
            initialized = bool(mt5.initialize())
        except Exception as exc:
            raise MarketDataError(
                ReasonCode.MT5_NOT_INITIALIZED,
                "MT5 initialize call failed",
            ) from exc
        if not initialized:
            try:
                last_error = mt5.last_error() if hasattr(mt5, "last_error") else None
            except Exception:
                last_error = None
            raise MarketDataError(
                ReasonCode.MT5_NOT_INITIALIZED,
                f"MT5 initialize failed: {last_error!r}",
            )
        self._initialized = True

    def shutdown(self) -> None:
        if self._initialized and self._mt5 is not None:
            self._mt5.shutdown()
        self._initialized = False

    def _require_ready(self) -> Any:
        if not self._initialized:
            raise MarketDataError(ReasonCode.MT5_NOT_INITIALIZED, "MT5 reader is not initialized")
        return self._module()

    def broker_module(self) -> Any:
        """Return the already-loaded MT5 module for governed execution adapters.

        The application passes this same initialized module to reconciliation and
        the narrow writer boundary. It is not a second broker client and does not
        grant permission to send orders; controller/gate checks remain mandatory.
        """

        return self._require_ready()

    def account_facts(self) -> AccountFacts:
        mt5 = self._require_ready()
        info = _broker_read(
            mt5.account_info,
            ReasonCode.DATA_UNAVAILABLE,
            "MT5 account_info read failed",
        )
        if info is None:
            raise MarketDataError(ReasonCode.DATA_UNAVAILABLE, "MT5 account_info returned no data")

        try:
            trade_mode = int(getattr(info, "trade_mode", -1))
            demo_value = int(getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", 0))
            if trade_mode == demo_value:
                mode = AccountMode.DEMO
            elif trade_mode < 0:
                mode = AccountMode.UNKNOWN
            else:
                mode = AccountMode.OTHER
            return AccountFacts(
                login=int(info.login),
                server=str(info.server),
                currency=str(info.currency),
                mode=mode,
                balance=float(info.balance),
                equity=float(info.equity),
                margin=float(info.margin),
                margin_free=float(info.margin_free),
                leverage=int(info.leverage),
            )
        except (AttributeError, TypeError, ValueError, OverflowError) as exc:
            raise MarketDataError(ReasonCode.DATA_CORRUPT, "invalid MT5 account facts") from exc

    def demo_guard(self, account: AccountFacts | None = None) -> DemoGuardResult:
        """Evaluate the positive V1 DEMO invariant without defining REAL policy."""

        facts = account or self.account_facts()
        if facts.mode is AccountMode.DEMO:
            return DemoGuardResult(decision=HardDecision.PASS, account_mode=facts.mode)
        return DemoGuardResult(
            decision=HardDecision.BLOCK if facts.mode is AccountMode.OTHER else HardDecision.UNKNOWN,
            account_mode=facts.mode,
            reason=Reason(
                code=ReasonCode.DEMO_GUARD_NOT_VERIFIED,
                message="connected account is not positively verified as DEMO",
            ),
        )

    def resolve_symbol(self, preferred: str, aliases: tuple[str, ...]) -> str:
        mt5 = self._require_ready()
        candidates = tuple(dict.fromkeys((preferred, *aliases)))
        for symbol in candidates:
            info = _broker_read(
                lambda symbol=symbol: mt5.symbol_info(symbol),
                ReasonCode.DATA_UNAVAILABLE,
                f"MT5 symbol_info read failed for {symbol}",
            )
            if info is None:
                continue
            if not bool(getattr(info, "visible", True)) and hasattr(mt5, "symbol_select"):
                selected = _broker_read(
                    lambda symbol=symbol: mt5.symbol_select(symbol, True),
                    ReasonCode.DATA_UNAVAILABLE,
                    f"MT5 symbol_select failed for {symbol}",
                )
                if not bool(selected):
                    continue
            return symbol
        raise MarketDataError(
            ReasonCode.SYMBOL_NOT_FOUND,
            f"none of the configured Gold symbols are available: {candidates!r}",
        )

    def symbol_spec(self, symbol: str) -> SymbolSpec:
        mt5 = self._require_ready()
        info = _broker_read(
            lambda: mt5.symbol_info(symbol),
            ReasonCode.DATA_UNAVAILABLE,
            f"MT5 symbol_info read failed for {symbol}",
        )
        if info is None:
            raise MarketDataError(ReasonCode.SYMBOL_NOT_FOUND, f"symbol not available: {symbol}")

        try:
            tick_size = float(getattr(info, "trade_tick_size", 0.0) or info.point)
            tick_value = float(
                getattr(info, "trade_tick_value", 0.0)
                or getattr(info, "trade_tick_value_profit", 0.0)
                or getattr(info, "trade_tick_value_loss", 0.0)
                or 0.0
            )
            filling_mode = _request_filling_mode(info, mt5)
            return SymbolSpec(
                symbol=symbol,
                digits=int(info.digits),
                point=float(info.point),
                tick_size=tick_size,
                tick_value=tick_value,
                contract_size=float(info.trade_contract_size),
                volume_min=float(info.volume_min),
                volume_max=float(info.volume_max),
                volume_step=float(info.volume_step),
                stops_level_points=int(getattr(info, "trade_stops_level", 0)),
                freeze_level_points=int(getattr(info, "trade_freeze_level", 0)),
                filling_mode=filling_mode,
            )
        except (AttributeError, TypeError, ValueError, OverflowError) as exc:
            raise MarketDataError(ReasonCode.DATA_CORRUPT, f"invalid symbol specification: {symbol}") from exc

    def quote(self, symbol: str) -> Quote:
        mt5 = self._require_ready()
        tick = _broker_read(
            lambda: mt5.symbol_info_tick(symbol),
            ReasonCode.DATA_UNAVAILABLE,
            f"MT5 symbol_info_tick read failed for {symbol}",
        )
        if tick is None:
            raise MarketDataError(ReasonCode.DATA_UNAVAILABLE, f"no live quote for {symbol}")

        time_msc = int(getattr(tick, "time_msc", 0) or 0)
        epoch = time_msc / 1000.0 if time_msc > 0 else float(getattr(tick, "time", 0))
        try:
            return Quote(
                symbol=symbol,
                bid=float(tick.bid),
                ask=float(tick.ask),
                time_utc=_utc_from_epoch(epoch),
            )
        except (AttributeError, TypeError, ValueError, OSError, OverflowError) as exc:
            raise MarketDataError(ReasonCode.DATA_CORRUPT, f"invalid quote for {symbol}") from exc

    def open_positions(self, symbol: str) -> tuple[OpenPositionFacts, ...]:
        """Return normalized current broker positions for one symbol.

        Empty tuple is valid complete truth when MT5 positively returns no positions.
        `None`/missing read capability is not converted into empty exposure.
        """

        mt5 = self._require_ready()
        getter = getattr(mt5, "positions_get", None)
        if not callable(getter):
            raise MarketDataError(
                ReasonCode.DATA_UNAVAILABLE,
                "MT5 positions_get is unavailable in this runtime",
            )
        rows = _broker_read(
            lambda: getter(symbol=symbol),
            ReasonCode.DATA_UNAVAILABLE,
            f"MT5 positions_get read failed for {symbol}",
        )
        if rows is None:
            raise MarketDataError(
                ReasonCode.DATA_UNAVAILABLE,
                f"MT5 positions_get returned unknown truth for {symbol}",
            )

        try:
            buy_type = int(getattr(mt5, "POSITION_TYPE_BUY", 0))
            sell_type = int(getattr(mt5, "POSITION_TYPE_SELL", 1))
        except (TypeError, ValueError, OverflowError) as exc:
            raise MarketDataError(
                ReasonCode.DATA_CORRUPT,
                "invalid MT5 position direction constants",
            ) from exc
        positions: list[OpenPositionFacts] = []
        try:
            for row in rows:
                row_symbol = str(_field(row, "symbol", "")).strip()
                if row_symbol != symbol:
                    raise ValueError("position symbol differs from requested symbol")
                raw_type = int(_field(row, "type", -1))
                if raw_type == buy_type:
                    direction = Direction.BUY
                elif raw_type == sell_type:
                    direction = Direction.SELL
                else:
                    raise ValueError("unsupported MT5 position direction")

                magic_raw = _field(row, "magic")
                comment_raw = _field(row, "comment")
                positions.append(
                    OpenPositionFacts(
                        ticket=int(_field(row, "ticket", 0)),
                        symbol=row_symbol,
                        direction=direction,
                        volume=float(_field(row, "volume", 0.0)),
                        price_open=float(_field(row, "price_open", 0.0)),
                        stop_loss=_optional_positive_price(_field(row, "sl", 0.0)),
                        take_profit=_optional_positive_price(_field(row, "tp", 0.0)),
                        magic=None if magic_raw is None else int(magic_raw),
                        comment=None if comment_raw is None else str(comment_raw),
                    )
                )
        except (TypeError, ValueError, OverflowError) as exc:
            raise MarketDataError(
                ReasonCode.DATA_CORRUPT,
                f"invalid open-position payload for {symbol}",
            ) from exc

        positions.sort(key=lambda position: position.ticket)
        if len({position.ticket for position in positions}) != len(positions):
            raise MarketDataError(
                ReasonCode.DATA_CORRUPT,
                f"duplicate open-position ticket returned for {symbol}",
            )
        return tuple(positions)

    def completed_candles(self, symbol: str, timeframe: Timeframe, count: int) -> CandleSeries:
        """Read completed candles only; MT5 bar position 0 is intentionally excluded."""

        if count <= 0:
            raise ValueError("count must be positive")

        mt5 = self._require_ready()
        mt5_timeframe = self._timeframe_constant(mt5, timeframe)
        rates = _broker_read(
            lambda: mt5.copy_rates_from_pos(symbol, mt5_timeframe, 1, count),
            ReasonCode.DATA_UNAVAILABLE,
            f"MT5 candle read failed for {symbol}/{timeframe}",
        )
        if rates is None:
            raise MarketDataError(
                ReasonCode.DATA_UNAVAILABLE,
                f"no completed {timeframe} candles available for {symbol}",
            )

        candles: list[Candle] = []
        try:
            for row in rates:
                candles.append(
                    Candle(
                        time_utc=_utc_from_epoch(_field(row, "time")),
                        open=float(_field(row, "open")),
                        high=float(_field(row, "high")),
                        low=float(_field(row, "low")),
                        close=float(_field(row, "close")),
                        tick_volume=int(_field(row, "tick_volume", 0)),
                        spread_points=int(_field(row, "spread", 0)),
                        real_volume=int(_field(row, "real_volume", 0)),
                    )
                )
        except (TypeError, ValueError, OSError, OverflowError) as exc:
            raise MarketDataError(
                ReasonCode.DATA_CORRUPT,
                f"invalid {timeframe} candle payload for {symbol}",
            ) from exc

        if not candles:
            raise MarketDataError(
                ReasonCode.DATA_INSUFFICIENT,
                f"zero completed {timeframe} candles returned for {symbol}",
            )

        candles.sort(key=lambda candle: candle.time_utc)
        try:
            return CandleSeries(timeframe=timeframe, candles=tuple(candles))
        except ValueError as exc:
            raise MarketDataError(
                ReasonCode.DATA_CORRUPT,
                f"non-chronological or duplicate {timeframe} candle data for {symbol}",
            ) from exc

    @staticmethod
    def _timeframe_constant(mt5: Any, timeframe: Timeframe) -> int:
        name = f"TIMEFRAME_{timeframe.value}"
        value = getattr(mt5, name, None)
        if value is None:
            raise MarketDataError(ReasonCode.DATA_UNAVAILABLE, f"MT5 constant missing: {name}")
        try:
            return int(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise MarketDataError(
                ReasonCode.DATA_CORRUPT,
                f"MT5 timeframe constant is invalid: {name}",
            ) from exc


def _broker_read(
    operation: Callable[[], Any],
    reason: ReasonCode,
    message: str,
) -> Any:
    """Convert an SDK read exception into an explicit typed boundary failure."""

    try:
        return operation()
    except MarketDataError:
        raise
    except Exception as exc:
        raise MarketDataError(reason, message) from exc


def _request_filling_mode(info: Any, mt5: Any) -> int | None:
    """Translate broker filling-policy flags into a request-ready enum.

    MT5 exposes ``SYMBOL_FILLING_MODE`` as a bitmask of allowed policies, while
    ``MqlTradeRequest.type_filling`` expects an ``ORDER_FILLING_*`` enum. Passing
    the bitmask through unchanged can select the wrong policy or be rejected by
    the broker, so an incomplete mapping remains unknown and fails closed.
    """

    allowed_raw = getattr(info, "filling_mode", None)
    execution_raw = getattr(info, "trade_exemode", None)
    if allowed_raw is None or execution_raw is None:
        return None
    try:
        allowed = int(allowed_raw)
        execution = int(execution_raw)
        symbol_fok = int(getattr(mt5, "SYMBOL_FILLING_FOK"))
        symbol_ioc = int(getattr(mt5, "SYMBOL_FILLING_IOC"))
        market_execution = int(getattr(mt5, "SYMBOL_TRADE_EXECUTION_MARKET"))
        order_fok = int(getattr(mt5, "ORDER_FILLING_FOK"))
        order_ioc = int(getattr(mt5, "ORDER_FILLING_IOC"))
        order_return = int(getattr(mt5, "ORDER_FILLING_RETURN"))
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None

    if allowed < 0 or execution < 0:
        return None
    if execution != market_execution:
        # RETURN is enabled for non-market execution modes according to the MT5
        # contract; using the request enum avoids treating flags as enum values.
        return order_return
    if allowed & symbol_fok:
        return order_fok
    if allowed & symbol_ioc:
        return order_ioc
    return None
