"""Durable managed-trade state using the lightweight Phase-6 StateStore."""

from __future__ import annotations

from datetime import datetime
from math import isfinite
from typing import Any

from goldswingtraderai.decisions.trade_plan import PlanTarget, TargetRole
from goldswingtraderai.domain.enums import Direction
from goldswingtraderai.domain.ids import EntityId
from goldswingtraderai.management.models import ManagedTrade, ObjectiveStage
from goldswingtraderai.persistence import StateIntegrityError, StateStore


MANAGED_TRADE_SCHEMA_VERSION = 1


class ManagedTradeRepository:
    def __init__(self, store: StateStore, scope: str) -> None:
        cleaned = scope.strip()
        if not cleaned:
            raise ValueError("managed-trade scope cannot be empty")
        self.store = store
        self.scope = cleaned

    def save(self, trade: ManagedTrade, *, event_type: str = "MANAGED_TRADE_UPDATED") -> None:
        self.store.save_record(
            "managed_trade",
            self.scope,
            _trade_to_payload(trade),
            schema_version=MANAGED_TRADE_SCHEMA_VERSION,
            event_type=event_type,
        )

    def load(self) -> ManagedTrade | None:
        record = self.store.load_record(
            "managed_trade",
            self.scope,
            expected_schema_version=MANAGED_TRADE_SCHEMA_VERSION,
        )
        return None if record is None else _trade_from_payload(record.payload)

    def clear_verified_closed(self) -> None:
        self.store.delete_record(
            "managed_trade",
            self.scope,
            event_type="MANAGED_TRADE_VERIFIED_CLOSED",
        )


def _target_to_payload(target: PlanTarget | None) -> dict[str, Any] | None:
    if target is None:
        return None
    return {
        "role": target.role.value,
        "price": target.price,
        "quality": target.quality,
        "source": target.source,
        "rr": target.rr,
    }


def _target_from_payload(payload: Any) -> PlanTarget | None:
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise StateIntegrityError("invalid persisted PlanTarget")
    try:
        return PlanTarget(
            role=TargetRole(_required_text(payload["role"], "target role")),
            price=_required_float(payload["price"], "target price"),
            quality=_required_float(payload["quality"], "target quality"),
            source=_required_text(payload["source"], "target source"),
            rr=_required_float(payload["rr"], "target rr"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise StateIntegrityError("invalid persisted PlanTarget") from exc


def _trade_to_payload(trade: ManagedTrade) -> dict[str, Any]:
    return {
        "trade_id": str(trade.trade_id),
        "position_ticket": trade.position_ticket,
        "plan_id": str(trade.plan_id),
        "opportunity_id": str(trade.opportunity_id),
        "episode_id": str(trade.episode_id),
        "symbol": trade.symbol,
        "direction": trade.direction.value,
        "volume": trade.volume,
        "entry_price": trade.entry_price,
        "original_stop": trade.original_stop,
        "original_r_price": trade.original_r_price,
        "current_stop": trade.current_stop,
        "broker_tp": trade.broker_tp,
        "primary_target": _target_to_payload(trade.primary_target),
        "expansion_target": _target_to_payload(trade.expansion_target),
        "runner_candidate": _target_to_payload(trade.runner_candidate),
        "active_runner_target": _target_to_payload(trade.active_runner_target),
        "objective_stage": trade.objective_stage.value,
        "opened_at_utc": trade.opened_at_utc.isoformat(),
        "updated_at_utc": trade.updated_at_utc.isoformat(),
    }


def _trade_from_payload(payload: dict[str, Any]) -> ManagedTrade:
    try:
        return ManagedTrade(
            trade_id=EntityId.parse(_required_text(payload["trade_id"], "trade_id")),
            position_ticket=_required_int(payload["position_ticket"], "position_ticket"),
            plan_id=EntityId.parse(_required_text(payload["plan_id"], "plan_id")),
            opportunity_id=EntityId.parse(
                _required_text(payload["opportunity_id"], "opportunity_id")
            ),
            episode_id=EntityId.parse(_required_text(payload["episode_id"], "episode_id")),
            symbol=_required_text(payload["symbol"], "symbol"),
            direction=Direction(_required_text(payload["direction"], "direction")),
            volume=_required_float(payload["volume"], "volume"),
            entry_price=_required_float(payload["entry_price"], "entry_price"),
            original_stop=_required_float(payload["original_stop"], "original_stop"),
            original_r_price=_required_float(payload["original_r_price"], "original_r_price"),
            current_stop=_required_float(payload["current_stop"], "current_stop"),
            broker_tp=_optional_float(payload.get("broker_tp")),
            primary_target=_target_from_payload(payload.get("primary_target")),
            expansion_target=_target_from_payload(payload.get("expansion_target")),
            runner_candidate=_target_from_payload(payload.get("runner_candidate")),
            active_runner_target=_target_from_payload(payload.get("active_runner_target")),
            objective_stage=ObjectiveStage(
                _required_text(payload["objective_stage"], "objective_stage")
            ),
            opened_at_utc=_required_datetime(payload["opened_at_utc"]),
            updated_at_utc=_required_datetime(payload["updated_at_utc"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise StateIntegrityError("invalid persisted ManagedTrade") from exc


def _required_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StateIntegrityError(f"persisted {label} must be non-empty text")
    return value


def _required_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise StateIntegrityError(f"persisted {label} must be an integer")
    return value


def _required_float(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise StateIntegrityError(f"persisted {label} must be numeric")
    parsed = float(value)
    if not isfinite(parsed):
        raise StateIntegrityError(f"persisted {label} must be finite")
    return parsed


def _optional_float(value: Any) -> float | None:
    return None if value is None else _required_float(value, "optional float")


def _required_datetime(value: Any) -> datetime:
    if not isinstance(value, str):
        raise StateIntegrityError("persisted managed-trade timestamp must be an ISO-8601 string")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise StateIntegrityError("invalid persisted managed-trade timestamp") from exc
