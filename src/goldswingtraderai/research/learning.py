"""Interpretable StrategyMemory summaries and bounded adaptive influence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from goldswingtraderai.domain.enums import Direction, StrategyFamily


class EvidenceEnvironment(StrEnum):
    REPLAY = "REPLAY"
    SHADOW = "SHADOW"
    DEMO_CANARY = "DEMO_CANARY"
    MAIN_DEMO = "MAIN_DEMO"


@dataclass(frozen=True, slots=True)
class LearningObservation:
    family: StrategyFamily
    direction: Direction
    regime: str
    session: str
    environment: EvidenceEnvironment
    policy_version: str
    realized_r: float
    entry_efficiency: float
    capture_efficiency: float
    attribution: str

    def __post_init__(self) -> None:
        if self.direction is Direction.NONE:
            raise ValueError("learning observation requires BUY or SELL direction")
        if not self.regime.strip() or not self.session.strip() or not self.policy_version.strip():
            raise ValueError("learning context/version cannot be empty")
        if not all(
            isfinite(value)
            for value in (self.realized_r, self.entry_efficiency, self.capture_efficiency)
        ):
            raise ValueError("learning values must be finite")
        if not 0 <= self.entry_efficiency <= 1 or not 0 <= self.capture_efficiency <= 1:
            raise ValueError("entry/capture efficiency must be between 0 and 1")
        if not self.attribution.strip():
            raise ValueError("learning observation requires outcome attribution")


@dataclass(frozen=True, slots=True)
class StrategyMemory:
    family: StrategyFamily
    direction: Direction
    regime: str
    session: str
    environment: EvidenceEnvironment
    policy_version: str
    samples: int
    average_r: float
    win_rate: float
    average_entry_efficiency: float
    average_capture_efficiency: float
    confidence: float
    bounded_score_adjustment: float


@dataclass(frozen=True, slots=True)
class LearningConfig:
    confidence_samples: int = 30
    maximum_score_adjustment: float = 3.0
    r_scale: float = 0.50
    efficiency_center: float = 0.55

    def __post_init__(self) -> None:
        if self.confidence_samples <= 0:
            raise ValueError("confidence sample requirement must be positive")
        if not 0 < self.maximum_score_adjustment <= 10:
            raise ValueError("bounded adjustment must be positive and modest")
        if self.r_scale <= 0:
            raise ValueError("R normalization scale must be positive")
        if not 0 < self.efficiency_center < 1:
            raise ValueError("efficiency center must be between 0 and 1")


def summarize_strategy_memory(
    observations: tuple[LearningObservation, ...],
    *,
    config: LearningConfig | None = None,
) -> StrategyMemory:
    """Summarize one isolated family/context/version/environment evidence bucket."""

    if not observations:
        raise ValueError("StrategyMemory requires at least one observation")
    cfg = config or LearningConfig()
    first = observations[0]
    key = _key(first)
    if any(_key(item) != key for item in observations[1:]):
        raise ValueError("StrategyMemory cannot mix family/context/version/environment buckets")

    samples = len(observations)
    average_r = sum(item.realized_r for item in observations) / samples
    win_rate = sum(item.realized_r > 0 for item in observations) / samples
    entry_efficiency = sum(item.entry_efficiency for item in observations) / samples
    capture_efficiency = sum(item.capture_efficiency for item in observations) / samples
    confidence = min(1.0, samples / cfg.confidence_samples)

    # Interpretability over cleverness: R and capture/entry quality contribute
    # a small bounded nudge. Tiny samples naturally approach zero influence.
    normalized_r = _clip(average_r / cfg.r_scale, -1.0, 1.0)
    efficiency_signal = _clip(
        ((entry_efficiency + capture_efficiency) / 2.0 - cfg.efficiency_center)
        / max(0.01, 1.0 - cfg.efficiency_center),
        -1.0,
        1.0,
    )
    signal = 0.65 * normalized_r + 0.35 * efficiency_signal
    adjustment = _clip(
        signal * confidence * cfg.maximum_score_adjustment,
        -cfg.maximum_score_adjustment,
        cfg.maximum_score_adjustment,
    )

    return StrategyMemory(
        family=first.family,
        direction=first.direction,
        regime=first.regime,
        session=first.session,
        environment=first.environment,
        policy_version=first.policy_version,
        samples=samples,
        average_r=average_r,
        win_rate=win_rate,
        average_entry_efficiency=entry_efficiency,
        average_capture_efficiency=capture_efficiency,
        confidence=confidence,
        bounded_score_adjustment=adjustment,
    )


def apply_bounded_memory_score(base_score: float, memory: StrategyMemory | None) -> float:
    """Apply memory as a bounded score nudge; it never returns broker/risk authority."""

    if not 0 <= base_score <= 100:
        raise ValueError("base score must be between 0 and 100")
    if memory is None:
        return base_score
    return _clip(base_score + memory.bounded_score_adjustment, 0.0, 100.0)


def _key(observation: LearningObservation) -> tuple[object, ...]:
    return (
        observation.family,
        observation.direction,
        observation.regime,
        observation.session,
        observation.environment,
        observation.policy_version,
    )


def _clip(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))
