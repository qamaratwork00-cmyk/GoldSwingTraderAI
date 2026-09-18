"""Research outcome metrics with strict actual/counterfactual separation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite


class OpportunityOutcomeKind(StrEnum):
    TAKEN = "TAKEN"
    ENTRY_WAIT = "ENTRY_WAIT"
    ENTRY_MISSED = "ENTRY_MISSED"
    SAFETY_BLOCKED = "SAFETY_BLOCKED"
    RISK_BLOCKED = "RISK_BLOCKED"
    EXECUTION_BLOCKED = "EXECUTION_BLOCKED"
    INVALIDATED = "INVALIDATED"
    NO_OPPORTUNITY = "NO_OPPORTUNITY"
    SYSTEM_FAULT = "SYSTEM_FAULT"


@dataclass(frozen=True, slots=True)
class TradeOutcome:
    realized_r: float
    mfe_r: float
    mae_r: float
    hold_minutes: float
    capture_efficiency: float
    reached_2r: bool
    reached_3r: bool
    reached_4r: bool

    def __post_init__(self) -> None:
        values = (
            self.realized_r,
            self.mfe_r,
            self.mae_r,
            self.hold_minutes,
            self.capture_efficiency,
        )
        if not all(isfinite(value) for value in values):
            raise ValueError("trade outcome values must be finite")
        if self.hold_minutes < 0:
            raise ValueError("hold time cannot be negative")
        if not 0 <= self.capture_efficiency <= 1:
            raise ValueError("capture efficiency must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class OpportunityOutcome:
    kind: OpportunityOutcomeKind
    meaningful_move: bool
    captured_move: bool
    counterfactual_mfe_r: float | None = None
    blocked_reason: str | None = None

    def __post_init__(self) -> None:
        if self.counterfactual_mfe_r is not None and not isfinite(self.counterfactual_mfe_r):
            raise ValueError("counterfactual MFE must be finite")
        if self.captured_move and not self.meaningful_move:
            raise ValueError("captured meaningful move requires meaningful_move=True")
        if self.kind is OpportunityOutcomeKind.TAKEN and self.blocked_reason is not None:
            raise ValueError("taken opportunity cannot have a block reason")


@dataclass(frozen=True, slots=True)
class ResearchMetrics:
    trades: int
    wins: int
    losses: int
    scratches: int
    net_r: float
    average_r: float
    profit_factor: float | None
    max_drawdown_r: float
    average_mfe_r: float
    average_mae_r: float
    average_capture_efficiency: float
    reach_2r_rate: float
    reach_3r_rate: float
    reach_4r_rate: float
    meaningful_opportunities: int
    captured_opportunities: int
    opportunity_recall: float | None
    missed_opportunity_rate: float | None
    safety_blocked: int
    risk_blocked: int
    execution_blocked: int
    system_faults: int


def summarize_research(
    trades: tuple[TradeOutcome, ...],
    opportunities: tuple[OpportunityOutcome, ...],
) -> ResearchMetrics:
    """Summarize actual trades separately from post-hoc counterfactual labels."""

    realized = tuple(item.realized_r for item in trades)
    wins = sum(value > 0 for value in realized)
    losses = sum(value < 0 for value in realized)
    scratches = len(realized) - wins - losses
    gross_profit = sum(value for value in realized if value > 0)
    gross_loss = -sum(value for value in realized if value < 0)
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else None

    meaningful = tuple(item for item in opportunities if item.meaningful_move)
    captured = sum(item.captured_move for item in meaningful)
    recall = captured / len(meaningful) if meaningful else None

    return ResearchMetrics(
        trades=len(trades),
        wins=wins,
        losses=losses,
        scratches=scratches,
        net_r=sum(realized),
        average_r=_average(realized),
        profit_factor=profit_factor,
        max_drawdown_r=_max_drawdown(realized),
        average_mfe_r=_average(tuple(item.mfe_r for item in trades)),
        average_mae_r=_average(tuple(item.mae_r for item in trades)),
        average_capture_efficiency=_average(
            tuple(item.capture_efficiency for item in trades)
        ),
        reach_2r_rate=_rate(tuple(item.reached_2r for item in trades)),
        reach_3r_rate=_rate(tuple(item.reached_3r for item in trades)),
        reach_4r_rate=_rate(tuple(item.reached_4r for item in trades)),
        meaningful_opportunities=len(meaningful),
        captured_opportunities=captured,
        opportunity_recall=recall,
        missed_opportunity_rate=None if recall is None else 1.0 - recall,
        safety_blocked=sum(
            item.kind is OpportunityOutcomeKind.SAFETY_BLOCKED for item in opportunities
        ),
        risk_blocked=sum(
            item.kind is OpportunityOutcomeKind.RISK_BLOCKED for item in opportunities
        ),
        execution_blocked=sum(
            item.kind is OpportunityOutcomeKind.EXECUTION_BLOCKED for item in opportunities
        ),
        system_faults=sum(
            item.kind is OpportunityOutcomeKind.SYSTEM_FAULT for item in opportunities
        ),
    )


def counterfactual_mfe_distribution(
    opportunities: tuple[OpportunityOutcome, ...],
) -> tuple[float, ...]:
    """Return isolated missed/blocked MFE values; never merge these into broker P/L."""

    return tuple(
        item.counterfactual_mfe_r
        for item in opportunities
        if item.kind is not OpportunityOutcomeKind.TAKEN
        and item.counterfactual_mfe_r is not None
    )


def _average(values: tuple[float, ...]) -> float:
    return sum(values) / len(values) if values else 0.0


def _rate(values: tuple[bool, ...]) -> float:
    return sum(values) / len(values) if values else 0.0


def _max_drawdown(realized: tuple[float, ...]) -> float:
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for value in realized:
        equity += value
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    return max_dd
