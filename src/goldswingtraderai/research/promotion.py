"""Governed challenger lifecycle with one-shot holdout and explicit approval.

Research may advance evidence stages, but this module never grants direct broker
authority. A locked candidate cannot change semantics and still reuse its holdout.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum

from goldswingtraderai.domain.ids import EntityId
from goldswingtraderai.persistence import StateStore


PROMOTION_SCHEMA_VERSION = 1
_PROMOTION_NAMESPACE = "candidate_promotion_registry"


class PromotionStage(StrEnum):
    PROPOSED = "PROPOSED"
    RESEARCHING = "RESEARCHING"
    VALIDATED = "VALIDATED"
    LOCKED = "LOCKED"
    HOLDOUT_PASSED = "HOLDOUT_PASSED"
    HOLDOUT_FAILED = "HOLDOUT_FAILED"
    STRESS_PASSED = "STRESS_PASSED"
    STRESS_FAILED = "STRESS_FAILED"
    SHADOW = "SHADOW"
    DEMO_CANARY = "DEMO_CANARY"
    PROMOTION_READY = "PROMOTION_READY"
    PROMOTED = "PROMOTED"
    REJECTED = "REJECTED"
    ROLLED_BACK = "ROLLED_BACK"
    DISABLED = "DISABLED"


@dataclass(frozen=True, slots=True)
class PromotionRecord:
    candidate_id: EntityId
    stage: PromotionStage
    policy_version: str
    updated_at_utc: datetime
    locked_fingerprint: str | None = None
    holdout_id: str | None = None
    holdout_consumed: bool = False
    rejection_reason: str | None = None
    rollback_target: str | None = None
    promoted_at_utc: datetime | None = None

    def __post_init__(self) -> None:
        if self.candidate_id.kind != "CAND":
            raise ValueError("promotion record requires CAND entity id")
        if not self.policy_version.strip():
            raise ValueError("policy version cannot be empty")
        _require_utc(self.updated_at_utc)
        if self.promoted_at_utc is not None:
            _require_utc(self.promoted_at_utc)
        if self.holdout_consumed and not (self.holdout_id or "").strip():
            raise ValueError("consumed holdout requires holdout identity")
        failed = {
            PromotionStage.REJECTED,
            PromotionStage.HOLDOUT_FAILED,
            PromotionStage.STRESS_FAILED,
            PromotionStage.DISABLED,
        }
        if self.stage in failed and not (self.rejection_reason or "").strip():
            raise ValueError("failed/disabled promotion state requires reason")
        if self.stage is PromotionStage.PROMOTED and self.promoted_at_utc is None:
            raise ValueError("promoted state requires promoted timestamp")

    @property
    def broker_authority(self) -> bool:
        # Even DEMO canary must pass the ordinary Risk/Execution path.
        return False


_ALLOWED: dict[PromotionStage, frozenset[PromotionStage]] = {
    PromotionStage.PROPOSED: frozenset({PromotionStage.RESEARCHING, PromotionStage.REJECTED}),
    PromotionStage.RESEARCHING: frozenset({PromotionStage.VALIDATED, PromotionStage.REJECTED}),
    PromotionStage.VALIDATED: frozenset({PromotionStage.LOCKED, PromotionStage.REJECTED}),
    PromotionStage.LOCKED: frozenset({PromotionStage.HOLDOUT_PASSED, PromotionStage.HOLDOUT_FAILED}),
    PromotionStage.HOLDOUT_PASSED: frozenset({PromotionStage.STRESS_PASSED, PromotionStage.STRESS_FAILED}),
    PromotionStage.STRESS_PASSED: frozenset({PromotionStage.SHADOW, PromotionStage.REJECTED}),
    PromotionStage.SHADOW: frozenset({PromotionStage.DEMO_CANARY, PromotionStage.REJECTED}),
    PromotionStage.DEMO_CANARY: frozenset({PromotionStage.PROMOTION_READY, PromotionStage.REJECTED}),
    PromotionStage.PROMOTION_READY: frozenset({PromotionStage.PROMOTED, PromotionStage.REJECTED}),
    PromotionStage.PROMOTED: frozenset({PromotionStage.ROLLED_BACK, PromotionStage.DISABLED}),
    PromotionStage.HOLDOUT_FAILED: frozenset(),
    PromotionStage.STRESS_FAILED: frozenset(),
    PromotionStage.REJECTED: frozenset(),
    PromotionStage.ROLLED_BACK: frozenset(),
    PromotionStage.DISABLED: frozenset(),
}


class PromotionRegistry:
    """Durable challenger lifecycle; no skipped stages or self-promotion."""

    def __init__(self, store: StateStore, scope: str = "default") -> None:
        self._store = store
        self._scope = scope.strip()
        if not self._scope:
            raise ValueError("promotion registry scope cannot be empty")

    def create(
        self,
        candidate_id: EntityId,
        policy_version: str,
        now_utc: datetime,
    ) -> PromotionRecord:
        _require_utc(now_utc)
        if any(item.candidate_id == candidate_id for item in self.all()):
            raise ValueError("candidate already has a promotion record")
        record = PromotionRecord(
            candidate_id=candidate_id,
            stage=PromotionStage.PROPOSED,
            policy_version=policy_version,
            updated_at_utc=now_utc,
        )
        self._save(record, "PROMOTION_RECORD_CREATED")
        return record

    def all(self) -> tuple[PromotionRecord, ...]:
        stored = self._store.load_record(
            _PROMOTION_NAMESPACE,
            self._scope,
            expected_schema_version=PROMOTION_SCHEMA_VERSION,
        )
        if stored is None:
            return ()
        rows = stored.payload.get("records")
        if not isinstance(rows, list):
            raise ValueError("promotion registry payload is invalid")
        return tuple(_from_payload(row) for row in rows)

    def get(self, candidate_id: EntityId) -> PromotionRecord:
        for item in self.all():
            if item.candidate_id == candidate_id:
                return item
        raise KeyError(f"promotion record not found: {candidate_id}")

    def advance(
        self,
        candidate_id: EntityId,
        target: PromotionStage,
        now_utc: datetime,
    ) -> PromotionRecord:
        """Advance ordinary success stages; special/failure stages use dedicated methods."""
        _require_utc(now_utc)
        special = {
            PromotionStage.LOCKED,
            PromotionStage.HOLDOUT_PASSED,
            PromotionStage.HOLDOUT_FAILED,
            PromotionStage.PROMOTED,
            PromotionStage.REJECTED,
            PromotionStage.STRESS_FAILED,
            PromotionStage.DISABLED,
            PromotionStage.ROLLED_BACK,
        }
        if target in special:
            raise ValueError("target requires its dedicated governed method")
        current = self.get(candidate_id)
        if target not in _ALLOWED[current.stage]:
            raise ValueError(f"invalid promotion transition: {current.stage} -> {target}")
        updated = replace(current, stage=target, updated_at_utc=now_utc)
        self._save(updated, f"PROMOTION_STAGE_{target.value}")
        return updated

    def lock(
        self,
        candidate_id: EntityId,
        fingerprint: str,
        now_utc: datetime,
    ) -> PromotionRecord:
        current = self.get(candidate_id)
        if current.stage is not PromotionStage.VALIDATED:
            raise ValueError("candidate must be VALIDATED before lock")
        cleaned = _fingerprint(fingerprint)
        _require_utc(now_utc)
        updated = replace(
            current,
            stage=PromotionStage.LOCKED,
            locked_fingerprint=cleaned,
            updated_at_utc=now_utc,
        )
        self._save(updated, "CANDIDATE_LOCKED")
        return updated

    def consume_holdout(
        self,
        candidate_id: EntityId,
        holdout_id: str,
        candidate_fingerprint: str,
        passed: bool,
        now_utc: datetime,
        *,
        failure_reason: str | None = None,
    ) -> PromotionRecord:
        current = self.get(candidate_id)
        if current.stage is not PromotionStage.LOCKED:
            raise ValueError("final holdout requires LOCKED candidate")
        if current.holdout_consumed:
            raise ValueError("final holdout is one-shot and already consumed")
        fingerprint = _fingerprint(candidate_fingerprint)
        if fingerprint != current.locked_fingerprint:
            raise ValueError("candidate changed after lock; create a new candidate/version")
        identity = holdout_id.strip()
        if not identity:
            raise ValueError("holdout identity cannot be empty")
        _require_utc(now_utc)
        stage = PromotionStage.HOLDOUT_PASSED if passed else PromotionStage.HOLDOUT_FAILED
        reason = None if passed else (failure_reason or "").strip()
        if not passed and not reason:
            raise ValueError("failed holdout requires reason")
        updated = replace(
            current,
            stage=stage,
            holdout_id=identity,
            holdout_consumed=True,
            rejection_reason=reason,
            updated_at_utc=now_utc,
        )
        self._save(updated, f"FINAL_HOLDOUT_{'PASS' if passed else 'FAIL'}")
        return updated

    def fail(
        self,
        candidate_id: EntityId,
        target: PromotionStage,
        reason: str,
        now_utc: datetime,
    ) -> PromotionRecord:
        if target not in {
            PromotionStage.REJECTED,
            PromotionStage.STRESS_FAILED,
            PromotionStage.DISABLED,
        }:
            raise ValueError("unsupported failure target")
        current = self.get(candidate_id)
        if target not in _ALLOWED[current.stage]:
            raise ValueError(f"invalid failure transition: {current.stage} -> {target}")
        cleaned = reason.strip()
        if not cleaned:
            raise ValueError("failure reason cannot be empty")
        _require_utc(now_utc)
        updated = replace(
            current,
            stage=target,
            rejection_reason=cleaned,
            updated_at_utc=now_utc,
        )
        self._save(updated, f"PROMOTION_{target.value}")
        return updated

    def promote(
        self,
        candidate_id: EntityId,
        now_utc: datetime,
        *,
        operator_approved: bool,
        rollback_target: str,
    ) -> PromotionRecord:
        current = self.get(candidate_id)
        if current.stage is not PromotionStage.PROMOTION_READY:
            raise ValueError("candidate is not PROMOTION_READY")
        if not operator_approved:
            raise PermissionError("candidate cannot self-promote; explicit approval required")
        rollback = rollback_target.strip()
        if not rollback:
            raise ValueError("promotion requires rollback target")
        _require_utc(now_utc)
        updated = replace(
            current,
            stage=PromotionStage.PROMOTED,
            rollback_target=rollback,
            promoted_at_utc=now_utc,
            updated_at_utc=now_utc,
        )
        self._save(updated, "CANDIDATE_PROMOTED")
        return updated

    def rollback(
        self,
        candidate_id: EntityId,
        now_utc: datetime,
        *,
        reason: str,
    ) -> PromotionRecord:
        current = self.get(candidate_id)
        if current.stage is not PromotionStage.PROMOTED:
            raise ValueError("only promoted candidate can roll back")
        cleaned = reason.strip()
        if not cleaned:
            raise ValueError("rollback requires reason")
        _require_utc(now_utc)
        updated = replace(
            current,
            stage=PromotionStage.ROLLED_BACK,
            rejection_reason=cleaned,
            updated_at_utc=now_utc,
        )
        self._save(updated, "CANDIDATE_ROLLED_BACK")
        return updated

    def _save(self, record: PromotionRecord, event_type: str) -> None:
        current = list(self.all())
        for index, existing in enumerate(current):
            if existing.candidate_id == record.candidate_id:
                current[index] = record
                break
        else:
            current.append(record)
        self._store.save_record(
            _PROMOTION_NAMESPACE,
            self._scope,
            {"records": [_payload(item) for item in current]},
            schema_version=PROMOTION_SCHEMA_VERSION,
            event_type=event_type,
        )


def _fingerprint(value: str) -> str:
    cleaned = value.strip().lower()
    if len(cleaned) != 64 or any(char not in "0123456789abcdef" for char in cleaned):
        raise ValueError("candidate fingerprint must be SHA-256 hex")
    return cleaned


def _payload(record: PromotionRecord) -> dict[str, object]:
    return {
        "candidate_id": str(record.candidate_id),
        "stage": record.stage.value,
        "policy_version": record.policy_version,
        "updated_at_utc": record.updated_at_utc.isoformat(),
        "locked_fingerprint": record.locked_fingerprint,
        "holdout_id": record.holdout_id,
        "holdout_consumed": record.holdout_consumed,
        "rejection_reason": record.rejection_reason,
        "rollback_target": record.rollback_target,
        "promoted_at_utc": (
            record.promoted_at_utc.isoformat() if record.promoted_at_utc else None
        ),
    }


def _from_payload(payload: object) -> PromotionRecord:
    if not isinstance(payload, dict):
        raise ValueError("promotion registry entry must be an object")
    updated = datetime.fromisoformat(str(payload["updated_at_utc"]))
    promoted_raw = payload.get("promoted_at_utc")
    promoted = datetime.fromisoformat(str(promoted_raw)) if promoted_raw else None
    return PromotionRecord(
        candidate_id=EntityId.parse(str(payload["candidate_id"])),
        stage=PromotionStage(str(payload["stage"])),
        policy_version=str(payload["policy_version"]),
        updated_at_utc=updated,
        locked_fingerprint=(
            str(payload["locked_fingerprint"])
            if payload.get("locked_fingerprint")
            else None
        ),
        holdout_id=str(payload["holdout_id"]) if payload.get("holdout_id") else None,
        holdout_consumed=bool(payload.get("holdout_consumed", False)),
        rejection_reason=(
            str(payload["rejection_reason"])
            if payload.get("rejection_reason")
            else None
        ),
        rollback_target=(
            str(payload["rollback_target"])
            if payload.get("rollback_target")
            else None
        ),
        promoted_at_utc=promoted,
    )


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("promotion timestamp must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("promotion timestamp must be UTC")
