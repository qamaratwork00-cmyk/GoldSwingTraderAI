# GoldSwingTraderAI — Persistence, Restart and Recovery

**Status:** PROVISIONAL — IMPLEMENTED FOUNDATION + LOCAL BACKUP + STARTUP RECOVERY  
**Version:** 0.6-implementation  
**Authority:** Durable lifecycle state, crash recovery, startup reconciliation, portable runtime checkpoints, automatic local backup cadence/retention, machine migration and backup/restore integrity.  
**Depends on:** `EXECUTION_AND_BROKER_SAFETY.md`, `RISK_CONTRACT.md`, `../20-trading-decisions/TRADE_PLAN.md`, `../40-research-learning/LEARNING_AND_AI_BOUNDARIES.md`

## Purpose

The bot must survive process restart, laptop loss/change and controlled migration without forgetting active obligations, strategy lineage or learning history.

> **Restart is not a fresh trading day unless actual risk/session rules say so. Machine replacement is not strategy amnesia. Restored state is context, not broker truth.**

## Current implementation checkpoint

Core owners now include:

```text
src/goldswingtraderai/persistence/store.py
src/goldswingtraderai/persistence/runtime_state.py
src/goldswingtraderai/persistence/checkpoint.py
src/goldswingtraderai/persistence/backup.py
src/goldswingtraderai/app/recovery.py
src/goldswingtraderai/security/financial_secrets.py
```

Subsystem repositories persist typed execution intents, managed trades, risk/opportunity/plan state, research episodes, candidate registry and promotion lifecycle on the same `StateStore` durability model.

## Durable local StateStore

`StateStore` uses standard-library SQLite with current records, append-only events, canonical JSON, SHA-256 checksums, explicit schema versions, WAL, `synchronous=FULL`, transactional writes and `PRAGMA quick_check`.

It verifies **both current records and event history**, exports deterministic `StoreSnapshot` state and restores a snapshot only into an otherwise empty store. Corrupt JSON/checksum/schema/timestamp state fails closed; it never becomes a blank safe-looking runtime state.

## Typed runtime recovery

`RuntimeStateRepository.load_recovery_bundle()` restores and validates:

- `RiskDayState`;
- `CooldownState`;
- `EpisodeRiskState`;
- active `Opportunity`;
- active `TradePlan`, including immutable original-R/objective context;
- Opportunity/Episode/TradePlan lineage.

Execution Intent and Managed Trade state use their own typed repositories on the same `StateStore`.

## Portable runtime checkpoint

Public-safe portable format:

```text
checkpoint_manifest.json
records.jsonl
events.jsonl
```

The manifest binds checkpoint/database schema versions, source label/version, UTC creation time, canonical filenames, records/events hashes/counts and `checkpoint_sha256`.

Export sequence:

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

Import rejects symlinks, missing/unexpected files, non-canonical filenames, unsupported schemas, hash/count/checksum mismatch, duplicate identities/event IDs, non-chronological events and financial-secret-shaped payloads.

`restore_runtime_checkpoint()` verifies the whole checkpoint, requires a non-existing destination DB, restores through a temporary `StateStore`, verifies integrity, checkpoints WAL, atomically installs the DB, reopens it and returns `broker_reconciliation_required=True`.

Restore never merges into or overwrites an existing live DB.

## Automatic local backup / catalog

Layout:

```text
<backup-root>/
├── backup_catalog.json
└── checkpoints/
    └── runtime-YYYYMMDDTHHMMSSZ-<sha12>/
```

Initial configurable engineering baseline:

```text
interval_minutes = 15
keep_latest      = 96
```

These are implementation defaults, not strategy/risk policy.

`create_backup_if_due()` verifies the existing catalog and referenced checkpoints, skips when not due, creates the new checkpoint in staging, verifies it, atomically installs it, writes the new hashed catalog and only then prunes older retention entries.

