from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from goldswingtraderai.domain.ids import new_id
from goldswingtraderai.persistence import StateStore
from goldswingtraderai.research.promotion import PromotionRegistry, PromotionStage


NOW = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
FINGERPRINT = "a" * 64


def _locked(registry: PromotionRegistry):
    candidate_id = new_id("CAND")
    registry.create(candidate_id, "GSW-0.1", NOW)
    registry.advance(candidate_id, PromotionStage.RESEARCHING, NOW + timedelta(minutes=1))
    registry.advance(candidate_id, PromotionStage.VALIDATED, NOW + timedelta(minutes=2))
    return registry.lock(candidate_id, FINGERPRINT, NOW + timedelta(minutes=3))


def _promotion_ready(registry: PromotionRegistry):
    locked = _locked(registry)
    candidate_id = locked.candidate_id
    registry.consume_holdout(
        candidate_id,
        "holdout-2025H2",
        FINGERPRINT,
        True,
        NOW + timedelta(minutes=4),
    )
    registry.advance(candidate_id, PromotionStage.STRESS_PASSED, NOW + timedelta(minutes=5))
    registry.advance(candidate_id, PromotionStage.SHADOW, NOW + timedelta(minutes=6))
    registry.advance(candidate_id, PromotionStage.DEMO_CANARY, NOW + timedelta(minutes=7))
    return registry.advance(
        candidate_id,
        PromotionStage.PROMOTION_READY,
        NOW + timedelta(minutes=8),
    )


def test_candidate_cannot_skip_evidence_stages(tmp_path) -> None:
    registry = PromotionRegistry(StateStore(tmp_path / "state.db"), "XAUUSDm")
    candidate_id = new_id("CAND")
    registry.create(candidate_id, "GSW-0.1", NOW)

    with pytest.raises(ValueError, match="invalid promotion transition"):
        registry.advance(candidate_id, PromotionStage.SHADOW, NOW + timedelta(minutes=1))


def test_final_holdout_is_one_shot_and_locked_fingerprint_is_enforced(tmp_path) -> None:
    registry = PromotionRegistry(StateStore(tmp_path / "state.db"), "XAUUSDm")
    locked = _locked(registry)

    with pytest.raises(ValueError, match="changed after lock"):
        registry.consume_holdout(
            locked.candidate_id,
            "holdout-2025H2",
            "b" * 64,
            True,
            NOW + timedelta(minutes=4),
        )

    passed = registry.consume_holdout(
        locked.candidate_id,
        "holdout-2025H2",
        FINGERPRINT,
        True,
        NOW + timedelta(minutes=5),
    )
    assert passed.stage is PromotionStage.HOLDOUT_PASSED
    assert passed.holdout_consumed is True

    with pytest.raises(ValueError, match="LOCKED"):
        registry.consume_holdout(
            locked.candidate_id,
            "holdout-OTHER",
            FINGERPRINT,
            True,
            NOW + timedelta(minutes=6),
        )


def test_autonomous_candidate_cannot_self_promote(tmp_path) -> None:
    registry = PromotionRegistry(StateStore(tmp_path / "state.db"), "XAUUSDm")
    ready = _promotion_ready(registry)

    assert ready.broker_authority is False
    with pytest.raises(PermissionError, match="cannot self-promote"):
        registry.promote(
            ready.candidate_id,
            NOW + timedelta(minutes=9),
            operator_approved=False,
            rollback_target="GSW-0.1",
        )

    assert registry.get(ready.candidate_id).stage is PromotionStage.PROMOTION_READY


def test_approved_promotion_and_rollback_survive_restart(tmp_path) -> None:
    path = tmp_path / "state.db"
    registry = PromotionRegistry(StateStore(path), "XAUUSDm")
    ready = _promotion_ready(registry)

    promoted = registry.promote(
        ready.candidate_id,
        NOW + timedelta(minutes=9),
        operator_approved=True,
        rollback_target="GSW-0.1",
    )
    assert promoted.stage is PromotionStage.PROMOTED
    assert promoted.broker_authority is False

    restarted = PromotionRegistry(StateStore(path), "XAUUSDm")
    restored = restarted.get(ready.candidate_id)
    assert restored == promoted

    rolled_back = restarted.rollback(
        ready.candidate_id,
        NOW + timedelta(minutes=10),
        reason="forward degradation",
    )
    assert rolled_back.stage is PromotionStage.ROLLED_BACK


def test_failed_holdout_terminates_candidate_and_records_reason(tmp_path) -> None:
    registry = PromotionRegistry(StateStore(tmp_path / "state.db"), "XAUUSDm")
    locked = _locked(registry)

    failed = registry.consume_holdout(
        locked.candidate_id,
        "holdout-2025H2",
        FINGERPRINT,
        False,
        NOW + timedelta(minutes=4),
        failure_reason="negative independent holdout",
    )

    assert failed.stage is PromotionStage.HOLDOUT_FAILED
    assert failed.rejection_reason == "negative independent holdout"
    with pytest.raises(ValueError, match="invalid promotion transition"):
        registry.advance(
            locked.candidate_id,
            PromotionStage.STRESS_PASSED,
            NOW + timedelta(minutes=5),
        )


def test_promotion_restore_rejects_coercive_boolean_fields(tmp_path) -> None:
    path = tmp_path / "state.db"
    store = StateStore(path)
    registry = PromotionRegistry(store, "XAUUSDm")
    candidate_id = new_id("CAND")
    registry.create(candidate_id, "GSW-0.1", NOW)

    record = store.load_record("candidate_promotion_registry", "XAUUSDm")
    assert record is not None
    rows = [dict(item) for item in record.payload["records"]]
    rows[0]["holdout_consumed"] = 0
    store.save_record(
        "candidate_promotion_registry",
        "XAUUSDm",
        {"records": rows},
        schema_version=1,
    )

    with pytest.raises(ValueError, match="holdout_consumed must be boolean"):
        PromotionRegistry(StateStore(path), "XAUUSDm").all()
