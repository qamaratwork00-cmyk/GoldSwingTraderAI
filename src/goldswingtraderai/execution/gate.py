"""Single final authority composer for irreversible broker writes."""

from __future__ import annotations

from dataclasses import dataclass

from goldswingtraderai.domain.enums import HardDecision
from goldswingtraderai.execution.models import AuthorityTrace, ExecutionPermission


@dataclass(frozen=True, slots=True)
class GateInputs:
    demo_guard: AuthorityTrace
    account_identity: AuthorityTrace
    market_data_quote: AuthorityTrace
    session_news: AuthorityTrace
    risk: AuthorityTrace
    position_capacity: AuthorityTrace
    order_lifecycle: AuthorityTrace
    controller: AuthorityTrace
    execution_checks: AuthorityTrace
    would_otherwise_trade: bool = True

    def traces(self) -> tuple[AuthorityTrace, ...]:
        return (
            self.demo_guard,
            self.account_identity,
            self.market_data_quote,
            self.session_news,
            self.risk,
            self.position_capacity,
            self.order_lifecycle,
            self.controller,
            self.execution_checks,
        )


def evaluate_execution_permission(inputs: GateInputs) -> ExecutionPermission:
    """Compose all hard authorities without weighting or score arithmetic."""

    traces = inputs.traces()
    blocked = tuple(trace for trace in traces if trace.decision is HardDecision.BLOCK)
    unknown = tuple(trace for trace in traces if trace.decision is HardDecision.UNKNOWN)

    if blocked:
        primary = blocked[0]
        secondary = tuple(trace.reason for trace in (*blocked[1:], *unknown))
        return ExecutionPermission(
            decision=HardDecision.BLOCK,
            primary_reason=primary.reason,
            secondary_reasons=secondary,
            authority_trace=traces,
            would_otherwise_trade=inputs.would_otherwise_trade,
        )
    if unknown:
        primary = unknown[0]
        return ExecutionPermission(
            decision=HardDecision.UNKNOWN,
            primary_reason=primary.reason,
            secondary_reasons=tuple(trace.reason for trace in unknown[1:]),
            authority_trace=traces,
            would_otherwise_trade=inputs.would_otherwise_trade,
        )
    return ExecutionPermission(
        decision=HardDecision.PASS,
        primary_reason="EXECUTION_ALLOWED",
        secondary_reasons=(),
        authority_trace=traces,
        would_otherwise_trade=inputs.would_otherwise_trade,
    )
