# GoldSwingTraderAI — Execution and Broker Safety

**Status:** PROVISIONAL  
**Version:** 0.4-design  
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
→ Central Execution Permission Gate
→ Persist intent
→ Broker pre-check
→ ONE governed order_send
→ Classify result
→ Verify / reconcile
```

No market score can bypass this path.

## Centralized broker-write permission gate

All final permission to create, modify or close a bot-managed broker position must pass through **one centralized execution-permission boundary**.

Individual facts/policies remain owned by their proper subsystems. Final irreversible-write permission is collected in one place rather than scattered across strategies, dashboard code or random MT5 call sites.

```text
Account / environment policy  ─┐
Market + quote integrity       ├─→ EXECUTION PERMISSION GATE
News/session permission        ┤          │
Risk permission                ┤          ├─ ALLOW
Position/capacity state        ┤          ├─ BLOCK
Order/reconciliation state     ┤          └─ UNKNOWN → BLOCK
Controller ownership           ┘
```

The gate exposes final `ALLOW/BLOCK/UNKNOWN`, primary/secondary blockers, authority trace, `Would Otherwise Trade` where meaningful, and environment authorization.

### Centralization invariant

There must not be multiple independent pieces of code that can directly decide to call `order_send`, modify a stop or close a position. All broker writes route through this governed boundary.

DEMO/REAL policy is also resolved here rather than through scattered `if demo` checks.

## Account identity pinning

At startup verify/pin intended broker identity facts such as login/account identifier, server, account mode/type, currency and trade permissions.

Every irreversible write verifies that the currently connected account still matches intended identity. Runtime mismatch produces `ACCOUNT_IDENTITY_MISMATCH` and blocks writes until resolved.

## DEMO-first policy

Initial release authorizes verified DEMO execution. A real account connection does not silently gain write authority unless a later explicit frozen release policy allows it.

This is a release safeguard, not a permanent architectural prohibition. Future approved REAL uses the same permission gate and ordinary safety checks.

## Symbol resolution and broker specs

Resolve intended Gold instrument and verify at least symbol existence/visibility, trade mode, digits/point/tick size, tick value/contract size, min/max/step volume, stops/freeze levels and supported filling modes.

Material broker-spec changes require revalidation before new writes.

## Fresh executable quote

Immediately before a market order verify fresh Bid/Ask and correct executable side:

- BUY uses Ask-side execution context;
- SELL uses Bid-side execution context.

Stale/unknown quote blocks submission without automatically invalidating the underlying opportunity.

## Dynamic spread policy — V1 frozen initial rule

Spread protection must be **dynamic**, not one hard-coded dollar/point number, because Gold spread differs by broker, session and market state.

Maintain a `HealthySpreadBaseline` for the verified broker/symbol using recent fresh quote observations collected only from healthy/open conditions. News blackout spikes, reopen dislocation, stale quotes and known abnormal periods must not contaminate the baseline.

A persisted recent healthy baseline may bootstrap restart/reopen; otherwise the system remains in warmup until enough valid observations exist. Exact sampling window/count is an implementation detail, but baseline quality must be testable and visible.

Define:

```text
SpreadRatio = CurrentExecutableSpread / HealthySpreadBaseline
```

Initial V1 classes:

```text
SpreadRatio <= 1.50
→ NORMAL

>1.50 and <=2.25
→ ELEVATED
→ not an automatic block
→ full risk/target-room/entry revalidation required

