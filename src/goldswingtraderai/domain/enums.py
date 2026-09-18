"""Core enums used as stable cross-subsystem vocabulary."""

from enum import StrEnum


class Timeframe(StrEnum):
    H4 = "H4"
    H1 = "H1"
    M15 = "M15"
    M5 = "M5"
    M1 = "M1"


class Direction(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    NONE = "NONE"


class HardDecision(StrEnum):
    PASS = "PASS"
    BLOCK = "BLOCK"
    UNKNOWN = "UNKNOWN"


class RuntimeRole(StrEnum):
    PRIMARY = "PRIMARY"
    STANDBY = "STANDBY"
    OBSERVER = "OBSERVER"
    RESEARCH = "RESEARCH"
    RECOVERING = "RECOVERING"


class AccountMode(StrEnum):
    DEMO = "DEMO"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class MarketState(StrEnum):
    OPEN = "OPEN"
    PRE_CLOSE = "PRE_CLOSE"
    CLOSED = "CLOSED"
    REOPEN_WARMUP = "REOPEN_WARMUP"
    HOLIDAY_CAUTION = "HOLIDAY_CAUTION"


class NewsSafetyState(StrEnum):
    NEWS_CLEAR = "NEWS_CLEAR"
    NEWS_BLACKOUT = "NEWS_BLACKOUT"
    NEWS_SAFETY_UNKNOWN = "NEWS_SAFETY_UNKNOWN"
    POST_NEWS_WARMUP = "POST_NEWS_WARMUP"


class RiskState(StrEnum):
    NORMAL = "NORMAL"
    LOSS_LOCKED = "LOSS_LOCKED"
    COOLDOWN = "COOLDOWN"
    BLOCKED = "BLOCKED"


class ExecutionState(StrEnum):
    READY = "READY"
    DEGRADED = "DEGRADED"
    RECONCILING = "RECONCILING"
    BLOCKED = "BLOCKED"


class PositionOwnership(StrEnum):
    BOT_MANAGED = "BOT_MANAGED"
    MANUAL = "MANUAL"
    FOREIGN_EA = "FOREIGN_EA"
    UNKNOWN_OWNER = "UNKNOWN_OWNER"


class TradeManagerAction(StrEnum):
    HOLD = "HOLD"
    PROTECT = "PROTECT"
    TRAIL = "TRAIL"
    RUNNER = "RUNNER"
    EXIT = "EXIT"


class StrategyFamily(StrEnum):
    TREND_PULLBACK_CONTINUATION = "TREND_PULLBACK_CONTINUATION"
    BREAKOUT_EXPANSION = "BREAKOUT_EXPANSION"
    BREAKOUT_RETEST_CONTINUATION = "BREAKOUT_RETEST_CONTINUATION"
    LIQUIDITY_SWEEP_REVERSAL = "LIQUIDITY_SWEEP_REVERSAL"
    FAILED_BREAKOUT_REVERSAL = "FAILED_BREAKOUT_REVERSAL"
    COMPRESSION_EXPANSION = "COMPRESSION_EXPANSION"


class OpportunityStage(StrEnum):
    DISCOVERED = "DISCOVERED"
    ARMED = "ARMED"
    WAITING = "WAITING"
    READY = "READY"
    TRIGGERED = "TRIGGERED"
    MISSED = "MISSED"
    RE_ARMED = "RE_ARMED"
    STALE = "STALE"
    INVALIDATED = "INVALIDATED"
