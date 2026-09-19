"""Build the read-only operator dashboard from authoritative live DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from goldswingtraderai.app.cycle import CycleAction, RuntimeCycleResult
from goldswingtraderai.app.recovery import RecoveryState
from goldswingtraderai.app.runtime import LiveCycleFacts, LiveStartupRuntime
from goldswingtraderai.domain.enums import HardDecision, Timeframe
from goldswingtraderai.domain.market import MarketSnapshot
from goldswingtraderai.decisions.opportunity import Opportunity
from goldswingtraderai.intelligence.snapshot import IntelligenceSnapshot, TimeframeIntelligence
from goldswingtraderai.management import ManagedTrade
from goldswingtraderai.operator import DashboardData, OpenTradeView
from goldswingtraderai.persistence import BackupRunResult, StateStoreError
from goldswingtraderai.risk import CooldownState, RiskEvaluation, resolve_account_profile
from goldswingtraderai.research.discovery import CandidateRegistry


def build_dashboard_data(
    runtime: LiveStartupRuntime,
    facts: LiveCycleFacts,
    cycle: RuntimeCycleResult,
    *,
    backup: BackupRunResult | None = None,
    backup_error: str | None = None,
) -> DashboardData:
    """Translate current authoritative state into the presentation DTO.

    This adapter may summarize existing decisions and permissions, but it never
    calls strategy, risk, gate or broker-write code to produce new authority.
    """

    market = cycle.market
    intelligence = cycle.intelligence
    decision = cycle.decision
    m5 = None if intelligence is None else _frame_or_none(intelligence, Timeframe.M5)
    decision_timing = None if decision is None else decision.timing
    opportunity = None if decision is None else decision.opportunity
    risk = cycle.risk if isinstance(cycle.risk, RiskEvaluation) else None
    cooldown = _load_cooldown(runtime)
    controller = runtime.controller
    lease = None if controller is None else controller.lease

    execution_reason = (
        cycle.permission.primary_reason
        if cycle.permission is not None
        else cycle.reason
    )
    execution_permission = (
        cycle.permission.decision.value if cycle.permission is not None else cycle.action.value
    )
    spread_state = _trace_reason(cycle, "execution_checks") or "UNKNOWN"
    account_profile = risk.profile.value if risk is not None and risk.profile is not None else _profile(runtime, market.account.equity)
    managed = _managed_trade_view(cycle.managed_trade, market, cycle)
    backup_state = _backup_state(backup, backup_error)
    research = _research_view(runtime)
    return DashboardData(
        project="GoldSwingTraderAI",
        symbol=market.meta.symbol,
        account_mode=market.account.mode.value,
        demo_guard=_trace_decision(facts, "execution_environment"),
        runtime_role=runtime.settings.runtime_mode.value,
        account_profile=account_profile,
        utc_time=cycle.as_of_utc,
        m5_seconds_remaining=_m5_remaining(market, cycle.as_of_utc),
        market_state=facts.session_news.market.state.value,
        bid=market.quote.bid,
        ask=market.quote.ask,
        spread_price=market.quote.spread_price,
        spread_state=spread_state,
        structure_summary=_structure_summary(intelligence),
        ema_fast=None if m5 is None else m5.quant.ema_fast,
        ema_slow=None if m5 is None else m5.quant.ema_slow,
        rsi=None if m5 is None else m5.quant.rsi,
        atr=None if m5 is None else m5.quant.atr,
        decision_action=_decision_action(cycle),
        decision_reason=_decision_reason(cycle),
        buy_score=None if decision is None else decision.board.buy.score,
        sell_score=None if decision is None else decision.board.sell.score,
        opportunity_score=None if decision is None or opportunity is None else opportunity.opportunity_score,
        entry_score=None if decision_timing is None else decision_timing.score,
        evidence_coverage=None if decision is None else decision.board.evidence_coverage * 100.0,
        strategy_family=_strategy_family(opportunity),
        risk_state=_risk_state(risk),
        proposed_risk_pct=None if risk is None else risk.all_in_risk_pct,
        proposed_volume=None if risk is None else risk.volume,
        day_safety_pl=None if risk is None or risk.day is None else risk.day.account_safety_pl,
        daily_loss_limit_pct=None if risk is None or risk.day is None else risk.day.daily_lock_pct,
        daily_remaining_pct=None if risk is None or risk.day is None else risk.day.remaining_loss_budget_pct,
        position_count=len(facts.startup.recovery_truth.snapshot.positions),
        position_capacity=1,
        loss_streak=cooldown.consecutive_losses,
        cooldown=_cooldown_label(cooldown, cycle.as_of_utc),
        execution_permission=execution_permission,
        execution_reason=execution_reason,
        controller_role=_controller_role(runtime, facts.startup.recovery.state),
        lease_epoch=None if lease is None else lease.epoch,
        broker_reconcile=facts.startup.recovery.reason,
        managed_trade=managed,
        learning_state=research.learning_state,
        backup_state=backup_state,
        system_health=_system_health(cycle, backup, backup_error),
        discovery_state=research.discovery_state,
        candidate=research.candidate,
        candidate_stage=research.candidate_stage,
        suppression_reason=research.suppression_reason,
    )


def _frame_or_none(
    intelligence: IntelligenceSnapshot,
    timeframe: Timeframe,
) -> TimeframeIntelligence | None:
    try:
        return intelligence.for_timeframe(timeframe)
    except KeyError:
        return None


def _load_cooldown(runtime: LiveStartupRuntime) -> CooldownState:
    if runtime.runtime_repository is None:
        return CooldownState()
    return runtime.runtime_repository.load_cooldown() or CooldownState()


def _profile(runtime: LiveStartupRuntime, equity: float) -> str:
    if runtime.runtime_repository is None:
        return "UNKNOWN"
    risk_day = runtime.runtime_repository.load_risk_day()
    profile = resolve_account_profile(risk_day.day_start_equity if risk_day is not None else equity)
    return "UNKNOWN" if profile is None else profile.value


def _trace_decision(facts: LiveCycleFacts, name: str) -> str:
    for trace in facts.startup.authorities.traces:
        if trace.authority == name:
            return trace.decision.value
    return "UNKNOWN"


def _trace_reason(cycle: RuntimeCycleResult, name: str) -> str | None:
    if cycle.permission is None:
        return None
    for trace in cycle.permission.authority_trace:
        if trace.authority == name:
            return trace.reason
    return None


def _structure_summary(intelligence: IntelligenceSnapshot | None) -> str:
    if intelligence is None:
        return "UNKNOWN"
    return " | ".join(
        f"{frame.timeframe.value} {frame.structure.state.value}"
        for frame in intelligence.frames
    ) or "UNKNOWN"


def _decision_action(cycle: RuntimeCycleResult) -> str:
    if cycle.management is not None:
        return cycle.management.action.value
    if cycle.decision is not None and cycle.decision.timing is not None:
        return cycle.decision.timing.action.value
    return cycle.action.value


def _decision_reason(cycle: RuntimeCycleResult) -> str:
    if cycle.management is not None:
        return cycle.management.reason
    if cycle.decision is not None and cycle.decision.timing is not None:
        if cycle.decision.timing.reasons:
            return cycle.decision.timing.reasons[0]
    return cycle.reason


def _strategy_family(opportunity: Opportunity | None) -> str | None:
    if opportunity is None or not opportunity.source_families:
        return None
    return opportunity.source_families[0].value


def _risk_state(risk: RiskEvaluation | None) -> str:
    if risk is None:
        return "UNKNOWN"
    if risk.decision is not HardDecision.PASS:
        return risk.reason
    if risk.day is not None and risk.day.loss_locked:
        return "LOSS_LOCKED"
    return risk.risk_band.value


def _cooldown_label(state: CooldownState, now_utc: datetime) -> str:
    if state.cooldown_until_utc is not None and now_utc < state.cooldown_until_utc:
        return "COOLDOWN"
    return "CLEAR"


def _controller_role(runtime: LiveStartupRuntime, recovery_state: RecoveryState) -> str:
    if recovery_state is not RecoveryState.READY:
        return recovery_state.value
    controller = runtime.controller
    if controller is None or controller.lease is None:
        return "UNKNOWN"
    return runtime.settings.runtime_mode.value


def _managed_trade_view(
    trade: ManagedTrade | None,
    market: MarketSnapshot,
    cycle: RuntimeCycleResult,
) -> OpenTradeView | None:
    if trade is None:
        return None
    current = market.quote.bid if trade.direction.value == "BUY" else market.quote.ask
    current_r = None
    if trade.original_r_price > 0:
        current_r = (
            (current - trade.entry_price) / trade.original_r_price
            if trade.direction.value == "BUY"
            else (trade.entry_price - current) / trade.original_r_price
        )
    return OpenTradeView(
        direction=trade.direction.value,
        entry=trade.entry_price,
        current=current,
        original_stop=trade.original_stop,
        current_stop=trade.current_stop,
        broker_tp=trade.broker_tp,
        primary_target=None if trade.primary_target is None else trade.primary_target.price,
        expansion_target=None if trade.expansion_target is None else trade.expansion_target.price,
        runner_target=None if trade.runner_candidate is None else trade.runner_candidate.price,
        current_r=current_r,
        manager_action="HOLD" if cycle.management is None else cycle.management.action.value,
        manager_reason="NO_MANAGEMENT_DECISION" if cycle.management is None else cycle.management.reason,
    )


def _m5_remaining(market: MarketSnapshot, now_utc: datetime) -> int | None:
    try:
        latest = market.candles(Timeframe.M5)[-1].time_utc
    except (KeyError, IndexError):
        return None
    remaining = int(max(0.0, (latest + timedelta(minutes=5) - now_utc).total_seconds()))
    return remaining


def _backup_state(backup: BackupRunResult | None, backup_error: str | None) -> str:
    if backup_error is not None:
        return "FAILED"
    if backup is None:
        return "PENDING"
    return "VERIFIED"


def _system_health(
    cycle: RuntimeCycleResult,
    backup: BackupRunResult | None,
    backup_error: str | None,
) -> str:
    if cycle.recovery_state is RecoveryState.BLOCKED:
        return "BLOCKED"
    if cycle.recovery_state is RecoveryState.RECONCILING:
        return "DEGRADED"
    if backup_error is not None:
        return "DEGRADED"
    if cycle.action in {CycleAction.ENTRY_BLOCKED, CycleAction.MANAGEMENT_BLOCKED}:
        return "WARN"
    return "HEALTHY"


@dataclass(frozen=True, slots=True)
class _ResearchView:
    learning_state: str
    discovery_state: str
    candidate: str | None = None
    candidate_stage: str | None = None
    suppression_reason: str | None = None


def _research_view(runtime: LiveStartupRuntime) -> _ResearchView:
    """Read durable research liveness without running or changing research."""

    if runtime.store is None or runtime.scope is None:
        return _ResearchView("PENDING", "PENDING")
    try:
        journal = runtime.store.load_record("research_episode_journal", runtime.scope)
        registry = CandidateRegistry(runtime.store, runtime.scope)
        candidates = registry.all()
        status = registry.load_discovery_status()
    except (StateStoreError, ValueError, KeyError, TypeError):
        return _ResearchView(
            "DEGRADED",
            "DEGRADED",
            suppression_reason="RESEARCH_STATE_INVALID",
        )

    learning = "ACTIVE" if journal is not None else "PENDING"
    latest = max(candidates, key=lambda item: item.created_at_utc, default=None)
    if status is not None:
        suppression = status.reasons[-1] if status.reasons and latest is None else None
        return _ResearchView(
            learning,
            status.health,
            None if latest is None else str(latest.candidate_id),
            None if latest is None else latest.stage.value,
            suppression,
        )
    if latest is not None:
        return _ResearchView(learning, "HEALTHY", str(latest.candidate_id), latest.stage.value)
    return _ResearchView(learning, "PENDING")
