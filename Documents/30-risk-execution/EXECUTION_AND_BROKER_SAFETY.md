# GoldSwingTraderAI — Execution and Broker Safety

**Status:** PROVISIONAL
**Version:** 0.1-execution
**Authority:** DEMO Guard, final permission, one-shot broker actions, controller and reconciliation

## Purpose

This is the last safety boundary before irreversible MT5 create, modify or
close operations.

## The only broker-write path

~~~mermaid
flowchart TB
    ACTION["Approved TradePlan or management action"] --> AUTHORITIES["DEMO, identity, data, risk, session/news, position and controller"]
    AUTHORITIES --> GATE{"Central gate ALLOW?"}
    GATE -->|"no or unknown"| BLOCK["Persist reason; no broker call"]
    GATE -->|"yes"| INTENT["Persist APPROVED Intent"]
    INTENT --> PRE["Fresh quote/spec/volume/margin/epoch check"]
    PRE --> SUB["Persist SUBMITTING and consume send allowance"]
    SUB --> WRITE["One MT5 order_send in mt5_writer.py"]
    WRITE --> ACK{"Acknowledgement"}
    ACK -->|"verified"| RECON["Reconcile broker truth"]
    ACK -->|"ambiguous"| WAIT["Reconciliation-only state; never blind retry"]
    ACK -->|"rejected"| FAIL["FAILED with broker reason"]
    RECON --> STORE["Persist verified lifecycle"]
    WAIT --> STORE
~~~

Only execution/mt5_writer.py reaches raw order_send. Strategy, dashboard,
research, management and recovery code use typed requests.

## Positive DEMO Guard

~~~text
AccountFacts.account_mode is positively DEMO
→ DEMO_GUARD = PASS
→ required gate input passes
~~~

If the account mode is unknown, REAL, mismatched or unavailable, writes are
not allowed. There is no switch that disables this rule and no alternate V1
REAL workflow.

## Gate inputs

Every create/modify/close action evaluates the applicable:

- DEMO Guard and account identity;
- symbol and quote freshness;
- spread, drift, stop and volume geometry;
- risk and capacity;
- session/news permission;
- Intent/order lifecycle;
- controller holder, unexpired lease and fencing epoch;
- action-specific ownership and reconciliation state.

BLOCK and UNKNOWN both prevent the write.

## Spread and drift baseline

~~~text
SpreadRatio ≤ 1.50       normal
1.50 < ratio ≤ 2.25      elevated; full revalidation
ratio > 2.25             block current entry
spread > 25% of SL       block current entry

Adverse drift ≤ 10%       normal revalidation
10% < drift ≤ 20%         elevated; full revalidation
drift > 20%               block/rebuild current intent
~~~

Fresh structural, target, risk or chase failure blocks regardless of ratio.

## Intent lifecycle

~~~text
CREATED → APPROVED → SUBMITTING
SUBMITTING → ACCEPTED_VERIFIED
SUBMITTING → ACCEPTED_UNKNOWN
SUBMITTING → FAILED
~~~

One Intent ID permits at most one irreversible send. Persisting SUBMITTING
consumes the allowance before the broker call. A later attempt after absence is
proven must use a fresh governed Intent ID.

## Reconciliation

Create checks positions/orders/deals and lineage. Modify checks actual ticket
SL/TP. Close checks position reduction/absence and deal/history evidence where
needed. Magic/comment help identify a request but do not replace broker truth.

## Controller and fencing

V1 has one PRIMARY per account/symbol, renewal target 10 seconds, lease TTL 30
seconds and monotonic fencing epoch. InMemoryCoordinationStore is for
deterministic tests. SQLiteCoordinationStore uses transactional acquisition
and a durable epoch ledger. shared_locking_verified=false remains the safe
default for unproven filesystems.

Takeover:

~~~text
old lease expires
→ standby obtains higher epoch
→ TAKEOVER_RECONCILIATION_REQUIRED
→ restore/check state and current broker truth
→ reconcile Intents and ManagedTrade
→ all RecoveryAuthorities pass
→ verify same holder and epoch
→ PRIMARY READY
~~~

A new epoch alone is not write permission.

## Startup recovery

app/recovery.py performs no broker write. APPROVED-but-never-SUBMITTING may be
cancelled safely; CREATED needs review; SUBMITTING/ACCEPTED_UNKNOWN reconcile;
verified broker OPEN without ManagedTrade remains RECONCILING.

## Source and tests

| Source | Role | Tests |
|---|---|---|
| execution/gate.py | central hard permission | test_execution_safety.py |
| execution/service.py | Intent and governed action | test_execution_safety.py |
| execution/mt5_writer.py | raw write boundary | test_execution_safety.py |
| execution/reconcile.py | broker outcome verification | test_execution_safety.py, test_recovery_mt5.py |
| execution/controller.py | lease/fencing | test_sqlite_coordination.py |
| execution/sqlite_coordination.py | durable coordination | test_sqlite_coordination.py |
| app/recovery.py | startup/takeover sequencing | test_startup_recovery.py, test_live_startup_runtime.py |

## Dashboard and release boundary

Show DEMO Guard, account/symbol, spread/drift, Intent ID/state, send count,
reconciliation, controller ID/epoch and blocker. Deterministic tests prove
software safety; real DEMO OPEN/MODIFY/CLOSE/restart/failover evidence remains
pending until performed.

## Explicit non-goals

Execution does not decide strategy, increase risk, redesign structural plans,
blind-retry, modify foreign positions, authorize multiple controllers or
assume a new epoch means recovery is complete.

