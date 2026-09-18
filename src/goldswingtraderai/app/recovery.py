"""Governed startup/recovery orchestration for critical runtime state.

This module does not create broker writes. It combines durable-state integrity,
current broker recovery facts, ambiguous Intent reconciliation, managed-trade
consistency and controller fencing. A takeover controller can become PRIMARY only
after every required recovery authority is PASS.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from math import isclose

from goldswingtraderai.domain.enums import AccountMode, Direction, HardDecision
from goldswingtraderai.domain.market import AccountFacts
from goldswingtraderai.execution.controller import ControllerLeaseManager, ControllerStatus
from goldswingtraderai.execution.intent_store import ExecutionIntentRepository
from goldswingtraderai.execution.models import (
    AuthorityTrace,
    ExecutionAction,
    ExecutionIntent,
    IntentState,
    mark_failed,
)
from goldswingtraderai.execution.reconcile import MT5Reconciler, ReconciliationStatus
from goldswingtraderai.management import ManagedTrade, ManagedTradeRepository
from goldswingtraderai.persistence import (
    RecoveryBundle,
    RuntimeStateRepository,
    StateStore,
    StateStoreError,
)


class RecoveryState(StrEnum):
    READY = "READY"
    RECONCILING = "RECONCILING"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class RecoveryAuthorities:
    """Hard authorities that recovery cannot infer from durable/broker state alone."""

    account_identity: AuthorityTrace
    market_data: AuthorityTrace
    session_news: AuthorityTrace
    risk: AuthorityTrace
    position_capacity: AuthorityTrace
    execution_environment: AuthorityTrace

    @property
    def traces(self) -> tuple[AuthorityTrace, ...]:
        return (
            self.account_identity,
            self.market_data,
            self.session_news,
            self.risk,
            self.position_capacity,
            self.execution_environment,
        )

    def aggregate(self) -> tuple[HardDecision, str]:
        blocked = next((trace for trace in self.traces if trace.decision is HardDecision.BLOCK), None)
        if blocked is not None:
            return HardDecision.BLOCK, blocked.reason
        unknown = next(
            (trace for trace in self.traces if trace.decision is HardDecision.UNKNOWN),
            None,
        )
        if unknown is not None:
            return HardDecision.UNKNOWN, unknown.reason
        return HardDecision.PASS, "RECOVERY_HARD_AUTHORITIES_PASS"


@dataclass(frozen=True, slots=True)
class BrokerRecoveryPosition:
    ticket: int
    symbol: str
    direction: Direction
    volume: float
    stop_loss: float | None
    take_profit: float | None

    def __post_init__(self) -> None:
        if self.ticket <= 0:
            raise ValueError("recovery position ticket must be positive")
        if not self.symbol.strip():
            raise ValueError("recovery position symbol cannot be empty")
        if self.direction is Direction.NONE:
            raise ValueError("recovery position direction must be BUY or SELL")
        if self.volume <= 0:
            raise ValueError("recovery position volume must be positive")
        if self.stop_loss is not None and self.stop_loss <= 0:
            raise ValueError("recovery position stop must be positive when present")
        if self.take_profit is not None and self.take_profit <= 0:
            raise ValueError("recovery position target must be positive when present")


@dataclass(frozen=True, slots=True)
class BrokerRecoverySnapshot:
    account: AccountFacts
    symbol: str
    positions: tuple[BrokerRecoveryPosition, ...]
    captured_at_utc: datetime
    positions_complete: bool = True

    def __post_init__(self) -> None:
        _require_utc(self.captured_at_utc)
        if not self.symbol.strip():
            raise ValueError("recovery snapshot symbol cannot be empty")
        if any(position.symbol != self.symbol for position in self.positions):
            raise ValueError("recovery snapshot positions must match snapshot symbol")


@dataclass(frozen=True, slots=True)
class StartupRecoveryResult:
    state: RecoveryState
    reason: str
    recovery_bundle: RecoveryBundle | None
    execution_intent: ExecutionIntent | None
    managed_trade: ManagedTrade | None
    controller_status: ControllerStatus | None
    takeover_completed: bool = False


class StartupRecoveryCoordinator:
    """Fail-closed recovery sequence before runtime may become write-ready."""

    def __init__(
        self,
        store: StateStore,
        runtime_repository: RuntimeStateRepository,
        intent_repository: ExecutionIntentRepository,
        managed_trade_repository: ManagedTradeRepository,
        controller: ControllerLeaseManager,
        reconciler: MT5Reconciler,
    ) -> None:
        self.store = store
        self.runtime_repository = runtime_repository
        self.intent_repository = intent_repository
        self.managed_trade_repository = managed_trade_repository
        self.controller = controller
        self.reconciler = reconciler

    def recover(
        self,
        snapshot: BrokerRecoverySnapshot,
        authorities: RecoveryAuthorities,
        now_utc: datetime,
        *,
        price_tolerance: float,
        allow_verified_not_created: bool = False,
    ) -> StartupRecoveryResult:
        _require_utc(now_utc)
        if price_tolerance <= 0:
            raise ValueError("recovery price tolerance must be positive")

        try:
            self.store.integrity_check()
            bundle = self.runtime_repository.load_recovery_bundle()
            intent = self.intent_repository.load()
            trade = self.managed_trade_repository.load()
        except StateStoreError:
            return _result(RecoveryState.BLOCKED, "PERSISTENCE_INTEGRITY_FAILED")

        if snapshot.account.mode is not AccountMode.DEMO:
            return _result(
                RecoveryState.BLOCKED,
                "DEMO_GUARD_NOT_VERIFIED",
                bundle=bundle,
                intent=intent,
                trade=trade,
            )
        if not snapshot.positions_complete:
            return _result(
                RecoveryState.RECONCILING,
                "BROKER_POSITION_TRUTH_INCOMPLETE",
                bundle=bundle,
                intent=intent,
                trade=trade,
            )

        mismatch = _identity_mismatch(snapshot, intent, trade)
        if mismatch is not None:
            return _result(
                RecoveryState.BLOCKED,
                mismatch,
                bundle=bundle,
                intent=intent,
                trade=trade,
            )

        intent, intent_reason = self._recover_intent(
            intent,
            now_utc,
            allow_verified_not_created=allow_verified_not_created,
        )
        if intent_reason is not None:
            return _result(
                RecoveryState.RECONCILING,
                intent_reason,
                bundle=bundle,
                intent=intent,
                trade=trade,
            )

        if (
            intent is not None
            and intent.action is ExecutionAction.OPEN
            and intent.state is IntentState.ACCEPTED_VERIFIED
            and trade is None
        ):
            return _result(
                RecoveryState.RECONCILING,
                "MANAGED_TRADE_CONTEXT_MISSING_FOR_VERIFIED_OPEN",
                bundle=bundle,
                intent=intent,
                trade=trade,
            )

        trade_decision, trade_reason = _verify_managed_trade(
            trade,
            snapshot.positions,
            price_tolerance=price_tolerance,
        )
        if trade_decision is not HardDecision.PASS:
            state = (
                RecoveryState.BLOCKED
                if trade_decision is HardDecision.BLOCK
                else RecoveryState.RECONCILING
            )
            return _result(
                state,
                trade_reason,
                bundle=bundle,
                intent=intent,
                trade=trade,
            )

        authority_decision, authority_reason = authorities.aggregate()
        if authority_decision is not HardDecision.PASS:
            state = (
                RecoveryState.BLOCKED
                if authority_decision is HardDecision.BLOCK
                else RecoveryState.RECONCILING
            )
            return _result(
                state,
                authority_reason,
                bundle=bundle,
                intent=intent,
                trade=trade,
            )

        takeover = self.controller.takeover_reconciliation_required
        if takeover:
            controller_status = self.controller.complete_takeover_reconciliation(now_utc)
        else:
            controller_status = self.controller.verify_write_authority(now_utc)

        if controller_status.decision is not HardDecision.PASS:
            state = (
                RecoveryState.BLOCKED
                if controller_status.decision is HardDecision.BLOCK
                else RecoveryState.RECONCILING
            )
            return _result(
                state,
                controller_status.reason,
                bundle=bundle,
                intent=intent,
                trade=trade,
                controller_status=controller_status,
            )

        return _result(
            RecoveryState.READY,
            "STARTUP_RECOVERY_READY",
            bundle=bundle,
            intent=intent,
            trade=trade,
            controller_status=controller_status,
            takeover_completed=takeover,
        )

    def _recover_intent(
        self,
        intent: ExecutionIntent | None,
        now_utc: datetime,
        *,
        allow_verified_not_created: bool,
    ) -> tuple[ExecutionIntent | None, str | None]:
        if intent is None or intent.lifecycle_clear_for_new_intent:
            return intent, None

        if intent.state is IntentState.APPROVED:
            cancelled = mark_failed(
                intent,
                message="RECOVERY_CANCELLED_PRE_SUBMIT_INTENT",
            )
            self.intent_repository.save(
                cancelled,
                event_type="INTENT_RECOVERY_CANCELLED_PRE_SUBMIT",
            )
            return cancelled, None

        if intent.state is IntentState.CREATED:
            return intent, "CREATED_INTENT_REQUIRES_RECOVERY_REVIEW"

        if intent.state in {IntentState.SUBMITTING, IntentState.ACCEPTED_UNKNOWN}:
            evidence = self.reconciler.reconcile(
                intent,
                now_utc,
                allow_verified_not_created=allow_verified_not_created,
            )
            recovered = self.reconciler.apply(self.intent_repository, intent, evidence)
            if evidence.status is ReconciliationStatus.UNRESOLVED:
                return recovered, "EXECUTION_INTENT_RECONCILIATION_UNRESOLVED"
            return recovered, None

        return intent, "ORDER_LIFECYCLE_PENDING"


def _identity_mismatch(
    snapshot: BrokerRecoverySnapshot,
    intent: ExecutionIntent | None,
    trade: ManagedTrade | None,
) -> str | None:
    if intent is not None:
        if intent.account_login != snapshot.account.login:
            return "RECOVERY_ACCOUNT_LOGIN_MISMATCH"
        if intent.account_server != snapshot.account.server:
            return "RECOVERY_ACCOUNT_SERVER_MISMATCH"
        if intent.symbol != snapshot.symbol:
            return "RECOVERY_INTENT_SYMBOL_MISMATCH"
    if trade is not None and trade.symbol != snapshot.symbol:
        return "RECOVERY_MANAGED_TRADE_SYMBOL_MISMATCH"
    return None


def _verify_managed_trade(
    trade: ManagedTrade | None,
    positions: tuple[BrokerRecoveryPosition, ...],
    *,
    price_tolerance: float,
) -> tuple[HardDecision, str]:
    if trade is None:
        return HardDecision.PASS, "NO_MANAGED_TRADE_TO_RECONCILE"

    matches = tuple(position for position in positions if position.ticket == trade.position_ticket)
    if not matches:
        return HardDecision.UNKNOWN, "MANAGED_TRADE_BROKER_POSITION_MISSING"
    if len(matches) != 1:
        return HardDecision.BLOCK, "MANAGED_TRADE_BROKER_POSITION_DUPLICATE"

    position = matches[0]
    if position.symbol != trade.symbol or position.direction is not trade.direction:
        return HardDecision.BLOCK, "MANAGED_TRADE_BROKER_IDENTITY_MISMATCH"
    if not isclose(position.volume, trade.volume, rel_tol=0.0, abs_tol=1e-8):
        return HardDecision.BLOCK, "MANAGED_TRADE_BROKER_VOLUME_MISMATCH"
    if position.stop_loss is None or not isclose(
        position.stop_loss,
        trade.current_stop,
        rel_tol=0.0,
        abs_tol=price_tolerance,
    ):
        return HardDecision.UNKNOWN, "MANAGED_TRADE_STOP_RECONCILIATION_REQUIRED"
    if trade.broker_tp is None:
        if position.take_profit is not None:
            return HardDecision.UNKNOWN, "MANAGED_TRADE_TARGET_RECONCILIATION_REQUIRED"
    elif position.take_profit is None or not isclose(
        position.take_profit,
        trade.broker_tp,
        rel_tol=0.0,
        abs_tol=price_tolerance,
    ):
        return HardDecision.UNKNOWN, "MANAGED_TRADE_TARGET_RECONCILIATION_REQUIRED"
    return HardDecision.PASS, "MANAGED_TRADE_BROKER_TRUTH_MATCHED"


def _result(
    state: RecoveryState,
    reason: str,
    *,
    bundle: RecoveryBundle | None = None,
    intent: ExecutionIntent | None = None,
    trade: ManagedTrade | None = None,
    controller_status: ControllerStatus | None = None,
    takeover_completed: bool = False,
) -> StartupRecoveryResult:
    return StartupRecoveryResult(
        state=state,
        reason=reason,
        recovery_bundle=bundle,
        execution_intent=intent,
        managed_trade=trade,
        controller_status=controller_status,
        takeover_completed=takeover_completed,
    )


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("recovery time must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("recovery time must be UTC")
