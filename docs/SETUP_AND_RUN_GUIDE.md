# GoldSwingTraderAI — Setup and Run Guide

**Status:** DRAFT  
**Version:** 0.4-design  
**Authority:** Operator workflow for installation, startup, safe shutdown, migration, restore and common blocked-state handling.  
**Depends on:** `50-operator/DASHBOARD_AND_UX.md`, `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md`, `30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md`

## Purpose

This guide describes the intended operator workflow. Exact shell commands, package names and launcher paths stay DRAFT until implementation exists.

## First-time setup

High-level sequence:

```text
install supported Python/runtime
→ install/open MetaTrader 5
→ install project dependencies
→ create local config from safe example
→ configure financial credentials locally
→ connect intended MT5 DEMO account
→ run startup verification
→ start bot
```

Financial-authority credentials must never be placed in the public repository.

## V1 environment rule

V1 uses a positive DEMO guard only:

```text
Connected MT5 account verified DEMO
→ DEMO_GUARD PASS
```

Broker writes require this guard plus all ordinary account/data/session/news/risk/controller/execution checks.

If DEMO status is not verified, broker-write permission is not granted. V1 does not define a separate REAL authorization workflow.

## Normal startup

Conceptual startup:

```text
load + validate durable state
→ connect MT5
→ verify account/server/DEMO status
→ resolve Gold symbol/specs
→ load/validate H4/H1/M15/M5 history
→ reconcile positions/orders/deals
→ restore risk/open-trade/opportunity state
→ load Strategy Registry + learning
→ verify news/session inputs
→ acquire controller lease/epoch
→ rebuild/revalidate market intelligence
→ evaluate centralized Execution Permission Gate
→ READY
```

Do not treat the bot as ready for broker writes merely because MT5 connected.

Typical ready state:

```text
Environment       DEMO VERIFIED
DEMO Guard        PASS
Controller        PRIMARY
Broker Reconcile  COMPLETE
Execution Gate    ALLOW
```

## Runtime roles

### PRIMARY

Single instance with governed broker-write authority for the managed account/symbol.

### STANDBY

May analyze and wait for controller lease expiry. It cannot write while another valid PRIMARY exists. After takeover it must reconcile before becoming PRIMARY READY.

### OBSERVER

Analysis/dashboard only; no broker writes.

### RESEARCH

Historical/replay/experimental use; no production broker writes.

### RECOVERING / RECONCILING

Runtime is restoring/reconciling state and is not yet broker-write ready.

## What to do on WAIT

Normally nothing.

Example:

```text
ENTRY_EXTENDED
Setup remains ARMED
```

Do not restart or alter settings simply because the bot is waiting for better timing.

## Expected policy blocks

Examples:

- `NEWS_BLACKOUT` — wait for event safety/normalization;
- `SESSION_PRE_CLOSE` — scheduled XAU closure approaching;
- `LOSS_LOCKED` — daily safety budget exhausted;
- `POSITION_CAPACITY_FULL` — one bot-managed Gold risk position already exists;
- `EXTERNAL_GOLD_EXPOSURE` — manual/foreign/unknown Gold exposure exists;
- `SPREAD_TOO_HIGH` / `PRICE_DRIFT` — current entry execution degraded;
- `ANOTHER_ACTIVE_CONTROLLER` — another instance owns the controller lease;
- `DEMO_GUARD_NOT_VERIFIED` or equivalent — positive DEMO verification is unavailable.

Follow the dashboard reason/action. Do not bypass the centralized Execution Permission Gate.

## System blocks

Examples such as `ACCOUNT_IDENTITY_MISMATCH`, unresolved broker acknowledgement, state corruption, controller coordination failure or required data/news truth failure require reconciliation/recovery rather than manual trade forcing.

Manual loss reset cannot clear unrelated technical/system blocks.

## Manual daily-loss reset

The feature is OFF by default.

If explicitly enabled by configuration, reset is only available from `LOSS_LOCKED`, requires deliberate `R,R` confirmation, is limited to one per UTC risk day and creates a durable audit event/new cycle reference without erasing cumulative day P/L.

Exact keyboard timing is an operator-UX implementation detail.

## Scheduled closure behaviour

V1 does not intentionally carry bot-managed Gold through scheduled XAU closure/reopen gap risk.

```text
Daily break:
T-20m stop new entries
T-10m mandatory governed flatten

Weekend:
T-60m stop new entries
T-30m mandatory governed flatten
```

Timing comes from the verified broker Gold session schedule rather than a hard-coded local clock.

After reopen:

```text
Daily   → normalized conditions + at least 1 clean completed M5
Weekend → gap assessment + normalized conditions + at least 2 clean completed M5
```

If flatten acknowledgement is ambiguous, preserve the unresolved position state and reconcile it. Do not pretend the trade is closed.

## Safe shutdown

Conceptual flow:

```text
stop new entry triggering
→ reconcile any in-flight broker write
→ persist risk/order/trade/opportunity/learning state
→ create/verify checkpoint as configured
→ release controller lease safely
→ exit
```

A manual process shutdown is not itself a reason to fake-close or erase an open position. Scheduled PRE_CLOSE rules remain independently authoritative.

## Planned laptop migration

```text
OLD PRIMARY
stop new intents
→ reconcile in-flight writes
→ safe shutdown
→ verify recovery checkpoint/backup
→ release controller lease

NEW MACHINE
clone/install project
→ configure financial credentials separately
→ restore portable state
→ validate schema/integrity
→ connect intended MT5 DEMO account
→ acquire new controller epoch
→ broker reconciliation
→ rebuild market intelligence
→ validate risk/news/session state
→ startup self-checks
→ PRIMARY READY
```

Strategy IDs, learning, Champion/Challenger history and research lineage must survive migration.

## Disaster recovery after laptop loss

Recovery requires:

- repository + portable recovery state/checkpoint;
- financial credentials supplied separately;
- access to intended MT5 DEMO account/provider services.

Then:

```text
restore code/state
→ validate integrity/schema
→ connect MT5
→ acquire controller ownership
→ reconcile broker truth
→ rebuild market intelligence
→ verify risk/session/news/execution state
→ resume only when READY
```

Never replay a stale backup assumption that a position is open or closed without checking the broker.

## Upgrade workflow

```text
safe shutdown
→ verified checkpoint
→ update code
→ validate schema/migration compatibility
→ startup reconciliation
→ required tests/self-checks
→ execution permission verification
→ resume
```

Do not casually replace files while the bot is performing irreversible writes.

## Public backup / secret rule

Public backup may contain code, docs, strategies, learned parameters, research/promotion history and portable recovery intelligence.

Never commit authority-bearing credentials/keys/tokens such as MT5 trading secrets, private broker/session tokens, paid API keys, GitHub PATs, private/signing keys or paid cloud/database credentials.

A financial-secret scanner should block unsafe publication. If a financial credential was committed publicly, rotate/revoke it; deletion from Git history alone is not enough.

## Persistent-state warning

Do not manually edit/delete critical risk/order/trade/controller state to clear a lock. Missing/corrupt critical state should fail safely and trigger restore/reconciliation.

## Logs and diagnostics

Structured logs/reports should support:

- market/decision trace;
- trade/risk lifecycle;
- execution permission and controller state;
- broker reconciliation;
- faults/recovery;
- research/learning;
- backup/integrity.

Reason codes should match the dashboard and journal.

## Exact commands pending implementation

This guide remains DRAFT until the real package layout, install command, configuration paths, launcher scripts, backup/export commands and operator keys exist and have been tested.
