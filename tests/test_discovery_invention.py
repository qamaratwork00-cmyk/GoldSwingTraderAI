from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from goldswingtraderai.domain.enums import Direction, StrategyFamily
from goldswingtraderai.persistence import StateStore
from goldswingtraderai.research.discovery import (
    ApprovedPrimitive,
    CandidateKind,
    CandidateRegistry,
    CandidateStage,
    DiscoveryObservation,
    DiscoveryTrigger,
    propose_candidate,
)
from goldswingtraderai.research.invention import DiscoveryHealth, run_invention_cycle


NOW = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)


def _observation(
    index: int,
    *,
    trigger: DiscoveryTrigger = DiscoveryTrigger.MISSED_MOVE,
    family: StrategyFamily | None = StrategyFamily.TREND_PULLBACK_CONTINUATION,
    primitives: tuple[ApprovedPrimitive, ...] = (
        ApprovedPrimitive.STRUCTURE_TREND,
        ApprovedPrimitive.TECHNICAL_LOCATION,
        ApprovedPrimitive.ENTRY_TIMING,
        ApprovedPrimitive.TARGET_PATH,
    ),
    regime: str = "TREND_EXPANDING",
    source_id: str | None = None,
    strength: float = 2.0,
) -> DiscoveryObservation:
    return DiscoveryObservation(
        source_id=source_id or f"episode-{index}",
        observed_at_utc=NOW + timedelta(hours=index),
        trigger=trigger,
        direction=Direction.BUY,
        regime=regime,
        session="LONDON_NY",
        primitives=primitives,
        evidence_strength_r=strength,
        family=family,
    )


def test_invention_liveness_creates_and_persists_candidate(tmp_path) -> None:
    store = StateStore(tmp_path / "state.db")
    registry = CandidateRegistry(store, "XAUUSDm")
    observations = tuple(_observation(index) for index in range(3))

    cycle = run_invention_cycle(observations, registry)

    assert cycle.health is DiscoveryHealth.HEALTHY
    assert len(cycle.created) == 1
    candidate = cycle.created[0]
    assert candidate.kind is CandidateKind.VARIANT
    assert candidate.parent_family is StrategyFamily.TREND_PULLBACK_CONTINUATION
    assert candidate.stage is CandidateStage.PROPOSED
    assert candidate.broker_authority is False
    assert set(candidate.evidence_source_ids) == {"episode-0", "episode-1", "episode-2"}

    restored = CandidateRegistry(StateStore(tmp_path / "state.db"), "XAUUSDm").all()
    assert restored == (candidate,)


def test_rejected_candidate_memory_suppresses_same_idea_after_restart(tmp_path) -> None:
    path = tmp_path / "state.db"
    registry = CandidateRegistry(StateStore(path), "XAUUSDm")
    observations = tuple(_observation(index) for index in range(3))
    first = run_invention_cycle(observations, registry)
    candidate = first.created[0]
    rejected = registry.reject(candidate.candidate_id, "failed independent validation")
    assert rejected.stage is CandidateStage.REJECTED

    restarted = CandidateRegistry(StateStore(path), "XAUUSDm")
    second = run_invention_cycle(observations, restarted)

    assert second.created == ()
    assert "SIMILAR_REJECTED_CANDIDATE" in second.reasons
    assert second.health is DiscoveryHealth.HEALTHY


def test_duplicate_source_does_not_fake_independent_evidence() -> None:
    observations = tuple(
        _observation(index, source_id="same-episode")
        for index in range(3)
    )

    result = propose_candidate(observations)

    assert result.candidate is None
    assert result.reason == "INSUFFICIENT_INDEPENDENT_EPISODES"
    assert result.independent_episodes == 1


def test_distinct_unrepresented_pattern_can_create_new_family_candidate(tmp_path) -> None:
    primitives = (
        ApprovedPrimitive.FVG,
        ApprovedPrimitive.ORDER_BLOCK,
        ApprovedPrimitive.SESSION_CONTEXT,
    )
    observations = tuple(
        _observation(index, family=None, primitives=primitives, regime="TRANSITION_REVERSAL")
        for index in range(3)
    )
    registry = CandidateRegistry(StateStore(tmp_path / "state.db"), "XAUUSDm")

    cycle = run_invention_cycle(observations, registry)

    assert len(cycle.created) == 1
    candidate = cycle.created[0]
    assert candidate.kind is CandidateKind.NEW_FAMILY
    assert candidate.parent_family is None
    assert candidate.recipe.complexity == 3


def test_false_entry_and_premature_exit_create_policy_challengers() -> None:
    observations = tuple(_observation(index, trigger=DiscoveryTrigger.FALSE_ENTRY) for index in range(3))
    entry = propose_candidate(observations).candidate
    assert entry is not None
    assert entry.kind is CandidateKind.ENTRY_POLICY

    exit_observations = tuple(
        _observation(index, trigger=DiscoveryTrigger.PREMATURE_EXIT)
        for index in range(3)
    )
    exit_candidate = propose_candidate(exit_observations).candidate
    assert exit_candidate is not None
    assert exit_candidate.kind is CandidateKind.EXIT_POLICY


def test_unapproved_primitive_is_rejected_before_candidate_generation() -> None:
    with pytest.raises(ValueError, match="ApprovedPrimitive"):
        DiscoveryObservation(
            source_id="bad-primitive",
            observed_at_utc=NOW,
            trigger=DiscoveryTrigger.MISSED_MOVE,
            direction=Direction.BUY,
            regime="TREND",
            session="LONDON",
            primitives=("eval('trade')", ApprovedPrimitive.TARGET_PATH),  # type: ignore[arg-type]
            evidence_strength_r=2.0,
        )


def test_insufficient_evidence_reports_idle_not_fake_healthy_candidate(tmp_path) -> None:
    registry = CandidateRegistry(StateStore(tmp_path / "state.db"), "XAUUSDm")
    cycle = run_invention_cycle((_observation(0), _observation(1)), registry)

    assert cycle.health is DiscoveryHealth.IDLE
    assert cycle.created == ()
    assert registry.all() == ()


def test_candidate_restore_rejects_coercive_text_fields(tmp_path) -> None:
    path = tmp_path / "state.db"
    store = StateStore(path)
    registry = CandidateRegistry(store, "XAUUSDm")
    run_invention_cycle(tuple(_observation(index) for index in range(3)), registry)

    record = store.load_record("strategy_candidate_registry", "XAUUSDm")
    assert record is not None
    candidates = [dict(item) for item in record.payload["candidates"]]
    candidates[0]["hypothesis"] = 123
    store.save_record(
        "strategy_candidate_registry",
        "XAUUSDm",
        {"candidates": candidates},
        schema_version=1,
    )

    with pytest.raises(ValueError, match="candidate hypothesis"):
        CandidateRegistry(StateStore(path), "XAUUSDm").all()
