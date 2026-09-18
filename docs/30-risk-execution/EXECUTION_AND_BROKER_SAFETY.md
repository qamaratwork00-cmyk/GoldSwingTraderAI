# GoldSwingTraderAI — Execution and Broker Safety

**Status:** PROVISIONAL — IMPLEMENTED BASELINE  
**Version:** 0.7-implementation  
**Authority:** MT5 account/symbol verification, execution readiness, broker request validation, one-shot irreversible submission, controller ownership and reconciliation.  
**Depends on:** `RISK_CONTRACT.md`, `SESSION_AND_RISK_STATE_MACHINE.md`, `../20-trading-decisions/TRADE_PLAN.md`, `../00-foundation/SYSTEM_CONTRACT.md`

## Purpose

This document owns the irreversible broker-write boundary.

> **Analysis may be wrong and lose a trade. Execution safety must not create duplicate, wrong-account, wrong-volume or uncontrolled exposure.**

## Current implementation checkpoint — Phase 7

Implemented owners:

```text
execution/models.py
execution/intent_store.py
execution/gate.py
execution/checks.py
execution/controller.py
execution/mt5_writer.py
execution/service.py
execution/reconcile.py
```

Deterministic CI currently proves the centralized gate, one-shot Intent lifecycle, persist-before-send ordering, stale-fencing rejection, no blind retry, OPEN/MODIFY/CLOSE request construction and broker reconciliation behaviour.

A successful MT5 `order_send` retcode is treated as **broker acknowledgement, not final truth**. The intent remains unresolved until positions/orders/deals or action-specific broker state verifies the result. Local trade state may not pretend an ambiguous modify/close succeeded.

The current `InMemoryCoordinationStore` exists only for deterministic lease/fencing tests. It is **not** a production cross-laptop backend. A shared backend satisfying the frozen atomic lease + authoritative expiry + monotonic fencing contract is still required before cross-machine failover can be certified.

Live Windows MT5 DEMO execution/fault-injection evidence remains pending; therefore this document is not VERIFIED.

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

No market score can bypass this path.

## Centralized broker-write permission gate

All create/modify/close actions pass one gate:

```text
DEMO guard / account identity ─┐
market + quote integrity       ├─→ EXECUTION PERMISSION GATE
news/session permission        ┤          │
risk permission                ┤          ├─ PASS
position/capacity state        ┤          ├─ BLOCK
order/reconciliation state     ┤          └─ UNKNOWN → no write
controller ownership           ┤
fresh execution checks         ┘
```

Output exposes decision, primary/secondary reasons, authority trace and `Would Otherwise Trade` where meaningful.

No intelligence, strategy, timing, Trade Plan, risk, management, dashboard, research or learning module may call raw `order_send` directly. The raw call lives only in the narrow MT5 writer boundary.

## Positive DEMO guard — V1

```text
Connected MT5 account positively verified DEMO
→ DEMO_GUARD = PASS
```

Broker writes may proceed only if this guard and every other required authority pass. If DEMO status is not verified, write permission is not granted.

V1 does not define a separate REAL authorization workflow, REAL hard-block contract, LIVE override or alternate REAL execution path.

## Account / symbol / fresh-broker truth

Immediately before irreversible execution, verify relevant current facts including:

- configured account login/server identity and DEMO status;
- intended XAU symbol and tradeability;
- fresh Bid/Ask;
- point/tick/digits/volume/stops/freeze/filling facts as required;
- Risk-approved volume against current broker constraints;
- exact broker margin/order pre-check where applicable;
- no unresolved lifecycle or foreign/manual exposure conflict.

BUY execution uses Ask context; SELL execution uses Bid context. Stale/unknown quote prevents the current write without automatically destroying the underlying opportunity.

## Spread policy — frozen initial rule

```text
SpreadRatio = CurrentExecutableSpread / HealthySpreadBaseline

<=1.50           → NORMAL
>1.50–2.25       → ELEVATED + full revalidation; not automatic block
>2.25            → current entry prevented
spread >25% of approved entry-to-structural-SL distance
                 → current entry prevented
```

The implemented execution checks preserve this non-restrictive distinction: elevated spread may still PASS after full revalidation.

Healthy baseline must exclude known abnormal/news/reopen/stale periods. Exact sampling window remains calibration/implementation work.

## Price drift — frozen initial rule

Adverse drift from Approved Entry Reference normalized by original planned stop distance:

```text
<=10%       → normal revalidation
>10–20%     → elevated full revalidation; not automatic block
>20%        → current intent prevented / WAIT-rebuild if thesis survives
```

Any fresh quote that breaks hard risk, structural stop geometry, target economics or chase validity prevents the current intent regardless of ratio. Execution never moves structural SL merely to make drift fit.

## Execution Intent lifecycle

Durable lifecycle:

```text
CREATED
→ APPROVED
→ SUBMITTING
   ├─ ACCEPTED_VERIFIED
   ├─ ACCEPTED_UNKNOWN
   └─ FAILED
```

A pre-submit failure may become `FAILED` with `submit_attempts=0`. Once `SUBMITTING` is durably stored, the single irreversible-send allowance is consumed.

### Lifetime one-shot invariant

One Execution Intent ID may cause **at most one** irreversible `order_send` for its lifetime. Recreating a new in-memory object with a previously used Intent ID may not bypass this rule; durable intent history is checked.

If reconciliation proves no broker exposure/action occurred, any later attempt must use a **fresh governed Intent ID**, not resend the consumed one.

Blind retry loops are prohibited.

