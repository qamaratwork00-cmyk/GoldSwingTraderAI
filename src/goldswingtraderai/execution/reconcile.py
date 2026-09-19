"""Broker-truth reconciliation for consumed/ambiguous Execution Intents."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from math import isclose
from typing import Any

from goldswingtraderai.domain.enums import Direction
from goldswingtraderai.execution.intent_store import ExecutionIntentRepository
from goldswingtraderai.execution.models import (
    ExecutionAction,
    ExecutionIntent,
    IntentState,
    mark_accepted_unknown,
    reconcile_accepted,
    reconcile_not_created,
)
from goldswingtraderai.execution.mt5_writer import MT5WriteConfig


class ReconciliationStatus(StrEnum):
    VERIFIED_ACCEPTED = "VERIFIED_ACCEPTED"
    VERIFIED_NOT_CREATED = "VERIFIED_NOT_CREATED"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    status: ReconciliationStatus
    reason: str
    broker_ticket: int | None = None


class MT5Reconciler:
    """Read broker positions/orders/deals and resolve one ambiguous intent."""

    def __init__(self, mt5_module: Any, config: MT5WriteConfig) -> None:
        self._mt5 = mt5_module
        self.config = config

    def reconcile(
        self,
        intent: ExecutionIntent,
        now_utc: datetime,
        *,
        allow_verified_not_created: bool = False,
        history_lookback: timedelta = timedelta(minutes=5),
    ) -> ReconciliationResult:
        _require_utc(now_utc)
        if intent.state not in {IntentState.SUBMITTING, IntentState.ACCEPTED_UNKNOWN}:
            raise ValueError("reconciliation requires SUBMITTING or ACCEPTED_UNKNOWN intent")
        if history_lookback <= timedelta(0):
            raise ValueError("history lookback must be positive")

        try:
            positions = self._positions(intent.symbol)
            orders = self._orders(intent.symbol)
            deals = self._deals(intent.created_at_utc - history_lookback, now_utc)
        except Exception:
            return ReconciliationResult(
                ReconciliationStatus.UNRESOLVED,
                "RECONCILIATION_READ_FAILED",
            )
        if positions is None or orders is None or deals is None:
            return ReconciliationResult(
                ReconciliationStatus.UNRESOLVED,
                "RECONCILIATION_TRUTH_INCOMPLETE",
            )

        accepted = self._accepted_evidence(intent, positions, orders, deals)
        if accepted is not None:
            row, reason = accepted
            broker_ticket = _ticket(row) or intent.position_ticket
            if broker_ticket is None or broker_ticket <= 0:
                return ReconciliationResult(
                    ReconciliationStatus.UNRESOLVED,
                    "MATCHED_BROKER_EVIDENCE_WITHOUT_TICKET",
                )
            return ReconciliationResult(
                ReconciliationStatus.VERIFIED_ACCEPTED,
                reason,
                broker_ticket=broker_ticket,
            )

        if allow_verified_not_created and self._can_prove_not_created(intent, positions):
            return ReconciliationResult(
                ReconciliationStatus.VERIFIED_NOT_CREATED,
                "BROKER_PROVED_INTENT_NOT_APPLIED",
            )
        return ReconciliationResult(
            ReconciliationStatus.UNRESOLVED,
            "NO_MATCH_YET_NOT_PROVEN_ABSENT",
        )

    def apply(
        self,
        repository: ExecutionIntentRepository,
        intent: ExecutionIntent,
        result: ReconciliationResult,
    ) -> ExecutionIntent:
        if result.status is ReconciliationStatus.VERIFIED_ACCEPTED:
            resolved = reconcile_accepted(
                intent,
                broker_ticket=result.broker_ticket,
                message=result.reason,
            )
            repository.save(resolved, event_type="INTENT_RECONCILED_ACCEPTED")
            return resolved
        if result.status is ReconciliationStatus.VERIFIED_NOT_CREATED:
            resolved = reconcile_not_created(intent, message=result.reason)
            repository.save(resolved, event_type="INTENT_RECONCILED_NOT_CREATED")
            return resolved
        if intent.state is IntentState.SUBMITTING:
            unresolved = mark_accepted_unknown(intent, message=result.reason)
            repository.save(unresolved, event_type="INTENT_RECONCILIATION_UNRESOLVED")
            return unresolved
        repository.save(intent, event_type="INTENT_RECONCILIATION_UNRESOLVED")
        return intent

    def _accepted_evidence(
        self,
        intent: ExecutionIntent,
        positions: Sequence[Any],
        orders: Sequence[Any],
        deals: Sequence[Any],
    ) -> tuple[Any, str] | None:
        if intent.action is ExecutionAction.MODIFY:
            position = _by_ticket(positions, intent.position_ticket)
            if position is not None and _levels_match(position, intent):
                return position, "BROKER_POSITION_LEVELS_MATCH_MODIFY_INTENT"
            return None

        if intent.action is ExecutionAction.CLOSE:
            tagged_deal = self._find_tagged(intent, deals, closing=True)
            if tagged_deal is not None:
                return tagged_deal, "BROKER_CLOSE_DEAL_MATCHED"
            return None

        tagged = self._find_tagged(intent, (*positions, *orders, *deals), closing=False)
        if tagged is not None:
            return tagged, "BROKER_OPEN_EXPOSURE_MATCHED"
        return None

    def _can_prove_not_created(
        self,
        intent: ExecutionIntent,
        positions: Sequence[Any],
    ) -> bool:
        if intent.action is ExecutionAction.OPEN:
            return True
        position = _by_ticket(positions, intent.position_ticket)
        if intent.action is ExecutionAction.MODIFY:
            # If the exact managed position still exists and its SL/TP differ from
            # the requested levels, complete broker truth can prove modify did not apply.
            return position is not None and not _levels_match(position, intent)
        if intent.action is ExecutionAction.CLOSE:
            # If the exact position still exists, the close was not applied. If it
            # vanished without our tagged deal, attribution is ambiguous (e.g. manual close).
            return position is not None
        return False

    def _find_tagged(
        self,
        intent: ExecutionIntent,
        rows: Sequence[Any],
        *,
        closing: bool,
    ) -> Any | None:
        tag = f"{self.config.comment_prefix}:{intent.intent_id.value[:12]}"
        matches: list[Any] = []
        for row in rows:
            if _text(row, "symbol") not in {None, intent.symbol}:
                continue
            if _int(row, "magic") not in {None, self.config.magic}:
                continue
            if tag not in (_text(row, "comment") or ""):
                continue
            volume = _float(row, "volume")
            if volume is not None and not isclose(volume, intent.volume, rel_tol=0.0, abs_tol=1e-8):
                continue
            if not self._direction_matches(intent, row, closing=closing):
                continue
            if closing and intent.position_ticket is not None:
                position_id = _int(row, "position_id")
                if position_id not in {None, intent.position_ticket}:
                    continue
            matches.append(row)

        # One intent may appear in more than one broker collection (for example
        # an order and its resulting position). That is safe when the evidence
        # resolves to one ticket; distinct tickets are ambiguous and must stay
        # unresolved rather than selecting broker iteration order.
        tickets = {_ticket(row) for row in matches if _ticket(row) is not None}
        if len(tickets) > 1:
            return None
        return matches[0] if matches else None

    def _direction_matches(self, intent: ExecutionIntent, row: Any, *, closing: bool) -> bool:
        row_type = _int(row, "type")
        if row_type is None:
            return True
        buy_type = getattr(self._mt5, "POSITION_TYPE_BUY", getattr(self._mt5, "ORDER_TYPE_BUY", 0))
        sell_type = getattr(self._mt5, "POSITION_TYPE_SELL", getattr(self._mt5, "ORDER_TYPE_SELL", 1))
        expected = intent.direction
        if closing:
            expected = Direction.SELL if intent.direction is Direction.BUY else Direction.BUY
        return row_type == (int(buy_type) if expected is Direction.BUY else int(sell_type))

    def _positions(self, symbol: str) -> tuple[Any, ...] | None:
        getter = getattr(self._mt5, "positions_get", None)
        if not callable(getter):
            return None
        value = getter(symbol=symbol)
        return None if value is None else tuple(value)

    def _orders(self, symbol: str) -> tuple[Any, ...] | None:
        getter = getattr(self._mt5, "orders_get", None)
        if not callable(getter):
            return None
        value = getter(symbol=symbol)
        return None if value is None else tuple(value)

    def _deals(self, start_utc: datetime, end_utc: datetime) -> tuple[Any, ...] | None:
        getter = getattr(self._mt5, "history_deals_get", None)
        if not callable(getter):
            return None
        value = getter(start_utc, end_utc)
        return None if value is None else tuple(value)


def _levels_match(row: Any, intent: ExecutionIntent) -> bool:
    for field, expected in (("sl", intent.stop_loss), ("tp", intent.take_profit)):
        if expected is None:
            continue
        actual = _float(row, field)
        if actual is None or not isclose(actual, expected, rel_tol=0.0, abs_tol=1e-8):
            return False
    return True


def _by_ticket(rows: Sequence[Any], ticket: int | None) -> Any | None:
    if ticket is None:
        return None
    matches = [row for row in rows if _ticket(row) == ticket]
    return matches[0] if len(matches) == 1 else None


def _field(row: Any, name: str, default: Any = None) -> Any:
    if isinstance(row, Mapping):
        return row.get(name, default)
    return getattr(row, name, default)


def _text(row: Any, name: str) -> str | None:
    value = _field(row, name)
    return None if value is None else str(value)


def _int(row: Any, name: str) -> int | None:
    value = _field(row, name)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float(row: Any, name: str) -> float | None:
    value = _field(row, name)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _ticket(row: Any) -> int | None:
    for name in ("ticket", "position_id", "order"):
        value = _int(row, name)
        if value is not None and value > 0:
            return value
    return None


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("reconciliation time must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("reconciliation time must be UTC")
