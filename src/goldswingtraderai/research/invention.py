"""Automatic governed discovery cycles over normalized research observations.

A cycle groups recurring evidence, proposes only declarative candidates, persists
novel candidates and reports liveness. It never mutates production policy.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum

from goldswingtraderai.research.discovery import (
    CandidateRegistry,
    DiscoveryConfig,
    DiscoveryObservation,
    StrategyCandidate,
    propose_candidate,
)


class DiscoveryHealth(StrEnum):
    IDLE = "IDLE"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"


@dataclass(frozen=True, slots=True)
class InventionCycleResult:
    health: DiscoveryHealth
    created: tuple[StrategyCandidate, ...]
    reasons: tuple[str, ...]
    observations_seen: int
    eligible_clusters: int


@dataclass(frozen=True, slots=True)
class InventionConfig:
    discovery: DiscoveryConfig = DiscoveryConfig()
    maximum_candidates_per_cycle: int = 3

    def __post_init__(self) -> None:
        if self.maximum_candidates_per_cycle <= 0:
            raise ValueError("maximum candidates per cycle must be positive")


def run_invention_cycle(
    observations: tuple[DiscoveryObservation, ...],
    registry: CandidateRegistry,
    *,
    config: InventionConfig | None = None,
) -> InventionCycleResult:
    """Automatically convert eligible recurring evidence into durable candidates."""

    cfg = config or InventionConfig()
    groups: dict[tuple[object, ...], list[DiscoveryObservation]] = defaultdict(list)
    for observation in observations:
        groups[(observation.trigger, observation.direction, observation.regime)].append(observation)

    ranked_groups = sorted(
        groups.values(),
        key=lambda items: (
            -len({item.source_id for item in items}),
            -sum(item.evidence_strength_r for item in items) / len(items),
        ),
    )

    created: list[StrategyCandidate] = []
    reasons: list[str] = []
    eligible_clusters = 0
    existing = list(registry.all())

    for items in ranked_groups:
        independent = len({item.source_id for item in items})
        if independent < cfg.discovery.minimum_independent_episodes:
            reasons.append("INSUFFICIENT_INDEPENDENT_EPISODES")
            continue
        eligible_clusters += 1
        result = propose_candidate(tuple(items), existing=tuple(existing), config=cfg.discovery)
        reasons.append(result.reason)
        if result.candidate is None:
            continue
        registry.save(result.candidate, event_type="AUTONOMOUS_CANDIDATE_CREATED")
        existing.append(result.candidate)
        created.append(result.candidate)
        if len(created) >= cfg.maximum_candidates_per_cycle:
            break

    if created:
        health = DiscoveryHealth.HEALTHY
    elif eligible_clusters == 0:
        health = DiscoveryHealth.IDLE
    elif reasons and all(
        reason in {
            "DUPLICATE_EXISTING_CANDIDATE",
            "SIMILAR_REJECTED_CANDIDATE",
            "EVIDENCE_STRENGTH_TOO_LOW",
            "NO_STABLE_PRIMITIVE_PATTERN",
            "INSUFFICIENT_INDEPENDENT_EPISODES",
        }
        for reason in reasons
    ):
        health = DiscoveryHealth.HEALTHY
    else:
        health = DiscoveryHealth.DEGRADED

    return InventionCycleResult(
        health=health,
        created=tuple(created),
        reasons=tuple(reasons),
        observations_seen=len(observations),
        eligible_clusters=eligible_clusters,
    )
