"""Analytical decision, opportunity, timing and structural Trade Plan contracts."""

from goldswingtraderai.decisions.fusion import DecisionBoard, FusionConfig, ThesisReport, fuse_decision
from goldswingtraderai.decisions.opportunity import (
    Opportunity,
    OpportunityConfig,
    rearm_missed_opportunity,
    transition_opportunity,
    update_opportunity,
)
from goldswingtraderai.decisions.snapshot import (
    DecisionConfig,
    DecisionSnapshot,
    build_decision_snapshot,
)
from goldswingtraderai.decisions.timing import (
    EntryTimingConfig,
    EntryTimingResult,
    TimingAction,
    evaluate_entry_timing,
)
from goldswingtraderai.decisions.trade_plan import (
    PlanState,
    PlanTarget,
    RRClass,
    StopQuality,
    TargetRole,
    TradePlan,
    TradePlanConfig,
    build_trade_plan,
)

__all__ = [
    "DecisionBoard",
    "DecisionConfig",
    "DecisionSnapshot",
    "EntryTimingConfig",
    "EntryTimingResult",
    "FusionConfig",
    "Opportunity",
    "OpportunityConfig",
    "PlanState",
    "PlanTarget",
    "RRClass",
    "StopQuality",
    "TargetRole",
    "ThesisReport",
    "TimingAction",
    "TradePlan",
    "TradePlanConfig",
    "build_decision_snapshot",
    "build_trade_plan",
    "evaluate_entry_timing",
    "fuse_decision",
    "rearm_missed_opportunity",
    "transition_opportunity",
    "update_opportunity",
]
