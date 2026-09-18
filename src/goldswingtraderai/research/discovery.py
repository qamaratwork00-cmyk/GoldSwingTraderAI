"""Governed strategy discovery models, candidate generation and durable registry.

Discovery turns repeated research observations into declarative candidates built only
from audited primitives. It never changes production strategy/risk/execution state.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
import json
from math import ceil, isfinite

from goldswingtraderai.domain.enums import Direction, StrategyFamily
from goldswingtraderai.domain.ids import EntityId, new_id
from goldswingtraderai.persistence import StateStore


REGISTRY_SCHEMA_VERSION = 1
_REGISTRY_NAMESPACE = "strategy_candidate_registry"


class ApprovedPrimitive(StrEnum):
    STRUCTURE_TREND = "STRUCTURE_TREND"
    STRUCTURE_BREAK = "STRUCTURE_BREAK"
    MSS_SHIFT = "MSS_SHIFT"
    CANDLE_REJECTION = "CANDLE_REJECTION"
    DISPLACEMENT = "DISPLACEMENT"
    COMPRESSION = "COMPRESSION"
    TECHNICAL_LOCATION = "TECHNICAL_LOCATION"
    LIQUIDITY_SWEEP = "LIQUIDITY_SWEEP"
    FVG = "FVG"
    ORDER_BLOCK = "ORDER_BLOCK"
    EMA_FLOW = "EMA_FLOW"
    RSI_MOMENTUM = "RSI_MOMENTUM"
    ATR_VOLATILITY = "ATR_VOLATILITY"
    SESSION_CONTEXT = "SESSION_CONTEXT"
    TARGET_PATH = "TARGET_PATH"
    ENTRY_TIMING = "ENTRY_TIMING"


class DiscoveryTrigger(StrEnum):
    MISSED_MOVE = "MISSED_MOVE"
    FALSE_ENTRY = "FALSE_ENTRY"
    PREMATURE_EXIT = "PREMATURE_EXIT"
    HIGH_CAPTURE_SEQUENCE = "HIGH_CAPTURE_SEQUENCE"
    REGIME_DETERIORATION = "REGIME_DETERIORATION"


class CandidateKind(StrEnum):
    VARIANT = "VARIANT"
    NEW_FAMILY = "NEW_FAMILY"
    ENTRY_POLICY = "ENTRY_POLICY"
    EXIT_POLICY = "EXIT_POLICY"


class CandidateStage(StrEnum):
    PROPOSED = "PROPOSED"
    VALIDATING = "VALIDATING"
    REJECTED = "REJECTED"


class TimingProfile(StrEnum):
    PULLBACK_RECLAIM = "PULLBACK_RECLAIM"
    BREAK_ACCEPTANCE = "BREAK_ACCEPTANCE"
    BREAK_RETEST_CONTINUATION = "BREAK_RETEST_CONTINUATION"
    SWEEP_RECLAIM_REVERSAL = "SWEEP_RECLAIM_REVERSAL"
    FAILED_ACCEPTANCE_REVERSAL = "FAILED_ACCEPTANCE_REVERSAL"
    COMPRESSION_RELEASE = "COMPRESSION_RELEASE"
    STRUCTURAL_REENTRY = "STRUCTURAL_REENTRY"


class InvalidationModel(StrEnum):
    STRUCTURAL = "STRUCTURAL"
    RECLAIM_FAILURE = "RECLAIM_FAILURE"


class TargetModel(StrEnum):
    STRUCTURAL_LIQUIDITY = "STRUCTURAL_LIQUIDITY"
    EXPANSION_PATH = "EXPANSION_PATH"


@dataclass(frozen=True, slots=True)
class DiscoveryObservation:
    source_id: str
    observed_at_utc: datetime
    trigger: DiscoveryTrigger
    direction: Direction
    regime: str
    session: str
    primitives: tuple[ApprovedPrimitive, ...]
    evidence_strength_r: float
    family: StrategyFamily | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("discovery observation source_id cannot be empty")
        _require_utc(self.observed_at_utc)
        if self.direction is Direction.NONE:
            raise ValueError("discovery observation requires BUY or SELL direction")
        if not self.regime.strip() or not self.session.strip():
            raise ValueError("discovery regime/session cannot be empty")
        if not isfinite(self.evidence_strength_r) or self.evidence_strength_r < 0:
            raise ValueError("discovery evidence strength must be finite and non-negative")
        if len(self.primitives) != len(set(self.primitives)):
            raise ValueError("discovery primitives cannot contain duplicates")
        if len(self.primitives) < 2:
            raise ValueError("discovery observation requires at least two primitives")
        if any(not isinstance(item, ApprovedPrimitive) for item in self.primitives):
            raise ValueError("discovery may use only ApprovedPrimitive values")


@dataclass(frozen=True, slots=True)
class CandidateRecipe:
    required: tuple[ApprovedPrimitive, ...]
    optional: tuple[ApprovedPrimitive, ...]
    preferred_regime: str
    timing_profile: TimingProfile
    invalidation_model: InvalidationModel
    target_model: TargetModel

    def __post_init__(self) -> None:
        if not self.required:
            raise ValueError("candidate recipe requires at least one primary primitive")
        if not self.preferred_regime.strip():
            raise ValueError("candidate preferred regime cannot be empty")
        if set(self.required) & set(self.optional):
            raise ValueError("candidate required/optional primitives must be disjoint")
        if len(self.required) != len(set(self.required)) or len(self.optional) != len(set(self.optional)):
            raise ValueError("candidate recipe primitives cannot contain duplicates")
        if any(not isinstance(item, ApprovedPrimitive) for item in (*self.required, *self.optional)):
            raise ValueError("candidate recipe may use only approved primitives")

    @property
    def complexity(self) -> int:
        return len(self.required) + len(self.optional)


@dataclass(frozen=True, slots=True)
class StrategyCandidate:
    candidate_id: EntityId
    kind: CandidateKind
    stage: CandidateStage
    direction: Direction
    parent_family: StrategyFamily | None
    recipe: CandidateRecipe
    created_at_utc: datetime
    trigger: DiscoveryTrigger
    evidence_source_ids: tuple[str, ...]
    hypothesis: str
    fingerprint: str
    rejection_reason: str | None = None

    def __post_init__(self) -> None:
        if self.candidate_id.kind != "CAND":
            raise ValueError("strategy candidate requires CAND entity id")
        _require_utc(self.created_at_utc)
        if self.direction is Direction.NONE:
            raise ValueError("candidate requires BUY or SELL direction")
        if not self.evidence_source_ids:
            raise ValueError("candidate requires evidence lineage")
        if len(self.evidence_source_ids) != len(set(self.evidence_source_ids)):
            raise ValueError("candidate evidence source IDs must be unique")
        if not self.hypothesis.strip():
            raise ValueError("candidate hypothesis cannot be empty")
        if len(self.fingerprint) != 64:
            raise ValueError("candidate fingerprint must be SHA-256 hex")
        if self.stage is CandidateStage.REJECTED and not (self.rejection_reason or "").strip():
            raise ValueError("rejected candidate requires rejection reason")
        if self.stage is not CandidateStage.REJECTED and self.rejection_reason is not None:
            raise ValueError("non-rejected candidate cannot carry rejection reason")

    @property
    def broker_authority(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class DiscoveryConfig:
    minimum_independent_episodes: int = 3
    minimum_mean_strength_r: float = 1.0
    required_support_fraction: float = 0.67
    optional_support_fraction: float = 0.34
    maximum_required_primitives: int = 4
    maximum_optional_primitives: int = 4
    variant_similarity: float = 0.55
    duplicate_similarity: float = 0.90

    def __post_init__(self) -> None:
        if self.minimum_independent_episodes < 2:
            raise ValueError("discovery requires at least two independent episodes")
        if self.minimum_mean_strength_r < 0:
            raise ValueError("minimum mean strength cannot be negative")
        if not 0 < self.optional_support_fraction <= self.required_support_fraction <= 1:
            raise ValueError("discovery support fractions are invalid")
        if self.maximum_required_primitives < 1 or self.maximum_optional_primitives < 0:
            raise ValueError("candidate complexity limits are invalid")
        if not 0 < self.variant_similarity < self.duplicate_similarity <= 1:
            raise ValueError("candidate similarity thresholds are invalid")


@dataclass(frozen=True, slots=True)
class ProposalResult:
    candidate: StrategyCandidate | None
    reason: str
    independent_episodes: int


_FAMILY_SIGNATURES: dict[StrategyFamily, frozenset[ApprovedPrimitive]] = {
    StrategyFamily.TREND_PULLBACK_CONTINUATION: frozenset({ApprovedPrimitive.STRUCTURE_TREND, ApprovedPrimitive.TECHNICAL_LOCATION, ApprovedPrimitive.EMA_FLOW, ApprovedPrimitive.ENTRY_TIMING, ApprovedPrimitive.TARGET_PATH}),
    StrategyFamily.BREAKOUT_EXPANSION: frozenset({ApprovedPrimitive.STRUCTURE_BREAK, ApprovedPrimitive.DISPLACEMENT, ApprovedPrimitive.ATR_VOLATILITY, ApprovedPrimitive.TARGET_PATH}),
    StrategyFamily.BREAKOUT_RETEST_CONTINUATION: frozenset({ApprovedPrimitive.STRUCTURE_BREAK, ApprovedPrimitive.TECHNICAL_LOCATION, ApprovedPrimitive.ENTRY_TIMING, ApprovedPrimitive.TARGET_PATH}),
    StrategyFamily.LIQUIDITY_SWEEP_REVERSAL: frozenset({ApprovedPrimitive.LIQUIDITY_SWEEP, ApprovedPrimitive.CANDLE_REJECTION, ApprovedPrimitive.MSS_SHIFT, ApprovedPrimitive.TECHNICAL_LOCATION}),
    StrategyFamily.FAILED_BREAKOUT_REVERSAL: frozenset({ApprovedPrimitive.STRUCTURE_BREAK, ApprovedPrimitive.CANDLE_REJECTION, ApprovedPrimitive.MSS_SHIFT, ApprovedPrimitive.TECHNICAL_LOCATION}),
    StrategyFamily.COMPRESSION_EXPANSION: frozenset({ApprovedPrimitive.COMPRESSION, ApprovedPrimitive.DISPLACEMENT, ApprovedPrimitive.ATR_VOLATILITY, ApprovedPrimitive.STRUCTURE_BREAK}),
}


def propose_candidate(observations: tuple[DiscoveryObservation, ...], *, existing: tuple[StrategyCandidate, ...] = (), config: DiscoveryConfig | None = None) -> ProposalResult:
    """Create one declarative candidate from one coherent evidence cluster."""
    cfg = config or DiscoveryConfig()
    unique = {item.source_id: item for item in observations}
    evidence = tuple(sorted(unique.values(), key=lambda item: item.observed_at_utc))
    if len(evidence) < cfg.minimum_independent_episodes:
        return ProposalResult(None, "INSUFFICIENT_INDEPENDENT_EPISODES", len(evidence))
    first = evidence[0]
    cluster_key = (first.trigger, first.direction, first.regime)
    if any((item.trigger, item.direction, item.regime) != cluster_key for item in evidence[1:]):
        raise ValueError("propose_candidate expects one trigger/direction/regime cluster")
    mean_strength = sum(item.evidence_strength_r for item in evidence) / len(evidence)
    if mean_strength < cfg.minimum_mean_strength_r:
        return ProposalResult(None, "EVIDENCE_STRENGTH_TOO_LOW", len(evidence))
    counts = Counter(primitive for item in evidence for primitive in item.primitives)
    required_cutoff = ceil(len(evidence) * cfg.required_support_fraction)
    optional_cutoff = ceil(len(evidence) * cfg.optional_support_fraction)
    ranked = sorted(counts, key=lambda item: (-counts[item], item.value))
    required = tuple(item for item in ranked if counts[item] >= required_cutoff)[:cfg.maximum_required_primitives]
    optional = tuple(item for item in ranked if item not in required and counts[item] >= optional_cutoff)[:cfg.maximum_optional_primitives]
    if len(required) < 2:
        return ProposalResult(None, "NO_STABLE_PRIMITIVE_PATTERN", len(evidence))
    parent = _parent_family(evidence, frozenset(required), cfg)
    kind = _candidate_kind(first.trigger, parent)
    recipe = CandidateRecipe(
        required=required,
        optional=optional,
        preferred_regime=first.regime,
        timing_profile=_timing_profile(required, parent),
        invalidation_model=InvalidationModel.RECLAIM_FAILURE if ApprovedPrimitive.LIQUIDITY_SWEEP in required else InvalidationModel.STRUCTURAL,
        target_model=TargetModel.EXPANSION_PATH if ApprovedPrimitive.DISPLACEMENT in required or ApprovedPrimitive.COMPRESSION in required else TargetModel.STRUCTURAL_LIQUIDITY,
    )
    fingerprint = candidate_fingerprint(kind, first.direction, parent, recipe)
    draft = StrategyCandidate(
        candidate_id=new_id("CAND"),
        kind=kind,
        stage=CandidateStage.PROPOSED,
        direction=first.direction,
        parent_family=parent,
        recipe=recipe,
        created_at_utc=evidence[-1].observed_at_utc,
        trigger=first.trigger,
        evidence_source_ids=tuple(item.source_id for item in evidence),
        hypothesis=_hypothesis(first.trigger, first.direction, parent, recipe),
        fingerprint=fingerprint,
    )
    duplicate = _similar_candidate(draft, existing, cfg.duplicate_similarity)
    if duplicate is not None:
        reason = "SIMILAR_REJECTED_CANDIDATE" if duplicate.stage is CandidateStage.REJECTED else "DUPLICATE_EXISTING_CANDIDATE"
        return ProposalResult(None, reason, len(evidence))
    return ProposalResult(draft, "CANDIDATE_CREATED", len(evidence))


def candidate_similarity(left: StrategyCandidate, right: StrategyCandidate) -> float:
    left_required = set(left.recipe.required)
    right_required = set(right.recipe.required)
    left_optional = set(left.recipe.optional)
    right_optional = set(right.recipe.optional)
    required = _jaccard(left_required, right_required)
    optional = _jaccard(left_optional, right_optional)
    timing = float(left.recipe.timing_profile is right.recipe.timing_profile)
    direction = float(left.direction is right.direction)
    return 0.65 * required + 0.15 * optional + 0.10 * timing + 0.10 * direction


def candidate_fingerprint(kind: CandidateKind, direction: Direction, parent_family: StrategyFamily | None, recipe: CandidateRecipe) -> str:
    payload = {
        "kind": kind.value,
        "direction": direction.value,
        "parent_family": parent_family.value if parent_family else None,
        "required": [item.value for item in recipe.required],
        "optional": [item.value for item in recipe.optional],
        "preferred_regime": recipe.preferred_regime,
        "timing_profile": recipe.timing_profile.value,
        "invalidation_model": recipe.invalidation_model.value,
        "target_model": recipe.target_model.value,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


class CandidateRegistry:
    """Small durable registry including rejected-candidate memory."""
    def __init__(self, store: StateStore, scope: str = "default") -> None:
        self._store = store
        self._scope = scope.strip()
        if not self._scope:
            raise ValueError("candidate registry scope cannot be empty")

    def all(self) -> tuple[StrategyCandidate, ...]:
        record = self._store.load_record(_REGISTRY_NAMESPACE, self._scope, expected_schema_version=REGISTRY_SCHEMA_VERSION)
        if record is None:
            return ()
        raw = record.payload.get("candidates")
        if not isinstance(raw, list):
            raise ValueError("candidate registry payload is invalid")
        return tuple(_candidate_from_payload(item) for item in raw)

    def save(self, candidate: StrategyCandidate, *, event_type: str = "CANDIDATE_SAVED") -> None:
        current = list(self.all())
        for index, existing in enumerate(current):
            if existing.candidate_id == candidate.candidate_id:
                current[index] = candidate
                break
        else:
            current.append(candidate)
        self._store.save_record(
            _REGISTRY_NAMESPACE,
            self._scope,
            {"candidates": [_candidate_payload(item) for item in current]},
            schema_version=REGISTRY_SCHEMA_VERSION,
            event_type=event_type,
        )

    def reject(self, candidate_id: EntityId, reason: str) -> StrategyCandidate:
        cleaned = reason.strip()
        if not cleaned:
            raise ValueError("candidate rejection reason cannot be empty")
        for candidate in self.all():
            if candidate.candidate_id == candidate_id:
                rejected = replace(candidate, stage=CandidateStage.REJECTED, rejection_reason=cleaned)
                self.save(rejected, event_type="CANDIDATE_REJECTED")
                return rejected
        raise KeyError(f"candidate not found: {candidate_id}")

    def mark_validating(self, candidate_id: EntityId) -> StrategyCandidate:
        for candidate in self.all():
            if candidate.candidate_id == candidate_id:
                if candidate.stage is CandidateStage.REJECTED:
                    raise ValueError("rejected candidate cannot re-enter validation unchanged")
                validating = replace(candidate, stage=CandidateStage.VALIDATING)
                self.save(validating, event_type="CANDIDATE_VALIDATING")
                return validating
        raise KeyError(f"candidate not found: {candidate_id}")


def _parent_family(observations: tuple[DiscoveryObservation, ...], required: frozenset[ApprovedPrimitive], cfg: DiscoveryConfig) -> StrategyFamily | None:
    family_counts = Counter(item.family for item in observations if item.family is not None)
    if family_counts:
        family, count = family_counts.most_common(1)[0]
        if count >= ceil(len(observations) * 0.5):
            return family
    best_family = None
    best_similarity = 0.0
    for family, signature in _FAMILY_SIGNATURES.items():
        similarity = _jaccard(set(required), set(signature))
        if similarity > best_similarity:
            best_family, best_similarity = family, similarity
    return best_family if best_similarity >= cfg.variant_similarity else None


def _candidate_kind(trigger: DiscoveryTrigger, parent: StrategyFamily | None) -> CandidateKind:
    if trigger is DiscoveryTrigger.PREMATURE_EXIT:
        return CandidateKind.EXIT_POLICY
    if trigger is DiscoveryTrigger.FALSE_ENTRY:
        return CandidateKind.ENTRY_POLICY
    return CandidateKind.VARIANT if parent is not None else CandidateKind.NEW_FAMILY


def _timing_profile(required: tuple[ApprovedPrimitive, ...], parent: StrategyFamily | None) -> TimingProfile:
    mapping = {
        StrategyFamily.TREND_PULLBACK_CONTINUATION: TimingProfile.PULLBACK_RECLAIM,
        StrategyFamily.BREAKOUT_EXPANSION: TimingProfile.BREAK_ACCEPTANCE,
        StrategyFamily.BREAKOUT_RETEST_CONTINUATION: TimingProfile.BREAK_RETEST_CONTINUATION,
        StrategyFamily.LIQUIDITY_SWEEP_REVERSAL: TimingProfile.SWEEP_RECLAIM_REVERSAL,
        StrategyFamily.FAILED_BREAKOUT_REVERSAL: TimingProfile.FAILED_ACCEPTANCE_REVERSAL,
        StrategyFamily.COMPRESSION_EXPANSION: TimingProfile.COMPRESSION_RELEASE,
    }
    if parent in mapping:
        return mapping[parent]
    if ApprovedPrimitive.LIQUIDITY_SWEEP in required:
        return TimingProfile.SWEEP_RECLAIM_REVERSAL
    if ApprovedPrimitive.COMPRESSION in required:
        return TimingProfile.COMPRESSION_RELEASE
    if ApprovedPrimitive.STRUCTURE_BREAK in required:
        return TimingProfile.BREAK_ACCEPTANCE
    return TimingProfile.STRUCTURAL_REENTRY


def _hypothesis(trigger: DiscoveryTrigger, direction: Direction, parent: StrategyFamily | None, recipe: CandidateRecipe) -> str:
    lineage = parent.value if parent else "NEW_MARKET_BEHAVIOUR"
    required = ", ".join(item.value for item in recipe.required)
    return f"{trigger.value}: repeated {direction.value} episodes around {lineage} share [{required}]; validate this declarative recipe before any production use."


def _similar_candidate(draft: StrategyCandidate, existing: tuple[StrategyCandidate, ...], threshold: float) -> StrategyCandidate | None:
    for candidate in existing:
        if candidate.fingerprint == draft.fingerprint or candidate_similarity(draft, candidate) >= threshold:
            return candidate
    return None


def _jaccard(left: set[object], right: set[object]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def _candidate_payload(candidate: StrategyCandidate) -> dict[str, object]:
    return {
        "candidate_id": str(candidate.candidate_id),
        "kind": candidate.kind.value,
        "stage": candidate.stage.value,
        "direction": candidate.direction.value,
        "parent_family": candidate.parent_family.value if candidate.parent_family else None,
        "recipe": {
            "required": [item.value for item in candidate.recipe.required],
            "optional": [item.value for item in candidate.recipe.optional],
            "preferred_regime": candidate.recipe.preferred_regime,
            "timing_profile": candidate.recipe.timing_profile.value,
            "invalidation_model": candidate.recipe.invalidation_model.value,
            "target_model": candidate.recipe.target_model.value,
        },
        "created_at_utc": candidate.created_at_utc.isoformat(),
        "trigger": candidate.trigger.value,
        "evidence_source_ids": list(candidate.evidence_source_ids),
        "hypothesis": candidate.hypothesis,
        "fingerprint": candidate.fingerprint,
        "rejection_reason": candidate.rejection_reason,
    }


def _candidate_from_payload(payload: object) -> StrategyCandidate:
    if not isinstance(payload, dict):
        raise ValueError("candidate registry entry must be an object")
    recipe_raw = payload.get("recipe")
    if not isinstance(recipe_raw, dict):
        raise ValueError("candidate recipe payload is invalid")
    created = datetime.fromisoformat(str(payload["created_at_utc"]))
    _require_utc(created)
    parent_raw = payload.get("parent_family")
    recipe = CandidateRecipe(
        required=tuple(ApprovedPrimitive(value) for value in recipe_raw["required"]),
        optional=tuple(ApprovedPrimitive(value) for value in recipe_raw["optional"]),
        preferred_regime=str(recipe_raw["preferred_regime"]),
        timing_profile=TimingProfile(str(recipe_raw["timing_profile"])),
        invalidation_model=InvalidationModel(str(recipe_raw["invalidation_model"])),
        target_model=TargetModel(str(recipe_raw["target_model"])),
    )
    return StrategyCandidate(
        candidate_id=EntityId.parse(str(payload["candidate_id"])),
        kind=CandidateKind(str(payload["kind"])),
        stage=CandidateStage(str(payload["stage"])),
        direction=Direction(str(payload["direction"])),
        parent_family=StrategyFamily(str(parent_raw)) if parent_raw else None,
        recipe=recipe,
        created_at_utc=created,
        trigger=DiscoveryTrigger(str(payload["trigger"])),
        evidence_source_ids=tuple(str(value) for value in payload["evidence_source_ids"]),
        hypothesis=str(payload["hypothesis"]),
        fingerprint=str(payload["fingerprint"]),
        rejection_reason=str(payload["rejection_reason"]) if payload.get("rejection_reason") is not None else None,
    )


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("discovery timestamp must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("discovery timestamp must be UTC")
