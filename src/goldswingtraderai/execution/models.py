"""Execution-domain contracts for the single governed broker-write boundary."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum

from goldswingtraderai.domain.enums import Direction, HardDecision
from goldswingtraderai.domain.ids import EntityId


class ExecutionAction(StrEnum):
    OPEN = "OPEN"
    MODIFY = "MODIFY"
    CLOSE = "CLOSE"


class IntentState(StrEnum):
    CREATED = "CREATED"
    APPROVED = "APPROVED"
    SUBMITTING = "SUBMITTING"
    ACCEPTED_VERIFIED = "ACCEPTED_VERIFIED"
    ACCEPTED_UNKNOWN = "ACCEPTED_UNKNOWN"
    FAILED = "FAILED"


_TERMINAL_INTENT_STATES = {
    IntentState.ACCEPTED_VERIFIED,
    IntentState.FAILED,
}


@dataclass(frozen=True, slots=True)
class ExecutionIntent:
    intent_id: EntityId
    action: ExecutionAction
    account_login: int
    account_server: str
    symbol: str
    direction: Direction
    volume: float
    approved_entry_reference: float
    stop_loss: float | None
    take_profit: float | None
    opportunity_id: EntityId
    episode_id: EntityId
    trade_plan_id: EntityId
    controller_id: EntityId
    fencing_epoch: int
    created_at_utc: datetime
    state: IntentState = IntentState.CREATED
    submit_attempts: int = 0
    broker_ticket: int | None = None
    broker_retcode: int | None = None
    result_message: str | None = None
    position_ticket: int | None = None
    filling_mode: int | None = None

    def __post_init__(self) -> None:
        _require_utc(self.created_at_utc)
        if self.account_login <= 0:
            raise ValueError("execution account login must be positive")
        if not self.account_server.strip() or not self.symbol.strip():
            raise ValueError("execution account server/symbol cannot be empty")
        if self.direction is Direction.NONE:
            raise ValueError("execution direction must be BUY or SELL")
        if self.volume <= 0 or self.approved_entry_reference <= 0:
            raise ValueError("execution volume/entry reference must be positive")
        if self.stop_loss is not None and self.stop_loss <= 0:
            raise ValueError("execution stop must be positive when supplied")
        if self.take_profit is not None and self.take_profit <= 0:
            raise ValueError("execution target must be positive when supplied")
        if self.fencing_epoch <= 0:
            raise ValueError("execution fencing epoch must be positive")
        if self.submit_attempts not in {0, 1}:
            raise ValueError("one Execution Intent permits at most one send attempt")
        if self.state in {IntentState.SUBMITTING, IntentState.ACCEPTED_UNKNOWN} and self.submit_attempts != 1:
            raise ValueError("submitting/unknown intent must record its single send attempt")
        if self.state is IntentState.ACCEPTED_VERIFIED and self.submit_attempts != 1:
            raise ValueError("accepted intent must record its single send attempt")
        if self.state in {IntentState.CREATED, IntentState.APPROVED} and self.submit_attempts != 0:
            raise ValueError("pre-submit intent cannot already consume its send attempt")
        if self.action in {ExecutionAction.MODIFY, ExecutionAction.CLOSE} and self.position_ticket is None:
            raise ValueError("modify/close intent requires the managed position ticket")

    @property
    def lifecycle_clear_for_new_intent(self) -> bool:
        return self.state in _TERMINAL_INTENT_STATES


def approve_intent(intent: ExecutionIntent) -> ExecutionIntent:
    if intent.state is not IntentState.CREATED:
        raise ValueError("only CREATED intent can become APPROVED")
    return replace(intent, state=IntentState.APPROVED)


def mark_submitting(intent: ExecutionIntent) -> ExecutionIntent:
    """Consume the one irreversible-send allowance before calling the broker."""

    if intent.state is not IntentState.APPROVED:
        raise ValueError("only APPROVED intent can become SUBMITTING")
    if intent.submit_attempts != 0:
        raise ValueError("Execution Intent send allowance already consumed")
    return replace(intent, state=IntentState.SUBMITTING, submit_attempts=1)


def mark_accepted_verified(
    intent: ExecutionIntent,
    *,
    broker_ticket: int | None,
    broker_retcode: int | None,
    message: str | None,
) -> ExecutionIntent:
    if intent.state is not IntentState.SUBMITTING:
        raise ValueError("only SUBMITTING intent can become ACCEPTED_VERIFIED")
    return replace(
        intent,
        state=IntentState.ACCEPTED_VERIFIED,
        broker_ticket=broker_ticket,
        broker_retcode=broker_retcode,
        result_message=message,
    )


def mark_accepted_unknown(
    intent: ExecutionIntent,
    *,
    message: str,
    broker_retcode: int | None = None,
    broker_ticket: int | None = None,
) -> ExecutionIntent:
    if intent.state is not IntentState.SUBMITTING:
        raise ValueError("only SUBMITTING intent can become ACCEPTED_UNKNOWN")
    return replace(
        intent,
        state=IntentState.ACCEPTED_UNKNOWN,
        broker_ticket=broker_ticket,
        broker_retcode=broker_retcode,
        result_message=message,
    )


def mark_failed(
    intent: ExecutionIntent,
    *,
    message: str,
    broker_retcode: int | None = None,
) -> ExecutionIntent:
    if intent.state not in {IntentState.APPROVED, IntentState.SUBMITTING}:
        raise ValueError("only APPROVED/SUBMITTING intent can become FAILED")
    return replace(
        intent,
        state=IntentState.FAILED,
        broker_retcode=broker_retcode,
        result_message=message,
    )


def reconcile_accepted(
    intent: ExecutionIntent,
    *,
    broker_ticket: int | None,
    message: str,
) -> ExecutionIntent:
    """Resolve a crash/ambiguous acknowledgement to confirmed broker exposure."""

    if intent.state not in {IntentState.SUBMITTING, IntentState.ACCEPTED_UNKNOWN}:
        raise ValueError("only ambiguous/submitting intent can reconcile as accepted")
    return replace(
        intent,
        state=IntentState.ACCEPTED_VERIFIED,
        broker_ticket=broker_ticket or intent.broker_ticket,
        result_message=message,
    )


def reconcile_not_created(intent: ExecutionIntent, *, message: str) -> ExecutionIntent:
    """Finalize a consumed attempt only after broker truth proves no exposure."""

    if intent.state not in {IntentState.SUBMITTING, IntentState.ACCEPTED_UNKNOWN}:
        raise ValueError("only ambiguous/submitting intent can reconcile as not created")
    return replace(intent, state=IntentState.FAILED, result_message=message)


@dataclass(frozen=True, slots=True)
class AuthorityTrace:
    authority: str
    decision: HardDecision
    reason: str


@dataclass(frozen=True, slots=True)
class ExecutionPermission:
    decision: HardDecision
    primary_reason: str
    secondary_reasons: tuple[str, ...]
    authority_trace: tuple[AuthorityTrace, ...]
    would_otherwise_trade: bool

    @property
    def allowed(self) -> bool:
        return self.decision is HardDecision.PASS


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("execution timestamp must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("execution timestamp must be UTC")
