"""Durable research episode journal and automatic discovery-observation bridge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite

from goldswingtraderai.domain.enums import Direction, StrategyFamily
from goldswingtraderai.persistence import StateStore
from goldswingtraderai.research.discovery import (
    ApprovedPrimitive,
    CandidateRegistry,
    DiscoveryObservation,
    DiscoveryTrigger,
)
from goldswingtraderai.research.invention import InventionConfig, InventionCycleResult, run_invention_cycle
from goldswingtraderai.research.metrics import OpportunityOutcomeKind


EPISODE_JOURNAL_SCHEMA_VERSION = 1
_EPISODE_NAMESPACE = "research_episode_journal"
_MAX_EPISODES = 5000


@dataclass(frozen=True, slots=True)
class ResearchEpisodeRecord:
    source_id: str
    observed_at_utc: datetime
    direction: Direction
    family: StrategyFamily | None
    regime: str
    session: str
    outcome_kind: OpportunityOutcomeKind
    strategy_evidence: tuple[str, ...]
    meaningful_move: bool
    realized_r: float | None = None
    mfe_r: float | None = None
    capture_efficiency: float | None = None
    counterfactual_mfe_r: float | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("research episode source_id cannot be empty")
        _require_utc(self.observed_at_utc)
        if self.direction is Direction.NONE:
            raise ValueError("research episode requires BUY or SELL direction")
        if not self.regime.strip() or not self.session.strip():
            raise ValueError("research episode regime/session cannot be empty")
        if not self.strategy_evidence:
            raise ValueError("research episode requires strategy evidence labels")
        for value in (self.realized_r, self.mfe_r, self.counterfactual_mfe_r):
            if value is not None and not isfinite(value):
                raise ValueError("research episode R values must be finite")
        if self.capture_efficiency is not None and not 0 <= self.capture_efficiency <= 1:
            raise ValueError("capture efficiency must be between 0 and 1")


class ResearchEpisodeRepository:
    """Persist outcome-labelled episodes so discovery survives restart."""

    def __init__(self, store: StateStore, scope: str = "default") -> None:
        self._store = store
        self._scope = scope.strip()
        if not self._scope:
            raise ValueError("research episode scope cannot be empty")

    def all(self) -> tuple[ResearchEpisodeRecord, ...]:
        record = self._store.load_record(
            _EPISODE_NAMESPACE,
            self._scope,
            expected_schema_version=EPISODE_JOURNAL_SCHEMA_VERSION,
        )
        if record is None:
            return ()
        raw = record.payload.get("episodes")
        if not isinstance(raw, list):
            raise ValueError("research episode journal payload is invalid")
        return tuple(_episode_from_payload(item) for item in raw)

    def save(self, episode: ResearchEpisodeRecord) -> None:
        current = list(self.all())
        for index, existing in enumerate(current):
            if existing.source_id == episode.source_id:
                current[index] = episode
                break
        else:
            current.append(episode)
        current.sort(key=lambda item: item.observed_at_utc)
        if len(current) > _MAX_EPISODES:
            current = current[-_MAX_EPISODES:]
        self._store.save_record(
            _EPISODE_NAMESPACE,
            self._scope,
            {"episodes": [_episode_payload(item) for item in current]},
            schema_version=EPISODE_JOURNAL_SCHEMA_VERSION,
            event_type="RESEARCH_EPISODE_SAVED",
        )


def discovery_observations_from_episodes(
    episodes: tuple[ResearchEpisodeRecord, ...],
) -> tuple[DiscoveryObservation, ...]:
    """Convert outcome-labelled episodes into eligible discovery observations."""

    output: list[DiscoveryObservation] = []
    for episode in episodes:
        trigger = _trigger(episode)
        if trigger is None:
            continue
        primitives = _primitives(episode.strategy_evidence)
        if len(primitives) < 2:
            continue
        output.append(
            DiscoveryObservation(
                source_id=episode.source_id,
                observed_at_utc=episode.observed_at_utc,
                trigger=trigger,
                direction=episode.direction,
                regime=episode.regime,
                session=episode.session,
                primitives=primitives,
                evidence_strength_r=_strength(episode, trigger),
                family=episode.family,
            )
        )
    return tuple(output)


def run_discovery_from_journal(
    journal: ResearchEpisodeRepository,
    registry: CandidateRegistry,
    *,
    config: InventionConfig | None = None,
) -> InventionCycleResult:
    """Run the autonomous discovery cycle from durable research evidence."""

    observations = discovery_observations_from_episodes(journal.all())
    return run_invention_cycle(observations, registry, config=config)


def _trigger(episode: ResearchEpisodeRecord) -> DiscoveryTrigger | None:
    missed_kinds = {
        OpportunityOutcomeKind.ENTRY_WAIT,
        OpportunityOutcomeKind.ENTRY_MISSED,
        OpportunityOutcomeKind.NO_OPPORTUNITY,
    }
    if (
        episode.meaningful_move
        and episode.outcome_kind in missed_kinds
        and (episode.counterfactual_mfe_r or 0.0) >= 1.0
    ):
        return DiscoveryTrigger.MISSED_MOVE
    if episode.outcome_kind is not OpportunityOutcomeKind.TAKEN:
        return None
    if (
        episode.capture_efficiency is not None
        and episode.capture_efficiency < 0.45
        and (episode.mfe_r or 0.0) >= 2.0
    ):
        return DiscoveryTrigger.PREMATURE_EXIT
    if (
        episode.capture_efficiency is not None
        and episode.capture_efficiency >= 0.75
        and (episode.mfe_r or 0.0) >= 2.0
    ):
        return DiscoveryTrigger.HIGH_CAPTURE_SEQUENCE
    if episode.realized_r is not None and episode.realized_r < 0 and (episode.mfe_r or 0.0) < 1.0:
        return DiscoveryTrigger.FALSE_ENTRY
    return None


def _strength(episode: ResearchEpisodeRecord, trigger: DiscoveryTrigger) -> float:
    if trigger is DiscoveryTrigger.MISSED_MOVE:
        return max(0.0, episode.counterfactual_mfe_r or 0.0)
    if trigger is DiscoveryTrigger.PREMATURE_EXIT:
        return max(0.0, (episode.mfe_r or 0.0) - max(episode.realized_r or 0.0, 0.0))
    if trigger is DiscoveryTrigger.HIGH_CAPTURE_SEQUENCE:
        return max(0.0, episode.mfe_r or 0.0)
    if trigger is DiscoveryTrigger.FALSE_ENTRY:
        return max(1.0, abs(episode.realized_r or 0.0))
    return 0.0


def _primitives(labels: tuple[str, ...]) -> tuple[ApprovedPrimitive, ...]:
    output: list[ApprovedPrimitive] = []
    for raw in labels:
        label = raw.upper()
        matches: list[ApprovedPrimitive] = []
        if "STRUCTURE" in label or "CONTEXT" in label:
            matches.append(ApprovedPrimitive.STRUCTURE_TREND)
        if "BREAK" in label or "ACCEPTANCE" in label:
            matches.append(ApprovedPrimitive.STRUCTURE_BREAK)
        if "MSS" in label or "SHIFT" in label:
            matches.append(ApprovedPrimitive.MSS_SHIFT)
        if "REJECTION" in label or "RESPONSE" in label:
            matches.append(ApprovedPrimitive.CANDLE_REJECTION)
        if "EXPANSION" in label or "MOMENTUM" in label or "RELEASE" in label:
            matches.append(ApprovedPrimitive.DISPLACEMENT)
        if "COMPRESSION" in label:
            matches.append(ApprovedPrimitive.COMPRESSION)
        if "LOCATION" in label:
            matches.append(ApprovedPrimitive.TECHNICAL_LOCATION)
        if "SWEEP" in label:
            matches.append(ApprovedPrimitive.LIQUIDITY_SWEEP)
        if "FVG" in label:
            matches.append(ApprovedPrimitive.FVG)
        if "ORDER_BLOCK" in label or label == "OB":
            matches.append(ApprovedPrimitive.ORDER_BLOCK)
        if "EMA" in label:
            matches.append(ApprovedPrimitive.EMA_FLOW)
        if "RSI" in label:
            matches.append(ApprovedPrimitive.RSI_MOMENTUM)
        if "VOLATILITY" in label or "ATR" in label:
            matches.append(ApprovedPrimitive.ATR_VOLATILITY)
        if "SESSION" in label:
            matches.append(ApprovedPrimitive.SESSION_CONTEXT)
        if "TARGET" in label or "LIQUIDITY_PATH" in label:
            matches.append(ApprovedPrimitive.TARGET_PATH)
        if "ENTRY" in label or "RETEST" in label or "RESUMPTION" in label:
            matches.append(ApprovedPrimitive.ENTRY_TIMING)
        for primitive in matches:
            if primitive not in output:
                output.append(primitive)
    return tuple(output)


def _episode_payload(episode: ResearchEpisodeRecord) -> dict[str, object]:
    return {
        "source_id": episode.source_id,
        "observed_at_utc": episode.observed_at_utc.isoformat(),
        "direction": episode.direction.value,
        "family": episode.family.value if episode.family else None,
        "regime": episode.regime,
        "session": episode.session,
        "outcome_kind": episode.outcome_kind.value,
        "strategy_evidence": list(episode.strategy_evidence),
        "meaningful_move": episode.meaningful_move,
        "realized_r": episode.realized_r,
        "mfe_r": episode.mfe_r,
        "capture_efficiency": episode.capture_efficiency,
        "counterfactual_mfe_r": episode.counterfactual_mfe_r,
    }


def _episode_from_payload(payload: object) -> ResearchEpisodeRecord:
    if not isinstance(payload, dict):
        raise ValueError("research episode entry must be an object")
    observed = datetime.fromisoformat(str(payload["observed_at_utc"]))
    _require_utc(observed)
    family_raw = payload.get("family")
    return ResearchEpisodeRecord(
        source_id=str(payload["source_id"]),
        observed_at_utc=observed,
        direction=Direction(str(payload["direction"])),
        family=StrategyFamily(str(family_raw)) if family_raw else None,
        regime=str(payload["regime"]),
        session=str(payload["session"]),
        outcome_kind=OpportunityOutcomeKind(str(payload["outcome_kind"])),
        strategy_evidence=tuple(str(value) for value in payload["strategy_evidence"]),
        meaningful_move=bool(payload["meaningful_move"]),
        realized_r=_optional_float(payload.get("realized_r")),
        mfe_r=_optional_float(payload.get("mfe_r")),
        capture_efficiency=_optional_float(payload.get("capture_efficiency")),
        counterfactual_mfe_r=_optional_float(payload.get("counterfactual_mfe_r")),
    )


def _optional_float(value: object) -> float | None:
    return None if value is None else float(value)


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("research episode timestamp must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("research episode timestamp must be UTC")
