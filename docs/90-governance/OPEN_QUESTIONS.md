# GoldSwingTraderAI — Open Questions / Freeze Matrix

**Status:** LIVING LEDGER  
**Version:** 2.8-design

This file separates remaining items so implementation is not delayed by values that should be learned from evidence or ordinary engineering choices.

```text
FIX BEFORE BUILD       = required architecture/safety decision still missing
CALIBRATE IN RESEARCH  = explicit deterministic baseline, tune only with chronological evidence
IMPLEMENTATION CHOICE  = coder may choose implementation preserving frozen contract
DEFER LATER            = not required for V1
```

At behavioural-contract level there are currently **no known `FIX BEFORE BUILD` items**.

## Current implementation status

Deterministic core exists through Phase 10 including:

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
   + verified historical PRE_CLOSE/session-policy replay integration
   + declared execution stress
   + fixed-policy walk-forward
   + dataset/evidence identity
   + portable research datasets
   + read-only MT5 historical acquisition
   + immutable evidence packages
   + metrics/learning/discovery/invention/promotion
```

Live DEMO release and real-data validation are not complete. Final runtime orchestration, production shared cross-laptop coordination, runtime-state backup/fresh-machine drill, controlled Windows/MT5 evidence and DEMO certification remain pending.

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

## Research / learning / evidence — implemented

- chronological Decision replay and confluence ablation;
- production Trade Plan/Trade Manager outcome replay;
- historical session schedule model with production PRE_CLOSE permission reuse;
- manager-replay PRE_CLOSE flatten integration;
- declared execution stress;
- fixed-policy walk-forward;
- content-addressed `ReplayDatasetIdentity`;
- portable dataset manifest + timeframe CSV bundles;
- read-only MT5 historical acquisition through existing `MT5Reader`;
- exact-count history checks and explicit historical-spread provenance;
- canonical `ResearchEvidenceManifest`;
- immutable evidence package persistence;
- metrics/StrategyMemory/research episode journal;
- discovery/invention liveness and governed promotion.

### Historical PRE_CLOSE/session software gap — CLOSED

`research/session_history.py` now requires named/versioned verified coverage plus explicit chronological tradeable intervals. It delegates DAILY/WEEKEND timing to production `evaluate_market_permission()`, so research does not maintain a second threshold table.

`research/management_replay.py` may consume this schedule and forwards mandatory flatten to the real Trade Manager. Outside verified schedule coverage or on a candle/schedule CLOSED contradiction, research fails explicitly rather than guessing.

What remains pending here is **external evidence**, not software semantics: a trustworthy historical broker-session source/version/coverage for the real XAU research periods.

### Evidence package software gap — CLOSED

`research/packages.py` stores:

```text
package_manifest.json
evidence_manifest.json
```

and binds:

```text
dataset_sha256
+ optional verified dataset_bundle_manifest_sha256
+ input_fingerprint_sha256
+ evidence manifest_sha256
+ evidence-file SHA-256
→ package_sha256
```

The package is write-new, verifies identities on import and deliberately does **not** duplicate large dataset bytes. Mutable paths are not authority.

### Frozen evidence principles

- no future leakage;
- no autonomous production promotion/hard-safety bypass;
- development context is not validation evidence;
- walk-forward cannot consume the one-shot final holdout;
- serious evidence identifies code/policy/content-addressed dataset/config/realism/limitations;
- partial historical data cannot silently shrink the declared sample;
- absent historical spread requires explicit handling rather than zero/current-live fallback;
- research acquisition reuses `MT5Reader`, never a second raw MT5 client;
- historical PRE_CLOSE parity requires explicit verified schedule facts; no guessed broker clock;
- portable datasets/evidence packages are trusted only after hash/content verification;
- existing immutable destinations are not silently overwritten;
- financial-authority secrets stay outside public/tracked evidence.

## Still pending — research/external evidence

- controlled Windows/MT5 real XAU history acquisition;
- source-label/source-version convention based on observed broker/history facts;
- reliable history-depth/terminal-limit evidence;
- trustworthy versioned historical broker-session schedule coverage for studied periods;
- broad regime-diverse XAU datasets and fixed-policy validation;
- empirical stress calibration;
- final untouched holdout, Shadow and DEMO forward evidence;
- higher-level catalog/index/publication convention across many immutable evidence packages.

## Still calibrate in research

- market-intelligence/scoring/timing/trailing thresholds;
- optional-confluence value and retention;
- real-data periods/sample sizes;
- walk-forward window sizes/stepping;
- stress severity and broker-friction distributions;
- promotion/Shadow/Canary thresholds;
- StrategyMemory and discovery similarity/recipe thresholds;
- Monte Carlo/block/regime-aware methodology.

## Persistence / backup — separate pending work

Runtime SQLite persistence is implemented. Portable **research data/evidence** is implemented. These do not replace Phase 11 runtime-state backup/recovery work.

Still pending:

- runtime checkpoint/export manifest;
- backup cadence/retention;
- public-safe automatic backup packaging;
- fresh-machine restore/reconciliation drill;
- future schema migration/rollback;
- production shared controller coordination backend.

## Operator / runtime / release pending

- authoritative dashboard runtime DTO + Discovery Health/confluence display;
- live provider/session adapters;
- final persistent runtime orchestrator;
- cross-laptop controller proof;
- controlled Windows/MT5 DEMO lifecycle/fault/restart certification;
- final release/docs audit based on actual evidence.

## Governance conclusion

No major behavioural redesign item is known. Current work is primarily **Phase 11 backup/recovery, real external evidence, runtime integration/failover and controlled certification**. Documents remain DRAFT/PROVISIONAL where real historical/live proof is incomplete.
