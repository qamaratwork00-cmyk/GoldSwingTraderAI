# GoldSwingTraderAI — Persistence, Restart and Recovery

**Status:** PROVISIONAL — IMPLEMENTED FOUNDATION + PORTABLE CHECKPOINT  
**Version:** 0.4-implementation  
**Authority:** Durable lifecycle state, crash recovery, restart reconciliation, portable runtime checkpoints, machine migration and backup/restore integrity.  
**Depends on:** `EXECUTION_AND_BROKER_SAFETY.md`, `RISK_CONTRACT.md`, `../20-trading-decisions/TRADE_PLAN.md`, `../40-research-learning/LEARNING_AND_AI_BOUNDARIES.md`

## Purpose

The bot must survive process restart, laptop loss/change and controlled migration without forgetting active obligations, strategy lineage or learning history.

> **Restart is not a fresh trading day unless the actual risk/session rules say so. Machine replacement is not strategy amnesia. A restored checkpoint is context, not broker truth.**

## Current implementation checkpoint

V1 local persistence uses Python standard-library `sqlite3`. Core owners now include:

```text
src/goldswingtraderai/persistence/store.py
src/goldswingtraderai/persistence/runtime_state.py
src/goldswingtraderai/persistence/checkpoint.py
src/goldswingtraderai/security/financial_secrets.py
```

Subsystem repositories/adapters persist typed execution intents, managed trades, runtime risk/opportunity/plan state, research episodes, candidate registry and promotion lifecycle on the same `StateStore` durability model.

## `store.py` — durable local authority

`StateStore` provides:

- SQLite durable current records;
- append-only event history;
- canonical JSON payloads;
- SHA-256 checksums;
- explicit database/record schema versions;
- WAL + `synchronous=FULL`;
- transactional upsert/delete + optional same-transaction event;
- `PRAGMA quick_check`;
- integrity verification for **both current records and event history**;
- deterministic `StoreSnapshot` export;
- restore of a verified snapshot only into an otherwise empty initialized store.

Corrupt JSON/checksum/schema/timestamp state raises an explicit persistence error. It never becomes a blank safe-looking runtime state.

## `runtime_state.py` — typed critical recovery

Typed round-trip adapters cover:

- `RiskDayState`;
- `CooldownState`;
- `EpisodeRiskState`;
- active `Opportunity`;
- active `TradePlan`, including immutable original-R/objective context.

`RuntimeStateRepository.load_recovery_bundle()` validates storage and Opportunity/Episode/Trade Plan lineage before returning recovery context.

## `checkpoint.py` — portable runtime checkpoint implemented

Phase 11 now has a public-safe canonical checkpoint format. It does **not** copy the live mutable SQLite database into Git.

V1 checkpoint directory:

```text
checkpoint_manifest.json
records.jsonl
events.jsonl
```

The checkpoint manifest records:

- checkpoint schema version;
- StateStore database schema version;
- source label/version;
- UTC creation time;
- canonical records/events filenames;
- records/events SHA-256 hashes and counts;
- `checkpoint_sha256` over manifest facts excluding its own hash.

### Export rules

```text
StateStore integrity_check
→ export deterministic StoreSnapshot
→ structured financial-secret scan
→ canonical records/events JSONL
→ text-level financial-secret scan
→ file hashes + manifest hash
→ write temporary sibling directory
→ atomic rename to new destination
```

Hard rules:

- destination is write-new; existing checkpoint is never overwritten;
- current records and append-only event history are both included;
- record/event original timestamps/checksums/event IDs are preserved;
- financial-authority credential-shaped payloads block export with `FINANCIAL_SECRET_DETECTED`;
- account identifiers that do not grant financial authority are not hidden merely because they identify a scope;
- live SQLite/WAL files are not the portable public backup format.

### Import rules

Import rejects:

