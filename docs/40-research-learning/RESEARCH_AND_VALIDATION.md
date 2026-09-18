# GoldSwingTraderAI — Research and Validation

**Status:** PROVISIONAL — IMPLEMENTED FOUNDATION  
**Version:** 0.8-implementation  
**Authority:** Chronological replay, no-lookahead validation, dataset/evidence identity, holdouts, robustness/stress evidence, opportunity/entry/exit research metrics and evidence claims.  
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

## Dataset identity and evidence manifests — implemented foundation

`research/evidence.py` makes serious research results content-addressable and reproducible.

### Dataset identity

`identify_replay_dataset()` creates a deterministic `ReplayDatasetIdentity` from:

- source label and explicit source version;
- replay realism and spread assumption;
- complete broker symbol specification relevant to calculations;
- non-secret economic account context used by replay;
- every OHLC/volume/spread field in every replay candle;
- canonical timeframe ordering;
- per-timeframe bar count, first/last open time and SHA-256 content hash.

The full dataset receives `dataset_sha256`. Series tuple order is normalized so identical content does not acquire a different identity merely because timeframes were passed in a different order.

Account endpoint identifiers (`login`, `server`) are deliberately excluded from the replay dataset hash because they identify a broker endpoint rather than the economic replay context. Account mode/currency/balance/equity/margin/free-margin/leverage remain in the hashed account-context fingerprint where they can affect reproducibility.

Changing candle content, source version, spread assumption, symbol geometry or hashed account context changes the dataset identity.

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

`input_fingerprint_sha256` intentionally excludes generation time and result values. It answers: **are these the same experiment inputs?**

`manifest_sha256` covers the complete evidence record except its own hash field. It changes when results, generation time, limitations or other manifested facts change.

Canonical JSON serialization uses sorted keys and stable compact separators. Equivalent configuration mappings therefore produce the same input fingerprint regardless of dictionary insertion order.

### Secret boundary

Evidence manifests are intended to be safe for public recovery/audit artifacts under the project's minimum-hide policy. Configuration/result mappings reject financial-secret-shaped keys such as password, API key, access/refresh token, private/secret key, client secret and similar authority-bearing fields with `FINANCIAL_SECRET_DETECTED`.

This is an additional guard, not a replacement for repository financial-secret scanning.

### Evidence claim rule

A serious historical result should not be quoted without enough identity to reconstruct:

```text
code revision
+ policy version
+ dataset SHA-256/source version
+ explicit configuration/window definitions
+ realism/stress assumptions
+ results
+ limitations
```

A filename like `gold_2025.csv` by itself is not sufficient dataset identity.

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

The final holdout is one-shot for the locked candidate. If it fails, alternate candidates must not repeatedly use the same data while still calling it untouched. Consumed holdout identity/status is durable under the promotion registry. Walk-forward/evidence utilities cannot consume it automatically.

## Ablation / stability / stress

Confluence ablation compares identical chronology under BASE, TRENDLINE, FIBONACCI, DIRECTIONAL_COMBINED and ALL. Decision-only metrics do not invent P/L. Bracket and manager layers may add resolved modeled outcome evidence.

Stress and confluence ablation are separate axes: confluence changes optional analytical evidence; stress holds analytical decisions fixed and changes declared execution friction.

Walk-forward should span multiple chronological periods/regimes. If optimization is later introduced, its selection data and validation data must remain explicitly separated and all tuning choices reproducible.

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
- historical period/window identities;
- replay/outcome/stress realism;
- explicit stress assumptions;
- random seed where relevant;
- limitations.

The implemented evidence manifest provides the deterministic container for these facts; broader historical-data ingestion/export packaging is the next integration layer.

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
- stable dataset identity despite incidental timeframe tuple order;
- dataset hash changes when candle content changes;
- endpoint login/server exclusion from economic replay identity;
- reproducible input fingerprint across mapping insertion order/result time changes;
- full manifest hash changes when evidence record changes;
- canonical JSON serialization;
- financial-secret-shaped manifest-field rejection;
- actual/counterfactual isolation;
- discovery/promotion governance.

Current deterministic CI after evidence-manifest foundation: **168 tests PASS**, Ruff PASS and financial-secret scan PASS.

Still required for full research validation:

- real historical XAU dataset ingestion/versioning using these identities;
- broad regime-diverse datasets;
- persisted/exported evidence packages tied to code revisions;
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
- place financial-authority secrets inside evidence manifests;
- overstate historical evidence.

## Open questions

- exact real-data source(s), periods and sample requirements;
- exact development/validation window sizes and stepping;
- dataset ingestion/export format and retention policy;
- evidence-package directory/naming/publication convention;
- exact Opportunity Recall labeling method;
- historical PRE_CLOSE/session integration;
- empirical spread/slippage/modify-failure distributions;
- variable-spread/tick-order modeling where data supports it;
- Monte Carlo/bootstrap method;
- minimum robustness/stress/validation thresholds;
- exact promotion evidence thresholds;
- final optional-confluence retention threshold.
