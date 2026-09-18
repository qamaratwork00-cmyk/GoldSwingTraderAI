# GoldSwingTraderAI — Execution and Broker Safety

**Status:** PROVISIONAL  
**Version:** 0.6-design  
**Authority:** MT5 account/symbol verification, execution readiness, broker request validation, one-shot irreversible submission, controller ownership and reconciliation.  
**Depends on:** `RISK_CONTRACT.md`, `SESSION_AND_RISK_STATE_MACHINE.md`, `../20-trading-decisions/TRADE_PLAN.md`, `../00-foundation/SYSTEM_CONTRACT.md`

## Purpose

This document owns the irreversible broker-write boundary.

> **Analysis may be wrong and lose a trade. Execution safety must not create duplicate, wrong-account, wrong-volume or uncontrolled exposure.**

## Governed execution path

```text
Approved Trade Plan
→ Risk PASS
→ Execution Readiness
→ Central Execution Permission Gate
→ Persist intent
→ Broker pre-check
→ ONE governed order_send
→ Classify result
→ Verify / reconcile
```

No market score can bypass this path.

## Centralized broker-write permission gate

All final permission to create, modify or close a bot-managed broker position passes through one centralized execution-permission boundary.

```text
Account / DEMO guard          ─┐
Market + quote integrity       ├─→ EXECUTION PERMISSION GATE
News/session permission        ┤          │
Risk permission                ┤          ├─ ALLOW
Position/capacity state        ┤          ├─ BLOCK
Order/reconciliation state     ┤          └─ UNKNOWN → BLOCK
Controller ownership           ┘
```

The gate exposes `ALLOW/BLOCK/UNKNOWN`, primary/secondary reasons, authority trace and `Would Otherwise Trade` where meaningful.

### Centralization invariant

There must not be multiple independent pieces of code that can directly decide to call `order_send`, modify a stop or close a position. All broker writes route through this governed boundary.

## Account identity pinning

At startup verify/pin intended broker identity facts such as login/account identifier, server, account mode/type, currency and trade permissions.

Every irreversible write verifies that the currently connected account still matches intended identity. Runtime mismatch produces `ACCOUNT_IDENTITY_MISMATCH` and prevents write permission until resolved.

## DEMO guard — V1 frozen policy

V1 uses one positive environment guard:

```text
Verified connected MT5 account is DEMO
→ DEMO_GUARD = PASS
→ broker writes may proceed if every other authority also passes

DEMO status not verified
→ DEMO_GUARD does not PASS
→ broker-write permission is not granted
```

A verified DEMO account is not dry-run simulation. When the DEMO guard and all ordinary strategy/risk/session/execution/controller checks pass, GoldSwingTraderAI may place, modify and close real-time orders on that DEMO account.

V1 defines **only the DEMO guard**. It does not define a separate REAL-account authorization policy, REAL hard-block policy, LIVE override or alternate REAL execution path. Any future non-DEMO execution design is outside this V1 contract and must not be inferred from it.

Suggested visibility:

```text
Account Mode     DEMO
DEMO Guard       PASS
Execution        ALLOW / BLOCK / UNKNOWN
```

Reason code: `DEMO_GUARD_NOT_VERIFIED` when DEMO status cannot be positively established.

## Symbol resolution and broker specs

Resolve intended Gold instrument and verify at least:

- symbol existence/visibility and trade mode;
- digits/point/tick size;
- tick value/contract size;
- min/max/step volume;
- stops/freeze levels;
- supported filling modes.

Material broker-spec changes require revalidation before new writes.

## Fresh executable quote

Immediately before a market order verify fresh Bid/Ask and correct executable side:

- BUY uses Ask-side execution context;
- SELL uses Bid-side execution context.

Stale/unknown quote prevents submission without automatically invalidating the underlying opportunity.

## Dynamic spread policy — V1 frozen initial rule

Maintain `HealthySpreadBaseline` from recent fresh quote observations collected only during healthy/open conditions. News spikes, reopen dislocation, stale quotes and known abnormal periods must not contaminate the baseline.

```text
SpreadRatio = CurrentExecutableSpread / HealthySpreadBaseline

<= 1.50          → NORMAL
>1.50 to <=2.25  → ELEVATED; full revalidation, not automatic rejection
>2.25            → current entry blocked with SPREAD_TOO_HIGH
```

Independent geometry guard:

```text
Current spread > 25% of approved entry-to-structural-SL price distance
→ current entry blocked
```

An ELEVATED spread may still execute only if all-in monetary risk, structural SL, target room/RR, quote freshness and all other execution checks pass.

