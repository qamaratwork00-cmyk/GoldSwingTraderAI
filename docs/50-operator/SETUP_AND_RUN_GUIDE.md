# GoldSwingTraderAI — Setup and Run Guide

**Status:** DRAFT  
**Version:** 0.1-design  
**Authority:** Operator workflow for installation, startup, safe shutdown, migration, restore and common blocked-state handling.  
**Depends on:** `DASHBOARD_AND_UX.md`, `../30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md`, `../30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md`

## Purpose

This guide describes the intended operator workflow without redefining strategy/risk behaviour. Exact commands and filenames remain DRAFT until the implementation/module structure exists.

## First-time setup

The intended high-level sequence is:

```text
install supported Python/runtime
→ install/open MetaTrader 5
→ install project dependencies
→ create local configuration from safe example
→ configure financial credentials locally
→ log into intended MT5 DEMO account
→ run startup verification
→ start bot
```

Do not document guessed shell commands as authoritative until the real package layout exists.

## Public repository policy

The repository may contain code, docs, tests, strategies, learning/research state/checkpoints and non-financial recovery metadata.

Never commit credentials/keys/tokens that can enable unauthorized financial action or direct paid-service cost, including:

- MT5 trading passwords/authentication secrets;
- broker/private session tokens;
- paid API secrets;
- GitHub PAT/access tokens;
- private/signing/encryption keys;
- cloud/database credentials with action/billing authority.

Real secrets belong in local environment/secret storage only.

## Normal startup

Conceptual startup:

```text
load/verify durable state
→ connect MT5
→ verify account/server/mode
→ resolve Gold symbol/specs
→ load/validate history
→ reconcile positions/orders/deals
→ restore risk/open-trade context
→ load Strategy Registry/learning
→ verify news/safety inputs
→ acquire runtime execution role
→ READY
```

Do not treat the bot as execution-ready until required startup checks pass.

## Runtime roles

### PRIMARY EXECUTOR

The single instance with governed broker-write authority for the managed account/symbol.

### OBSERVER

May analyze/display/research but has no broker-write authority.

### RESEARCH

Historical/replay/experimental use; no production broker writes.

If another active controller exists, this instance must not silently become an executor.

## What to do on WAIT

Nothing. `WAIT` is often normal operation.

Example:

```text
ENTRY_EXTENDED
Setup remains ARMED
```

Do not restart or change settings merely because the bot is waiting.

## What to do on expected BLOCKED states

Examples:

- `NEWS_BLACKOUT` — usually wait for safety to clear;
- `LOSS_LOCKED` — wait for risk-day reset or use the governed manual reset if deliberately allowed;
- `POSITION_CAPACITY_FULL` — existing managed position owns capacity.

Follow the reason/action shown by the dashboard.

## What to do on system BLOCKED

Examples such as `ACCOUNT_IDENTITY_MISMATCH`, `STATE_CORRUPT` or unresolved broker lifecycle require the action shown by System Health. Manual risk reset must not be used to bypass a technical/system block.

## Manual daily-loss reset

If/when implemented according to the frozen Risk Contract, reset uses deliberate confirmation (for example double-key `R,R`), creates an audit event and does not erase broker P/L history.

Exact keys/reset counts remain owned by the frozen risk/operator contract.

## Safe shutdown

Conceptual flow:

```text
stop new trade triggering
→ reconcile any in-flight broker write
→ persist risk/order/trade/learning state
→ flush journal/checkpoint as required
→ release execution-controller authority
→ exit
```

An open broker position is not automatically closed merely because the process is shutting down unless a future explicit holding policy requires it.

If shutdown occurs with unresolved order state, persist that uncertainty and require startup reconciliation before new entries.

## Laptop migration

Preferred flow:

```text
OLD MACHINE
safe shutdown
→ create/verify recovery checkpoint
→ ensure repository/state backup is current

NEW MACHINE
clone/install project
→ configure financial credentials separately
→ restore portable state/checkpoint
→ validate integrity/schema
→ connect intended MT5 account
→ broker reconciliation
→ rebuild market intelligence
→ acquire execution authority
→ READY
```

Strategy IDs, Champion/Challenger status, learning and research lineage should survive migration.

## Disaster recovery

If the old laptop is lost, recovery should require only:

- project repository/recovery state;
- required local financial credentials or secure credential source;
- access to the intended MT5 account/provider services.

After restore, broker truth must still be reconciled before new trading.

## Upgrade workflow

Conceptually:

```text
safe shutdown
→ verified backup/checkpoint
→ update code
→ validate state schema/migration
→ startup reconciliation
→ required tests/self-checks
→ resume
```

Do not replace live files casually while the bot is executing broker writes.

## Persistent state warning

Do not manually edit/delete critical state files to clear locks/errors. Use governed reset/recovery tools when implemented. Missing/corrupt critical state should fail safely rather than quietly becoming a fresh account state.

## Logs and diagnostics

Operator normally uses the dashboard. Structured logs/reports should support troubleshooting for:

- runtime/decision;
- trade/risk;
- execution/reconciliation;
- faults/recovery;
- research/learning.

Reason codes should match dashboard/journal terminology.

## Exact commands pending implementation

This guide remains DRAFT until actual package names, install commands, configuration paths, backup commands and launcher scripts are implemented and verified.