>2.25
→ BLOCK current entry
→ SPREAD_TOO_HIGH
```

Independent geometry guard:

```text
Current spread > 25% of approved entry-to-structural-SL price distance
→ BLOCK current entry
```

This prevents an unusually tight setup from paying excessive friction even when a rolling baseline is itself elevated.

An ELEVATED spread may still execute only if:

- all-in monetary risk remains within the active Risk Contract band/ceiling;
- structural SL remains valid;
- target room/RR remains acceptable under the Trade Plan;
- quote freshness and other execution checks pass.

If spread blocks the current entry, the opportunity may remain `ARMED/WAIT` rather than being invalidated.

Reason codes:

```text
SPREAD_ELEVATED
SPREAD_TOO_HIGH
SPREAD_CONTEXT_UNKNOWN
```

A quoted spread such as `$0.26` is treated as price distance and converted through broker symbol facts where monetary effect is required.

## Price drift and fresh-plan revalidation — V1 frozen initial rule

Price drift is measured from the `ApprovedEntryReference` to the fresh executable quote on the correct side immediately before send.

Use the approved original entry-to-structural-SL **price distance** as the normalization base.

For **adverse drift**:

```text
<= 10% of planned stop distance
→ NORMAL REVALIDATION
→ may execute if all checks still pass

>10% to <=20%
→ PRICE_DRIFT_ELEVATED
→ full Trade Plan + Risk + target-room + chase revalidation
→ may still execute if the plan remains genuinely valid