If spread prevents the current entry, the opportunity may remain `ARMED/WAIT` rather than becoming invalid.

Reason codes include `SPREAD_ELEVATED`, `SPREAD_TOO_HIGH`, `SPREAD_CONTEXT_UNKNOWN`.

## Price drift and fresh-plan revalidation — V1 frozen initial rule

Measure adverse drift from `ApprovedEntryReference` to fresh executable quote, normalized by approved original entry-to-structural-SL price distance.

```text
<=10%             → normal revalidation
>10% to <=20%     → PRICE_DRIFT_ELEVATED + full plan/risk/target/chase revalidation
>20%              → current Execution Intent blocked; return to WAIT/rebuild if thesis survives
```

Favorable drift is not automatically rejected, but geometry, risk and target room are recalculated from the fresh quote.

Regardless of ratio, prevent the current write if fresh drift breaks risk ceiling, broker stop geometry, target-room/RR, chase validity or structural thesis. Execution never moves structural SL merely to compensate for drift.

## Stop/TP geometry

Broker-normalized SL/TP must satisfy direction, tick/digit, minimum-stop and freeze constraints. Harmless rounding is allowed. A broker constraint that materially changes structural intent makes the plan unexecutable rather than silently redesigning it.

## Volume and margin

Execution revalidates Risk-approved volume against current broker specs and fresh margin/account state. It may reject changed facts but does not improvise new risk policy.

## Persist intent before send

Before irreversible submit, durable state contains at least:

- Execution Intent ID;
- Decision/Opportunity/Episode IDs;
- strategy/policy version;
- direction and volume;
- approved entry reference;
- SL/TP/objectives as applicable;
- account identity;
- risk snapshot;
- timestamp;
- lifecycle state such as `SUBMITTING`;
- current controller lease identity/fencing epoch.

## Order lifecycle

```text
CREATED
APPROVED
SUBMITTING
├─ ACCEPTED_VERIFIED
├─ ACCEPTED_UNKNOWN
└─ FAILED
```

## One-shot submission invariant

For one approved Execution Intent ID, there is at most one irreversible `order_send` attempt until reconciliation proves the prior attempt did not create broker exposure and a fresh explicit intent is authorized.

Blind retry loops are prohibited.

## Ambiguous acknowledgement

```text
SUBMITTING
→ ACCEPTED_UNKNOWN
→ prevent new entries
→ reconcile broker positions/orders/deals
```

Do not automatically resubmit.

## Reconciliation

Use positions, pending orders, deals/history, symbol/direction/volume, broker ticket/position IDs, magic/comment identifiers where available, execution-intent lineage and time window.

Only after reconciliation may ambiguous lifecycle become verified/final.

## Ownership

Positions are classified at least:

```text
BOT_MANAGED
MANUAL
FOREIGN_EA
UNKNOWN_OWNER
```

Magic number alone is not sufficient ownership proof. Manual/foreign/unknown positions are never modified as bot-owned.

## V1 Gold position capacity

V1 allows one independently risk-bearing Gold position at a time.

```text
No Gold exposure / capacity 0/1 → new bot entry may qualify
One BOT_MANAGED Gold position / capacity 1/1 → second independent entry prevented
MANUAL / FOREIGN_EA / UNKNOWN_OWNER Gold exposure → new bot Gold entry prevented
```

Opposite evidence routes first to Trade Manager; it does not authorize an automatic hedge/second position.

## Modification and close safety

SL/TP modification and close requests are also irreversible broker writes. They require ownership verification, broker-valid geometry/volume, fresh facts, no blind retry after ambiguity, controller verification and reconciliation before another write when outcome is uncertain.

## Filling mode and order_check

Supported filling mode must be discovered/validated before submission. Do not try a sequence of alternative irreversible requests after failure in a way that could duplicate exposure.

`order_check` may be used before submission; successful `order_check` is not proof of execution. Durable intent must exist before actual send.

## Failure classes

```text
PRE_SUBMIT_BLOCK
BROKER_REJECTED
AMBIGUOUS_ACK
ACCEPTED_VERIFIED
RECONCILIATION_FAILED
```

## Execution states

```text
READY
DEGRADED
RECONCILING
BLOCKED
```

`RECONCILING` prevents new entries while uncertain broker writes are resolved.

## Single active execution controller — V1 frozen policy

V1 uses a shared controller lease with fencing so two laptops/processes cannot both believe they are PRIMARY for the same managed account/symbol.

Every runtime has unique `ControllerInstanceID`. Shared coordination maintains:

