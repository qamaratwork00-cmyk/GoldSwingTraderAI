# GoldSwingTraderAI — Research and Validation

**Status:** PROVISIONAL — IMPLEMENTED FOUNDATION  
**Version:** 0.9-implementation  
**Authority:** Chronological replay, no-lookahead validation, dataset/evidence identity, portable research datasets, holdouts, robustness/stress evidence, opportunity/entry/exit research metrics and evidence claims.  
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
- per-timeframe content hashes and dataset-level SHA-256 identity;
- reproducible research input fingerprints separated from result/time hashes;
- canonical public-serializable evidence manifests;
- rejection of financial-secret-shaped manifest fields;
- portable integrity-checked replay dataset bundles using canonical JSON + timeframe CSVs;
- round-trip preservation of optional supported timeframe series such as M1;
- broker endpoint login/server exclusion from portable research bundles;
- manifest, per-file and recomputed dataset identity verification on import;
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

Manager outcomes:

```text
PLAN_NOT_READY
STOP_FILLED
TARGET_FILLED
MANAGER_EXIT
BOTH_TOUCHED_AMBIGUOUS
HORIZON_OPEN
```

Default realism is `BAR_CLOSE_IDEALIZED`; this is not broker-certified P/L.

## Declared execution-stress model — implemented foundation

Research-only `ManagementReplayAssumptions` support:

```text
adverse_entry_slippage_r
barrier_spread_price
modify_delay_bars
reject_every_nth_modify
```

Adverse fill never moves structural stop/target or rewrites immutable original R. Positive barrier spread treats candle OHLC as a mid-price proxy with BUY exits on Bid and SELL exits on Ask. Pending synthetic modify state suppresses overlapping modify submissions. Same-bar stop+TP remains ambiguous.

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

Rules:

- development/validation event counts are explicit configuration;
- validation slices cannot overlap;
- development history may reconstruct production Opportunity state but is not scored;
- production policy/config stays fixed; no automatic parameter search;
- outcome/management dataset is truncated at validation end;
- later-window candles therefore cannot resolve an earlier validation trade;
- near-boundary trades may honestly remain `HORIZON_OPEN`;
- declared execution stress may be attached to validation evidence;
- walk-forward cannot consume or replace the governed one-shot final holdout.

Exact window sizes/sample requirements remain research-calibratable.

## Dataset identity and evidence manifests — implemented

`research/evidence.py` makes serious research results content-addressable and reproducible.

### Dataset identity

`identify_replay_dataset()` creates deterministic `ReplayDatasetIdentity` from source label/version, replay realism/spread, calculation-relevant symbol specification, economic replay account context and every candle OHLC/volume/spread field.

Each timeframe records bar count, first/last open UTC and SHA-256 content hash. The full dataset receives `dataset_sha256`. Series tuple order is normalized before hashing.

Broker endpoint identifiers (`login`, `server`) are deliberately excluded because they identify an account endpoint rather than replay economics. Account mode/currency/balance/equity/margin/free-margin/leverage remain in the hashed economic context.

### Evidence manifest

`build_research_evidence_manifest()` records:

```text
schema version
evidence kind
generation UTC time
code revision
policy version
ReplayDatasetIdentity
normalized configuration
normalized results
explicit limitations
input_fingerprint_sha256
manifest_sha256
```

`input_fingerprint_sha256` excludes generation time/result values and answers whether the experiment inputs are the same. `manifest_sha256` identifies the complete evidence record except its own hash field.

Configuration/result mappings reject authority-bearing secret-shaped keys with `FINANCIAL_SECRET_DETECTED`. This supplements, not replaces, repository secret scanning.

## Portable replay dataset bundles — implemented

`research/datasets.py` owns the inspectable offline research bundle format.

A V1 bundle is a directory containing:

```text
dataset_manifest.json
H4.csv
H1.csv
M15.csv
M5.csv
[optional supported timeframe CSVs, e.g. M1.csv]
```

The manifest includes:

- schema version;
- source label/version;
- `dataset_sha256`, symbol-spec hash and account-context hash;
- replay realism and spread assumption;
- calculation-relevant `SymbolSpec`;
- non-secret economic replay account context;
- one entry per exported timeframe containing canonical filename, bar count and file SHA-256;
- manifest SHA-256.

Export rules:

- destination must not already exist; an existing research bundle is never silently overwritten;
- files are first written into a temporary sibling directory and renamed only after successful completion;
- all dataset series are exported, not only the four minimum decision timeframes;
- broker endpoint `login` and `server` are not exported;
- UTF-8 CSV uses explicit chronological candle fields only.

Import rules:

- manifest checksum must match before dataset reconstruction;
- only known `Timeframe` values are accepted;
- required H4/H1/M15/M5 files must exist;
- optional supported timeframes such as M1 are preserved through round-trip;
- timeframe CSV filenames must be canonical and cannot contain paths;
- manifest/CSV symlinks are rejected;
- each CSV SHA-256 and declared bar count must match;
- reconstructed `ReplayDatasetIdentity` must match dataset/symbol/account hashes in the manifest;
- imported broker endpoint identity is neutral offline context (`login=1`, `server=RESEARCH_DATASET`) and is not treated as live account truth.

This bundle is for reproducible offline research and backup of public-safe historical inputs. It is **not** a credential/account export and has zero broker authority.

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

The final holdout is one-shot for the locked candidate. If it fails, alternate candidates must not repeatedly use the same data while still calling it untouched. Consumed holdout identity/status is durable under the promotion registry. Walk-forward/evidence/dataset utilities cannot consume it automatically.

## Ablation / stability / stress

Confluence ablation compares identical chronology under BASE, TRENDLINE, FIBONACCI, DIRECTIONAL_COMBINED and ALL. Decision-only metrics do not invent P/L. Bracket and manager layers may add resolved modeled outcome evidence.

Stress and confluence ablation are separate axes: confluence changes optional analytical evidence; stress holds analytical decisions fixed and changes declared execution friction.

A feature that slightly improves headline accuracy by eliminating too many good opportunities is not automatically an improvement. Evaluate Opportunity Recall and trade-frequency cost alongside quality and modeled economics.

## Core performance metrics

When realism supports them, report modeled/resolved trades, Net/Average R, Profit Factor, drawdown/loss streak, MFE/MAE, Capture Efficiency, giveback, action mix, 2R/3R/4R reach, Opportunity Recall, missed-opportunity rate, entry/exit efficiency, trade-frequency changes, ambiguity/open coverage, and per-window plus aggregate validation results without hiding failed windows.

Win rate alone is insufficient.

## Counterfactuals and attribution

Blocked/missed opportunities may receive post-hoc hypothetical MFE/MAE but remain counterfactual, never actual broker P/L. Outcome attribution should distinguish strategy quality, optional confluence, timing, Trade Plan, execution/slippage, management, news/shock, system fault and normal statistical loss.

## Versioning and reproducibility

Every serious evidence package should identify:

- code revision;
- strategy/policy version;
- configuration version/values;
- dataset source/version and content hash;
- portable bundle manifest hash when a bundle is used;
- historical period/window identities;
- replay/outcome/stress realism;
- explicit stress assumptions;
- random seed where relevant;
- limitations.

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
- confluence chronology and ablation;
- ambiguity-safe bracket and manager outcomes;
- immutable-R stress accounting;
- fixed-policy walk-forward chronology and validation-boundary clipping;
- stable content-addressed dataset/evidence identities;
- canonical evidence serialization and secret-shaped-field rejection;
- portable bundle round-trip identity;
- optional M1 series preservation;
- broker endpoint login/server exclusion from bundle manifest;
- CSV tamper detection;
- manifest tamper detection;
- immutable/no-overwrite export destination;
- actual/counterfactual isolation;
- discovery/promotion governance.

Current deterministic CI after portable-dataset bundle coverage: **173 tests PASS**, Ruff PASS and financial-secret scan PASS.

Still required for full research validation:

- authoritative real historical XAU acquisition/ingestion into this bundle contract;
- broad regime-diverse datasets;
- persisted result/evidence-package directory conventions tied to code revisions;
- empirical stress calibration from broker/DEMO evidence;
- historical PRE_CLOSE/session integration;
- sufficiently large walk-forward/independent validation;
- final untouched holdout;
- Shadow/DEMO forward evidence and replay-versus-DEMO comparison.

## Explicit non-goals

Research must not:

- directly send orders or silently mutate production;
- use walk-forward as hidden auto-tuning or as the final holdout;
- score development context as validation;
- leak later-window data backward;
- treat unresolved/counterfactual modeled results as broker P/L;
- favorably guess same-bar ordering;
- hide stress assumptions;
- rewrite structural geometry/original R to improve stressed results;
- identify datasets only by mutable filenames;
- export broker endpoint credentials/login/server as research dataset authority;
- silently overwrite an existing dataset bundle;
- accept a bundle whose file/manifest/content identity fails verification;
- overstate historical evidence.

## Open questions

- exact authoritative real-data source(s), periods and acquisition workflow;
- exact development/validation window sizes and stepping;
- evidence-package directory/naming/publication convention around dataset bundles;
- exact Opportunity Recall labeling method;
- historical PRE_CLOSE/session integration;
- empirical spread/slippage/modify-failure distributions;
- variable-spread/tick-order modeling where data supports it;
- Monte Carlo/bootstrap method;
- minimum robustness/stress/validation thresholds;
- exact promotion evidence thresholds;
- final optional-confluence retention threshold.
