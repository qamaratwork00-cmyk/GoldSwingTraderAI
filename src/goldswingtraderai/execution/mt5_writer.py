"""Narrow MetaTrader 5 irreversible-write adapter.

The writer builds/checks requests and performs one order_send call. It never retries,
never decides strategy/risk permission and never hides an ambiguous acknowledgement.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from goldswingtraderai.domain.enums import Direction
from goldswingtraderai.domain.market import Quote
from goldswingtraderai.execution.models import ExecutionAction, ExecutionIntent


class BrokerSubmitClass(StrEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class MT5WriteConfig:
    magic: int
    deviation_points: int
    comment_prefix: str = "GSTAI"

    def __post_init__(self) -> None:
        if self.magic <= 0:
            raise ValueError("MT5 magic must be a positive explicit integer")
        if self.deviation_points < 0:
            raise ValueError("MT5 deviation points cannot be negative")
        prefix = self.comment_prefix.strip()
        if not prefix or len(prefix) > 12:
            raise ValueError("MT5 comment prefix must contain 1-12 characters")


@dataclass(frozen=True, slots=True)
class BrokerCheckResult:
    passed: bool
    reason: str
    retcode: int | None
    comment: str | None
    required_margin: float | None
    request: dict[str, Any]


@dataclass(frozen=True, slots=True)
class BrokerSubmitResult:
    classification: BrokerSubmitClass
    retcode: int | None
    broker_ticket: int | None
    deal_ticket: int | None
    comment: str | None


class MT5Writer:
    """Injected official-MT5 boundary; caller owns initialization and permission."""

    def __init__(self, mt5_module: Any, config: MT5WriteConfig) -> None:
        self._mt5 = mt5_module
        self.config = config

    def precheck(self, intent: ExecutionIntent, quote: Quote) -> BrokerCheckResult:
        request = self.build_request(intent, quote)
        required_margin = self._required_margin(intent, quote)
        if intent.action in {ExecutionAction.OPEN, ExecutionAction.CLOSE} and intent.filling_mode is None:
            return BrokerCheckResult(
                passed=False,
                reason="FILLING_MODE_UNKNOWN",
                retcode=None,
                comment=None,
                required_margin=required_margin,
                request=request,
            )

        order_check = getattr(self._mt5, "order_check", None)
        if not callable(order_check):
            return BrokerCheckResult(
                passed=False,
                reason="ORDER_CHECK_UNAVAILABLE",
                retcode=None,
                comment=None,
                required_margin=required_margin,
                request=request,
            )
        try:
            result = order_check(request)
        except Exception as exc:
            return BrokerCheckResult(
                passed=False,
                reason=f"ORDER_CHECK_EXCEPTION:{type(exc).__name__}",
                retcode=None,
                comment=None,
                required_margin=required_margin,
                request=request,
            )
        if result is None:
            return BrokerCheckResult(
                passed=False,
                reason="ORDER_CHECK_NO_RESULT",
                retcode=None,
                comment=None,
                required_margin=required_margin,
                request=request,
            )

        retcode = _int_field(result, "retcode")
        comment = _text_field(result, "comment")
        passed = retcode == 0
        return BrokerCheckResult(
            passed=passed,
            reason="ORDER_CHECK_PASS" if passed else "ORDER_CHECK_REJECTED",
            retcode=retcode,
            comment=comment,
            required_margin=required_margin,
            request=request,
        )

    def send_once(self, request: Mapping[str, Any]) -> BrokerSubmitResult:
        """Perform exactly one irreversible order_send call and classify its result."""

        order_send = getattr(self._mt5, "order_send", None)
        if not callable(order_send):
            return BrokerSubmitResult(
                classification=BrokerSubmitClass.UNKNOWN,
                retcode=None,
                broker_ticket=None,
                deal_ticket=None,
                comment="order_send unavailable",
            )
        try:
            result = order_send(dict(request))
        except Exception as exc:
            return BrokerSubmitResult(
                classification=BrokerSubmitClass.UNKNOWN,
                retcode=None,
                broker_ticket=None,
                deal_ticket=None,
                comment=f"order_send exception: {type(exc).__name__}",
            )
        if result is None:
            return BrokerSubmitResult(
                classification=BrokerSubmitClass.UNKNOWN,
                retcode=None,
                broker_ticket=None,
                deal_ticket=None,
                comment="order_send returned no acknowledgement",
            )

        retcode = _int_field(result, "retcode")
        broker_ticket = _positive_ticket(result, "order") or _positive_ticket(result, "position")
        deal_ticket = _positive_ticket(result, "deal")
        comment = _text_field(result, "comment")
        if retcode is None:
            classification = BrokerSubmitClass.UNKNOWN
        elif retcode in self._accepted_retcodes():
            classification = BrokerSubmitClass.ACCEPTED
        else:
            classification = BrokerSubmitClass.REJECTED
        return BrokerSubmitResult(
            classification=classification,
            retcode=retcode,
            broker_ticket=broker_ticket,
            deal_ticket=deal_ticket,
            comment=comment,
        )

    def build_request(self, intent: ExecutionIntent, quote: Quote) -> dict[str, Any]:
        if quote.symbol != intent.symbol:
            raise ValueError("execution quote symbol does not match intent symbol")
        if intent.action is ExecutionAction.MODIFY:
            return self._modify_request(intent)
        if intent.filling_mode is None:
            # Keep the request inspectable for diagnostics/precheck, but precheck
            # prevents irreversible send until filling mode is explicitly known.
            filling_mode = None
        else:
            filling_mode = intent.filling_mode

        is_open = intent.action is ExecutionAction.OPEN
        order_direction = intent.direction if is_open else _opposite(intent.direction)
        price = quote.ask if order_direction is Direction.BUY else quote.bid
        request: dict[str, Any] = {
            "action": self._constant("TRADE_ACTION_DEAL"),
            "symbol": intent.symbol,
            "volume": intent.volume,
            "type": self._order_type(order_direction),
            "price": price,
            "deviation": self.config.deviation_points,
            "magic": self.config.magic,
            "comment": self.intent_comment(intent),
            "type_time": self._constant("ORDER_TIME_GTC"),
        }
        if filling_mode is not None:
            request["type_filling"] = filling_mode
        if intent.stop_loss is not None and is_open:
            request["sl"] = intent.stop_loss
        if intent.take_profit is not None and is_open:
            request["tp"] = intent.take_profit
        if intent.action is ExecutionAction.CLOSE:
            request["position"] = intent.position_ticket
        return request

    def intent_comment(self, intent: ExecutionIntent) -> str:
        """Compact reconciliation aid; durable intent ID remains real authority."""

        return f"{self.config.comment_prefix}:{intent.intent_id.value[:12]}"

    def required_margin_for(
        self,
        *,
        direction: Direction,
        symbol: str,
        volume: float,
        quote: Quote,
    ) -> float | None:
        """Return broker-calculated margin when MT5 exposes that authority.

        Risk may use this value as a second pass after lot sizing. A missing or
        invalid broker calculation remains ``None`` and is never replaced with a
        guessed margin value.
        """

        if volume <= 0 or not symbol.strip():
            raise ValueError("margin request requires positive volume and symbol")
        if quote.symbol != symbol:
            raise ValueError("margin quote symbol does not match requested symbol")
        order_type = self._order_type(direction)
        price = quote.ask if direction is Direction.BUY else quote.bid
        return self._calculate_required_margin(order_type, symbol, volume, price)

    def _modify_request(self, intent: ExecutionIntent) -> dict[str, Any]:
        return {
            "action": self._constant("TRADE_ACTION_SLTP"),
            "symbol": intent.symbol,
            "position": intent.position_ticket,
            "sl": intent.stop_loss or 0.0,
            "tp": intent.take_profit or 0.0,
            "magic": self.config.magic,
            "comment": self.intent_comment(intent),
        }

    def _required_margin(self, intent: ExecutionIntent, quote: Quote) -> float | None:
        if intent.action is not ExecutionAction.OPEN:
            return 0.0
        price = quote.ask if intent.direction is Direction.BUY else quote.bid
        return self._calculate_required_margin(
            self._order_type(intent.direction),
            intent.symbol,
            intent.volume,
            price,
        )

    def _calculate_required_margin(
        self,
        order_type: int,
        symbol: str,
        volume: float,
        price: float,
    ) -> float | None:
        calculator = getattr(self._mt5, "order_calc_margin", None)
        if not callable(calculator):
            return None
        try:
            value = calculator(order_type, symbol, volume, price)
        except Exception:
            return None
        if value is None:
            return None
        try:
            margin = float(value)
        except (TypeError, ValueError):
            return None
        return margin if margin >= 0 else None

    def _order_type(self, direction: Direction) -> int:
        if direction is Direction.BUY:
            return self._constant("ORDER_TYPE_BUY")
        if direction is Direction.SELL:
            return self._constant("ORDER_TYPE_SELL")
        raise ValueError("MT5 market order requires BUY or SELL direction")

    def _constant(self, name: str) -> int:
        value = getattr(self._mt5, name, None)
        if value is None:
            raise ValueError(f"required MT5 constant is unavailable: {name}")
        return int(value)

    def _accepted_retcodes(self) -> frozenset[int]:
        names = ("TRADE_RETCODE_DONE", "TRADE_RETCODE_DONE_PARTIAL", "TRADE_RETCODE_PLACED")
        values = {
            int(value)
            for name in names
            if (value := getattr(self._mt5, name, None)) is not None
        }
        return frozenset(values)


def _opposite(direction: Direction) -> Direction:
    if direction is Direction.BUY:
        return Direction.SELL
    if direction is Direction.SELL:
        return Direction.BUY
    raise ValueError("position direction must be BUY or SELL")


def _field(row: Any, name: str, default: Any = None) -> Any:
    if isinstance(row, Mapping):
        return row.get(name, default)
    return getattr(row, name, default)


def _int_field(row: Any, name: str) -> int | None:
    value = _field(row, name)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _positive_ticket(row: Any, name: str) -> int | None:
    value = _int_field(row, name)
    return value if value is not None and value > 0 else None


def _text_field(row: Any, name: str) -> str | None:
    value = _field(row, name)
    return None if value is None else str(value)
