# GoldSwingTraderAI — Research and Validation

**Status:** PROVISIONAL — IMPLEMENTED FOUNDATION  
**Version:** 1.0-implementation  
**Authority:** Chronological replay, no-lookahead validation, dataset/evidence identity, portable research datasets, historical acquisition, holdouts, robustness/stress evidence, opportunity/entry/exit research metrics and evidence claims.  
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
research/metrics.py
research/learning.py
research/episode_journal.py
research/discovery.py
research/invention.py
research/promotion.py
```

The research foundation is chronological completed-bar research reusing production Intelligence, Decision, Trade Plan and Trade Manager semantics rather than a separate simplified backtest strategy.

Current deterministic infrastructure supports:

- prefix-only/no-lookahead analytical replay;
- same-chronology confluence ablation;
- production Trade Plan reconstruction and ambiguity-safe bracket outcomes;
- chronological production Trade Manager replay;
- declared execution-friction stress;
- fixed-policy walk-forward validation with non-overlapping scored validation slices;
- content-addressed replay-dataset identity;
- reproducible evidence manifests and input fingerprints;
- portable integrity-checked replay dataset bundles using canonical JSON + timeframe CSVs;
- read-only MT5 historical acquisition through the existing production `MT5Reader`;
- exact requested completed-candle counts, including optional supported timeframes such as M1;
- explicit historical-spread provenance rather than hidden zero/live-spread assumptions;
- direct acquisition → portable bundle export;
- decision/bracket/management metrics, learning, discovery/invention and governed promotion state.

This remains a **software/research foundation**, not completed market validation. Broad real XAU datasets, empirical stress calibration, sufficiently large validation, untouched holdout and DEMO forward evidence remain required before claiming edge.

## Replay principle

Where parity is claimed, historical replay reuses the same core market-intelligence, strategy, timing, planning and management semantics as live operation, with different data/execution adapters only where necessary.

A simplified `backtest strategy` whose rules materially differ from production is prohibited.

## Chronology and no-lookahead

Every fact becomes available only when it existed historically. Confirmed swings use `confirmed_at`; BOS/MSS/FVG/OB/sweep/confluence/session facts cannot leak future candles; future bars may later label outcomes but never alter the original decision.

## Event-driven replay

```text
new completed candle/event
→ update prefix-only snapshot
→ run production analytical semantics
→ build production Trade Plan when ENTER is reached
→ model active stop/TP on later bars
→ run production Trade Manager only after each surviving bar completes
→ apply only the declared execution model's state transition
→ advance time
```

## Outcome-labeling boundary

```text
historical information available at T
→ production decision at T
→ production Trade Plan reconstructed at T
→ freeze decision/plan facts
→ inspect only later candles for outcome/management research
```

Initial bracket vocabulary:

```text
TARGET_FIRST
STOP_FIRST
BOTH_TOUCHED_AMBIGUOUS
HORIZON_UNRESOLVED
```

Ambiguous/unresolved cases stay outside resolved bracket P/L.

## Trade Manager replay — implemented

`research/management_replay.py` reuses production `evaluate_trade_manager()` and `apply_management_decision()`.

Each later M5 first checks the currently active stop/TP. If neither closes the modeled trade, the bar completes, fresh chronological intelligence is built and production HOLD/PROTECT/TRAIL/RUNNER/EXIT logic may affect the following bar.

Default realism is `BAR_CLOSE_IDEALIZED`; this is not broker-certified P/L.

## Declared execution-stress model — implemented foundation

Research-only `ManagementReplayAssumptions` support adverse entry slippage, executable-side spread approximation, completed-M5 modify delay and deterministic modify rejection. Adverse fill never moves structural stop/target or rewrites immutable original R. Same-bar stop+TP remains ambiguous.

Default transparent V1 calibration probes:

```text
BASE                no added friction
WIDER_SPREAD        1.50x dataset spread
ADVERSE_ENTRY       0.10R adverse fill
MODIFY_DELAY        1 completed M5
MODIFY_REJECTION    every 2nd submitted modify rejected
COMBINED            all four together
```

These are calibration baselines only, not frozen broker assumptions or production safety thresholds.

## Fixed-policy walk-forward validation — implemented scaffold

`research/validation.py` owns `FIXED_POLICY_WALK_FORWARD`.

```text
DEVELOPMENT CONTEXT
→ immediately later VALIDATION SLICE
```

Development history may reconstruct Opportunity state but is not scored. Validation slices cannot overlap, policy/config stays fixed, outcome history is clipped at each validation end, later windows cannot resolve earlier trades, and walk-forward cannot consume the governed one-shot final holdout.

Exact window sizes/sample requirements remain research-calibratable.

## Dataset identity and evidence manifests — implemented

`research/evidence.py` creates deterministic content-addressed dataset/evidence identities.

`ReplayDatasetIdentity` includes source label/version, replay realism/spread, calculation-relevant symbol specification, economic replay account context and every candle OHLC/volume/spread field. Each timeframe records bar count, first/last open UTC and SHA-256 content hash. Series tuple order is normalized before hashing.

Broker endpoint `login/server` are deliberately excluded from replay-economic identity. Account mode/currency/balance/equity/margin/free-margin/leverage remain part of the hashed economic context.

`ResearchEvidenceManifest` records code revision, policy version, dataset identity, normalized configuration/results, limitations, experiment-input fingerprint and full manifest SHA-256. Financial-secret-shaped config/result keys are rejected with `FINANCIAL_SECRET_DETECTED`.

## Portable replay dataset bundles — implemented

`research/datasets.py` owns the inspectable offline research bundle format:

```text
dataset_manifest.json
H4.csv
H1.csv
M15.csv
M5.csv
[optional supported timeframe CSVs, e.g. M1.csv]
```

Rules:

- destination is write-new/immutable; existing bundles are never silently overwritten;
- all series present in the dataset are exported;
- login/server are not exported;
- manifest and each CSV have SHA-256 integrity evidence;
- required H4/H1/M15/M5 must exist;
- optional supported timeframes such as M1 survive round-trip;
- canonical timeframe filenames are required and manifest/CSV symlinks are rejected;
- declared bar counts must match parsed rows;
- reconstructed dataset/symbol/account hashes must match before the dataset is exposed;
- imported endpoint identity is neutral offline `login=1`, `server=RESEARCH_DATASET` context.

This bundle is public-safe research input, not a live account/credential backup and has zero broker authority.

## Read-only MT5 historical acquisition — implemented software adapter

`research/acquisition.py` bridges the existing production `MT5Reader` into the portable replay-dataset contract without creating a second MT5 client or any broker-write path.

Flow:

```text
initialized MT5Reader
→ resolve configured Gold symbol/alias
→ read AccountFacts + SymbolSpec
→ request exact completed-candle counts per declared timeframe
→ verify actual count == requested count
→ derive declared historical replay spread
→ build ReplayDataset
→ optionally export immediately through research/datasets.py
```

Rules:

- H4/H1/M15/M5 counts are mandatory in `HistoricalAcquisitionRequest`;
- optional supported timeframes such as M1 may be requested;
- only `MT5Reader.completed_candles()` is reused, so bar position 0/forming candle remains excluded by the existing read boundary;
- partial history is **not silently accepted**: if MT5 returns fewer bars than requested, acquisition fails with `HistoricalAcquisitionError`;
- default constant replay spread is the median of positive historical M5 `spread_points × SymbolSpec.point` values;
- if historical M5 spread points are unavailable, acquisition fails unless an explicit non-negative `spread_price_override` is supplied;
- live current spread is not silently substituted for missing historical spread;
- source label/version are explicit caller-provided research provenance;
- `acquire_and_export_mt5_bundle()` composes acquisition with the integrity-checked portable bundle writer;
- acquisition is read-only and has zero execution/promotion authority.

The software adapter is implemented and deterministic-tested. **Controlled Windows/MT5 evidence using real broker history is still pending** and is required before claiming the external data source/version or available history depth is verified.

## Execution realism

Current layers:

```text
Decision replay          BAR_CLOSE
Initial bracket outcomes BAR_HIGH_LOW
Trade Manager replay     BAR_CLOSE_IDEALIZED + active barriers
Execution stress         BAR_CLOSE_EXECUTION_STRESS + declared assumptions
Walk-forward             FIXED_POLICY_WALK_FORWARD over declared replay layers
```

None is tick-perfect broker execution.

## Evidence chronology

```text
DEVELOPMENT / SELECTION DATA
→ INDEPENDENT VALIDATION / WALK-FORWARD
→ LOCK ONE CANDIDATE
→ FINAL UNTOUCHED HOLDOUT
→ STRESS
→ SHADOW
→ DEMO CANARY
```

Walk-forward is repeatable chronological validation evidence; it is not the final untouched holdout.

## Final holdout rule

The final holdout is one-shot for the locked candidate. Walk-forward/evidence/dataset/acquisition utilities cannot consume it automatically.

## Ablation / stability / stress

Confluence ablation compares identical chronology under BASE, TRENDLINE, FIBONACCI, DIRECTIONAL_COMBINED and ALL. Stress and confluence ablation are separate axes. A feature that slightly improves headline accuracy by eliminating too many good opportunities is not automatically an improvement; Opportunity Recall and trade-frequency cost remain first-class evidence.

## Core performance metrics

When realism supports them, report modeled/resolved trades, Net/Average R, Profit Factor, drawdown/loss streak, MFE/MAE, Capture Efficiency, giveback, action mix, 2R/3R/4R reach, Opportunity Recall, missed-opportunity rate, entry/exit efficiency, trade-frequency changes, ambiguity/open coverage, and per-window plus aggregate validation results without hiding failed windows.

Win rate alone is insufficient.

## Versioning and reproducibility

Every serious evidence package should identify code revision, strategy/policy version, configuration, dataset source/version/content hash, portable bundle manifest hash when used, historical window identities, replay/stress realism, explicit assumptions and limitations.

A mutable filename such as `gold_2025.csv` is not sufficient evidence identity.

## Evidence claims

Use precise language such as:

- `positive on specified historical replay`;
- `resolved initial-bracket evidence under BAR_HIGH_LOW model`;
- `resolved management evidence under BAR_CLOSE_IDEALIZED model`;
- `execution-stress result under declared scenario assumptions`;
- `fixed-policy walk-forward result on declared validation windows`;
- `passed final untouched holdout`;
- `positive DEMO forward evidence`.

Do not claim `proven profitable` from historical results alone.

## Tests / current evidence

Deterministic coverage includes:

- chronological/no-lookahead replay;
- confluence chronology/ablation;
- ambiguity-safe bracket/manager outcomes;
- immutable-R stress accounting;
- fixed-policy walk-forward boundaries;
- content-addressed dataset/evidence identities;
- portable bundle round-trip/tamper detection and optional M1 preservation;
- exact-count read-only historical acquisition;
- historical M5 median-spread derivation;
- explicit spread override when history lacks spread fields;
- incomplete-history rejection;
- acquisition → bundle → verified re-import;
- actual/counterfactual isolation;
- discovery/promotion governance.

Current deterministic CI after MT5 historical-acquisition coverage: **178 tests PASS**, Ruff PASS and financial-secret scan PASS.

Still required for full research validation:

- controlled Windows/MT5 acquisition against real broker history and documented source/version convention;
- broad regime-diverse XAU datasets;
- persisted result/evidence-package directory convention tied to code revisions;
- empirical stress calibration from broker/DEMO evidence;
- historical PRE_CLOSE/session integration;
- sufficiently large walk-forward/independent validation;
- final untouched holdout;
- Shadow/DEMO forward evidence and replay-versus-DEMO comparison.

## Explicit non-goals

Research must not directly send orders, silently mutate production, use walk-forward as hidden auto-tuning/final holdout, leak later-window data backward, favorably guess same-bar ordering, rewrite original R under stress, silently accept partial MT5 history, silently invent zero/live spread when historical spread is unavailable, export broker endpoint identity as research authority, accept tampered bundles or overstate historical evidence.

## Open questions

- exact controlled Windows/MT5 source/version naming convention and maximum reliable history depth;
- exact real-data periods/sample requirements;
- development/validation window sizes and stepping;
- evidence-package directory/naming/publication convention around dataset bundles;
- historical PRE_CLOSE/session integration;
- empirical spread/slippage/modify-failure distributions;
- variable-spread/tick-order modeling where data supports it;
- Monte Carlo/bootstrap method;
- minimum robustness/stress/validation thresholds;
- promotion evidence thresholds;
- final optional-confluence retention threshold.
