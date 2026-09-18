"""Governed one-shot execution service.

This is the only application service allowed to invoke MT5Writer.send_once. It
persists intent state before the irreversible call and never retries ambiguity.
"""

from __future__ import annotations

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
    mark_failed,
    mark_submitting,
)
from goldswingtraderai.execution.mt5_writer import BrokerSubmitClass, MT5Writer
from goldswingtraderai.execution.reconcile import MT5Reconciler


class ExecutionService:
    """Persist → precheck → controller verify → send once → broker reconciliation."""

    def __init__(
        self,
        repository: ExecutionIntentRepository,
        writer: MT5Writer,
        controller: ControllerLeaseManager,
        reconciler: MT5Reconciler,
    ) -> None:
        self.repository = repository
        self.writer = writer
        self.controller = controller
        self.reconciler = reconciler

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
        if self.repository.intent_id_seen(intent.intent_id):
            raise PermissionError("Execution Intent ID has already been used")

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
        if result.classification is BrokerSubmitClass.REJECTED:
            failed = mark_failed(
                submitting,
                message=result.comment or "broker rejected order_send",
                broker_retcode=result.retcode,
            )
            self.repository.save(failed, event_type="INTENT_BROKER_REJECTED")
            return failed

        pending = mark_accepted_unknown(
            submitting,
            message=result.comment or "broker acknowledgement requires verification",
            broker_retcode=result.retcode,
            broker_ticket=result.broker_ticket or result.deal_ticket,
        )
        self.repository.save(pending, event_type="INTENT_ACK_PENDING_VERIFICATION")

        # Even a broker success retcode is verified against positions/orders/deals.
        # If broker history is not visible yet, ACCEPTED_UNKNOWN remains durable and
        # new sends stay blocked until a later reconciliation pass resolves it.
        evidence = self.reconciler.reconcile(pending, now_utc)
        return self.reconciler.apply(self.repository, pending, evidence)


def _precheck_message(reason: str, comment: str | None) -> str:
    return reason if not comment else f"{reason}: {comment}"
