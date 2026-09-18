"""Compact read-only terminal dashboard.

The renderer accepts already-authoritative values. It never recalculates strategy,
risk or execution permission and has no broker-write dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class DashboardData:
    project: str
    symbol: str
    account_mode: str
    demo_guard: str
    runtime_role: str
    account_profile: str
    utc_time: datetime
    m5_seconds_remaining: int | None
    market_state: str
    bid: float | None
    ask: float | None
    spread_price: float | None
    spread_state: str
    structure_summary: str
    ema_fast: float | None
    ema_slow: float | None
    rsi: float | None
    atr: float | None
    decision_action: str
    decision_reason: str
    buy_score: float | None
    sell_score: float | None
    opportunity_score: float | None
    entry_score: float | None
    evidence_coverage: float | None
    strategy_family: str | None
    risk_state: str
    proposed_risk_pct: float | None
    proposed_volume: float | None
    day_safety_pl: float | None
    daily_loss_limit_pct: float | None
    daily_remaining_pct: float | None
    position_count: int
    position_capacity: int
    loss_streak: int
    cooldown: str
    execution_permission: str
    execution_reason: str
    controller_role: str
    lease_epoch: int | None
    broker_reconcile: str
    managed_trade: "OpenTradeView | None" = None
    learning_state: str = "PENDING"
    backup_state: str = "PENDING"
    system_health: str = "HEALTHY"

    def __post_init__(self) -> None:
        if self.utc_time.tzinfo is None or self.utc_time.utcoffset() is None:
            raise ValueError("dashboard UTC time must be timezone-aware")
        if self.utc_time.utcoffset() != timezone.utc.utcoffset(self.utc_time):
            raise ValueError("dashboard time must be UTC")
        if self.m5_seconds_remaining is not None and self.m5_seconds_remaining < 0:
            raise ValueError("M5 remaining seconds cannot be negative")
        if self.position_count < 0 or self.position_capacity <= 0:
            raise ValueError("position count/capacity is invalid")
        if self.position_count > self.position_capacity:
            raise ValueError("position count cannot exceed displayed capacity")
        if self.loss_streak < 0:
            raise ValueError("loss streak cannot be negative")


@dataclass(frozen=True, slots=True)
class OpenTradeView:
    direction: str
    entry: float
    current: float
    original_stop: float
    current_stop: float
    broker_tp: float | None
    primary_target: float | None
    expansion_target: float | None
    runner_target: float | None
    current_r: float | None
    manager_action: str
    manager_reason: str


def render_dashboard(data: DashboardData, *, emoji: bool = True, width: int = 78) -> str:
    """Render one stable terminal frame with no trading side effects."""

    width = max(64, width)
    divider = "─" * width
    title = f" {data.project} ".center(width, "═")
    marker = _markers(emoji)
    lines = [
        title,
        _fit(
            f"{data.symbol} | {data.account_mode} {_guard_marker(data.demo_guard, marker)} | "
            f"{data.account_profile} | {data.runtime_role} | {data.utc_time:%H:%M:%S} UTC",
            width,
        ),
        _fit(
            f"Bid {_num(data.bid)} | Ask {_num(data.ask)} | Spread {_num(data.spread_price)} "
            f"[{data.spread_state}] | M5 {_countdown(data.m5_seconds_remaining)} | {data.market_state}",
            width,
        ),
        divider,
        f"{marker['market']} MARKET      {data.structure_summary}",
        _fit(
            f"EMA20 {_num(data.ema_fast)} | EMA50 {_num(data.ema_slow)} | "
            f"RSI {_num(data.rsi, 1)} | ATR {_num(data.atr, 3)}",
            width,
        ),
        f"{marker['decision']} DECISION    {_action_marker(data.decision_action, marker)} {data.decision_action}",
        _fit(
            f"BUY {_num(data.buy_score, 1)} | SELL {_num(data.sell_score, 1)} | "
            f"Opportunity {_num(data.opportunity_score, 1)} | Entry {_num(data.entry_score, 1)} | "
            f"Coverage {_pct(data.evidence_coverage)}",
            width,
        ),
        _fit(
            f"Strategy {data.strategy_family or '—'} | Reason {data.decision_reason}",
            width,
        ),
        f"{marker['risk']} RISK        {_state_marker(data.risk_state, marker)} {data.risk_state}",
        _fit(
            f"Risk {_pct(data.proposed_risk_pct)} | Lot {_num(data.proposed_volume, 2)} | "
            f"Day P/L {_money(data.day_safety_pl)} | Limit {_pct(data.daily_loss_limit_pct)} | "
            f"Remaining {_pct(data.daily_remaining_pct)}",
            width,
        ),
        _fit(
            f"Position {data.position_count}/{data.position_capacity} | Loss Streak {data.loss_streak} | "
            f"Cooldown {data.cooldown}",
            width,
        ),
        f"{marker['execution']} EXECUTION   {_state_marker(data.execution_permission, marker)} {data.execution_permission}",
        _fit(
            f"Controller {data.controller_role} | Epoch {data.lease_epoch or '—'} | "
            f"Reconcile {data.broker_reconcile} | Reason {data.execution_reason}",
            width,
        ),
    ]

    if data.managed_trade is not None:
        trade = data.managed_trade
        lines.extend(
            [
                f"{marker['trade']} OPEN TRADE  {trade.direction} | Manager {trade.manager_action}",
                _fit(
                    f"Entry {_num(trade.entry)} | Now {_num(trade.current)} | "
                    f"SL {_num(trade.current_stop)} (orig {_num(trade.original_stop)}) | "
                    f"TP {_num(trade.broker_tp)} | R {_num(trade.current_r, 2)}",
                    width,
                ),
                _fit(
                    f"Primary {_num(trade.primary_target)} | Expansion {_num(trade.expansion_target)} | "
                    f"Runner {_num(trade.runner_target)} | Reason {trade.manager_reason}",
                    width,
                ),
            ]
        )

    lines.extend(
        [
            divider,
            _fit(
                f"{marker['learning']} Learning {data.learning_state} | "
                f"{marker['state']} Backup {data.backup_state} | "
                f"{marker['health']} Health {data.system_health}",
                width,
            ),
            _fit(f"{marker['message']} {_reason_explanation(data.decision_reason)}", width),
            "═" * width,
        ]
    )
    return "\n".join(lines)


def _markers(emoji: bool) -> dict[str, str]:
    if emoji:
        return {
            "market": "🌍",
            "decision": "⚖️",
            "trade": "📈",
            "risk": "🛡️",
            "execution": "⚙️",
            "learning": "🧠",
            "state": "💾",
            "health": "🩺",
            "message": "💬",
            "ok": "✅",
            "wait": "🟡",
            "block": "🔴",
            "warn": "⚠️",
        }
    return {
        "market": "[MARKET]",
        "decision": "[DECISION]",
        "trade": "[TRADE]",
        "risk": "[RISK]",
        "execution": "[EXEC]",
        "learning": "[LEARN]",
        "state": "[STATE]",
        "health": "[HEALTH]",
        "message": "[WHY]",
        "ok": "[OK]",
        "wait": "[WAIT]",
        "block": "[BLOCK]",
        "warn": "[WARN]",
    }


def _action_marker(action: str, marker: dict[str, str]) -> str:
    upper = action.upper()
    if upper.startswith("ENTER") or upper in {"HOLD", "PROTECT", "TRAIL", "RUNNER"}:
        return marker["ok"]
    if upper in {"WAIT", "MISSED"}:
        return marker["wait"]
    if upper in {"BLOCKED", "INVALID", "EXIT"}:
        return marker["block"]
    return marker["warn"]


def _state_marker(state: str, marker: dict[str, str]) -> str:
    upper = state.upper()
    if upper in {"PASS", "ALLOW", "READY", "NORMAL", "HEALTHY", "CLEAR"}:
        return marker["ok"]
    if upper in {"WAIT", "DEGRADED", "COOLDOWN", "PRE_CLOSE", "RECONCILING"}:
        return marker["wait"]
    if upper in {"BLOCK", "BLOCKED", "LOSS_LOCKED", "FAILED", "UNKNOWN"}:
        return marker["block"]
    return marker["warn"]


def _guard_marker(state: str, marker: dict[str, str]) -> str:
    return marker["ok"] if state.upper() == "PASS" else marker["block"]


def _num(value: float | None, decimals: int = 3) -> str:
    return "—" if value is None else f"{value:.{decimals}f}"


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value:.2f}%"


def _money(value: float | None) -> str:
    if value is None:
        return "—"
    sign = "+" if value > 0 else ""
    return f"{sign}${value:.2f}"


def _countdown(seconds: int | None) -> str:
    if seconds is None:
        return "—"
    minutes, remainder = divmod(seconds, 60)
    return f"{minutes:02d}:{remainder:02d}"


def _fit(text: str, width: int) -> str:
    return text if len(text) <= width else text[: max(0, width - 1)] + "…"


def _reason_explanation(reason: str) -> str:
    explanations = {
        "ENTRY_EXTENDED": "Entry extended hai; setup valid ho sakta hai, better timing ka wait.",
        "TARGET_ROOM_POOR": "Current entry par credible structural target room kam hai.",
        "NEWS_BLACKOUT": "Scheduled news safety window active hai; new entry pause hai.",
        "NEWS_SAFETY_UNKNOWN": "Required news truth verify nahi hui; new entry authority available nahi.",
        "SESSION_PRE_CLOSE": "Gold session close qareeb hai; new entry allowed nahi.",
        "PRE_CLOSE_FLATTEN": "Scheduled close qareeb hai; managed trade governed close path par hai.",
        "MIN_LOT_UNAFFORDABLE": "Current setup par broker minimum lot actual risk ceiling se bahar hai.",
        "SPREAD_TOO_HIGH": "Current spread execution ke liye excessive hai; setup survive kar sakta hai.",
        "PRICE_DRIFT": "Price approved entry se zyada drift kar chuki hai; chase nahi karenge.",
        "THESIS_HEALTHY_HOLD": "Trade thesis healthy hai; unnecessary early exit nahi.",
        "PRIMARY_CHECKPOINT_CONTINUATION": "Primary checkpoint reached; continuation abhi healthy hai.",
        "RUNNER_EARNED_BY_CONTINUATION": "Fresh continuation aur next objective ne runner earn kiya.",
        "THESIS_REVERSAL_CONFIRMED": "Opposing structure strong hai aur continuation materially weak hui.",
    }
    return explanations.get(reason, reason.replace("_", " ").title())
