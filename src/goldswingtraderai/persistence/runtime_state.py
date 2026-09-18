"""Typed persistence adapters for critical V1 runtime state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
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
            utc_day=date.fromisoformat(str(payload["utc_day"])),
            day_start_equity=float(payload["day_start_equity"]),
            net_non_trading_cash_flow=float(payload["net_non_trading_cash_flow"]),
            cycle_reference_equity=float(payload["cycle_reference_equity"]),
            cycle_start_safety_pl=float(payload["cycle_start_safety_pl"]),
            manual_reset_enabled=bool(payload["manual_reset_enabled"]),
            manual_reset_count=int(payload["manual_reset_count"]),
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
            consecutive_losses=int(payload["consecutive_losses"]),
            triggered_at_utc=_dt_in(payload.get("triggered_at_utc")),
            cooldown_until_utc=_dt_in(payload.get("cooldown_until_utc")),
        )
    except (TypeError, ValueError) as exc:
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
            episode_id=EntityId.parse(str(payload["episode_id"])),
            entries_taken=int(payload["entries_taken"]),
            losses=int(payload["losses"]),
            locked=bool(payload["locked"]),
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
            opportunity_id=EntityId.parse(str(payload["opportunity_id"])),
            episode_id=EntityId.parse(str(payload["episode_id"])),
            direction=Direction(str(payload["direction"])),
            stage=OpportunityStage(str(payload["stage"])),
            created_at_utc=_dt_required(payload["created_at_utc"]),
            updated_at_utc=_dt_required(payload["updated_at_utc"]),
            opportunity_score=float(payload["opportunity_score"]),
            thesis_score=float(payload["thesis_score"]),
            source_families=tuple(
                StrategyFamily(str(value)) for value in payload["source_families"]
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
            plan_id=EntityId.parse(str(payload["plan_id"])),
            opportunity_id=EntityId.parse(str(payload["opportunity_id"])),
            episode_id=EntityId.parse(str(payload["episode_id"])),
            family=StrategyFamily(str(payload["family"])),
            direction=Direction(str(payload["direction"])),
            state=PlanState(str(payload["state"])),
            signal_price=float(payload["signal_price"]),
            approved_entry_reference=float(payload["approved_entry_reference"]),
            invalidation_level=_optional_float(payload.get("invalidation_level")),
            invalidation_source=str(payload["invalidation_source"]),
            initial_stop=_optional_float(payload.get("initial_stop")),
            stop_buffer=_optional_float(payload.get("stop_buffer")),
            stop_quality=StopQuality(str(payload["stop_quality"])),
            original_r_price=_optional_float(payload.get("original_r_price")),
            immediate_obstacle=_target_from_payload(payload.get("immediate_obstacle")),
            primary_target=_target_from_payload(payload.get("primary_target")),
            expansion_target=_target_from_payload(payload.get("expansion_target")),
            runner_target=_target_from_payload(payload.get("runner_target")),
            broker_tp_target=_target_from_payload(payload.get("broker_tp_target")),
            rr_class=RRClass(str(payload["rr_class"])),
            path_quality=float(payload["path_quality"]),
            plan_quality=float(payload["plan_quality"]),
            created_at_utc=_dt_required(payload["created_at_utc"]),
            reason=str(payload["reason"]),
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
            role=TargetRole(str(payload["role"])),
            price=float(payload["price"]),
            quality=float(payload["quality"]),
            source=str(payload["source"]),
            rr=float(payload["rr"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise StateIntegrityError("invalid persisted PlanTarget") from exc


def _dt_out(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat()


def _dt_in(value: Any) -> datetime | None:
    return None if value is None else _dt_required(value)


def _dt_required(value: Any) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise StateIntegrityError("invalid persisted datetime") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise StateIntegrityError("persisted datetime must be timezone-aware UTC")
    return parsed


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)
