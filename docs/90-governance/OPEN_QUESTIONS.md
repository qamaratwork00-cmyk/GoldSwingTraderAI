# GoldSwingTraderAI — Open Questions / Freeze Matrix

**Status:** LIVING LEDGER  
**Version:** 2.9-design

This file separates remaining items so implementation is not delayed by values that should be learned from evidence or ordinary engineering choices.

```text
FIX BEFORE BUILD       = required architecture/safety decision still missing
CALIBRATE IN RESEARCH  = explicit deterministic baseline, tune only with chronological evidence
IMPLEMENTATION CHOICE  = coder may choose implementation preserving frozen contract
DEFER LATER            = not required for V1
```

At behavioural-contract level there are currently **no known `FIX BEFORE BUILD` items**.

## Current implementation status

Deterministic core exists through Phase 10 plus Phase-11 checkpoint foundation:

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
   + verified historical PRE_CLOSE/session replay
   + stress / fixed-policy walk-forward
   + dataset/evidence identity + portable datasets
   + read-only MT5 historical acquisition
   + immutable evidence packages
   + learning/discovery/invention/promotion
11 Portable runtime StateStore checkpoint/export/restore foundation
```

Live DEMO release and real-data validation are not complete. Final runtime orchestration, production shared cross-laptop coordination, automatic backup publication, real fresh-machine/broker drill, controlled Windows/MT5 evidence and DEMO certification remain pending.

## Frozen trading principles still in force

- completed candles own structural confirmation;
- Trendline/Fibonacci/POC are optional bonus-only confluence, not hard filters;
- six production strategy families remain parallel;
- credible target room `<1.20R` rejects current plan; 1.20–<1.50R conditional, 1.50–<2R good, 2R+ strong;
- no fixed-pip TP; Primary checkpoint / Expansion default target / evidence-earned Runner;
- SMALL is any positive day-start equity below `$300`; no `$100` floor;
- Gold capacity `0/1` independently risk-bearing position;
- daily/session/news/execution hard safety remains separate from soft scoring;
- verified connected DEMO is required for V1 broker-write permission.

## Research / learning / evidence — implemented foundation

Chronological replay, production manager outcomes, historical PRE_CLOSE software integration, execution stress, fixed-policy walk-forward, content-addressed datasets/evidence, portable research bundles, exact-count read-only MT5 acquisition, immutable evidence packages, learning/discovery/invention and governed promotion are implemented deterministically.

Still external/pending: controlled real XAU history, trustworthy historical broker-session coverage, broad validation, empirical friction calibration, final holdout, Shadow and DEMO forward evidence.

## Persistence / backup — Phase 11 foundation implemented

### Portable checkpoint format gap — CLOSED

`persistence/checkpoint.py` now owns:

```text
checkpoint_manifest.json
records.jsonl
events.jsonl
```

The checkpoint captures the authoritative `StateStore` current records plus append-only event history and binds:

```text
checkpoint schema version
+ StateStore database schema version
+ source label/version
+ UTC creation time
+ records file SHA/count
+ events file SHA/count
→ checkpoint_sha256
```

### StateStore snapshot gap — CLOSED

`StateStore` now:

- validates current record **and event** integrity;
- exports deterministic `StoreSnapshot` state;
- restores a verified snapshot only into an empty store;
- preserves record/event checksums, timestamps and event IDs;
- can checkpoint WAL before fresh-database handoff.

### Public-safe secret boundary — CLOSED for checkpoint software

`security/financial_secrets.py` centralizes financial-authority secret detection. Runtime checkpoint export/import applies structured payload scanning in addition to text scanning. Credential-shaped password/token/private/recovery-key fields hard-block with `FINANCIAL_SECRET_DETECTED`.

This does not hide ordinary strategy/research/learning state or non-authority account identifiers under the chosen minimum-hide policy.

### Fresh local DB restore — CLOSED at deterministic software level

Restore requires a non-existing destination database, restores through a temporary StateStore, verifies integrity, checkpoints WAL and atomically installs the result. The restore result explicitly requires broker reconciliation.

A checkpoint is recovery context only. It cannot grant execution authority or blindly replay stale OPEN/Intent state.

## Phase 11 still pending

### IMPLEMENTATION CHOICE

- automatic checkpoint cadence;
- backup retention count/age policy;
- public-safe checkpoint naming/catalog/index convention;
- automatic GitHub publication workflow for allowed checkpoints;
- last-known-good preservation policy on publication failure;
- integrated startup hook that selects/restores a checkpoint when explicitly requested.

### CONTROLLED EVIDENCE PENDING

- fresh-machine restore on another machine;
- current MT5 DEMO account/symbol verification after restore;
- restored unresolved Intent/open-trade reconciliation against current positions/orders/deals;
- old-backup + newer broker-truth conflict drill;
- shared cross-laptop controller/fencing backend and failover proof.

### DEFER UNTIL SCHEMA V2 EXISTS

- real migration/rollback transforms between schema versions. Current code correctly rejects unsupported versions; speculative v1→v2 migration code is not required before v2 exists.

## Frozen backup/security principles

- live SQLite DB is runtime state, not a Git merge artifact;
- portable checkpoints are canonical content, not raw DB copies;
- checkpoint export is write-new; failed export cannot overwrite a known-good checkpoint;
- restore never overwrites/merges an existing local DB;
- source and restored integrity must verify;
- financial-authority secrets never enter public/tracked checkpoints;
- exposure/order/position truth comes from broker after restore;
- restored laptop must obtain fresh controller authority before any broker write;
- two restored laptops cannot independently trade the same account.

## Still calibrate in research

- market-intelligence/scoring/timing/trailing thresholds;
- optional-confluence value and retention;
- real-data periods/sample sizes;
- walk-forward window sizes/stepping;
- stress severity and broker-friction distributions;
- promotion/Shadow/Canary thresholds;
- StrategyMemory and discovery similarity/recipe thresholds;
- Monte Carlo/block/regime-aware methodology.

## Operator / runtime / release pending

- authoritative dashboard runtime DTO + backup/recovery/Discovery Health display;
- live provider/session adapters;
- final persistent runtime orchestrator;
- cross-laptop controller proof;
- controlled Windows/MT5 DEMO lifecycle/fault/restart certification;
- final release/docs audit based on actual evidence.

## Current deterministic evidence

Portable runtime checkpoint foundation is covered by typed/generic state round-trip, event-history preservation, tamper detection, secret blocking, no-overwrite export/restore and event corruption tests.

Current checkpoint: **195 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Governance conclusion

No major behavioural redesign item is known. Current work is primarily **remaining Phase-11 backup automation/failover integration**, followed by real external evidence, runtime orchestration and controlled DEMO certification.