>20%
→ BLOCK current Execution Intent
→ PRICE_DRIFT
→ return opportunity to WAIT/rebuild from current market if thesis survives
```

This avoids both tiny-tick overblocking and uncontrolled chasing.

A favorable price move is not automatically rejected, but the system must recalculate structural geometry, risk and target room from the fresh executable quote before send.

Regardless of percentage band, block the current plan if fresh drift causes any of the following:

- actual all-in risk exceeds the profile hard ceiling;
- broker stop geometry becomes invalid;
- target room/RR becomes unacceptable under Trade Plan authority;
- Entry Timing classifies the fresh quote as chased/severely extended;
- structural thesis/invalidation changes materially.

Execution does not silently move the structural SL to compensate for drift.

## Stop/TP geometry

Broker-normalized SL/TP must satisfy direction, tick/digit, minimum-stop and freeze constraints.

Harmless rounding is allowed. A broker constraint that materially changes structural intent makes the plan unexecutable rather than silently moving stop/target.

## Volume and margin

Execution revalidates Risk-approved volume against current broker specs and fresh margin/account state. It may block due to changed facts but must not improvise new volume/risk policy.

## Persist intent before send

Before irreversible submit, durable state contains at least:

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

For one approved Execution Intent ID, there is at most **one irreversible `order_send` attempt** until reconciliation proves the prior attempt did not create broker exposure and a fresh explicit intent is authorized.

Blind retry loops are prohibited.

## Ambiguous acknowledgement

If submit returns timeout/ambiguous acknowledgement:

```text
SUBMITTING
→ ACCEPTED_UNKNOWN
→ block new entries
→ reconcile broker positions/orders/deals
```

Do not automatically resubmit.

## Reconciliation

Reconciliation may use positions, pending orders, deals/history, symbol/direction/volume, broker ticket/position IDs, magic/comment identifiers where available, and execution-intent lineage/time window.

Only after reconciliation may an ambiguous lifecycle become verified/final.

## Ownership

Positions are classified as at least:

```text
BOT_MANAGED
MANUAL
FOREIGN_EA
UNKNOWN_OWNER
```

Magic number alone is not sufficient ownership proof. Manual/foreign/unknown positions are never modified as bot-owned.

## V1 Gold position-capacity policy

V1 allows **one independently risk-bearing Gold position at a time** on the managed account/symbol.

```text
No Gold exposure / capacity 0/1 → new bot entry may qualify
One BOT_MANAGED Gold position / capacity 1/1 → block second independent entry
Unexpected MANUAL / FOREIGN_EA / UNKNOWN_OWNER Gold exposure → block new bot entry
```

Opposite evidence routes first to Trade Manager. It does not authorize an automatic hedge/second position.

External Gold exposure is displayed, never managed as bot-owned, and new bot Gold entry remains blocked until exposure disappears and reconciliation passes.

## Modification and close safety

SL/TP modification and close requests are irreversible broker writes and require ownership verification, broker-valid geometry/volume, appropriate fresh facts, no blind retry after ambiguous result and reconciliation before another write when outcome is uncertain.

They pass through the same centralized permission boundary.

## Filling mode

Supported filling mode must be discovered/validated before submission. Do not try a sequence of alternative irreversible requests after failure in a way that could duplicate exposure.

## `order_check`

Broker pre-check may be used before submission. Successful `order_check` is not proof of execution. Durable intent must exist before actual send.

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

`RECONCILING` blocks new entries while uncertain broker writes are resolved.

## Single active execution controller

Only one bot instance may hold active broker-write authority for one managed account/symbol. Observer/Research/Shadow instances may not submit/modify/close positions.

Failover requires broker/state reconciliation before replacement becomes READY.

Reason code: `ANOTHER_ACTIVE_CONTROLLER`.

## Broker truth

Broker positions/deals own actual exposure/P&L truth. Local state owns intent, strategy context and lifecycle history. Conflict requires reconciliation, not silent deletion or duplication.

## Market closure/reopen

No write attempts should be spammed while XAU unavailable. After reopen, session warmup, fresh quotes/specs/data and safety readiness must pass before execution.

## Outputs and diagnostics

Expose at least:

- account/symbol verification;
- quote freshness;
- Current Spread, Healthy Spread Baseline and Spread Ratio;
- spread state `NORMAL/ELEVATED/BLOCKED/UNKNOWN`;
- approved entry reference, fresh executable quote and normalized Price Drift;
- volume/margin/stop validation;
- execution lifecycle state;
- ownership/capacity state;
- primary/secondary blockers;
- centralized permission trace;
- reconciliation status;
- controller/observer role.

## Tests required

- centralized gate is only route to irreversible broker writes;
- no strategy/risk/dashboard module can broker-write directly;
- DEMO/REAL environment policy resolved in one permission path;
- account switch/mismatch blocks writes;
- symbol-spec validation/change;
- stale quote rejection;
- healthy spread baseline excludes abnormal/news/reopen samples;
- spread ratio `<=1.5` NORMAL;
- spread ratio `>1.5–2.25` ELEVATED and revalidated rather than auto-blocked;
- spread ratio `>2.25` blocks with `SPREAD_TOO_HIGH`;
- spread >25% of structural stop distance blocks current entry;
- adverse drift `<=10%` can pass revalidation;
- adverse drift `>10–20%` is elevated and fully revalidated;
- adverse drift `>20%` blocks current intent without killing surviving opportunity;
- favorable drift still forces full geometry/risk/target recalculation;
- drift that breaks risk/target/chase/stop validity blocks regardless of percentage;
- stop/volume/margin checks;
- exactly-one send per intent;
- ambiguous acknowledgement reconciliation;
- crash after send without duplicate;
- modify/close ambiguity reconciliation;
- second independent Gold entry blocked at capacity 1/1;
- opposite opportunity cannot create automatic hedge;
- manual/foreign position never modified and blocks new bot Gold entry;
- unknown ownership fails closed;
- multi-instance controller/failover tests.

## Explicit non-goals

Execution must not:

- decide strategy direction;
- resize risk on its own;
- redesign structural SL/targets;
- use a single broker-independent hard-coded spread number as the sole spread rule;
- chase price beyond drift policy;
- blind-retry ambiguous writes;
- assume unknown broker exposure is zero;
- open a second independent Gold position/automatic hedge in V1;
- modify manual/foreign positions as bot-owned;
- let multiple laptops independently write same managed account/symbol;
- permit alternate broker-write paths around centralized gate.

## Open questions

- exact DEMO-to-real future release policy;
- exact healthy-spread sampling window/minimum-sample implementation;
- exact execution-lease implementation and timeout/failover mechanics;
- future research-backed changes to initial spread/drift bands.