- checkpoint root/file symlinks;
- missing or unexpected files;
- non-canonical filenames;
- unsupported checkpoint/database schema;
- manifest hash mismatch;
- records/events file hash mismatch;
- count mismatch;
- duplicate record identities;
- non-chronological/duplicate event IDs;
- per-record/per-event checksum mismatch;
- financial-authority secret-shaped payloads.

### Fresh-database restore

`restore_runtime_checkpoint()`:

```text
verify entire checkpoint
→ require destination DB does not exist
→ restore into temporary new StateStore
→ verify record/event integrity
→ checkpoint SQLite WAL
→ atomically move completed DB into destination
→ reopen + integrity_check
→ return broker_reconciliation_required = True
```

Restore never merges into or overwrites an existing live database. This avoids silently combining stale and current authority-bearing lifecycle state.

## Shared financial-secret detection

`security/financial_secrets.py` is the shared security owner. Repository text scanning preserves source-code-safe semantics, while structured checkpoint scanning inspects serialized payload keys directly so a real `password`/token/key field cannot enter a public recovery checkpoint.

This implements the chosen **minimum-hide / financial-authority-only secrecy** policy: strategy/research/learning/performance state may be backed up; credentials/tokens/private keys capable of authenticated financial action or paid-resource abuse may not.

## Later-phase typed persistence already implemented

Durable state includes:

- `ExecutionIntent` lifecycle/history;
- managed open-trade state;
- research episodes;
- candidate/rejected memory;
- promotion lifecycle/final-holdout/rollback state.

These states survive deterministic restart tests and are captured generically by the portable StoreSnapshot/checkpoint layer because the checkpoint serializes the authoritative StateStore namespaces rather than maintaining a second per-feature backup schema.

## State categories

Durable state is logically separated rather than stored as one opaque mutable blob:

- risk state;
- runtime/system state;
- execution intent/order lifecycle;
- managed trade lifecycle;
- Trade Plan/original R context;
- Opportunity / Market Episode identity;
- trade/opportunity/research journal;
- performance/learning evidence;
- Candidate/Strategy Registry;
- research/discovery/invention state;
- promotion/rollback history;
- diagnostics/fault history;
- backup manifests/schema metadata.

## Daily risk / intent / open-trade recovery

Restart must not erase daily loss locks, cooldown or Market Episode churn protection.

```text
restored SUBMITTING / ACCEPTED_UNKNOWN ExecutionIntent
→ DO NOT RESEND
→ query broker truth
→ reconcile positions/orders/deals/action state
→ classify VERIFIED / FAILED / still UNKNOWN
```

Broker position facts alone are insufficient to manage a restored trade. Local state preserves strategy/policy lineage, Opportunity/Episode/Trade IDs, entry/fill references, original SL/R, objective chain and management context; broker truth still owns current position/SL/TP/deals.

## Rebuildable versus durable market state

Rolling candles and derived market intelligence may be rebuilt chronologically from validated history. Durable financial/order/trade/learning evidence must not depend on a replaceable candle cache.

## Broker versus local truth

```text
local checkpoint says OPEN
broker says no open position
→ inspect current positions/orders/deals/account identity
→ reconcile closure/manual action/data failure
→ never blindly replay the old OPEN record into a new order
```

A restored checkpoint cannot grant order-send authority by itself.

## Target startup / fresh-machine sequence

```text
clone/install code
→ restore verified portable checkpoint to NEW local DB
→ configure financial credentials separately
→ integrity-check restored state
→ connect intended MT5 DEMO account
→ verify account/symbol
→ fetch current positions/orders/deals
→ reconcile unresolved ExecutionIntents
→ reconcile managed trades
→ restore/validate risk state
→ rebuild market intelligence chronologically
→ revalidate stored opportunities
→ load research/candidate/promotion/learning state
→ acquire fresh controller lease/epoch
→ evaluate hard permissions
→ READY
```

The portable checkpoint/restore software is implemented. The complete broker-connected fresh-machine drill and integrated runtime startup orchestration remain pending.

