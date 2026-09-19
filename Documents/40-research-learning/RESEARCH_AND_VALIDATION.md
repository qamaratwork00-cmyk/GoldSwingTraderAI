# GoldSwingTraderAI — Research and Validation

**Status:** PROVISIONAL
**Version:** 0.1-research
**Authority:** Chronological replay, datasets, metrics, holdouts, stress and evidence packages

## Purpose

Research tests the documented system without future leakage, hidden assumptions
or untraceable datasets. A positive historical result is evidence about one
specified simulation, not a promise of future profit.

## Evidence pipeline

~~~mermaid
flowchart TB
    DATA["Verified portable dataset"] --> ID["Content identity and provenance"]
    ID --> REPLAY["Chronological production-semantics replay"]
    REPLAY --> METRICS["Outcomes, MFE/MAE, capture and ablation"]
    METRICS --> WFA["Fixed-policy validation and holdout"]
    WFA --> PACKAGE["Immutable evidence package"]
    PACKAGE --> GOVERN["Candidate/promotion review"]
~~~

Research may reuse production intelligence, decisions, Trade Plan and
management semantics. It cannot use broker-write authority.

## No-lookahead contract

~~~text
facts known at T
→ decision/plan at T
→ freeze decision facts
→ later bars label outcome only
~~~

Future pivots, later event revisions, later candle extremes and final-bar
hindsight cannot alter the earlier decision. Same-bar stop/target ambiguity
remains unresolved/open rather than being guessed.

## Replay realism

| Layer | Baseline |
|---|---|
| decision | completed-bar chronology |
| initial bracket | BAR_HIGH_LOW with declared ambiguity |
| Trade Manager | BAR_CLOSE_IDEALIZED plus active barriers |
| session | verified historical intervals when supplied |
| execution stress | declared spread, delay and rejection assumptions |
| walk-forward | fixed policy; no optimizer or final-holdout search |

Omitting a verified historical session schedule preserves basic replay only; it
must not be called historical PRE_CLOSE parity.

## Portable datasets

dataset bundle:

~~~text
dataset_manifest.json
H4.csv
H1.csv
M15.csv
M5.csv
optional supported series
~~~

Manifest identity covers source/version, symbol geometry, replay assumptions and
every OHLC/volume/spread field. Bundles are write-new, canonical and
secret-safe. Symlinks, wrong counts, tampered files and identity mismatches
fail import.

## MT5 historical acquisition

research/acquisition.py reuses MT5Reader and reads completed candles only.
Required H4/H1/M15/M5 counts must be exact. Historical M5 spread points are
preferred; an explicit non-negative override is required when absent. Current
live spread is never a hidden historical fallback.

Command:

~~~text
python scripts/acquire_mt5_dataset.py DATASET_BUNDLE
  --source-label <source>
  --source-version <version>
~~~

No broker write or promotion authority exists in acquisition.

## Evidence package

research/evidence.py and research/packages.py record code revision, policy
version, dataset identity, configuration, outcomes, limitations and hashes.
Package export is write-new; import recomputes all recorded identities. Large
dataset bytes are not copied into every package.

Walk-forward command:

~~~text
python scripts/run_walk_forward.py DATASET_BUNDLE EVIDENCE_PACKAGE
  --development-events 200
  --validation-events 50
  --step-events 50
  --horizon-m5-bars 96
  --code-revision <reviewed>
  --policy-version <version>
~~~

The command is reproducible evidence, not profitability or DEMO certification.

## Metrics

Review Net/Avg R, Profit Factor, max drawdown, MFE/MAE, Capture Efficiency,
giveback, entry efficiency, premature-exit cost, Opportunity Recall, missed
meaningful moves, trade frequency, 2R/3R/4R reach, PRE_CLOSE outcomes and
ambiguous/open coverage. Optional confluence is measured in ablation against
the base strategy; fewer trades is not automatically better.

## Source and tests

| Source | Role | Tests |
|---|---|---|
| research/replay.py | chronological decision replay | test_research_validation.py |
| research/management_replay.py | production management replay | test_management_replay.py |
| research/session_history.py | verified historical session intervals | test_research_session_history.py |
| research/stress.py | declared execution stress | test_research_stress.py |
| research/validation.py | fixed-policy walk-forward | test_research_validation.py |
| research/datasets.py, acquisition.py | portable data and MT5 acquisition | test_research_datasets.py, test_research_acquisition.py |
| research/evidence.py, packages.py | content-addressed evidence | test_research_evidence.py, test_research_packages.py |
| research/metrics.py, outcomes.py, ablation.py | metrics and counterfactual separation | test_research_outcomes.py, test_research_ablation.py |
| scripts/run_walk_forward.py | operator boundary | test_walk_forward_script.py |

## Explicit non-goals

Research must not guess session times, accept tampered inputs, copy credentials,
mutate production, use final holdout repeatedly or claim future profitability.

