# GoldSwingTraderAI — Persistence, Restart and Recovery

**Status:** PROVISIONAL — IMPLEMENTED FOUNDATION + LOCAL BACKUP + LIVE-READ RECOVERY  
**Version:** 0.7-implementation  
**Authority:** Durable lifecycle state, crash recovery, startup reconciliation, portable runtime checkpoints, automatic local backup cadence/retention, machine migration and backup/restore integrity.  
**Depends on:** `EXECUTION_AND_BROKER_SAFETY.md`, `RISK_CONTRACT.md`, `../10-market-intelligence/MARKET_DATA_AND_HISTORY.md`, `../20-trading-decisions/TRADE_PLAN.md`, `../40-research-learning/LEARNING_AND_AI_BOUNDARIES.md`

## Purpose

The bot must survive process restart, laptop loss/change and controlled migration without forgetting active obligations, strategy lineage or learning history.

> **Restart is not a fresh trading day unless actual rules say so. Restored state is context, never broker truth. Unknown broker exposure is never zero exposure.**

## Current owners

```text
persistence/store.py
persistence/runtime_state.py
persistence/checkpoint.py
persistence/backup.py
app/recovery.py
app/recovery_mt5.py
market_data/mt5_reader.py
security/financial_secrets.py
```

## Durable StateStore

Standard-library SQLite stores canonical current records + append-only events with checksums, schema versions, WAL, `synchronous=FULL`, transactional writes and integrity verification. Corruption fails closed.

`RuntimeStateRepository` validates risk/cooldown/Episode/Opportunity/TradePlan lineage. Execution Intent and Managed Trade repositories use the same StateStore.

## Portable checkpoint + local backup

Portable checkpoint:

```text
checkpoint_manifest.json
records.jsonl
events.jsonl
```

It is write-new, content-hashed, secret-scanned and restored only into a NEW DB. Restore explicitly requires broker reconciliation.

Local rolling backup:

```text
backup_catalog.json
checkpoints/runtime-YYYYMMDDTHHMMSSZ-<sha12>/...
```

Initial configurable baseline is 15-minute cadence / keep 96. New state is staged + verified before catalog replacement and retention prune. Failed backup preserves previous known-good state.

## Governed startup recovery

`app/recovery.py` owns the fail-closed READY sequence:

```text
StateStore integrity
→ typed runtime bundle
→ current ExecutionIntent
→ current ManagedTrade
→ current DEMO/account/server/symbol truth
→ unresolved Intent reconciliation
→ ManagedTrade vs current broker position
→ all hard RecoveryAuthorities PASS
→ fresh controller holder/epoch verification
→ takeover completion only now
→ READY
```

It performs no broker write.

### Intent semantics

- terminal/none: lifecycle may continue;
- APPROVED pre-submit: may be safely cancelled to FAILED with zero sends;
- CREATED: explicit review/reconciliation;
- SUBMITTING / ACCEPTED_UNKNOWN: existing broker reconciler, never blind resend;
- VERIFIED OPEN without ManagedTrade context: RECONCILING.

### Managed Trade semantics

Restored ManagedTrade must match exactly one current broker position by ticket/symbol/direction/volume. Current SL/TP must match within an explicit broker-derived price tolerance. Missing/mismatched state prevents READY.

## Live MT5 recovery truth — implemented deterministic foundation

`app/recovery_mt5.py` now builds the current recovery snapshot through the **existing `MT5Reader` only**:

```text
MT5Reader.account_facts()
→ resolve_symbol()
→ symbol_spec()
→ open_positions()
→ MT5RecoveryTruth
```

`MT5RecoveryTruth` contains:

- `BrokerRecoverySnapshot` with current account, resolved symbol and normalized open positions;
- verified `SymbolSpec`;
- `price_tolerance = SymbolSpec.tick_size`.

This means recovery no longer needs a guessed Gold SL/TP tolerance and does not create a second raw MetaTrader5 read client.

### Exposure fail-closed rule

`MT5Reader.open_positions(symbol)` distinguishes:

```text
MT5 returns empty collection → complete zero-position truth
MT5 returns None             → DATA_UNAVAILABLE / no recovery snapshot
corrupt/duplicate position   → DATA_CORRUPT / no recovery snapshot
```

A failed position read never becomes `positions_complete=True` with fabricated empty exposure.

Normalized recovery position facts include ticket, symbol, direction, volume, open price, SL/TP, optional magic/comment. Recovery ownership still depends on durable lineage; broker position facts alone do not prove bot ownership.

## Controller takeover integration

A higher epoch after expiry remains blocked by `CONTROLLER_TAKEOVER_RECONCILIATION_REQUIRED`. Startup recovery clears it only after durable state, live broker recovery facts and all hard authorities pass, followed by fresh same-holder/same-epoch verification.

## Fresh-machine target sequence

```text
clone/install code
→ obtain + verify checkpoint/catalog
→ restore to NEW local DB
→ configure credentials separately
→ initialize existing MT5Reader
→ build live MT5RecoveryTruth
→ governed StartupRecoveryCoordinator
→ rebuild/revalidate market intelligence/opportunities
→ load learning/research/candidate state
→ all hard runtime permissions
→ READY
```

Software pieces for checkpoint restore + live position snapshot + governed recovery are now deterministic. A real second-machine/Windows MT5 drill remains external evidence.

## Remote publication boundary

Local backup code does not contain GitHub/cloud auth. Publication credentials stay external; only verified public-safe artifacts may be published.

## Multi-machine safety

Portable state does not grant controller authority. SQLite coordination semantics are implemented, but real cross-laptop shared-storage locking/durability still needs controlled certification.

## Dashboard visibility target

```text
State Integrity       VERIFIED / FAILED
Backup Catalog        VERIFIED / FAILED / PENDING
Latest Checkpoint     VERIFIED / STALE / FAILED / NONE
Live Broker Snapshot  VERIFIED / FAILED / PENDING
Open Gold Positions   count / UNKNOWN
Recovery State        READY / RECONCILING / BLOCKED
Recovery Reason       exact reason
Execution Intent      CLEAR / RECONCILING
Managed Trade         NONE / MATCHED / RECONCILING / BLOCKED
Controller            PRIMARY / OBSERVER / TAKEOVER_RECONCILING / UNKNOWN
```

## Tests / current evidence

Deterministic coverage includes persistence/checkpoint/catalog integrity, secret blocking, controller takeover fencing, startup recovery, live account/symbol/spec/open-position normalization, positive empty exposure, unknown read fail-closed, invalid/duplicate position rejection and broker-tick-derived recovery tolerance.

Current deterministic checkpoint: **226 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Explicit non-goals

Recovery must not treat backup as broker truth, convert unknown exposure into zero, create a duplicate MetaTrader5 client, invent a Gold price tolerance, blind-resend an uncertain Intent, invent missing ManagedTrade context, clear takeover before reconciliation, or embed publication credentials.

## Remaining work

- wire live runtime startup so `MT5RecoveryTruth` feeds `StartupRecoveryCoordinator` automatically;
- supply `RecoveryAuthorities` from authoritative risk/session/data/execution owners;
- real fresh-machine + Windows MT5 broker reconciliation drill;
- controlled cross-laptop coordination/failover proof;
- authenticated public backup publication;
- final persistent runtime loop + shutdown/restart certification;
- schema migration transforms when v2 exists.