```text
Managed Account Identity
Managed Gold Symbol Scope
Lease Holder Instance ID
Monotonic Lease/Fencing Epoch
Lease Expiry
Last Successful Renewal
```

### Coordination-store requirements

The backend must support atomic acquire/compare-and-set or equivalent ownership, one winner under contention, monotonic fencing epoch, authoritative/server-side time semantics and durable enough state to survive one process/laptop failure.

A plain local-only file lock is not sufficient for cross-laptop protection.

### Initial lease timing

```text
Heartbeat / renewal target   10 seconds
Lease TTL                    30 seconds
```

### Fresh ownership for every broker write

Immediately before every create/modify/close request verify:

- this instance is current holder;
- lease is unexpired;
- fencing epoch matches current coordination-store epoch;
- coordination truth is reachable/verified.

Unknown ownership or coordination failure prevents broker writes with `CONTROLLER_OWNERSHIP_UNKNOWN` / `CONTROLLER_COORDINATION_UNAVAILABLE`. Analysis/dashboard/research may continue read-only.

### Second laptop

If another valid lease holder exists, second laptop remains `OBSERVER` for broker writes. Reason: `ANOTHER_ACTIVE_CONTROLLER`.

### Planned handoff

```text
OLD PRIMARY
stop new intents
→ reconcile in-flight writes
→ persist/flush state
→ release lease

NEW MACHINE
load/validate state
→ acquire new epoch atomically
→ broker reconciliation
→ account/symbol/risk/session revalidation
→ PRIMARY READY
```

### Crash / standby failover

A configured `STANDBY` may attempt takeover only after prior lease expiry in coordination-store truth.

```text
expired/no valid lease
→ atomically acquire NEW fencing epoch
→ RECOVERING/RECONCILING
→ validate durable state
→ reconcile broker positions/orders/deals and ambiguous intents
→ verify account/symbol/risk/session/execution
→ PRIMARY READY
```

Lease ownership alone is not enough to trade. Stale old epochs can never broker-write after takeover.

## Broker truth

Broker positions/deals own actual exposure/P&L truth. Local state owns intent, strategy context and lifecycle history. Conflict requires reconciliation, not silent deletion or duplication.

## Market closure/reopen

No write attempts are spammed while XAU unavailable. After reopen, session warmup, fresh quotes/specs/data and safety readiness must pass before execution.

## Outputs and diagnostics

Expose at least account/symbol verification, Account Mode, DEMO Guard, quote freshness, current/baseline spread and ratio, drift, volume/margin/stop validation, lifecycle, ownership/capacity, permission trace, reconciliation and controller role/epoch/lease health.

## Tests required

- centralized gate is only route to irreversible broker writes;
- verified DEMO account can receive broker-write authority when all other permissions pass;
- DEMO status not verified means DEMO guard does not pass;
- no separate REAL authorization/override path exists in V1;
- account switch/mismatch prevents writes;
- symbol-spec/stale-quote checks;
- spread baseline excludes abnormal/news/reopen samples;
- spread ratio/geometry guards;
- price-drift bands and full revalidation;
- stop/volume/margin validation;
- exactly-one send per intent;
- ambiguous acknowledgement reconciliation;
- crash-after-send without duplicate;
- modify/close ambiguity reconciliation;
- position-capacity and external-ownership checks;
- simultaneous controller acquire yields one PRIMARY;
- second laptop stays OBSERVER while another valid lease exists;
- stale fencing epoch cannot write;
- coordination outage prevents writes;
- takeover reconciles before READY;
- planned handoff creates no duplicate exposure.

## Explicit non-goals

Execution must not:

- decide strategy direction or resize risk;
- redesign structural SL/targets;
- use a single hard-coded Gold spread number as sole spread rule;
- chase beyond drift policy;
- blind-retry ambiguous writes;
- assume unknown exposure is zero;
- open an automatic hedge/second independent Gold position in V1;
- modify manual/foreign positions as bot-owned;
- let multiple laptops independently write the same managed account/symbol;
- treat a local-only lock as sufficient cross-laptop ownership;
- continue writes on an unverified/stale controller lease;
- provide a hidden non-DEMO authorization path;
- permit alternate broker-write paths around the centralized gate.

## Open questions

- exact healthy-spread sampling window/minimum-sample implementation;
- final shared coordination-store backend/library satisfying frozen lease/fencing contract;
- exact broker comment/magic/lineage conventions;
- exact retry policy for safe read-only/pre-submit operations;
- future research-backed changes to initial spread/drift bands or lease timing.
