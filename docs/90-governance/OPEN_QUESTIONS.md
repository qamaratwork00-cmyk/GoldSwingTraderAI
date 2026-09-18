# GoldSwingTraderAI — Open Questions / Freeze Matrix

**Status:** LIVING LEDGER  
**Version:** 3.0-design

This file separates remaining items so implementation is not delayed by values that should be learned from evidence or ordinary engineering choices.

```text
FIX BEFORE BUILD       = required architecture/safety decision still missing
CALIBRATE IN RESEARCH  = explicit deterministic baseline, tune only with chronological evidence
IMPLEMENTATION CHOICE  = coder may choose implementation preserving frozen contract
DEFER LATER            = not required for V1
```

At behavioural-contract level there are currently **no known `FIX BEFORE BUILD` items**.

## Current implementation status

Deterministic core exists through Phase 10 plus current Phase-11 local backup foundation:

```text
1  Foundation/config/domain/CI
2  MT5 read layer + market snapshots
3  Market intelligence + Trendline/Fibonacci/POC
4  Strategies/fusion/Opportunity/Entry Timing
5  Trade Plan + Risk
6  Session/news permission + SQLite persistence
7  Execution intent/gate/controller/writer/reconciliation
8  Trade Manager + execution bridge
9  Dashboard renderer
10 Replay / ablation / outcomes / manager replay
   + historical PRE_CLOSE/session replay
   + stress / fixed-policy walk-forward
   + portable datasets / exact-count MT5 history acquisition
   + evidence identity/packages
   + learning/discovery/invention/promotion
11 StateStore snapshot + portable runtime checkpoint
   + fresh-local-DB restore
   + automatic local checkpoint cadence
   + verified backup catalog + count-based retention
```

Live DEMO release and real-data validation are not complete. Final runtime orchestration, authenticated remote publication, production shared cross-laptop coordination, real fresh-machine/broker drill, controlled Windows/MT5 evidence and DEMO certification remain pending.

## Frozen trading principles still in force

- completed candles own structural confirmation;
- Trendline/Fibonacci/POC are optional bonus-only confluence, not hard filters;
- six production strategy families remain parallel;
- target-room RR policy, structural targets and evidence-earned runner remain frozen;
- SMALL is any positive day-start equity below `$300`; no `$100` floor;
- Gold capacity `0/1` independently risk-bearing position;
- daily/session/news/execution hard safety remains separate from soft scoring;
- verified connected DEMO is required for V1 broker-write permission.

## Research / learning / evidence

Deterministic foundation is implemented. External evidence still pending: controlled real XAU history, trustworthy historical broker-session coverage, broad validation, empirical friction calibration, final holdout, Shadow and DEMO forward evidence.

## Persistence / backup — Phase 11

### Portable checkpoint / StateStore snapshot — CLOSED

`persistence/checkpoint.py` and `StateStore` provide canonical current-record + append-only-event export/import, event integrity verification, financial-secret blocking and fresh-DB-only restore with broker reconciliation explicitly required.

### Automatic local cadence / retention / catalog — CLOSED at software-foundation level

`persistence/backup.py` now owns local verified rolling backups.

Initial configurable baseline:

```text
interval_minutes = 15
keep_latest      = 96
```

These values are engineering defaults, not trading/risk policy.

Implemented guarantees:

- verify current catalog and every referenced checkpoint before creating another;
- skip when not due;
- stage and fully verify new checkpoint before cataloging it;
- timestamp + SHA-derived safe checkpoint naming;
- canonical `backup_catalog.json` with `catalog_sha256`;
- chronological entries containing checkpoint SHA and record/event counts;
- `latest_verified_checkpoint()` verifies before returning;
- count-based newest-N retention;
- write new catalog before pruning old directories;
- failed new backup preserves previous known-good catalog/checkpoint;
- checkpoint name path traversal rejected;
- tampered catalog or referenced checkpoint fails closed.

### Remote publication boundary — still pending

`backup.py` intentionally contains no GitHub/cloud authentication and no PAT/token handling.

Still required:

- authenticated publication mechanism for **already verified public-safe artifacts**;
- publication credentials supplied externally and never serialized into checkpoint/repo state;
- remote destination/layout/catalog convention;
- failure semantics that preserve local known-good backup even when remote publication fails;
- proof that publication never uploads financial-authority secrets.

This may be implemented as external CLI/CI/provider adapter; it must not move credentials into runtime backup state.

### Fresh-machine / broker truth — controlled evidence pending

- restore on another machine;
- MT5 DEMO account/symbol verification after restore;
- unresolved Intent/open-trade reconciliation against current positions/orders/deals;
- old-backup + newer broker-truth conflict drill;
- no stale order replay;
- fresh controller authority before any broker write.

### Cross-laptop controller — pending

- production shared atomic coordination backend;
- monotonic fencing across machines;
- lease expiry/takeover/reconciliation proof;
- split-brain denial under network/process failure.

### Integrated startup — pending

- explicit restore/startup path;
- automatic integrity/reconciliation sequence;
- operator-visible backup/restore/controller health;
- no READY state until broker/current-controller hard authorities verify.

### Schema migration — defer until v2 exists

Current code rejects unsupported schemas. Real migration/rollback transforms should be implemented when a second schema actually exists, not guessed in advance.

## Frozen backup/security principles

- live SQLite DB is runtime state, not a Git merge artifact;
- portable checkpoints/catalogs are canonical verified content;
- failed export/new backup cannot overwrite the previous known-good checkpoint;
- restore never overwrites/merges an existing local DB;
- financial-authority secrets never enter public/tracked backup state;
- account identifiers without authority are not hidden merely because they identify scope;
- broker truth owns current exposure after restore;
- restored laptop needs fresh controller authority before any broker write;
- two restored laptops cannot independently trade the same account;
- remote publication credentials stay external to backup artifacts.

## Still calibrate in research

- market-intelligence/scoring/timing/trailing thresholds;
- optional-confluence value and retention;
- real-data periods/sample sizes;
- walk-forward window sizes/stepping;
- stress severity and broker-friction distributions;
- promotion/Shadow/Canary thresholds;
- StrategyMemory/discovery similarity/recipe thresholds;
- Monte Carlo/block/regime-aware methodology.

## Operator / runtime / release pending

- authoritative dashboard runtime DTO + backup/recovery/Discovery Health display;
- live provider/session adapters;
- final persistent runtime orchestrator;
- cross-laptop controller proof;
- controlled Windows/MT5 DEMO lifecycle/fault/restart certification;
- final release/docs audit based on actual evidence.

## Current deterministic evidence

Phase-11 backup tests cover portable state round-trip, event-history integrity, secret blocking, checkpoint tamper, no-overwrite restore, due/skip cadence, retention, catalog tamper, referenced-checkpoint tamper, latest verified selection and previous-known-good preservation after failed secret backup.

Current checkpoint: **202 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Governance conclusion

No major behavioural redesign item is known. Current work is primarily **remaining Phase-11 authenticated publication + real fresh-machine/broker reconciliation + shared-controller failover**, followed by runtime orchestration and controlled DEMO certification.
