"""One governed live analysis, management and execution cycle.

The cycle deliberately keeps orchestration in the application layer. Analytical
modules remain pure, risk remains independent, and every broker write still
travels through the central gate, durable Intent and ``ExecutionService``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from math import isclose

from goldswingtraderai.app.recovery import RecoveryState
from goldswingtraderai.app.runtime import LiveCycleFacts, LiveStartupRuntime
from goldswingtraderai.decisions import (
    DecisionSnapshot,
    PlanState,
    TradePlan,
    build_decision_snapshot,
    build_trade_plan,
)
from goldswingtraderai.decisions.opportunity import (
    Opportunity,
    transition_opportunity,
)
from goldswingtraderai.decisions.timing import EntryTimingResult, TimingAction
from goldswingtraderai.domain.enums import (
    DataQuality,
    HardDecision,
    MarketState,
    OpportunityStage,
    Timeframe,
)
from goldswingtraderai.domain.ids import new_execution_intent_id
from goldswingtraderai.domain.market import MarketSnapshot, OpenPositionFacts
from goldswingtraderai.execution import (
    AuthorityTrace,
    ExecutionAction,
    ExecutionIntent,
    ExecutionPermission,
    GateInputs,
    IntentState,
    evaluate_execution_checks,
    evaluate_execution_permission,
    evaluate_management_execution_checks,
)
from goldswingtraderai.intelligence import build_intelligence_snapshot
from goldswingtraderai.intelligence.snapshot import IntelligenceSnapshot
from goldswingtraderai.management import (
    ManagedTrade,
    TradeManagementDecision,
    apply_verified_management_result,
    evaluate_trade_manager,
    management_intent_from_decision,
    managed_trade_from_fill,
    ManagedTradeRepository,
)
from goldswingtraderai.persistence import RuntimeStateRepository
from goldswingtraderai.risk import (
    CooldownState,
    EpisodeRiskState,
    ExposureSnapshot,
    RiskContext,
    cooldown_decision,
    evaluate_risk,
    register_episode_entry,
    RiskEvaluation,
)
from goldswingtraderai.execution.checks import ExecutionCheckResult


class CycleAction(StrEnum):
    RECOVERY_RECONCILING = "RECOVERY_RECONCILING"
    WAIT = "WAIT"
    ENTRY_BLOCKED = "ENTRY_BLOCKED"
    ENTRY_FAILED = "ENTRY_FAILED"
    OPENED = "OPENED"
    HOLD = "HOLD"
    MANAGEMENT_BLOCKED = "MANAGEMENT_BLOCKED"
    MANAGED = "MANAGED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


@dataclass(frozen=True, slots=True)
class RuntimeCycleResult:
    """Immutable operator/research view of one live cycle."""

    as_of_utc: datetime
    action: CycleAction
    reason: str
    recovery_state: RecoveryState
    market: MarketSnapshot
    intelligence: IntelligenceSnapshot | None = None
    decision: DecisionSnapshot | None = None
    plan: TradePlan | None = None
    risk: RiskEvaluation | None = None
    permission: ExecutionPermission | None = None
    intent: ExecutionIntent | None = None
    managed_trade: ManagedTrade | None = None
    management: TradeManagementDecision | None = None

    def __post_init__(self) -> None:
        _require_utc(self.as_of_utc)


class GovernedRuntimeCycle:
    """Run the documented strategy → risk → gate → execution sequence."""

    def __init__(
        self,
        runtime: LiveStartupRuntime,
        *,
        healthy_spread_baseline: float | None = None,
    ) -> None:
        self.runtime = runtime
        self.healthy_spread_baseline = (
            runtime.settings.healthy_spread_baseline
            if healthy_spread_baseline is None
            else healthy_spread_baseline
        )
        if self.healthy_spread_baseline is not None and self.healthy_spread_baseline <= 0:
            raise ValueError("healthy spread baseline must be positive")

    def run(self, facts: LiveCycleFacts) -> RuntimeCycleResult:
        """Evaluate one fresh cycle; no write occurs before all authorities pass."""

        startup = facts.startup
        market = startup.market_snapshot
        now_utc = market.meta.as_of_utc
        if startup.recovery.state is not RecoveryState.READY:
            return RuntimeCycleResult(
                as_of_utc=now_utc,
                action=CycleAction.RECOVERY_RECONCILING,
                reason=startup.recovery.reason,
                recovery_state=startup.recovery.state,
                market=market,
            )

        runtime_repository, managed_repository = self._repositories()
        previous = runtime_repository.load_active_opportunity()
        intelligence = build_intelligence_snapshot(
            market,
            news=facts.news,
            holiday_context=facts.holiday_context,
        )
        decision = build_decision_snapshot(
            intelligence,
            now_utc,
            previous_opportunity=previous,
        )
        opportunity = decision.opportunity
        if opportunity is not None:
            runtime_repository.save_active_opportunity(opportunity)
            self._ensure_episode(runtime_repository, opportunity)

        trade = managed_repository.load()
        if trade is not None:
            return self._manage_open_trade(
                facts,
                intelligence,
                decision,
                trade,
            )
        return self._consider_entry(
            facts,
            intelligence,
            decision,
            previous=previous,
        )

    def _consider_entry(
        self,
        facts: LiveCycleFacts,
        intelligence: IntelligenceSnapshot,
        decision: DecisionSnapshot,
        *,
        previous: Opportunity | None,
    ) -> RuntimeCycleResult:
        market = facts.startup.market_snapshot
        now_utc = market.meta.as_of_utc
        timing = decision.timing
        if timing is None or timing.action not in {TimingAction.ENTER_BUY, TimingAction.ENTER_SELL}:
            return RuntimeCycleResult(
                as_of_utc=now_utc,
                action=CycleAction.WAIT,
                reason=_timing_reason(timing, decision),
                recovery_state=facts.startup.recovery.state,
                market=market,
                intelligence=intelligence,
                decision=decision,
            )

        opportunity = timing.opportunity
        runtime_repository, _ = self._repositories()
        runtime_repository.save_active_opportunity(opportunity)
        try:
            plan = build_trade_plan(opportunity, intelligence, market, now_utc)
        except ValueError as exc:
            return self._entry_result(
                facts,
                intelligence,
                decision,
                CycleAction.ENTRY_BLOCKED,
                f"TRADE_PLAN_BUILD_FAILED:{type(exc).__name__}",
            )
        runtime_repository.save_trade_plan(plan)
        if plan.state is not PlanState.READY:
            return self._entry_result(
                facts,
                intelligence,
                decision,
                CycleAction.ENTRY_BLOCKED,
                plan.reason,
                plan=plan,
            )

        risk = self._evaluate_entry_risk(
            facts,
            intelligence,
            plan,
            opportunity,
            previous=previous,
        )
        if risk.decision is not HardDecision.PASS or risk.volume is None:
            return self._entry_result(
                facts,
                intelligence,
                decision,
                CycleAction.ENTRY_BLOCKED,
                risk.reason,
                plan=plan,
                risk=risk,
            )

        writer = self.runtime.writer
        if writer is None:
            raise RuntimeError("live writer is not assembled")
        broker_margin = writer.required_margin_for(
            direction=plan.direction,
            symbol=market.meta.symbol,
            volume=risk.volume,
            quote=market.quote,
        )
        if broker_margin is not None:
            risk = self._evaluate_entry_risk(
                facts,
                intelligence,
                plan,
                opportunity,
                previous=previous,
                broker_required_margin=broker_margin,
            )
            if risk.decision is not HardDecision.PASS or risk.volume is None:
                return self._entry_result(
                    facts,
                    intelligence,
                    decision,
                    CycleAction.ENTRY_BLOCKED,
                    risk.reason,
                    plan=plan,
                    risk=risk,
                )

        permission, execution_check = self._entry_permission(
            facts,
            plan,
            risk,
        )
        if not permission.allowed:
            return self._entry_result(
                facts,
                intelligence,
                decision,
                CycleAction.ENTRY_BLOCKED,
                permission.primary_reason,
                plan=plan,
                risk=risk,
                permission=permission,
            )

        intent = self._open_intent(plan, risk.volume, facts)
        assert self.runtime.execution_service is not None
        result = self.runtime.execution_service.execute(
            intent,
            permission,
            market.quote,
            market.meta.as_of_utc,
        )
        if result.state is not IntentState.ACCEPTED_VERIFIED:
            return self._entry_result(
                facts,
                intelligence,
                decision,
                CycleAction.RECONCILIATION_REQUIRED
                if result.state is IntentState.ACCEPTED_UNKNOWN
                else CycleAction.ENTRY_FAILED,
                result.result_message or result.state.value,
                plan=plan,
                risk=risk,
                permission=permission,
                intent=result,
            )

        managed = self._finalize_verified_open(
            facts,
            opportunity,
            plan,
            result,
        )
        if managed is None:
            return self._entry_result(
                facts,
                intelligence,
                decision,
                CycleAction.RECONCILIATION_REQUIRED,
                "VERIFIED_OPEN_POSITION_CONTEXT_NOT_FOUND",
                plan=plan,
                risk=risk,
                permission=permission,
                intent=result,
            )
        return self._entry_result(
            facts,
            intelligence,
            decision,
            CycleAction.OPENED,
            "OPEN_VERIFIED_AND_MANAGED",
            plan=plan,
            risk=risk,
            permission=permission,
            intent=result,
            managed_trade=managed,
        )

    def _manage_open_trade(
        self,
        facts: LiveCycleFacts,
        intelligence: IntelligenceSnapshot,
        decision: DecisionSnapshot,
        trade: ManagedTrade,
    ) -> RuntimeCycleResult:
        market = facts.startup.market_snapshot
        now_utc = market.meta.as_of_utc
        management = evaluate_trade_manager(
            trade,
            market,
            intelligence,
            pre_close_flatten=facts.session_news.flatten_required,
        )
        if not management.requires_broker_write:
            return RuntimeCycleResult(
                as_of_utc=now_utc,
                action=CycleAction.HOLD,
                reason=management.reason,
                recovery_state=facts.startup.recovery.state,
                market=market,
                intelligence=intelligence,
                decision=decision,
                managed_trade=trade,
                management=management,
            )

        permission, _ = self._management_permission(facts, trade, management)
        if not permission.allowed:
            return RuntimeCycleResult(
                as_of_utc=now_utc,
                action=CycleAction.MANAGEMENT_BLOCKED,
                reason=permission.primary_reason,
                recovery_state=facts.startup.recovery.state,
                market=market,
                intelligence=intelligence,
                decision=decision,
                permission=permission,
                managed_trade=trade,
                management=management,
            )

        controller = self.runtime.controller
        if controller is None or controller.lease is None:
            raise RuntimeError("controller lease is unavailable after PASS gate")
        intent = management_intent_from_decision(
            trade,
            management,
            account_login=market.account.login,
            account_server=market.account.server,
            controller_id=self.runtime.controller_id,
            fencing_epoch=controller.lease.epoch,
            created_at_utc=now_utc,
            filling_mode=market.symbol_spec.filling_mode,
        )
        if intent is None:
            raise RuntimeError("management write permission produced no intent")
        assert self.runtime.execution_service is not None
        result = self.runtime.execution_service.execute(
            intent,
            permission,
            market.quote,
            now_utc,
        )
        if result.state is not IntentState.ACCEPTED_VERIFIED:
            action = (
                CycleAction.RECONCILIATION_REQUIRED
                if result.state is IntentState.ACCEPTED_UNKNOWN
                else CycleAction.MANAGEMENT_BLOCKED
            )
            return RuntimeCycleResult(
                as_of_utc=now_utc,
                action=action,
                reason=result.result_message or result.state.value,
                recovery_state=facts.startup.recovery.state,
                market=market,
                intelligence=intelligence,
                decision=decision,
                permission=permission,
                intent=result,
                managed_trade=trade,
                management=management,
            )

        _, managed_repository = self._repositories()
        updated = apply_verified_management_result(
            managed_repository,
            trade,
            management,
            result,
            verified_at_utc=now_utc,
        )
        if management.action.value == "EXIT":
            runtime_repository, _ = self._repositories()
            runtime_repository.clear_active_opportunity()
            runtime_repository.clear_trade_plan()
        return RuntimeCycleResult(
            as_of_utc=now_utc,
            action=CycleAction.MANAGED,
            reason=management.reason,
            recovery_state=facts.startup.recovery.state,
            market=market,
            intelligence=intelligence,
            decision=decision,
            permission=permission,
            intent=result,
            managed_trade=updated,
            management=management,
        )

    def _entry_permission(
        self,
        facts: LiveCycleFacts,
        plan: TradePlan,
        risk: RiskEvaluation,
    ) -> tuple[ExecutionPermission, ExecutionCheckResult]:
        market = facts.startup.market_snapshot
        now_utc = market.meta.as_of_utc
        checks = evaluate_execution_checks(
            plan,
            market.quote,
            healthy_spread_baseline=self.healthy_spread_baseline,
            quote_fresh=_quote_fresh(market, now_utc),
            # The plan, risk and authorities were all rebuilt from this fresh
            # cycle snapshot; this is the required full pre-submit revalidation.
            full_revalidation_passed=True,
        )
        controller_trace = self._controller_trace(now_utc)
        lifecycle_trace = self._lifecycle_trace()
        permission = evaluate_execution_permission(
            GateInputs(
                demo_guard=self._demo_trace(market),
                account_identity=facts.startup.authorities.account_identity,
                market_data_quote=self._market_quote_trace(market, now_utc),
                session_news=self._session_trace(facts, for_new_entry=True),
                risk=AuthorityTrace("risk", risk.decision, risk.reason),
                position_capacity=self._position_trace(facts, for_new_entry=True),
                order_lifecycle=lifecycle_trace,
                controller=controller_trace,
                execution_checks=AuthorityTrace("execution_checks", checks.decision, checks.reason),
                would_otherwise_trade=True,
            )
        )
        return permission, checks

    def _management_permission(
        self,
        facts: LiveCycleFacts,
        trade: ManagedTrade,
        decision: TradeManagementDecision,
    ) -> tuple[ExecutionPermission, ExecutionCheckResult]:
        market = facts.startup.market_snapshot
        now_utc = market.meta.as_of_utc
        checks = evaluate_management_execution_checks(
            trade,
            market.quote,
            healthy_spread_baseline=self.healthy_spread_baseline,
            quote_fresh=_quote_fresh(market, now_utc),
        )
        controller_trace = self._controller_trace(now_utc)
        lifecycle_trace = self._lifecycle_trace()
        permission = evaluate_execution_permission(
            GateInputs(
                demo_guard=self._demo_trace(market),
                account_identity=facts.startup.authorities.account_identity,
                market_data_quote=self._market_quote_trace(market, now_utc),
                session_news=self._session_trace(facts, for_new_entry=False),
                risk=facts.startup.authorities.risk,
                position_capacity=self._position_trace(facts, for_new_entry=False),
                order_lifecycle=lifecycle_trace,
                controller=controller_trace,
                execution_checks=AuthorityTrace("execution_checks", checks.decision, checks.reason),
                would_otherwise_trade=True,
            )
        )
        return permission, checks

    def _evaluate_entry_risk(
        self,
        facts: LiveCycleFacts,
        intelligence: IntelligenceSnapshot,
        plan: TradePlan,
        opportunity: Opportunity,
        *,
        previous: Opportunity | None,
        broker_required_margin: float | None = None,
    ) -> RiskEvaluation:
        runtime_repository, _ = self._repositories()
        risk_day = runtime_repository.load_risk_day()
        if risk_day is None:
            raise RuntimeError("startup READY without a RiskDayState")
        episode = runtime_repository.load_episode_risk(opportunity.episode_id)
        if episode is None:
            episode = EpisodeRiskState(episode_id=opportunity.episode_id)
            runtime_repository.save_episode_risk(episode)
        cooldown_state = runtime_repository.load_cooldown() or CooldownState()
        lifecycle, _ = self._lifecycle_value()
        fresh_event = _fresh_structural_event(intelligence, previous)
        cooldown = cooldown_decision(
            cooldown_state,
            plan.created_at_utc,
            latest_completed_m15_utc=_latest_candle_time(facts.startup.market_snapshot, Timeframe.M15),
            unresolved_execution_fault=lifecycle is not HardDecision.PASS,
            fresh_opportunity=fresh_event or episode.entries_taken == 0,
        )
        exposure = _exposure_snapshot(facts, None)
        return evaluate_risk(
            plan,
            facts.startup.market_snapshot,
            RiskContext(
                risk_day=risk_day,
                cooldown=cooldown,
                episode=episode,
                fresh_structural_event=fresh_event,
                exposure=exposure,
                broker_required_margin=broker_required_margin,
            ),
        )

    def _finalize_verified_open(
        self,
        facts: LiveCycleFacts,
        opportunity: Opportunity,
        plan: TradePlan,
        intent: ExecutionIntent,
    ) -> ManagedTrade | None:
        market = facts.startup.market_snapshot
        before = facts.startup.recovery_truth.open_positions
        fresh_truth = self.runtime.capture_cycle(now_utc=market.meta.as_of_utc).startup.recovery_truth
        position = _find_open_position(
            fresh_truth.open_positions,
            intent,
            self.runtime.settings.mt5_magic,
            self.runtime.settings.mt5_comment_prefix,
            before_tickets={item.ticket for item in before},
        )
        if position is None:
            return None
        _, managed_repository = self._repositories()
        managed = managed_trade_from_fill(
            plan,
            position_ticket=position.ticket,
            volume=position.volume,
            fill_price=position.price_open,
            opened_at_utc=market.meta.as_of_utc,
            symbol=position.symbol,
        )
        managed_repository.save(managed, event_type="MANAGED_TRADE_OPENED_VERIFIED")
        runtime_repository, _ = self._repositories()
        runtime_repository.save_active_opportunity(
            transition_opportunity(opportunity, OpportunityStage.TRIGGERED, market.meta.as_of_utc)
        )
        episode = runtime_repository.load_episode_risk(opportunity.episode_id)
        if episode is None:
            episode = EpisodeRiskState(episode_id=opportunity.episode_id)
        runtime_repository.save_episode_risk(
            register_episode_entry(episode, fresh_structural_event=True)
        )
        return managed

    def _open_intent(
        self,
        plan: TradePlan,
        volume: float,
        facts: LiveCycleFacts,
    ) -> ExecutionIntent:
        market = facts.startup.market_snapshot
        controller = self.runtime.controller
        if controller is None or controller.lease is None:
            raise RuntimeError("controller lease is unavailable after PASS gate")
        return ExecutionIntent(
            intent_id=new_execution_intent_id(),
            action=ExecutionAction.OPEN,
            account_login=market.account.login,
            account_server=market.account.server,
            symbol=market.meta.symbol,
            direction=plan.direction,
            volume=volume,
            approved_entry_reference=plan.approved_entry_reference,
            stop_loss=plan.initial_stop,
            take_profit=plan.broker_tp_target.price if plan.broker_tp_target is not None else None,
            opportunity_id=plan.opportunity_id,
            episode_id=plan.episode_id,
            trade_plan_id=plan.plan_id,
            controller_id=self.runtime.controller_id,
            fencing_epoch=controller.lease.epoch,
            created_at_utc=market.meta.as_of_utc,
            filling_mode=market.symbol_spec.filling_mode,
        )

    def _repositories(self) -> tuple[RuntimeStateRepository, ManagedTradeRepository]:
        if self.runtime.runtime_repository is None or self.runtime.managed_trade_repository is None:
            raise RuntimeError("runtime repositories are not assembled")
        return self.runtime.runtime_repository, self.runtime.managed_trade_repository

    def _ensure_episode(self, repository: RuntimeStateRepository, opportunity: Opportunity) -> None:
        if repository.load_episode_risk(opportunity.episode_id) is None:
            repository.save_episode_risk(EpisodeRiskState(episode_id=opportunity.episode_id))

    def _entry_result(
        self,
        facts: LiveCycleFacts,
        intelligence: IntelligenceSnapshot,
        decision: DecisionSnapshot,
        action: CycleAction,
        reason: str,
        *,
        plan: TradePlan | None = None,
        risk: RiskEvaluation | None = None,
        permission: ExecutionPermission | None = None,
        intent: ExecutionIntent | None = None,
        managed_trade: ManagedTrade | None = None,
    ) -> RuntimeCycleResult:
        return RuntimeCycleResult(
            as_of_utc=facts.startup.market_snapshot.meta.as_of_utc,
            action=action,
            reason=reason,
            recovery_state=facts.startup.recovery.state,
            market=facts.startup.market_snapshot,
            intelligence=intelligence,
            decision=decision,
            plan=plan,
            risk=risk,
            permission=permission,
            intent=intent,
            managed_trade=managed_trade,
        )

    def _demo_trace(self, market: MarketSnapshot) -> AuthorityTrace:
        guard = self.runtime.reader.demo_guard(market.account)
        reason = "DEMO_GUARD_VERIFIED" if guard.decision is HardDecision.PASS else (
            guard.reason.code.value if guard.reason is not None else "DEMO_GUARD_UNKNOWN"
        )
        return AuthorityTrace("demo_guard", guard.decision, reason)

    def _market_quote_trace(self, market: MarketSnapshot, now_utc: datetime) -> AuthorityTrace:
        if market.quality is DataQuality.CORRUPT:
            return AuthorityTrace("market_data_quote", HardDecision.BLOCK, "MARKET_DATA_CORRUPT")
        if not _quote_fresh(market, now_utc):
            return AuthorityTrace("market_data_quote", HardDecision.UNKNOWN, "QUOTE_STALE")
        if market.quality is not DataQuality.HEALTHY:
            return AuthorityTrace(
                "market_data_quote",
                HardDecision.UNKNOWN,
                f"MARKET_DATA_{market.quality.value}",
            )
        return AuthorityTrace("market_data_quote", HardDecision.PASS, "QUOTE_AND_DATA_FRESH")

    def _session_trace(self, facts: LiveCycleFacts, *, for_new_entry: bool) -> AuthorityTrace:
        permission = facts.session_news
        if permission.decision is HardDecision.UNKNOWN:
            return AuthorityTrace(
                "session_news",
                HardDecision.UNKNOWN,
                permission.reasons[0] if permission.reasons else "SESSION_NEWS_UNKNOWN",
            )
        if for_new_entry:
            return AuthorityTrace(
                "session_news",
                permission.decision,
                permission.reasons[0] if permission.reasons else "SESSION_NEWS_CLEAR",
            )
        market_state = permission.market.state
        if market_state is MarketState.CLOSED:
            return AuthorityTrace("session_news", HardDecision.BLOCK, "SESSION_CLOSED")
        return AuthorityTrace("session_news", HardDecision.PASS, "SESSION_MANAGEMENT_ALLOWED")

    def _position_trace(self, facts: LiveCycleFacts, *, for_new_entry: bool) -> AuthorityTrace:
        trade = self.runtime.managed_trade_repository.load() if self.runtime.managed_trade_repository else None
        positions = facts.startup.recovery_truth.snapshot.positions
        if trade is not None:
            matching = tuple(position for position in positions if position.ticket == trade.position_ticket)
            if len(matching) != 1:
                return AuthorityTrace(
                    "position_capacity",
                    HardDecision.UNKNOWN,
                    "BOT_MANAGED_POSITION_RECONCILIATION_REQUIRED",
                )
            if for_new_entry:
                return AuthorityTrace("position_capacity", HardDecision.BLOCK, "POSITION_CAPACITY_FULL")
            return AuthorityTrace("position_capacity", HardDecision.PASS, "BOT_MANAGED_POSITION_RECONCILED")
        if positions:
            return AuthorityTrace(
                "position_capacity",
                HardDecision.BLOCK,
                "EXTERNAL_GOLD_EXPOSURE",
            )
        return AuthorityTrace("position_capacity", HardDecision.PASS, "POSITION_CAPACITY_CLEAR")

    def _controller_trace(self, now_utc: datetime) -> AuthorityTrace:
        if self.runtime.controller is None:
            return AuthorityTrace("controller", HardDecision.UNKNOWN, "CONTROLLER_OWNERSHIP_UNKNOWN")
        return self.runtime.controller.verify_write_authority(now_utc).as_trace()

    def _lifecycle_trace(self) -> AuthorityTrace:
        decision, reason = self._lifecycle_value()
        return AuthorityTrace("order_lifecycle", decision, reason)

    def _lifecycle_value(self) -> tuple[HardDecision, str]:
        if self.runtime.intent_repository is None:
            return HardDecision.UNKNOWN, "ORDER_LIFECYCLE_UNKNOWN"
        return self.runtime.intent_repository.lifecycle_permission()


def _timing_reason(timing: EntryTimingResult | None, decision: DecisionSnapshot) -> str:
    if timing is not None and timing.reasons:
        return timing.reasons[0]
    if decision.opportunity is None:
        return "OPPORTUNITY_NONE"
    return decision.opportunity.stage.value


def _quote_fresh(market: MarketSnapshot, now_utc: datetime) -> bool:
    return market.quality is DataQuality.HEALTHY and market.quote.age_seconds(now_utc) <= 10.0


def _latest_candle_time(market: MarketSnapshot, timeframe: Timeframe) -> datetime | None:
    try:
        return market.candles(timeframe)[-1].time_utc
    except (KeyError, IndexError):
        return None


def _fresh_structural_event(
    intelligence: IntelligenceSnapshot,
    previous: Opportunity | None,
) -> bool:
    if previous is None:
        return True
    for timeframe in (Timeframe.M15, Timeframe.M5):
        try:
            frame = intelligence.for_timeframe(timeframe)
        except KeyError:
            continue
        if any(event.event_time > previous.updated_at_utc for event in frame.structure.events):
            return True
    return False


def _exposure_snapshot(facts: LiveCycleFacts, trade: ManagedTrade | None) -> ExposureSnapshot:
    positions = facts.startup.recovery_truth.snapshot.positions
    if trade is None:
        return ExposureSnapshot(
            bot_gold_positions=0,
            external_gold_exposure=bool(positions),
            ownership_known=True,
        )
    matching = [position for position in positions if position.ticket == trade.position_ticket]
    external = len(positions) != 1 or not matching
    return ExposureSnapshot(
        bot_gold_positions=1 if matching else 0,
        external_gold_exposure=external,
        ownership_known=True,
    )


def _find_open_position(
    positions: tuple[OpenPositionFacts, ...],
    intent: ExecutionIntent,
    magic: int | None,
    comment_prefix: str,
    before_tickets: set[int],
) -> OpenPositionFacts | None:
    tag = f"{comment_prefix}:{intent.intent_id.value[:12]}"
    tagged = tuple(
        position
        for position in positions
        if position.symbol == intent.symbol
        and position.direction is intent.direction
        and isclose(position.volume, intent.volume, rel_tol=0.0, abs_tol=1e-8)
        and tag in (position.comment or "")
        and (magic is None or position.magic in {None, magic})
    )
    if len(tagged) == 1:
        return tagged[0]
    if intent.broker_ticket is not None:
        by_ticket = tuple(position for position in positions if position.ticket == intent.broker_ticket)
        if len(by_ticket) == 1:
            return by_ticket[0]
    candidates = tuple(
        position
        for position in positions
        if position.ticket not in before_tickets
        if position.symbol == intent.symbol
        and position.direction is intent.direction
        and isclose(position.volume, intent.volume, rel_tol=0.0, abs_tol=1e-8)
    )
    return candidates[0] if len(candidates) == 1 else None


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("cycle timestamp must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("cycle timestamp must be UTC")