## Broker acknowledgement and reconciliation

`order_send` returning a success-like retcode is not sufficient to finalize local truth.

```text
SUBMITTING
→ broker ACK
→ reconcile broker truth
   → ACCEPTED_VERIFIED
   OR
   → ACCEPTED_UNKNOWN
```

Ambiguity prevents conflicting new writes and triggers reconciliation; it never triggers automatic resubmission.

Reconciliation uses appropriate broker evidence:

- OPEN: positions/orders/deals plus durable intent lineage, magic/comment reconciliation aids, direction/volume/time context;
- MODIFY: current broker position SL/TP and position identity;
- CLOSE: current position absence/reduced exposure plus deal/history evidence where required.

Magic/comment are aids, not sole ownership authority.

Broker positions/orders/deals own current exposure truth; local state owns intent and strategy lifecycle context.

## Stop/TP / modification / close safety

Broker-normalized geometry must preserve structural intent. Harmless broker rounding is allowed; a broker constraint that materially changes the thesis makes the request unexecutable instead of silently redesigning the stop/target.

PROTECT/TRAIL/RUNNER modifications and EXIT/PRE_CLOSE closes are irreversible broker writes and use the same Intent/gate/controller/reconciliation path as new entries.

Management code updates durable local SL/TP/closed state only after `ACCEPTED_VERIFIED`.

## `order_check` / filling mode

Supported filling mode must be known for market OPEN/CLOSE requests. Do not cycle through alternative irreversible sends hoping one succeeds.

`order_check` is pre-submit validation only. If it fails, no send attempt is consumed. If it passes, it is still not execution proof.

## Position ownership / capacity

V1 allows `0/1` independently risk-bearing Gold position.

```text
no Gold exposure                    → capacity may be available
one BOT_MANAGED Gold position       → second independent entry prevented
MANUAL / FOREIGN_EA / UNKNOWN Gold  → fresh bot Gold entry prevented
```

Manual/foreign/unknown positions are never modified as bot-owned. Opposite evidence routes to Trade Manager first rather than opening an automatic hedge.

## Single active execution controller — frozen policy

For one managed account/symbol scope:

```text
one PRIMARY
renewal target 10s
lease TTL 30s
monotonic fencing epoch
fresh ownership verification before every broker write
```

The production coordination backend must support atomic acquire/CAS-equivalent semantics, one winner under contention, authoritative expiry/time semantics, monotonic fencing and sufficient durability across process/laptop failure. A local-only file lock is not sufficient.

If another valid holder exists, the second instance is Observer for writes. After prior lease expiry a standby may atomically acquire a new epoch, but remains RECOVERING/RECONCILING until durable state and broker truth reconcile and all account/risk/session/execution checks pass.

A returned stale primary cannot write with an old epoch. Coordination uncertainty prevents irreversible writes while read-only analysis/dashboard may continue.

## Failure / runtime states

Typical lifecycle/failure classes:

```text
PRE_SUBMIT_BLOCK
BROKER_REJECTED
AMBIGUOUS_ACK
ACCEPTED_VERIFIED
RECONCILIATION_FAILED
```

Runtime execution states include `READY`, `DEGRADED`, `RECONCILING`, `BLOCKED`. `RECONCILING` prevents conflicting new writes until uncertainty resolves.

## Market closure/reopen

No write attempts are spammed while Gold is unavailable. PRE_CLOSE flatten uses the governed close path. After reopen, hard warmup/data/spread/reconciliation requirements must pass before fresh entry execution.

## Diagnostics

Expose enough state for operator/audit visibility:

- account/symbol + DEMO guard;
- fresh quote and spread baseline/ratio;
- drift and execution-check state;
- volume/margin/stop validation;
- Intent ID/state/send-attempt count;
- reconciliation result;
- ownership/capacity;
- controller ID/epoch/lease status;
- gate primary/secondary reasons.

## Tests required

- centralized gate is the only route to raw irreversible writes;
- positive DEMO guard composition;
- account mismatch/stale quote/spec changes prevent current write;
- elevated spread/drift can pass after full revalidation;
- hard spread/drift limits prevent current intent;
- precheck rejection gives zero sends;
- persist `SUBMITTING` before send;
- maximum one send per Intent ID lifetime;
- success acknowledgement still requires broker verification;
- ambiguous acknowledgement is never blind-retried;
- restart with `SUBMITTING/ACCEPTED_UNKNOWN` reconciles before new writes;
- OPEN/MODIFY/CLOSE action-specific reconciliation;
- manual/foreign ownership protection;
- two controller contenders yield one holder;
- stale fencing epoch cannot write;
- coordination outage prevents writes;
- takeover must reconcile before PRIMARY READY;
- controlled real MT5 DEMO fault-injection proof before VERIFIED release.

## Explicit non-goals

Execution must not decide strategy direction, increase risk, redesign structural SL/targets, use a fixed Gold spread number as sole rule, blind-retry ambiguity, assume unknown exposure is zero, open an automatic hedge/second Gold position, modify foreign positions, allow multiple write controllers, provide hidden non-DEMO authorization, or permit alternate raw broker-write paths.

## Remaining implementation / calibration work

- production shared cross-laptop coordination backend satisfying frozen lease/fencing semantics;
- real MT5 account/symbol/filling/order-check/modify/close DEMO validation;
- healthy-spread baseline sampling/persistence details;
- broker-specific magic/comment values and safe read-only retry/backoff configuration;
- future evidence-backed spread/drift/lease timing refinements.
