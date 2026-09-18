# GoldSwingTraderAI — Research and Validation

**Status:** PROVISIONAL — IMPLEMENTED FOUNDATION  
**Version:** 1.1-implementation  
**Authority:** Chronological replay, no-lookahead validation, dataset/evidence identity, portable research datasets, historical acquisition, immutable evidence packaging, holdouts, robustness/stress evidence and research claims.  
**Depends on:** `../00-foundation/SYSTEM_CONTRACT.md`, `../10-market-intelligence/CANDLE_STRUCTURE.md`, `../20-trading-decisions/ENTRY_TIMING.md`, `../20-trading-decisions/TRADE_MANAGER_AND_EXIT.md`

## Purpose

Research must test the real documented trading semantics without future leakage, cherry-picking, untraceable datasets or exaggerated claims.

> **A positive backtest is evidence about a specified historical simulation, not proof of future profitability.**

## Current implementation checkpoint — Phase 10

Implemented owners include:

```text
research/replay.py
research/ablation.py
research/outcomes.py
research/management_replay.py
research/stress.py
research/validation.py
research/evidence.py
research/datasets.py
research/acquisition.py
research/packages.py
research/metrics.py
research/learning.py
research/episode_journal.py
research/discovery.py
research/invention.py
research/promotion.py
```

The foundation reuses production Intelligence, Decision, Trade Plan and Trade Manager semantics rather than a separate simplified backtest strategy.

Implemented deterministic infrastructure includes prefix-only replay, confluence ablation, ambiguity-safe Trade Plan/Trade Manager outcomes, declared execution stress, fixed-policy walk-forward, content-addressed dataset/evidence identity, portable datasets, read-only MT5 historical acquisition, immutable evidence packages, metrics/learning and governed discovery/invention/promotion.

This remains a **software/research foundation**, not completed market validation. Broad real XAU datasets, empirical calibration, sufficiently large validation, untouched holdout and DEMO forward evidence remain required before claiming edge.

## No-lookahead / replay boundary

Every fact becomes available only when it existed historically. Future bars may later label outcomes but never alter the original historical decision.

```text
historical facts at T
→ production decision/Trade Plan at T
→ freeze decision facts
→ only later bars may label outcome/management evidence
```

Same-bar stop/target ambiguity is preserved; unresolved/open cases stay outside resolved P/L.

## Trade Manager / stress / walk-forward

`research/management_replay.py` reuses production HOLD/PROTECT/TRAIL/RUNNER/EXIT logic after active barrier checks. Default manager realism is `BAR_CLOSE_IDEALIZED`.

`research/stress.py` holds analytical decisions fixed and can declare adverse entry, executable-side spread, completed-M5 modify delay and deterministic modify rejection. Structural stop/target/original R are not rewritten to improve results.

`research/validation.py` owns `FIXED_POLICY_WALK_FORWARD`: development history may reconstruct state but is not scored; validation slices do not overlap; outcomes are clipped at each validation end; no optimizer exists; final one-shot holdout authority stays separate.

## Dataset identity and evidence manifests

`research/evidence.py` creates content-addressed `ReplayDatasetIdentity` and `ResearchEvidenceManifest` records.

Dataset identity covers source label/version, replay realism/spread, calculation-relevant symbol geometry, economic replay account context and every candle OHLC/volume/spread field. Broker endpoint `login/server` are intentionally excluded.

Evidence manifests record code revision, policy version, dataset identity, normalized configuration/results, limitations, `input_fingerprint_sha256` and `manifest_sha256`. Financial-secret-shaped keys are rejected with `FINANCIAL_SECRET_DETECTED`.

## Portable replay dataset bundles

`research/datasets.py` owns public-safe offline input bundles:

```text
dataset_manifest.json
H4.csv
H1.csv
M15.csv
M5.csv
[optional supported timeframe CSVs such as M1.csv]
```

Bundles are write-new/immutable, contain all present series, exclude broker endpoint login/server, and verify manifest/file/bar-count/recomputed dataset identity on import. Canonical filenames are required and manifest/CSV symlinks are rejected.

## Read-only MT5 historical acquisition

`research/acquisition.py` reuses the existing `MT5Reader`; it does not create a second raw MetaTrader5 boundary.

Rules:

- H4/H1/M15/M5 requested counts mandatory; optional supported M1 may be requested;
- completed candles only through existing read boundary;
- actual history count must equal requested count or acquisition fails;
- default replay spread = median positive historical M5 `spread_points × point`;
- absent historical spread requires explicit non-negative override;
- current live spread is not used as hidden historical fallback;
- source label/version are explicit provenance;
- `acquire_and_export_mt5_bundle()` composes directly with the portable dataset writer;
- acquisition has zero broker-write/promotion authority.

