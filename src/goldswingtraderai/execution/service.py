"""Governed one-shot execution service.

This is the only application service allowed to invoke MT5Writer.send_once. It
persists intent state before the irreversible call and never retries ambiguity.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from goldswingtraderai.domain.enums import HardDecision
from goldswingtraderai.domain.market import Quote
from goldswingtraderai.execution.controller import ControllerLeaseManager
from goldswingtraderai.execution.intent_store import ExecutionIntentRepository
from goldswingtraderai.execution.models import (
    ExecutionIntent,
    ExecutionPermission,
    IntentState,
    approve_intent,
    mark_accepted_unknown,
    mark_accepted_verified,
    mark_failed,
    mark_submitting,
)
from goldswingtraderai.execution.mt5_writer import BrokerSubmitClass, MT5Writer


class ExecutionService:
    """Persist → precheck → fresh controller verify → persist SUBMITTING → send once."""

    def __init__(
        self,
        repository: ExecutionIntentRepository,
        writer: MT5Writer,
        controller: ControllerLeaseManager,
    ) -> None:
        self.repository = repository
        self.writer = writer
        self.controller = controller

    def execute(
        self,
        intent: ExecutionIntent,
        permission: ExecutionPermission,
        quote: Quote,
        now_utc: datetime,
    ) -> ExecutionIntent:
        if intent.state is not IntentState.CREATED:
            raise ValueError("ExecutionService requires a fresh CREATED intent")
        if not permission.allowed:
            raise PermissionError(
                f"execution permission not granted: {permission.decision}/{permission.primary_reason}"
            )

        lifecycle, lifecycle_reason = self.repository.lifecycle_permission()
        if lifecycle is not HardDecision.PASS:
            raise PermissionError(f"execution lifecycle is not clear: {lifecycle_reason}")

        approved = approve_intent(intent)
        self.repository.save(approved, event_type="INTENT_APPROVED")

        check = self.writer.precheck(approved, quote)
        if not check.passed:
            failed = mark_failed(
                approved,
                message=_precheck_message(check.reason, check.comment),
                broker_retcode=check.retcode,
            )
            self.repository.save(failed, event_type="INTENT_PRECHECK_FAILED")
            return failed

        controller_status = self.controller.verify_write_authority(now_utc)
        if controller_status.decision is not HardDecision.PASS or controller_status.lease is None:
            failed = mark_failed(
                approved,
                message=f"controller authority failed: {controller_status.reason}",
            )
            self.repository.save(failed, event_type="INTENT_CONTROLLER_FAILED")
            return failed
        if controller_status.lease.holder_id != approved.controller_id:
            failed = mark_failed(approved, message="execution intent controller identity mismatch")
            self.repository.save(failed, event_type="INTENT_CONTROLLER_FAILED")
            return failed
        if controller_status.lease.epoch != approved.fencing_epoch:
            failed = mark_failed(approved, message="execution intent fencing epoch is stale")
            self.repository.save(failed, event_type="INTENT_CONTROLLER_FAILED")
            return failed

        # Persisting SUBMITTING consumes the single send allowance before the broker
        # call. A crash from this point forward must reconcile; it must never retry.
        submitting = mark_submitting(approved)
        self.repository.save(submitting, event_type="INTENT_SUBMITTING")

        result = self.writer.send_once(check.request)
        if result.classification is BrokerSubmitClass.ACCEPTED:
            accepted = mark_accepted_verified(
                submitting,
                broker_ticket=result.broker_ticket or result.deal_ticket,
                broker_retcode=result.retcode,
                message=result.comment,
            )
            self.repository.save(accepted, event_type="INTENT_ACCEPTED_VERIFIED")
            return accepted
        if result.classification is BrokerSubmitClass.REJECTED:
            failed = mark_failed(
                submitting,
                message=result.comment or "broker rejected order_send",
                broker_retcode=result.retcode,
            )
            self.repository.save(failed, event_type="INTENT_BROKER_REJECTED")
            return failed

        unknown = mark_accepted_unknown(
            submitting,
            message=result.comment or "broker acknowledgement is ambiguous",
            broker_retcode=result.retcode,
        )
        self.repository.save(unknown, event_type="INTENT_ACCEPTED_UNKNOWN")
        return unknown


def bind_execution_price(intent: ExecutionIntent, quote: Quote) -> ExecutionIntent:
    """Return intent with fresh quote recorded only for diagnostics if desired.

    The immutable approved-entry reference remains the Trade Plan reference; this
    helper intentionally does not overwrite it. Kept as a no-op semantic marker for
    callers that must distinguish planning reference from executable quote.
    """

    if quote.symbol != intent.symbol:
        raise ValueError("execution quote symbol does not match intent")
    return replace(intent)


def _precheck_message(reason: str, comment: str | None) -> str:
    return reason if not comment else f"{reason}: {comment}"
