# GoldSwingTraderAI — Execution and Broker Safety

**Status:** PROVISIONAL — IMPLEMENTED BASELINE + DURABLE COORDINATION + RECOVERY GATE  
**Version:** 0.9-implementation  
**Authority:** MT5 account/symbol verification, execution readiness, broker request validation, one-shot irreversible submission, controller ownership/fencing, takeover reconciliation and broker reconciliation.  
**Depends on:** `RISK_CONTRACT.md`, `SESSION_AND_RISK_STATE_MACHINE.md`, `PERSISTENCE_RESTART_AND_RECOVERY.md`, `../20-trading-decisions/TRADE_PLAN.md`, `../00-foundation/SYSTEM_CONTRACT.md`

## Purpose

This document owns the irreversible broker-write boundary.

> **Analysis may be wrong and lose a trade. Execution safety must not create duplicate, wrong-account, wrong-volume or uncontrolled exposure.**

## Current implementation checkpoint

Implemented owners:

```text
execution/models.py
execution/intent_store.py
execution/gate.py
execution/checks.py
execution/controller.py
execution/sqlite_coordination.py
execution/mt5_writer.py
execution/service.py
execution/reconcile.py
app/recovery.py
```

Deterministic CI proves centralized permission, one-shot Intent lifecycle, persist-before-send ordering, no blind retry, broker reconciliation, durable monotonic controller epochs, reconciliation-gated takeover and governed startup recovery sequencing.

A successful MT5 `order_send` return is broker acknowledgement, not final truth. Positions/orders/deals or action-specific broker state must verify the result.

## Governed execution path

```text
Approved Trade Plan / verified management action
→ hard authorities PASS
→ Central Execution Permission Gate
→ durable ExecutionIntent APPROVED
→ broker pre-check
→ fresh controller/fencing verification
→ persist SUBMITTING and consume one send allowance
→ ONE governed order_send
→ classify acknowledgement
→ verify/reconcile broker truth
```

No market score can bypass this path. Raw `order_send` remains confined to `execution/mt5_writer.py`.

## Centralized permission gate

All create/modify/close actions require PASS from required hard authorities:

```text
DEMO guard / account identity
market + quote integrity
news/session permission
risk permission
position/capacity
order/reconciliation lifecycle
controller ownership
fresh execution checks
```

BLOCK prevents the write. UNKNOWN also prevents the write.

## Positive DEMO guard

Broker writes require a positively verified connected MT5 DEMO account. V1 has no hidden REAL-money override or alternate write path.

## Account / symbol / fresh broker truth

Before irreversible execution verify relevant current account/server, intended Gold symbol, fresh Bid/Ask, symbol geometry, approved volume, broker margin/order pre-check, capacity/ownership and unresolved lifecycle state.

BUY uses Ask context; SELL uses Bid context. Unknown/stale truth blocks the current write.

## Spread / drift — frozen initial rules

```text
SpreadRatio <=1.50       NORMAL
>1.50–2.25                ELEVATED + full revalidation
>2.25                     block current entry
spread >25% SL distance  block current entry

Adverse drift <=10%      normal revalidation
>10–20%                  elevated + full revalidation
>20%                      block current intent / rebuild if thesis survives
```

Fresh structural/risk/target/chase invalidation blocks regardless of ratio. Execution never moves a structural SL merely to fit execution conditions.

## Execution Intent lifecycle

```text
CREATED
→ APPROVED
→ SUBMITTING
   ├─ ACCEPTED_VERIFIED
   ├─ ACCEPTED_UNKNOWN
   └─ FAILED
```

One Intent ID may cause at most one irreversible `order_send` for its lifetime. Persisting `SUBMITTING` consumes that allowance before the broker call.

If an ambiguous/consumed attempt is later proven absent, a future attempt requires a **fresh governed Intent ID**. Blind retries are prohibited.

## Broker reconciliation

`SUBMITTING` / `ACCEPTED_UNKNOWN` must reconcile current broker truth:

- OPEN: positions/orders/deals + lineage/tag/context;
- MODIFY: actual position SL/TP + ticket;
- CLOSE: position absence/reduced exposure plus deal/history evidence where needed.

Magic/comment are aids, not ownership authority. Broker truth owns current exposure; persistence owns intent/context/history.

## Stop/TP / modification / close safety

PROTECT/TRAIL/RUNNER modifications and EXIT/PRE_CLOSE closes use the same Intent/gate/controller/reconciliation path. Local management state changes only after broker acceptance is verified.

Broker normalization may perform harmless rounding; it may not redesign structural geometry.

## Position ownership / capacity

V1 allows `0/1` independently risk-bearing Gold position. Manual/foreign/unknown Gold exposure blocks fresh bot entry and is never modified as bot-owned.

## Single active execution controller

Frozen initial policy:

```text
one PRIMARY per managed account/symbol scope
renewal target 10s
lease TTL 30s
monotonic fencing epoch
fresh holder/epoch/expiry verification before every broker write
```

### Coordination backends

`InMemoryCoordinationStore` is deterministic-test-only.

`SQLiteCoordinationStore` implements transactional acquire/renew/release with `BEGIN IMMEDIATE` and a separate durable monotonic epoch ledger. Deterministic tests prove one winner under independent-instance contention, higher epoch after expiry/reopen, stale-holder denial and persisted lease/epoch integrity.

`shared_locking_verified=False` by default. Setting it true is only a deployment assertion; code cannot self-certify arbitrary network/shared filesystems. Real cross-laptop deployment remains pending controlled fault proof.

### Takeover is not immediate write permission

If a valid holder exists, a contender is blocked with `ANOTHER_ACTIVE_CONTROLLER`.

After prior lease expiry a standby may atomically obtain a newer epoch, but it returns:

```text
BLOCK — CONTROLLER_TAKEOVER_RECONCILIATION_REQUIRED
```

Renewal preserves this blocked state. `verify_write_authority()` also remains blocked.

Required takeover sequence:

```text
old lease expires
→ standby gets higher epoch
→ takeover recovery BLOCK
→ durable state integrity/restore
→ broker current truth
→ unresolved Intent reconciliation
→ ManagedTrade reconciliation
→ all hard recovery authorities PASS
→ fresh same holder + same epoch verification
→ complete_takeover_reconciliation()
→ CONTROLLER_PRIMARY
```

## Startup recovery integration — implemented deterministic foundation

`app/recovery.py` is now the governed software owner of the valid call sequence for takeover completion.

It loads/validates persistent recovery state, checks current DEMO/account/server/symbol context, reconciles ambiguous Intents, checks ManagedTrade against current broker-position facts, requires explicit hard recovery authorities PASS, and only then may call `complete_takeover_reconciliation()`.

Important semantics:

- `APPROVED` but never `SUBMITTING` may be cancelled safely on recovery with zero sends;
- `CREATED` requires review/reconciliation rather than implicit send;
- `SUBMITTING` / `ACCEPTED_UNKNOWN` use existing `MT5Reconciler` and never resend blindly;
- verified OPEN without durable ManagedTrade context stays `RECONCILING`;
- missing/mismatched ManagedTrade broker truth cannot become READY;
- any hard authority BLOCK/UNKNOWN prevents takeover completion;
- if holder/epoch changes during recovery, completion fails.

The coordinator itself performs no broker write.

## Failure / runtime states

Typical states/reasons include:

```text
PRE_SUBMIT_BLOCK
BROKER_REJECTED
AMBIGUOUS_ACK
ACCEPTED_VERIFIED
RECONCILIATION_FAILED
CONTROLLER_TAKEOVER_RECONCILIATION_REQUIRED
STARTUP_RECOVERY_READY
```

Runtime may be `READY`, `DEGRADED`, `RECONCILING`, or `BLOCKED`. Uncertainty prevents conflicting writes.

## Diagnostics

Expose account/symbol/DEMO guard, quote/spread/drift, volume/margin/stop validation, Intent ID/state/send count, reconciliation result, ownership/capacity, controller ID/epoch/lease, takeover-recovery state and exact gate/recovery reason.

## Tests / current evidence

Deterministic coverage includes:

- central gate + raw-writer confinement;
- exactly one send per Intent ID;
- ambiguous ACK no blind retry;
- action-specific reconciliation;
- stale fencing denial;
- SQLite one-winner contention + monotonic epoch;
- stale renew/release denial;
- takeover blocked until explicit reconciliation;
- authority loss during takeover prevents completion;
- clean startup recovery READY;
- non-DEMO/account mismatch recovery block;
- unresolved intent preserves RECONCILING;
- ManagedTrade broker mismatch preserves RECONCILING/BLOCK;
- hard-authority UNKNOWN prevents READY;
- startup coordinator is the governed successful takeover-completion path.

Current repository checkpoint: **219 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Explicit non-goals

Execution must not decide strategy direction, increase risk, redesign structural SL/targets, blind-retry ambiguity, assume unknown exposure is zero, hedge with a second independent Gold position, modify foreign positions, permit multiple write controllers, treat a new epoch as sufficient write authority, or provide hidden non-DEMO authorization.

## Remaining work

- read-only live MT5 recovery-snapshot adapter through the existing MT5 read boundary;
- final runtime wiring so live startup supplies all recovery authorities from authoritative owners;
- controlled shared-storage/cross-laptop failover proof;
- real MT5 DEMO account/symbol/filling/modify/close/takeover fault evidence;
- healthy-spread baseline persistence/calibration;
- broker-specific magic/comment and safe read retry configuration.
