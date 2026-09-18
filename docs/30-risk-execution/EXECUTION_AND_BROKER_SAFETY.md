# GoldSwingTraderAI — Execution and Broker Safety

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** MT5 account/symbol verification, execution readiness, broker request validation, one-shot irreversible submission, ownership and reconciliation.  
**Depends on:** `RISK_CONTRACT.md`, `SESSION_AND_RISK_STATE_MACHINE.md`, `../20-trading-decisions/TRADE_PLAN.md`, `../00-foundation/SYSTEM_CONTRACT.md`

## Purpose

This document owns the narrow irreversible broker-write boundary.

> **Analysis may be wrong and lose a trade. Execution safety must not create duplicate, wrong-account, wrong-volume or uncontrolled exposure.**

## Governed execution path

```text
Approved Trade Plan
→ Risk PASS
→ Execution Readiness
→ Persist intent
→ Broker pre-check
→ ONE governed order_send
→ Classify result
→ Verify / reconcile
```

No market score can bypass this path.

## Account identity pinning

At startup the system should verify and pin intended broker identity facts such as:

- login/account identifier;
- server;
- account mode/type;
- currency;
- trade permissions.

Every irreversible write must verify the currently connected account still matches the intended/pinned identity.

Runtime account change produces `ACCOUNT_IDENTITY_MISMATCH` and blocks new writes until safely resolved.

## DEMO-first policy

Initial implementation/release is intended for verified DEMO execution. A real account connection must not silently gain production broker-write authority unless a later explicit frozen release policy allows it.

## Symbol resolution and broker specs

The adapter should resolve the intended Gold instrument and verify at least:

- symbol existence/visibility;
- trade mode;
- digits/point/tick size;
- tick value/contract size;
- min/max/step volume;
- stops/freeze levels;
- supported filling modes.

Symbol specs are broker facts. Unexpected material spec changes require revalidation before new writes.

## Fresh executable quote

Immediately before a market order, the system must verify fresh Bid/Ask and correct executable side:

- BUY uses Ask-side execution context;
- SELL uses Bid-side execution context.

Stale/unknown quote blocks submission without invalidating the underlying opportunity automatically.

## Price drift and fresh plan revalidation

Before send, fresh quote must be checked against the approved plan for:

- price drift;
- current monetary risk;
- target room/RR;
- extension/chase;
- stop geometry;
- spread.

If the plan materially degrades, return to WAIT/DEGRADED rather than chase.

## Spread and execution quality

Analysis-time spread is descriptive. Immediate pre-send spread is execution authority. Excessive spread can block a submission while preserving the setup.

Exact thresholds remain open/calibrated.

## Stop/TP geometry

Broker-normalized SL/TP must satisfy direction, tick/digit, minimum-stop and freeze constraints.

Harmless rounding is allowed. A broker constraint that materially changes structural intent makes the plan unexecutable rather than silently moving the stop/target.

## Volume and margin

Execution revalidates the Risk-approved volume against current broker specs and fresh margin/account state. It may block due to changed facts but must not improvise a new volume or risk policy.

## Persist intent before send

Before the irreversible submit, durable state must contain at least:

- Execution Intent ID;
- Decision/Opportunity/Episode IDs;
- strategy/policy version;
- direction;
- volume;
- approved entry reference;
- SL/TP/objectives as applicable;
- account identity;
- risk snapshot;
- timestamp;
- lifecycle state such as `SUBMITTING`.

This allows safe crash recovery.

## Order lifecycle

Provisional lifecycle:

```text
CREATED
APPROVED
SUBMITTING
├─ ACCEPTED_VERIFIED
├─ ACCEPTED_UNKNOWN
└─ FAILED
```

Verified accepted intent later maps into the managed open-position lifecycle.

## One-shot submission invariant

For one approved Execution Intent ID, there is at most **one irreversible `order_send` attempt** until reconciliation proves the prior attempt did not create broker exposure and a fresh explicit intent is authorized.

Blind retry loops are prohibited.

## Ambiguous acknowledgement

