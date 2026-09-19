from __future__ import annotations

from datetime import datetime, timedelta, timezone

from goldswingtraderai.domain.enums import Direction, StrategyFamily
from goldswingtraderai.persistence import StateStore
from goldswingtraderai.research.discovery import (
    ApprovedPrimitive,
    CandidateKind,
    CandidateRegistry,
)
from goldswingtraderai.research.episode_journal import (
    ResearchEpisodeRecord,
    ResearchEpisodeRepository,
    discovery_observations_from_episodes,
    run_discovery_from_journal,
)
from goldswingtraderai.research.invention import DiscoveryHealth
from goldswingtraderai.research.metrics import OpportunityOutcomeKind


NOW = datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc)


def _missed(index: int) -> ResearchEpisodeRecord:
    return ResearchEpisodeRecord(
        source_id=f"missed-{index}",
        observed_at_utc=NOW + timedelta(hours=index),
        direction=Direction.BUY,
        family=StrategyFamily.TREND_PULLBACK_CONTINUATION,
        regime="TREND_EXPANDING",
        session="LONDON_NY",
        outcome_kind=OpportunityOutcomeKind.ENTRY_MISSED,
        strategy_evidence=(
            "H1_STRUCTURE",
            "M15_LOCATION",
            "M5_RESUMPTION",
            "EMA_FLOW",
            "TARGET_ROOM",
        ),
        meaningful_move=True,
        counterfactual_mfe_r=2.5 + index * 0.1,
    )


def test_durable_episode_journal_feeds_discovery_after_restart(tmp_path) -> None:
    path = tmp_path / "state.db"
    journal = ResearchEpisodeRepository(StateStore(path), "XAUUSDm")
    for index in range(3):
        journal.save(_missed(index))

    restarted_journal = ResearchEpisodeRepository(StateStore(path), "XAUUSDm")
    registry = CandidateRegistry(StateStore(path), "XAUUSDm")
    cycle = run_discovery_from_journal(restarted_journal, registry)

    assert cycle.health is DiscoveryHealth.HEALTHY
    assert len(cycle.created) == 1
    assert cycle.created[0].kind is CandidateKind.VARIANT
    assert len(registry.all()) == 1
    status = registry.load_discovery_status()
    assert status is not None
    assert status.health == DiscoveryHealth.HEALTHY.value
    assert status.observations_seen == 3
    assert status.eligible_clusters == 1


def test_episode_evidence_maps_to_multiple_approved_primitives() -> None:
    observations = discovery_observations_from_episodes((_missed(0),))

    assert len(observations) == 1
    observation = observations[0]
    assert len(observation.primitives) >= 4
    assert observation.evidence_strength_r == 2.5


def test_technical_confluence_labels_are_audited_discovery_primitives() -> None:
    episode = ResearchEpisodeRecord(
        source_id="confluence-1",
        observed_at_utc=NOW,
        direction=Direction.BUY,
        family=StrategyFamily.TREND_PULLBACK_CONTINUATION,
        regime="TREND_EXPANDING",
        session="LONDON_NY",
        outcome_kind=OpportunityOutcomeKind.ENTRY_MISSED,
        strategy_evidence=(
            "H1_STRUCTURE",
            "TRENDLINE_PULLBACK_SUPPORT",
            "FIB_CORE_RETRACEMENT",
            "POC_LOCATION_CONFLUENCE",
            "TARGET_ROOM",
        ),
        meaningful_move=True,
        counterfactual_mfe_r=2.2,
    )

    observation = discovery_observations_from_episodes((episode,))[0]

    assert ApprovedPrimitive.TRENDLINE in observation.primitives
    assert ApprovedPrimitive.FIBONACCI in observation.primitives
    assert ApprovedPrimitive.VOLUME_PROFILE_POC in observation.primitives


def test_ordinary_small_move_does_not_spam_discovery(tmp_path) -> None:
    path = tmp_path / "state.db"
    journal = ResearchEpisodeRepository(StateStore(path), "XAUUSDm")
    for index in range(3):
        episode = _missed(index)
        journal.save(
            ResearchEpisodeRecord(
                source_id=episode.source_id,
                observed_at_utc=episode.observed_at_utc,
                direction=episode.direction,
                family=episode.family,
                regime=episode.regime,
                session=episode.session,
                outcome_kind=episode.outcome_kind,
                strategy_evidence=episode.strategy_evidence,
                meaningful_move=False,
                counterfactual_mfe_r=0.4,
            )
        )

    cycle = run_discovery_from_journal(
        journal,
        CandidateRegistry(StateStore(path), "XAUUSDm"),
    )

    assert cycle.health is DiscoveryHealth.IDLE
    assert cycle.created == ()
