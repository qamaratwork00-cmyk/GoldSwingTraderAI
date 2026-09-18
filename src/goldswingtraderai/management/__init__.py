"""Post-entry Trade Manager public API."""

from goldswingtraderai.management.manager import (
    TradeManagerConfig,
    derive_management_evidence,
    evaluate_trade_manager,
)
from goldswingtraderai.management.models import (
    ManagedTrade,
    ManagementEvidence,
    ObjectiveStage,
    StructuralStopReference,
    TradeManagementDecision,
    apply_management_decision,
    managed_trade_from_fill,
)
from goldswingtraderai.management.store import ManagedTradeRepository

__all__ = [
    "ManagedTrade",
    "ManagedTradeRepository",
    "ManagementEvidence",
    "ObjectiveStage",
    "StructuralStopReference",
    "TradeManagementDecision",
    "TradeManagerConfig",
    "apply_management_decision",
    "derive_management_evidence",
    "evaluate_trade_manager",
    "managed_trade_from_fill",
]