If the submit returns timeout/ambiguous acknowledgement, the correct response is:

```text
SUBMITTING
→ ACCEPTED_UNKNOWN
→ block new entries
→ reconcile broker positions/orders/deals
```

Do not automatically resubmit.

## Reconciliation

Reconciliation may use:

- positions;
- pending orders;
- deals/history;
- symbol/direction/volume;
- broker ticket/position IDs;
- magic/comment identifiers where available;
- execution-intent lineage and time window.

Only after reconciliation may an ambiguous lifecycle become verified/final.

## Ownership

Positions should be classified as at least:

```text
BOT_MANAGED
MANUAL
FOREIGN_EA
UNKNOWN_OWNER
```

Magic number alone is not sufficient ownership proof. Managed lineage should use persisted execution/trade identities plus broker facts.

Manual/foreign positions must never be modified as if bot-owned. V1 may conservatively block new Gold entries when unexpected exposure exists; final policy remains open.

## Position capacity

If V1 freezes one independently risk-bearing Gold position at a time, new independent entries are blocked with `POSITION_CAPACITY_FULL` while analysis/research continues.

## Modification and close safety

SL/TP modification and close requests are also irreversible broker writes. They require:

- account/position ownership verification;
- broker-valid geometry/volume;
- appropriate fresh market facts;
- no blind retry after ambiguous result;
- reconciliation before another write when outcome is uncertain.

## Filling mode

Supported filling mode must be discovered/validated before submission. The system must not try a sequence of alternative irreversible requests after failure in a way that could duplicate exposure.

## `order_check`

Broker pre-check may be used before submission. A successful `order_check` is not proof of execution. Durable intent must exist before the actual irreversible send.

## Failure classes

The execution layer should distinguish:

```text
PRE_SUBMIT_BLOCK
BROKER_REJECTED
AMBIGUOUS_ACK
ACCEPTED_VERIFIED
RECONCILIATION_FAILED
```

Reason codes must preserve operational meaning.

## Execution states

Suggested subsystem states:

```text
READY
DEGRADED
RECONCILING
BLOCKED
```

`RECONCILING` blocks new entries while uncertain broker writes are resolved.

## Single active execution controller

For one managed account/symbol, only one bot instance may hold active broker-write authority at a time.

Other instances may run as Observer/Research/Shadow but must not submit/modify/close broker positions.

A future execution-lease/controller mechanism must ensure failover performs broker/state reconciliation before a replacement instance becomes READY.

Reason code example: `ANOTHER_ACTIVE_CONTROLLER`.

## Broker truth

Broker positions/deals own actual exposure/P&L truth. Local state owns intent, strategy context and lifecycle history. Conflict requires reconciliation, not silent deletion or duplication.

## Market closure/reopen

No write attempts should be spammed when broker tradeability/quotes show XAU unavailable. After reopen, fresh quotes/specs/data and safety readiness must be re-established before execution.

## Outputs and diagnostics

The desk should expose:

- account/symbol verification;
- quote freshness;
- spread/price-drift state;
- volume/margin/stop validation;
- execution lifecycle state;
- ownership/capacity state;
- primary/secondary blocker reason codes;
- reconciliation status;
- controller/observer role.

## Tests required

- account switch/mismatch blocks writes;
- DEMO/real policy;
- symbol-spec validation/change;
- stale quote and drift rejection;
- stop/volume/margin checks;
- exactly-one send per intent;
- ambiguous acknowledgement reconciliation;
- crash after send without duplicate;
- modify/close ambiguity reconciliation;
- manual/foreign ownership protection;
- multi-instance controller/failover tests.

## Explicit non-goals

Execution must not:

- decide strategy direction;
- resize risk on its own;
- redesign structural SL/targets;
- blind-retry ambiguous writes;
- assume unknown broker exposure is zero;
- let multiple laptops independently write the same managed account/symbol.

## Open questions

- exact DEMO-to-real future release policy;
- exact price-drift/spread limits;
- final V1 unexpected-manual-position policy;
- final one-position policy confirmation;
- exact execution-lease implementation and timeout/failover mechanics.