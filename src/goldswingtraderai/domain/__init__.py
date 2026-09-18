"""Stable domain contracts shared across GoldSwingTraderAI subsystems."""

from goldswingtraderai.domain.enums import (
    AccountMode,
    Direction,
    ExecutionState,
    HardDecision,
    MarketState,
    NewsSafetyState,
    OpportunityStage,
    PositionOwnership,
    RiskState,
    RuntimeRole,
    StrategyFamily,
    Timeframe,
    TradeManagerAction,
)
from goldswingtraderai.domain.ids import EntityId
from goldswingtraderai.domain.models import (
    ControllerLease,
    DemoGuardResult,
    ExecutionIntent,
    MarketSnapshotMeta,
    PermissionResult,
    Reason,
)

__all__ = [
    "AccountMode",
    "ControllerLease",
    "DemoGuardResult",
    "Direction",
    "EntityId",
    "ExecutionIntent",
    "ExecutionState",
    "HardDecision",
    "MarketSnapshotMeta",
    "MarketState",
    "NewsSafetyState",
    "OpportunityStage",
    "PermissionResult",
    "PositionOwnership",
    "Reason",
    "RiskState",
    "RuntimeRole",
    "StrategyFamily",
    "Timeframe",
    "TradeManagerAction",
]
