"""Analytical decision fusion, opportunity lifecycle and entry timing."""

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

__all__ = [
    "DecisionBoard",
    "DecisionConfig",
    "DecisionSnapshot",
    "EntryTimingConfig",
    "EntryTimingResult",
    "FusionConfig",
    "Opportunity",
    "OpportunityConfig",
    "ThesisReport",
    "TimingAction",
    "build_decision_snapshot",
    "evaluate_entry_timing",
    "fuse_decision",
    "rearm_missed_opportunity",
    "transition_opportunity",
    "update_opportunity",
]