Controlled Windows/MT5 evidence against real broker history remains pending.

## Immutable research evidence packages — implemented

`research/packages.py` persists a finished `ResearchEvidenceManifest` as an immutable integrity-checked directory without copying a potentially large historical dataset.

V1 package:

```text
package_manifest.json
evidence_manifest.json
```

`package_manifest.json` binds:

- package schema version;
- canonical evidence filename;
- evidence file SHA-256;
- evidence `manifest_sha256`;
- evidence `input_fingerprint_sha256`;
- evidence `dataset_sha256`;
- optional verified portable-dataset `manifest_sha256`.

Export rules:

- destination is write-new; existing evidence packages are never overwritten;
- canonical evidence JSON is written in a temporary sibling directory before rename;
- if a portable dataset bundle is supplied, it is fully verified first and its `dataset_sha256` must match the evidence dataset;
- large dataset bytes are **not duplicated** inside every evidence package.

Import rules:

- package manifest SHA-256 must match;
- canonical evidence filename and file SHA-256 must match;
- the evidence manifest's own internal `manifest_sha256` is recomputed;
- the evidence input fingerprint is recomputed from experiment-input fields;
- dataset/input/evidence identities must agree between the two manifests;
- an optional supplied dataset bundle is verified by dataset identity and, when recorded, bundle-manifest identity.

This gives stable pairing:

```text
dataset_sha256
↔ optional dataset bundle manifest SHA
↔ evidence input fingerprint
↔ evidence manifest SHA
↔ package SHA
```

The evidence package has no trading, risk, execution or promotion authority.

## Execution realism

```text
Decision replay          BAR_CLOSE
Initial bracket outcomes BAR_HIGH_LOW
Trade Manager replay     BAR_CLOSE_IDEALIZED + active barriers
Execution stress         BAR_CLOSE_EXECUTION_STRESS + declared assumptions
Walk-forward             FIXED_POLICY_WALK_FORWARD over declared replay layers
```

None is tick-perfect broker execution.

## Evidence chronology / final holdout

```text
DEVELOPMENT / SELECTION DATA
→ INDEPENDENT VALIDATION / WALK-FORWARD
→ LOCK ONE CANDIDATE
→ FINAL UNTOUCHED HOLDOUT
→ STRESS
→ SHADOW
→ DEMO CANARY
```

Walk-forward/evidence/package utilities cannot consume the final holdout automatically.

## Quality objective

Evaluate not only win rate but modeled Net/Average R, Profit Factor, drawdown, MFE/MAE, Capture Efficiency, giveback, action mix, 2R/3R/4R reach, Opportunity Recall, missed-opportunity rate, trade frequency and ambiguity/open coverage.

A feature that slightly raises accuracy by removing too many good opportunities is not automatically an improvement. Optional confluence exists to improve quality, not recreate filter soup.

## Reproducibility requirements

Serious evidence should identify code revision, policy version, configuration, dataset source/version/content hash, bundle manifest hash where applicable, evidence input/manifest/package hashes, historical windows, realism/stress assumptions and limitations. A mutable filename alone is insufficient.

## Tests / current evidence

Deterministic coverage includes no-lookahead replay, confluence ablation, ambiguity-safe outcomes, execution stress, walk-forward boundary isolation, dataset/evidence identity, portable dataset integrity, exact-count MT5 acquisition and immutable evidence package integrity.

Evidence-package tests prove:

- package round-trip with a verified dataset bundle;
- dataset binding without copying dataset bytes;
- mismatched dataset bundle rejection;
- evidence-file tamper detection;
- package-manifest tamper detection;
- no-overwrite destination policy.

Current deterministic CI after evidence-package coverage: **183 tests PASS**, Ruff PASS and financial-secret scan PASS.

Still required for full validation:

- controlled Windows/MT5 acquisition on real broker history;
- broad regime-diverse XAU datasets;
- actual real-data evidence packages and walk-forward reports;
- empirical execution-friction calibration;
- historical PRE_CLOSE/session integration;
- final untouched holdout;
- Shadow/DEMO forward evidence and replay-versus-DEMO comparison.

## Explicit non-goals

Research packaging must not duplicate large datasets unnecessarily, rely on mutable paths as identity, accept tampered evidence/data, export financial authority, mutate production, hide uncertainty or turn historical evidence into a profitability guarantee.

## Open questions

- controlled Windows/MT5 source/version convention and reliable history depth;
- real-data periods/sample requirements;
- higher-level publication/catalog convention for many evidence packages;
- walk-forward window sizes/stepping;
- historical PRE_CLOSE integration;
- empirical spread/slippage/modify-failure distributions;
- Monte Carlo/bootstrap method;
- minimum robustness/validation/promotion thresholds;
- final optional-confluence retention threshold.