`latest_verified_checkpoint()` returns a newest checkpoint only after full catalog + checkpoint verification. Path traversal is rejected. Failed creation, including `FINANCIAL_SECRET_DETECTED`, preserves the previous known-good catalog/checkpoint.

## Governed startup recovery — implemented deterministic foundation

`app/recovery.py` owns the fail-closed recovery sequence that decides whether restored/current local context is safe enough to become runtime READY. It has **no broker-write authority**.

Core DTOs:

```text
RecoveryState                  READY / RECONCILING / BLOCKED
RecoveryAuthorities            required hard-authority traces
BrokerRecoveryPosition         normalized current broker position
BrokerRecoverySnapshot         account + symbol + complete position truth
StartupRecoveryResult          recovery outcome + restored context
StartupRecoveryCoordinator     sequencing owner
```

### Recovery sequence

```text
StateStore integrity_check
→ load RuntimeState recovery bundle
→ load current ExecutionIntent
→ load current ManagedTrade
→ require positively verified DEMO account
→ require complete current broker-position truth
→ verify persisted account/server/symbol identity
→ reconcile unresolved ExecutionIntent
→ reconcile ManagedTrade against current broker position
→ require all supplied hard recovery authorities PASS
→ freshly verify controller holder/epoch
→ if takeover pending, complete takeover reconciliation only now
→ READY
```

No later step may make an earlier failed/unknown authority disappear.

### Execution Intent restart semantics

```text
none / terminal intent
→ lifecycle may continue

APPROVED but never SUBMITTING
→ safe recovery cancellation to FAILED
→ no send allowance was consumed

CREATED
→ RECONCILING / explicit review

SUBMITTING / ACCEPTED_UNKNOWN
→ existing MT5Reconciler
→ query positions/orders/deals
→ VERIFIED_ACCEPTED / VERIFIED_NOT_CREATED / UNRESOLVED
→ never blind resend
```

A VERIFIED OPEN with no durable ManagedTrade context remains `RECONCILING`; the system does not invent management state.

### Managed Trade versus broker truth

A restored ManagedTrade must match one current broker position by:

- exact position ticket;
- symbol;
- direction;
- volume;
- current SL within explicit price tolerance;
- current TP within explicit price tolerance / expected absence.

Missing current position or SL/TP mismatch is `RECONCILING`. Duplicate position identity or direction/volume identity conflict is `BLOCKED`.

The caller supplies price tolerance from verified broker geometry; recovery does not guess a Gold tolerance.

### Hard authorities

`RecoveryAuthorities` carries hard facts recovery cannot infer from storage alone:

```text
account_identity
market_data
session_news
risk
position_capacity
execution_environment
```

Any BLOCK blocks recovery. Any UNKNOWN keeps recovery `RECONCILING`. Only all PASS may reach controller completion/READY.

### Takeover completion is orchestrated

If a standby already acquired a newer fencing epoch after previous lease expiry, `ControllerLeaseManager` remains blocked with `CONTROLLER_TAKEOVER_RECONCILIATION_REQUIRED`.

`StartupRecoveryCoordinator` calls `complete_takeover_reconciliation()` only **after** durable state, current broker truth, Intent/ManagedTrade recovery and all hard authorities pass. The controller then freshly verifies the same holder/epoch before clearing the takeover block.

If controller authority changes during recovery, startup cannot become READY.

## Broker versus local truth

```text
restored SUBMITTING / ACCEPTED_UNKNOWN
→ DO NOT RESEND
→ current broker positions/orders/deals
→ reconcile
→ VERIFIED / FAILED / still UNKNOWN
```

```text
local ManagedTrade says OPEN
broker position missing/mismatched
→ RECONCILING/BLOCKED
→ never submit a replacement merely because local state said OPEN
```

Broker owns current positions/orders/deals. Local state owns lifecycle context and history.

## Fresh-machine target sequence

