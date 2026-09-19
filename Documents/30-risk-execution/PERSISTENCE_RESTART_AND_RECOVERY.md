# GoldSwingTraderAI — Persistence, Restart and Recovery

**Status:** PROVISIONAL
**Version:** 0.1-recovery
**Authority:** Durable lifecycle, checkpoint, backup, restore and startup reconciliation

## Purpose

Restart or laptop change must not erase obligations. Durable state is context
and history; current broker exposure is always refreshed from MT5.

## Truth layers

~~~mermaid
flowchart TB
    STATE["SQLite StateStore — records, events, checksums"] --> LOAD["Strict typed load"]
    CHECK["Portable verified checkpoint"] --> LOAD
    BROKER["Fresh MT5RecoveryTruth"] --> RECON["Reconcile intent/trade/exposure"]
    LOAD --> RECON
    RECON --> AUTH["RecoveryAuthorities"]
    AUTH --> CTRL["Controller holder and fencing"]
    CTRL --> READY{"READY?"}
    READY -->|"no"| BLOCK["RECONCILING/BLOCKED"]
    READY -->|"yes"| RUN["Persistent runtime"]
~~~

| Layer | Authority |
|---|---|
| local durable records | lifecycle intent, risk, plans, opportunities and history |
| portable checkpoint | verified transport of local context |
| MT5 truth | current account, positions, orders, deals and actual SL/TP |
| RecoveryAuthorities | whether the current combination may continue |

Restore never directly grants a broker write.

## StateStore rules

Standard-library SQLite uses canonical JSON payloads, explicit schema versions,
SHA-256 checksums, transactional transitions, WAL and synchronous durability.
Malformed types, non-finite numbers, bad UTC or checksum mismatch fail
explicitly; they do not become empty defaults.

Durable groups include risk-day/cooldown, Opportunity/Episode, TradePlan,
ExecutionIntent, ManagedTrade, research journal/candidates/promotion and
backup metadata.

## Intent and ManagedTrade recovery

~~~text
terminal Intent → continue
APPROVED before submit → safe cancellation may be possible
CREATED → review/reconcile
SUBMITTING or ACCEPTED_UNKNOWN → broker reconciliation
broker OPEN without ManagedTrade → RECONCILING
~~~

ManagedTrade must match exactly one current broker position by ticket, symbol,
direction and volume; SL/TP must match within broker-derived tick tolerance.
Unknown positions are not zero exposure.

## Portable checkpoint

A checkpoint is a new, verified artifact containing manifest, records and
events. Restore:

1. verifies schema, hashes and types;
2. refuses to overwrite an existing runtime database;
3. creates a new database;
4. reports broker_reconciliation_required=true;
5. keeps trading_authority_granted=false until live recovery completes.

## Local backup and public-safe staging

The runtime may create verified rolling backups, initially 15-minute cadence and
keep 96. A new catalog entry is staged and verified before retention pruning.
Failed backup keeps the last known-good catalog.

publication.py stages only a catalog-verified artifact to a new destination,
writes a publication manifest and scans for financial secrets. It does not
authenticate, commit or push.

Commands:

~~~text
python scripts/stage_public_backup.py <backup-root> <destination>
python scripts/restore_runtime_checkpoint.py <checkpoint> <new-db>
python scripts/scan_financial_secrets.py <path>
~~~

## Fresh-machine sequence

~~~text
install repository and dependencies
→ restore checkpoint into new DB
→ configure credentials separately
→ connect intended DEMO MT5
→ capture MT5RecoveryTruth
→ build repositories/reconciler/controller
→ reconcile intents and managed positions
→ evaluate authorities
→ READY only after all pass
~~~

## Source and tests

| Source | Role | Tests |
|---|---|---|
| persistence/store.py | SQLite records/events/checksums | test_persistence_recovery.py |
| persistence/runtime_state.py | typed runtime state | test_persistence_recovery.py |
| persistence/checkpoint.py | export/restore new DB | test_runtime_checkpoint.py |
| persistence/backup.py | catalog/cadence/retention | test_backup_catalog.py |
| persistence/publication.py | public-safe staging | test_operator_scripts.py, test_backup_catalog.py |
| app/recovery.py | startup reconciliation | test_startup_recovery.py |
| app/recovery_mt5.py | current broker truth | test_recovery_mt5.py |

## Dashboard/release boundary

Show state integrity, latest checkpoint/catalog, broker snapshot, open position
count, Intent and ManagedTrade reconciliation, controller role and recovery
reason. Fresh-machine, cross-laptop and live broker drills remain release
evidence, not deterministic test claims.

## Explicit non-goals

Backup is not broker truth; restore is not permission; no credentials are
embedded; no duplicate MT5 reader is created; uncertain actions are not resent;
and recovery never invents missing exposure or tolerance.

