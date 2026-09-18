# GoldSwingTraderAI — Persistence, Restart and Recovery

**Status:** PROVISIONAL — IMPLEMENTED FOUNDATION + LOCAL BACKUP CATALOG  
**Version:** 0.5-implementation  
**Authority:** Durable lifecycle state, crash recovery, restart reconciliation, portable runtime checkpoints, automatic local checkpoint cadence/retention, machine migration and backup/restore integrity.  
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
src/goldswingtraderai/persistence/backup.py
src/goldswingtraderai/security/financial_secrets.py
```

Subsystem repositories/adapters persist typed execution intents, managed trades, runtime risk/opportunity/plan state, research episodes, candidate registry and promotion lifecycle on the same `StateStore` durability model.

## `store.py` — durable local authority

`StateStore` provides SQLite durable current records, append-only events, canonical JSON, SHA-256 checksums, schema versions, WAL + `synchronous=FULL`, transactional writes, `PRAGMA quick_check`, record/event integrity verification, deterministic `StoreSnapshot` export and restore only into an empty store.

Corrupt JSON/checksum/schema/timestamp state raises an explicit persistence error. It never becomes a blank safe-looking runtime state.

## `runtime_state.py` — typed critical recovery

Typed round-trip adapters cover `RiskDayState`, `CooldownState`, `EpisodeRiskState`, active `Opportunity` and active `TradePlan` including immutable original-R/objective context.

`RuntimeStateRepository.load_recovery_bundle()` validates storage and Opportunity/Episode/Trade Plan lineage before returning recovery context.

## `checkpoint.py` — portable runtime checkpoint implemented

The public-safe portable format is:

```text
checkpoint_manifest.json
records.jsonl
events.jsonl
```

The manifest records checkpoint/database schema versions, source label/version, UTC creation time, canonical filenames, records/events SHA-256 hashes/counts and `checkpoint_sha256`.

### Export

```text
StateStore integrity_check
→ deterministic StoreSnapshot
→ structured financial-secret scan
→ canonical records/events JSONL
→ text-level secret scan
→ hashes
→ temporary sibling directory
→ atomic rename to NEW destination
```

Current records and append-only events are both included with original timestamps/checksums/event IDs. Financial-authority credential-shaped payloads block export with `FINANCIAL_SECRET_DETECTED`. Live SQLite/WAL files are not the portable public backup format.

### Import / restore

Import rejects symlinks, missing/unexpected files, non-canonical filenames, unsupported schemas, hash/count/checksum mismatch, duplicate records/events and secret-shaped payloads.

`restore_runtime_checkpoint()` verifies the entire checkpoint, requires a non-existing destination DB, restores through a temporary `StateStore`, verifies integrity, checkpoints WAL, atomically installs the DB, reopens it and returns `broker_reconciliation_required=True`.

Restore never merges into or overwrites an existing live DB.

## `backup.py` — automatic local cadence / retention / catalog implemented

Phase 11 now has a verified local backup manager on top of immutable checkpoints.

Layout:

```text
<backup-root>/
├── backup_catalog.json
└── checkpoints/
    ├── runtime-YYYYMMDDTHHMMSSZ-<sha12>/
    └── ...