## Public GitHub backup policy

Allowed recovery material includes source/docs, strategies, learned parameters, Candidate/Strategy Registry, autonomous candidates/genealogy/rejected memory, learning summaries, research/promotion/rollback history, performance/evidence metadata and verified runtime checkpoints.

Never publish MT5 passwords, broker/session tokens, paid API keys, GitHub PATs, private/signing keys, recovery/encryption keys or other authority-bearing credentials.

If a credential was ever committed publicly, deletion is insufficient; revoke/rotate it.

## Backup verification

A backup is valid only when:

- source `StateStore.integrity_check()` passes;
- structured + text financial-secret checks pass;
- manifest/file/record/event hashes pass;
- import parsing succeeds;
- schema versions are supported;
- restore into a fresh DB succeeds in drill/certification;
- old known-good backup is not destroyed by a failed new export.

Exact automatic cadence/retention/publication policy remains Phase-11 work.

## Multi-machine safety

Portable state does not grant two machines broker-write authority. Controller ownership/fencing remains governed by `EXECUTION_AND_BROKER_SAFETY.md`.

The deterministic in-memory coordination backend is test-only; real shared atomic coordination is still required before cross-laptop failover certification.

## Dashboard visibility

Compact recovery facts should include, as available:

```text
State Integrity       VERIFIED / FAILED
Checkpoint            VERIFIED / STALE / FAILED / PENDING
Checkpoint SHA        <short hash>
Checkpoint Records    count
Checkpoint Events     count
Restore               NONE / VERIFIED / RECONCILING
Broker Reconcile      PENDING / COMPLETE
Controller            PRIMARY / OBSERVER / UNKNOWN
```

## Tests / current evidence

Deterministic coverage now includes:

- risk-day/cooldown/Episode restart;
- Opportunity/TradePlan lineage restart;
- current-record checksum corruption fail-closed;
- **event-history corruption fail-closed**;
- ExecutionIntent/managed-trade/research/candidate/promotion restart semantics;
- portable checkpoint typed-state round-trip;
- generic StrategyMemory-style namespace preservation;
- event count/history preservation;
- checkpoint manifest and records tamper detection;
- financial-secret payload export block with no artifact left behind;
- no-overwrite checkpoint export;
- no-overwrite fresh-database restore;
- restored result explicitly requiring broker reconciliation.

Current deterministic checkpoint: **195 tests PASS**, Ruff PASS and financial-secret scan PASS.

Still required before release verification:

- automatic backup cadence/retention/publication workflow;
- controlled fresh-machine restore against a real broker account with reconciliation;
- old-backup + live-broker reconciliation drill;
- final integrated startup/shutdown/recovery orchestration;
- production shared-controller failover recovery;
- schema migration/rollback fixtures once schema v2+ exists.

## Explicit non-goals

Persistence/backup must not:

- treat stale backup as current broker truth;
- silently reset critical state after corruption;
- embed financial credentials in checkpoints;
- publish raw live mutable SQLite as a mergeable Git source artifact;
- overwrite an existing restore DB;
- allow machine-specific IDs to redefine strategy identity;
- permit two restored laptops to trade the same account independently;
- add an ORM/service layer where SQLite + typed adapters satisfy V1.

## Open / later implementation items

Resolved for V1 software foundation:

- local durable runtime engine: **standard-library SQLite**;
- record shape: **canonical JSON + SHA-256 checksum**;
- typed repositories/adapters for critical state;
- event integrity verification;
- portable runtime checkpoint format;
- checkpoint financial-secret blocking;
- atomic restore to a fresh local DB.

Still pending:

- automatic backup cadence/retention;
- public GitHub publication/catalog workflow for allowed checkpoints;
- migration/rollback compatibility when schema v2+ exists;
- production shared execution-controller coordinator;
- final integrated startup/shutdown/recovery orchestration;
- real fresh-machine + broker reconciliation certification.
