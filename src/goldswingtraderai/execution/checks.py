"""Fresh execution-time spread/drift checks.

Elevated conditions trigger full revalidation; they are not arbitrary automatic
trade vetoes. Frozen hard limits remain explicit and auditable.
"""

from __future__ import annotations

from dataclasses import dataclass

from goldswingtraderai.decisions.trade_plan import PlanState, TradePlan
from goldswingtraderai.domain.enums import Direction, HardDecision
from goldswingtraderai.domain.market import Quote


@dataclass(frozen=True, slots=True)
class ExecutionCheckResult:
    decision: HardDecision
    reason: str
    executable_price: float | None
    spread_ratio: float | None
    spread_to_stop_ratio: float | None
    adverse_drift_ratio: float | None
    elevated: bool


@dataclass(frozen=True, slots=True)
class ExecutionCheckConfig:
    normal_spread_ratio: float = 1.50
    max_spread_ratio: float = 2.25
    max_spread_to_stop_ratio: float = 0.25
    normal_adverse_drift_ratio: float = 0.10
    max_adverse_drift_ratio: float = 0.20

    def __post_init__(self) -> None:
        if not 1.0 <= self.normal_spread_ratio < self.max_spread_ratio:
            raise ValueError("spread ratio thresholds are invalid")
        if not 0 < self.max_spread_to_stop_ratio < 1:
            raise ValueError("spread-to-stop ratio must be between 0 and 1")
        if not 0 <= self.normal_adverse_drift_ratio < self.max_adverse_drift_ratio < 1:
            raise ValueError("adverse drift thresholds are invalid")


def evaluate_execution_checks(
    plan: TradePlan,
    quote: Quote,
    *,
    healthy_spread_baseline: float | None,
    quote_fresh: bool,
    full_revalidation_passed: bool,
    config: ExecutionCheckConfig | None = None,
) -> ExecutionCheckResult:
    """Evaluate frozen spread/drift rules against one fresh executable quote."""

    cfg = config or ExecutionCheckConfig()
    if plan.state is not PlanState.READY:
        return _result(HardDecision.BLOCK, "TRADE_PLAN_NOT_READY")
    if not quote_fresh:
        return _result(HardDecision.UNKNOWN, "DATA_STALE")
    if plan.original_r_price is None or plan.original_r_price <= 0:
        return _result(HardDecision.UNKNOWN, "RISK_GEOMETRY_TOO_LARGE")
    if healthy_spread_baseline is None or healthy_spread_baseline <= 0:
        return _result(HardDecision.UNKNOWN, "SPREAD_CONTEXT_UNKNOWN")

    executable_price = quote.ask if plan.direction is Direction.BUY else quote.bid
    spread_ratio = quote.spread_price / healthy_spread_baseline
    spread_to_stop = quote.spread_price / plan.original_r_price
    adverse_drift = _adverse_drift(plan.direction, plan.approved_entry_reference, executable_price)
    adverse_drift_ratio = max(0.0, adverse_drift) / plan.original_r_price

    if spread_ratio > cfg.max_spread_ratio or spread_to_stop > cfg.max_spread_to_stop_ratio:
        return ExecutionCheckResult(
            decision=HardDecision.BLOCK,
            reason="SPREAD_TOO_HIGH",
            executable_price=executable_price,
            spread_ratio=spread_ratio,
            spread_to_stop_ratio=spread_to_stop,
            adverse_drift_ratio=adverse_drift_ratio,
            elevated=False,
        )
    if adverse_drift_ratio > cfg.max_adverse_drift_ratio:
        return ExecutionCheckResult(
            decision=HardDecision.BLOCK,
            reason="PRICE_DRIFT",
            executable_price=executable_price,
            spread_ratio=spread_ratio,
            spread_to_stop_ratio=spread_to_stop,
            adverse_drift_ratio=adverse_drift_ratio,
            elevated=False,
        )

    elevated_spread = spread_ratio > cfg.normal_spread_ratio
    elevated_drift = adverse_drift_ratio > cfg.normal_adverse_drift_ratio
    if (elevated_spread or elevated_drift) and not full_revalidation_passed:
        return ExecutionCheckResult(
            decision=HardDecision.UNKNOWN,
            reason="EXECUTION_REVALIDATION_REQUIRED",
            executable_price=executable_price,
            spread_ratio=spread_ratio,
            spread_to_stop_ratio=spread_to_stop,
            adverse_drift_ratio=adverse_drift_ratio,
            elevated=True,
        )

    if elevated_drift:
        reason = "PRICE_DRIFT_ELEVATED"
    elif elevated_spread:
        reason = "SPREAD_ELEVATED"
    else:
        reason = "EXECUTION_CHECKS_PASS"
    return ExecutionCheckResult(
        decision=HardDecision.PASS,
        reason=reason,
        executable_price=executable_price,
        spread_ratio=spread_ratio,
        spread_to_stop_ratio=spread_to_stop,
        adverse_drift_ratio=adverse_drift_ratio,
        elevated=elevated_spread or elevated_drift,
    )


def _adverse_drift(direction: Direction, approved: float, executable: float) -> float:
    if direction is Direction.BUY:
        return executable - approved
    if direction is Direction.SELL:
        return approved - executable
    raise ValueError("execution drift requires BUY or SELL direction")


def _result(decision: HardDecision, reason: str) -> ExecutionCheckResult:
    return ExecutionCheckResult(
        decision=decision,
        reason=reason,
        executable_price=None,
        spread_ratio=None,
        spread_to_stop_ratio=None,
        adverse_drift_ratio=None,
        elevated=False,
    )