```text
clone/install code
→ obtain + verify selected checkpoint/catalog
→ restore checkpoint to NEW local DB
→ configure financial credentials separately
→ connect intended MT5 DEMO
→ build current broker recovery snapshot
→ governed StartupRecoveryCoordinator
→ rebuild market intelligence chronologically
→ revalidate stored opportunities
→ load learning/research/candidate/promotion state
→ all hard permissions
→ READY
```

The deterministic recovery coordinator is implemented. A live MT5 recovery-snapshot adapter, real second-machine drill and final persistent runtime wiring remain pending.

## Shared financial-secret boundary

`security/financial_secrets.py` is the shared owner. The chosen policy remains **minimum-hide / financial-authority-only secrecy**: strategy/research/learning/performance state may be backed up; authority-bearing credentials/tokens/private keys may not.

## Remote publication boundary

`backup.py` deliberately stops at local public-safe artifact management. It does not authenticate to GitHub or embed a PAT/token. Remote publication must use external authenticated tooling and only already-verified public-safe artifacts.

## Multi-machine safety

Portable state never grants two machines broker-write authority. Controller/fencing is owned by `EXECUTION_AND_BROKER_SAFETY.md`. A new fencing epoch after takeover still remains blocked until governed recovery completes.

`SQLiteCoordinationStore` now exists as a deterministic durable backend, but real cross-laptop use is not certified until the exact shared-storage locking/durability behavior passes controlled fault tests.

## Dashboard visibility

Compact recovery facts should expose:

```text
State Integrity       VERIFIED / FAILED
Backup Catalog        VERIFIED / FAILED / PENDING
Latest Checkpoint     VERIFIED / STALE / FAILED / NONE
Checkpoint SHA        <short hash>
Restore               NONE / VERIFIED / RECONCILING
Execution Intent      CLEAR / RECONCILING
Managed Trade         NONE / MATCHED / RECONCILING / BLOCKED
Broker Reconcile      PENDING / COMPLETE
Controller            PRIMARY / OBSERVER / TAKEOVER_RECONCILING / UNKNOWN
Recovery State        READY / RECONCILING / BLOCKED
Recovery Reason       exact stable reason
```

## Tests / current evidence

Deterministic coverage now includes:

- record/event corruption fail-closed;
- portable checkpoint typed/generic state round-trip;
- manifest/file/checksum tamper detection;
- financial-secret blocking;
- no-overwrite export/restore;
- automatic backup due/skip cadence + retention + catalog integrity;
- previous-known-good preservation after failed backup;
- clean startup recovery READY;
- non-DEMO/account mismatch BLOCK;
- pre-submit APPROVED Intent cancellation without send;
- unresolved `SUBMITTING/ACCEPTED_UNKNOWN` staying RECONCILING;
- verified OPEN without ManagedTrade context staying RECONCILING;
- ManagedTrade broker-position/SL mismatch recovery behavior;
- UNKNOWN hard authority preventing READY;
- expired-lease takeover completing only after governed recovery passes.

Current deterministic checkpoint: **219 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Explicit non-goals

Persistence/recovery must not treat stale backup as broker truth, silently reset corruption, embed credentials, publish raw SQLite as a Git merge artifact, overwrite/merge a live restore DB, blind-resend an uncertain Intent, invent ManagedTrade context, clear takeover fencing before recovery passes, or permit two restored laptops to trade independently.

## Remaining work

Resolved at V1 deterministic software-foundation level:

- SQLite local durability + typed repositories;
- portable checkpoint + secret blocking;
- fresh-DB restore;
- automatic local cadence/retention/catalog;
- governed startup recovery sequencing;
- Intent and ManagedTrade recovery checks;
- reconciliation-gated controller takeover integration.

Still pending:

- read-only live MT5 recovery-snapshot adapter through the existing MT5 boundary;
- authenticated/public GitHub publication workflow for allowed artifacts;
- real fresh-machine + live broker reconciliation certification;
- controlled cross-laptop coordination/failover proof;
- final persistent runtime startup/shutdown loop;
- migration/rollback transforms once schema v2+ exists.
