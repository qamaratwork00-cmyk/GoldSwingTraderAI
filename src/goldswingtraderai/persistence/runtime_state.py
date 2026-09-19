"""Typed persistence adapters for critical V1 runtime state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from math import isfinite
from typing import Any

from goldswingtraderai.decisions.opportunity import Opportunity
from goldswingtraderai.decisions.trade_plan import (
    PlanState,
    PlanTarget,
    RRClass,
    StopQuality,
    TargetRole,
    TradePlan,
)
from goldswingtraderai.domain.enums import Direction, OpportunityStage, StrategyFamily
from goldswingtraderai.domain.ids import EntityId
from goldswingtraderai.persistence.store import StateIntegrityError, StateStore
from goldswingtraderai.risk.state import CooldownState, EpisodeRiskState, RiskDayState


RECORD_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class RecoveryBundle:
    risk_day: RiskDayState | None
    cooldown: CooldownState | None
    active_opportunity: Opportunity | None
    trade_plan: TradePlan | None
    episode_risk: EpisodeRiskState | None


class RuntimeStateRepository:
    """Persist/restore critical state for one managed account+symbol scope."""

    def __init__(self, store: StateStore, scope: str) -> None:
        cleaned = scope.strip()
        if not cleaned:
            raise ValueError("runtime state scope cannot be empty")
        self.store = store
        self.scope = cleaned

    def save_risk_day(self, state: RiskDayState) -> None:
        self.store.save_record(
            "risk_day",
            self.scope,
            _risk_day_to_payload(state),
            schema_version=RECORD_SCHEMA_VERSION,
            event_type="RISK_DAY_SAVED",
        )

    def load_risk_day(self) -> RiskDayState | None:
        record = self.store.load_record(
            "risk_day",
            self.scope,
            expected_schema_version=RECORD_SCHEMA_VERSION,
        )
        return None if record is None else _risk_day_from_payload(record.payload)

    def save_cooldown(self, state: CooldownState) -> None:
        self.store.save_record(
            "cooldown",
            self.scope,
            _cooldown_to_payload(state),
            schema_version=RECORD_SCHEMA_VERSION,
            event_type="COOLDOWN_SAVED",
        )

    def load_cooldown(self) -> CooldownState | None:
        record = self.store.load_record(
            "cooldown",
            self.scope,
            expected_schema_version=RECORD_SCHEMA_VERSION,
        )
        return None if record is None else _cooldown_from_payload(record.payload)

    def save_episode_risk(self, state: EpisodeRiskState) -> None:
        self.store.save_record(
            "episode_risk",
            self._episode_key(state.episode_id),
            _episode_to_payload(state),
            schema_version=RECORD_SCHEMA_VERSION,
            event_type="EPISODE_RISK_SAVED",
        )

    def load_episode_risk(self, episode_id: EntityId) -> EpisodeRiskState | None:
        record = self.store.load_record(
            "episode_risk",
            self._episode_key(episode_id),
            expected_schema_version=RECORD_SCHEMA_VERSION,
        )
        return None if record is None else _episode_from_payload(record.payload)

    def save_active_opportunity(self, opportunity: Opportunity) -> None:
        self.store.save_record(
            "active_opportunity",
            self.scope,
            _opportunity_to_payload(opportunity),
            schema_version=RECORD_SCHEMA_VERSION,
            event_type="OPPORTUNITY_SAVED",
        )

    def load_active_opportunity(self) -> Opportunity | None:
        record = self.store.load_record(
            "active_opportunity",
            self.scope,
            expected_schema_version=RECORD_SCHEMA_VERSION,
        )
        return None if record is None else _opportunity_from_payload(record.payload)

    def clear_active_opportunity(self) -> None:
        self.store.delete_record(
            "active_opportunity",
            self.scope,
            event_type="OPPORTUNITY_CLEARED",
        )

    def save_trade_plan(self, plan: TradePlan) -> None:
        self.store.save_record(
            "trade_plan",
            self.scope,
            _trade_plan_to_payload(plan),
            schema_version=RECORD_SCHEMA_VERSION,
            event_type="TRADE_PLAN_SAVED",
        )

    def load_trade_plan(self) -> TradePlan | None:
        record = self.store.load_record(
            "trade_plan",
            self.scope,
            expected_schema_version=RECORD_SCHEMA_VERSION,
        )
        return None if record is None else _trade_plan_from_payload(record.payload)

    def clear_trade_plan(self) -> None:
        self.store.delete_record(
            "trade_plan",
            self.scope,
            event_type="TRADE_PLAN_CLEARED",
        )

    def load_recovery_bundle(self) -> RecoveryBundle:
        """Validate storage, restore current state and reject broken lineage."""

        self.store.integrity_check()
        risk_day = self.load_risk_day()
        cooldown = self.load_cooldown()
        opportunity = self.load_active_opportunity()
        plan = self.load_trade_plan()

        if plan is not None and opportunity is None:
            raise StateIntegrityError("stored Trade Plan has no active Opportunity context")
        if plan is not None and opportunity is not None:
            if plan.opportunity_id != opportunity.opportunity_id:
                raise StateIntegrityError("Trade Plan/Opportunity identity mismatch")
            if plan.episode_id != opportunity.episode_id:
                raise StateIntegrityError("Trade Plan/Market Episode identity mismatch")

        episode = self.load_episode_risk(opportunity.episode_id) if opportunity is not None else None
        if episode is not None and opportunity is not None and episode.episode_id != opportunity.episode_id:
            raise StateIntegrityError("Episode risk identity mismatch")

        return RecoveryBundle(
            risk_day=risk_day,
            cooldown=cooldown,
            active_opportunity=opportunity,
            trade_plan=plan,
            episode_risk=episode,
        )

    def _episode_key(self, episode_id: EntityId) -> str:
        return f"{self.scope}:{episode_id}"


def _risk_day_to_payload(state: RiskDayState) -> dict[str, Any]:
    return {
        "utc_day": state.utc_day.isoformat(),
        "day_start_equity": state.day_start_equity,
        "net_non_trading_cash_flow": state.net_non_trading_cash_flow,
        "cycle_reference_equity": state.cycle_reference_equity,
        "cycle_start_safety_pl": state.cycle_start_safety_pl,
        "manual_reset_enabled": state.manual_reset_enabled,
        "manual_reset_count": state.manual_reset_count,
    }


def _risk_day_from_payload(payload: dict[str, Any]) -> RiskDayState:
    try:
        return RiskDayState(
            utc_day=date.fromisoformat(_required_text(payload["utc_day"], "utc_day")),
            day_start_equity=_required_float(payload["day_start_equity"], "day_start_equity"),
            net_non_trading_cash_flow=_required_float(
                payload["net_non_trading_cash_flow"],
                "net_non_trading_cash_flow",
            ),
            cycle_reference_equity=_required_float(
                payload["cycle_reference_equity"],
                "cycle_reference_equity",
            ),
            cycle_start_safety_pl=_required_float(
                payload["cycle_start_safety_pl"],
                "cycle_start_safety_pl",
            ),
            manual_reset_enabled=_required_bool(
                payload["manual_reset_enabled"],
                "manual_reset_enabled",
            ),
            manual_reset_count=_required_int(payload["manual_reset_count"], "manual_reset_count"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise StateIntegrityError("invalid persisted RiskDayState") from exc


def _cooldown_to_payload(state: CooldownState) -> dict[str, Any]:
    return {
        "consecutive_losses": state.consecutive_losses,
        "triggered_at_utc": _dt_out(state.triggered_at_utc),
        "cooldown_until_utc": _dt_out(state.cooldown_until_utc),
    }


def _cooldown_from_payload(payload: dict[str, Any]) -> CooldownState:
    try:
        return CooldownState(
            consecutive_losses=_required_int(payload["consecutive_losses"], "consecutive_losses"),
            triggered_at_utc=_dt_in(payload.get("triggered_at_utc")),
            cooldown_until_utc=_dt_in(payload.get("cooldown_until_utc")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise StateIntegrityError("invalid persisted CooldownState") from exc


def _episode_to_payload(state: EpisodeRiskState) -> dict[str, Any]:
    return {
        "episode_id": str(state.episode_id),
        "entries_taken": state.entries_taken,
        "losses": state.losses,
        "locked": state.locked,
    }


def _episode_from_payload(payload: dict[str, Any]) -> EpisodeRiskState:
    try:
        return EpisodeRiskState(
            episode_id=EntityId.parse(_required_text(payload["episode_id"], "episode_id")),
            entries_taken=_required_int(payload["entries_taken"], "entries_taken"),
            losses=_required_int(payload["losses"], "losses"),
            locked=_required_bool(payload["locked"], "locked"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise StateIntegrityError("invalid persisted EpisodeRiskState") from exc


def _opportunity_to_payload(opportunity: Opportunity) -> dict[str, Any]:
    return {
        "opportunity_id": str(opportunity.opportunity_id),
        "episode_id": str(opportunity.episode_id),
        "direction": opportunity.direction.value,
        "stage": opportunity.stage.value,
        "created_at_utc": opportunity.created_at_utc.isoformat(),
        "updated_at_utc": opportunity.updated_at_utc.isoformat(),
        "opportunity_score": opportunity.opportunity_score,
        "thesis_score": opportunity.thesis_score,
        "source_families": [family.value for family in opportunity.source_families],
    }


def _opportunity_from_payload(payload: dict[str, Any]) -> Opportunity:
    try:
        return Opportunity(
            opportunity_id=EntityId.parse(
                _required_text(payload["opportunity_id"], "opportunity_id")
            ),
            episode_id=EntityId.parse(_required_text(payload["episode_id"], "episode_id")),
            direction=Direction(_required_text(payload["direction"], "direction")),
            stage=OpportunityStage(_required_text(payload["stage"], "stage")),
            created_at_utc=_dt_required(payload["created_at_utc"]),
            updated_at_utc=_dt_required(payload["updated_at_utc"]),
            opportunity_score=_required_float(payload["opportunity_score"], "opportunity_score"),
            thesis_score=_required_float(payload["thesis_score"], "thesis_score"),
            source_families=tuple(
                StrategyFamily(_required_text(value, "source_family"))
                for value in _required_sequence(payload["source_families"], "source_families")
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise StateIntegrityError("invalid persisted Opportunity") from exc


def _trade_plan_to_payload(plan: TradePlan) -> dict[str, Any]:
    return {
        "plan_id": str(plan.plan_id),
        "opportunity_id": str(plan.opportunity_id),
        "episode_id": str(plan.episode_id),
        "family": plan.family.value,
        "direction": plan.direction.value,
        "state": plan.state.value,
        "signal_price": plan.signal_price,
        "approved_entry_reference": plan.approved_entry_reference,
        "invalidation_level": plan.invalidation_level,
        "invalidation_source": plan.invalidation_source,
        "initial_stop": plan.initial_stop,
        "stop_buffer": plan.stop_buffer,
        "stop_quality": plan.stop_quality.value,
        "original_r_price": plan.original_r_price,
        "immediate_obstacle": _target_to_payload(plan.immediate_obstacle),
        "primary_target": _target_to_payload(plan.primary_target),
        "expansion_target": _target_to_payload(plan.expansion_target),
        "runner_target": _target_to_payload(plan.runner_target),
        "broker_tp_target": _target_to_payload(plan.broker_tp_target),
        "rr_class": plan.rr_class.value,
        "path_quality": plan.path_quality,
        "plan_quality": plan.plan_quality,
        "created_at_utc": plan.created_at_utc.isoformat(),
        "reason": plan.reason,
    }


def _trade_plan_from_payload(payload: dict[str, Any]) -> TradePlan:
    try:
        return TradePlan(
            plan_id=EntityId.parse(_required_text(payload["plan_id"], "plan_id")),
            opportunity_id=EntityId.parse(
                _required_text(payload["opportunity_id"], "opportunity_id")
            ),
            episode_id=EntityId.parse(_required_text(payload["episode_id"], "episode_id")),
            family=StrategyFamily(_required_text(payload["family"], "family")),
            direction=Direction(_required_text(payload["direction"], "direction")),
            state=PlanState(_required_text(payload["state"], "state")),
            signal_price=_required_float(payload["signal_price"], "signal_price"),
            approved_entry_reference=_required_float(
                payload["approved_entry_reference"],
                "approved_entry_reference",
            ),
            invalidation_level=_optional_float(payload.get("invalidation_level")),
            invalidation_source=_required_text(payload["invalidation_source"], "invalidation_source"),
            initial_stop=_optional_float(payload.get("initial_stop")),
            stop_buffer=_optional_float(payload.get("stop_buffer")),
            stop_quality=StopQuality(_required_text(payload["stop_quality"], "stop_quality")),
            original_r_price=_optional_float(payload.get("original_r_price")),
            immediate_obstacle=_target_from_payload(payload.get("immediate_obstacle")),
            primary_target=_target_from_payload(payload.get("primary_target")),
            expansion_target=_target_from_payload(payload.get("expansion_target")),
            runner_target=_target_from_payload(payload.get("runner_target")),
            broker_tp_target=_target_from_payload(payload.get("broker_tp_target")),
            rr_class=RRClass(_required_text(payload["rr_class"], "rr_class")),
            path_quality=_required_float(payload["path_quality"], "path_quality"),
            plan_quality=_required_float(payload["plan_quality"], "plan_quality"),
            created_at_utc=_dt_required(payload["created_at_utc"]),
            reason=_required_text(payload["reason"], "reason"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise StateIntegrityError("invalid persisted TradePlan") from exc


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


def _dt_out(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat()


def _dt_in(value: Any) -> datetime | None:
    return None if value is None else _dt_required(value)


def _dt_required(value: Any) -> datetime:
    if not isinstance(value, str):
        raise StateIntegrityError("persisted datetime must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise StateIntegrityError("invalid persisted datetime") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise StateIntegrityError("persisted datetime must be timezone-aware UTC")
    return parsed


def _optional_float(value: Any) -> float | None:
    return None if value is None else _required_float(value, "optional float")


def _required_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StateIntegrityError(f"persisted {label} must be non-empty text")
    return value


def _required_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise StateIntegrityError(f"persisted {label} must be boolean")
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


def _required_sequence(value: Any, label: str) -> list[Any] | tuple[Any, ...]:
    if not isinstance(value, (list, tuple)):
        raise StateIntegrityError(f"persisted {label} must be a sequence")
    return value