```

`BackupPolicy` initial configurable engineering baseline:

```text
interval_minutes = 15
keep_latest      = 96
```

At the default cadence this represents roughly one day of rolling local checkpoints. These are **implementation defaults, not trading/risk policy** and may be changed without altering strategy behaviour.

### Backup creation

`create_backup_if_due()`:

```text
verify current catalog + every referenced checkpoint
→ if latest backup is not due: SKIPPED_NOT_DUE
→ export new checkpoint to hidden staging directory
→ immediately import/verify the new checkpoint
→ assign deterministic timestamp + SHA-derived name
→ atomically move staging to final checkpoint directory
→ write new hashed catalog atomically
→ only then prune checkpoints outside retention
```

This ordering protects the last known-good catalog: pruning never happens before the replacement catalog/checkpoint is successfully verified and published locally.

### Catalog integrity

`backup_catalog.json` is canonical JSON containing:

- catalog schema version;
- UTC update time;
- chronological checkpoint entries;
- checkpoint name, creation time, SHA, record count and event count;
- `catalog_sha256` over catalog facts excluding its own hash.

`load_backup_catalog(..., verify_checkpoints=True)` verifies both catalog integrity and every referenced checkpoint. `latest_verified_checkpoint()` returns the newest checkpoint only after full verification.

Catalog names are basenames only; path traversal is rejected. A tampered/missing catalogued checkpoint makes the catalog verification fail closed.

### Retention safety

Retention keeps the newest configured count. The new catalog is atomically written **before** old checkpoint directories are pruned. A crash may therefore leave an unreferenced old directory, which is safe; it must not leave a valid catalog deliberately pointing at a checkpoint deleted first.

### Failed backup safety

If checkpoint export fails — including `FINANCIAL_SECRET_DETECTED` — the prior catalog and prior known-good checkpoint remain unchanged. Temporary staging is removed.

## Shared financial-secret detection

`security/financial_secrets.py` is the shared security owner. Repository text scanning preserves source-code-safe semantics, while structured checkpoint scanning inspects serialized payload keys directly.

The chosen policy remains **minimum-hide / financial-authority-only secrecy**: strategy/research/learning/performance state may be backed up; credentials/tokens/private keys capable of authenticated financial action or paid-resource abuse may not.

## Remote publication boundary

`backup.py` deliberately stops at local public-safe artifact management. It does **not** authenticate to GitHub, embed a PAT/token, or perform a remote push.

Remote GitHub publication must be performed by external authenticated tooling whose credential remains outside repository/checkpoint state. The publication layer may consume only already-verified public-safe catalog/checkpoint artifacts.

This separation prevents the backup system from solving durability by putting its own financial/security authority into the backup.

## Durable state captured generically

Current StateStore-based namespaces include risk/session state, execution intent lifecycle, managed trades, Opportunity/TradePlan/original-R context, research episodes, StrategyMemory/learning evidence, candidate/rejected memory, promotion/final-holdout/rollback state and diagnostics/event history.

The checkpoint captures authoritative StateStore namespaces generically rather than maintaining a second per-feature backup schema.

## Broker versus local truth

```text
restored SUBMITTING / ACCEPTED_UNKNOWN intent
→ DO NOT RESEND
→ query broker positions/orders/deals
→ reconcile
→ VERIFIED / FAILED / still UNKNOWN
```

```text
local checkpoint says OPEN
broker says no open position
→ inspect broker truth + lifecycle history
→ reconcile closure/manual action/data failure
→ never submit a replacement merely because backup said OPEN
```

A restored checkpoint cannot grant order-send authority by itself.

## Target fresh-machine sequence

```text
clone/install code
→ obtain/verify selected checkpoint/catalog
→ restore checkpoint to NEW local DB
→ configure financial credentials separately
→ integrity-check restored state
→ connect intended MT5 DEMO account
→ verify account/symbol
→ fetch current positions/orders/deals
→ reconcile unresolved ExecutionIntents + managed trades
→ validate restored risk state
→ rebuild market intelligence chronologically
→ revalidate stored opportunities
→ load learning/research/candidate/promotion state
→ acquire fresh controller lease/epoch
→ evaluate all hard permissions
→ READY
```

Portable checkpoint and local rolling-backup software are implemented. Broker-connected fresh-machine certification and integrated startup orchestration remain pending.

## Public GitHub backup policy

Allowed: source/docs, strategies, learned parameters, Strategy Registry/candidates/rejected memory, research/promotion/rollback history, performance/evidence metadata and verified public-safe runtime checkpoints/catalogs.

Never publish MT5 passwords, broker/session tokens, paid API keys, GitHub PATs, private/signing keys, recovery/encryption keys or other authority-bearing credentials.

If a credential was ever committed publicly, deletion is insufficient; revoke/rotate it.

## Backup validity

A backup is valid only when source StateStore integrity, structured/text secret checks, checkpoint hashes/counts/checksums, catalog hash, checkpoint import and supported schemas all verify. Release certification additionally requires a real fresh-machine restore + broker reconciliation drill.

## Multi-machine safety

Portable/local backup state does not grant two machines broker-write authority. Controller ownership/fencing remains governed by `EXECUTION_AND_BROKER_SAFETY.md`.

The deterministic in-memory coordination backend is test-only; a real shared atomic coordinator remains required before cross-laptop failover certification.

## Dashboard visibility

Compact recovery facts should include:

```text
State Integrity       VERIFIED / FAILED
Backup Catalog        VERIFIED / FAILED / PENDING
Latest Checkpoint     VERIFIED / STALE / FAILED / NONE
Checkpoint SHA        <short hash>
Checkpoint Records    count
Checkpoint Events     count
Next Backup Due       timestamp / not due
Restore               NONE / VERIFIED / RECONCILING
Broker Reconcile      PENDING / COMPLETE
Controller            PRIMARY / OBSERVER / UNKNOWN
```

## Tests / current evidence

Deterministic coverage includes restart lineage, current-record/event corruption fail-closed, portable checkpoint typed/generic state round-trip, event preservation, manifest/file tamper detection, secret blocking, no-overwrite export/restore, broker-reconciliation-required restore, backup due/skip cadence, retention pruning, latest verified selection, catalog tamper detection, referenced-checkpoint tamper detection and failed-secret-backup preservation of the previous known-good backup.

Current deterministic checkpoint: **202 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Explicit non-goals

Persistence/backup must not treat stale backup as broker truth, silently reset corruption, embed credentials, publish raw SQLite as a Git merge artifact, overwrite an existing restore DB, silently merge stale/current lifecycle state, permit two restored laptops to trade independently, or hard-code remote publication credentials.

## Open / later implementation items

Resolved at V1 software-foundation level:

- standard-library SQLite local durability;
- canonical record/event integrity;
- portable runtime checkpoint format;
- checkpoint financial-secret blocking;
- atomic restore to a fresh DB;
- configurable automatic local checkpoint cadence;
- verified local backup catalog;
- count-based local retention;
- latest-known-good verified selection.

Still pending:

- authenticated/public GitHub publication workflow for allowed artifacts;
- real fresh-machine + broker reconciliation certification;
- production shared execution-controller coordinator/failover;
- final integrated startup/shutdown/recovery orchestration;
- migration/rollback transforms once schema v2+ exists.
