"""Post-entry Trade Manager public API."""

from goldswingtraderai.management.execution import (
    apply_verified_management_result,
    management_intent_from_decision,
)
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
    "apply_verified_management_result",
    "derive_management_evidence",
    "evaluate_trade_manager",
    "managed_trade_from_fill",
    "management_intent_from_decision",
]
