"""Durable Execution Intent lifecycle built on the Phase-6 StateStore."""

from __future__ import annotations

from typing import Any

from goldswingtraderai.domain.enums import Direction, HardDecision
from goldswingtraderai.domain.ids import EntityId
from goldswingtraderai.execution.models import ExecutionAction, ExecutionIntent, IntentState
from goldswingtraderai.persistence import StateIntegrityError, StateStore


INTENT_SCHEMA_VERSION = 1


class ExecutionIntentRepository:
    """Persist the current execution intent for one managed account/symbol scope."""

    def __init__(self, store: StateStore, scope: str) -> None:
        cleaned = scope.strip()
        if not cleaned:
            raise ValueError("execution intent scope cannot be empty")
        self.store = store
        self.scope = cleaned

    def save(self, intent: ExecutionIntent, *, event_type: str | None = None) -> None:
        self.store.save_record(
            "execution_intent",
            self.scope,
            _intent_to_payload(intent),
            schema_version=INTENT_SCHEMA_VERSION,
            event_type=event_type or f"INTENT_{intent.state.value}",
        )

    def load(self) -> ExecutionIntent | None:
        record = self.store.load_record(
            "execution_intent",
            self.scope,
            expected_schema_version=INTENT_SCHEMA_VERSION,
        )
        return None if record is None else _intent_from_payload(record.payload)

    def lifecycle_permission(self) -> tuple[HardDecision, str]:
        """Return whether a fresh independent intent may be created."""

        current = self.load()
        if current is None or current.lifecycle_clear_for_new_intent:
            return HardDecision.PASS, "ORDER_LIFECYCLE_CLEAR"
        if current.state in {IntentState.SUBMITTING, IntentState.ACCEPTED_UNKNOWN}:
            return HardDecision.UNKNOWN, "ORDER_ACK_UNKNOWN"
        return HardDecision.BLOCK, "ORDER_LIFECYCLE_PENDING"


def _intent_to_payload(intent: ExecutionIntent) -> dict[str, Any]:
    return {
        "intent_id": str(intent.intent_id),
        "action": intent.action.value,
        "account_login": intent.account_login,
        "account_server": intent.account_server,
        "symbol": intent.symbol,
        "direction": intent.direction.value,
        "volume": intent.volume,
        "approved_entry_reference": intent.approved_entry_reference,
        "stop_loss": intent.stop_loss,
        "take_profit": intent.take_profit,
        "opportunity_id": str(intent.opportunity_id),
        "episode_id": str(intent.episode_id),
        "trade_plan_id": str(intent.trade_plan_id),
        "controller_id": str(intent.controller_id),
        "fencing_epoch": intent.fencing_epoch,
        "created_at_utc": intent.created_at_utc.isoformat(),
        "state": intent.state.value,
        "submit_attempts": intent.submit_attempts,
        "broker_ticket": intent.broker_ticket,
        "broker_retcode": intent.broker_retcode,
        "result_message": intent.result_message,
        "position_ticket": intent.position_ticket,
        "filling_mode": intent.filling_mode,
    }


def _intent_from_payload(payload: dict[str, Any]) -> ExecutionIntent:
    from datetime import datetime

    try:
        return ExecutionIntent(
            intent_id=EntityId.parse(str(payload["intent_id"])),
            action=ExecutionAction(str(payload["action"])),
            account_login=int(payload["account_login"]),
            account_server=str(payload["account_server"]),
            symbol=str(payload["symbol"]),
            direction=Direction(str(payload["direction"])),
            volume=float(payload["volume"]),
            approved_entry_reference=float(payload["approved_entry_reference"]),
            stop_loss=_optional_float(payload.get("stop_loss")),
            take_profit=_optional_float(payload.get("take_profit")),
            opportunity_id=EntityId.parse(str(payload["opportunity_id"])),
            episode_id=EntityId.parse(str(payload["episode_id"])),
            trade_plan_id=EntityId.parse(str(payload["trade_plan_id"])),
            controller_id=EntityId.parse(str(payload["controller_id"])),
            fencing_epoch=int(payload["fencing_epoch"]),
            created_at_utc=datetime.fromisoformat(str(payload["created_at_utc"])),
            state=IntentState(str(payload["state"])),
            submit_attempts=int(payload["submit_attempts"]),
            broker_ticket=_optional_int(payload.get("broker_ticket")),
            broker_retcode=_optional_int(payload.get("broker_retcode")),
            result_message=_optional_text(payload.get("result_message")),
            position_ticket=_optional_int(payload.get("position_ticket")),
            filling_mode=_optional_int(payload.get("filling_mode")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise StateIntegrityError("invalid persisted ExecutionIntent") from exc


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _optional_int(value: Any) -> int | None:
    return None if value is None else int(value)


def _optional_text(value: Any) -> str | None:
    return None if value is None else str(value)
