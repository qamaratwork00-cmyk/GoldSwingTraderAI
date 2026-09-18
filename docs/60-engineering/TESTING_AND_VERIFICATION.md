# GoldSwingTraderAI — Testing and Verification

**Status:** PROVISIONAL  
**Version:** 1.1-design  
**Authority:** Test taxonomy, executable proof requirements, replay/live parity, research-evidence integrity, portable dataset integrity, crash/restart, migration, learning-governance and release verification.  
**Depends on:** `../90-governance/DOCUMENTATION_STANDARD.md`, `../40-research-learning/RESEARCH_AND_VALIDATION.md`, `../30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md`

## Purpose

Testing must prove documented invariants. `VERIFIED` is reserved for behaviour that actually passed required executable validation against the exact implementation.

> **Software verification and strategy validation are separate.**

## Test layers

```text
Unit / Contract Tests
→ Component Tests
→ Deterministic Replay Tests
→ Research Ablation / Outcome / Management / Stress / Walk-Forward / Evidence / Dataset Tests
→ Integration Tests
→ Fault / Crash Injection
→ Persistence / Migration Tests
→ Broker DEMO Tests
→ Learning / Discovery / Promotion Governance Tests
→ End-to-End DEMO Certification
```

## No-lookahead tests

Must prove future candles/facts cannot leak into structure, confluence, decisions, Trade Plans, manager actions or earlier walk-forward windows. A manager action affects only following bars. Post-hoc labels never feed back into the original decision. Validation outcome history is clipped at validation end.

Future-data leakage is release-blocking.

## Replay/live parity labels

```text
Decision replay          BAR_CLOSE
Initial bracket outcomes BAR_HIGH_LOW
Trade Manager replay     BAR_CLOSE_IDEALIZED + active barriers
Execution stress         BAR_CLOSE_EXECUTION_STRESS + declared assumptions
Walk-forward             FIXED_POLICY_WALK_FORWARD over declared replay layers
```

Do not claim tick/broker parity without sufficient historical/live evidence.

## Strategy / confluence / lifecycle tests

Cover valid and negative family fixtures, independent BUY/SELL theses, conflict, missing optional evidence, bounded correlation, one-strong-family opportunity creation, bonus-only Trendline/Fib/POC, causal anchors/history and production defaults ON.

Entry lifecycle covers WAIT preservation, MISSED versus INVALID, fresh second chance, stale duplicate rejection, episode re-entry limits and chase/drift defer semantics.

Trade Plan tests cover structural invalidation, volatility buffer, Stop Quality, RR guards, target roles, immutable original R and indivisible 0.01 management.

## Research outcome / manager tests

Initial Trade Plan outcome tests prove historical geometry reconstruction, symmetric BUY/SELL touch logic, immutable-R MFE/MAE, conservative same-bar ambiguity and unresolved-horizon isolation.

Trade Manager replay tests prove active stop/TP checks before new management, production HOLD/PROTECT/TRAIL/RUNNER/EXIT reuse, no retroactive modifications, runner transitions through production state, manager EXIT attribution and unresolved/ambiguous isolation from resolved metrics.

## Execution-stress tests

Prove one clean BASE, explicit scenario assumptions, executable-side spread approximation, immutable-R adverse fill, no structural stop/target rewrite, completed-M5 modify delay, pending-write suppression, deterministic rejection and signed deltas versus BASE.

Default probe values remain calibration baselines only:

```text
WIDER_SPREAD        1.50x dataset spread
ADVERSE_ENTRY       0.10R adverse fill
MODIFY_DELAY        1 completed M5
MODIFY_REJECTION    every 2nd submitted modify rejected
COMBINED            all four together
```

## Fixed-policy walk-forward tests

Prove windows are chronological, validation slices do not overlap, development context is not scored, outcome history is clipped at validation end, later windows cannot resolve earlier trades, optional stress does not reselect policy, no hidden tuning exists and final one-shot holdout authority remains separate.

Synthetic CI windows prove chronology/software only, not market edge.

## Research dataset/evidence identity tests

`research/evidence.py` must prove stable content-addressed dataset identity, timeframe-order normalization, content-change sensitivity, source/spread/symbol/economic-context representation, broker endpoint login/server exclusion, canonical evidence normalization, input/full-record hashing and `FINANCIAL_SECRET_DETECTED` rejection for authority-bearing secret-shaped fields.

The evidence-level secret check is defense in depth; CI financial-secret scan remains required separately.

## Portable research dataset bundle tests

`research/datasets.py` must prove:

- export → import round-trip preserves `dataset_sha256`;
- H4/H1/M15/M5 are mandatory for replay bundles;
- optional supported series such as M1 survive round-trip rather than disappearing;
- broker endpoint login/server are absent from the bundle manifest;
- imported endpoint identity is neutral offline research context, not a live account identity;
- existing destination directories are never silently overwritten;
- manifest SHA-256 mismatch fails import;
- CSV SHA-256 mismatch fails before candle data is trusted;
- declared bar count must match actual CSV rows;
- unknown timeframe keys fail;
- canonical `<TIMEFRAME>.csv` filenames are required;
- manifest/CSV symlink inputs fail;
- recomputed dataset/symbol/account hashes must match the manifest before the reconstructed dataset is exposed.

Portable bundle integrity is software evidence only; it does not prove the external source data was truthful. Source provenance/version remains part of research evidence.

## Risk / execution / controller / session tests

Risk covers SMALL/MEDIUM/NORMAL boundaries, any positive equity below $300 as SMALL, min-lot actual-risk evaluation, 0/1 capacity, external ownership, margin authority, UTC risk day, cash-flow-adjusted AccountSafetyPL, floating drawdown, daily lock/reset/cooldown/episode persistence and unknown-state fail-closed behaviour.

Execution covers verified DEMO guard, centralized gate, spread/drift, exactly-one-send Intent semantics, ambiguous ACK reconciliation, manual/foreign exposure and modify/close ambiguity.

Controller tests prove one PRIMARY, observer standby, lease/epoch freshness, stale-epoch denial, uncertainty blocking and safe takeover. Cross-machine certification requires a real shared atomic backend.

Session/news tests cover Tier windows, required truth failure, post-news warmup, daily/weekend PRE_CLOSE timing, verified schedule, reopen clean-M5 rules and ambiguous-close reconciliation.

## Crash / persistence / migration / restore tests

Fault injection covers intent/send/fill/modify/close/PRE_CLOSE/daily-lock/controller/atomic-write boundaries. Recovery must never duplicate exposure.

Persistence tests cover checksum/schema/truncation failure, atomic interruption, Opportunity/TradePlan/original-R/risk state, unresolved intents and research/candidate/promotion state.

Fresh-machine restore must preserve important durable strategy/research/trading context while excluding financial-authority secrets and reconciling broker truth.

## Dashboard / learning / discovery / promotion tests

Dashboard remains presentation-only. Learning is bounded/context-isolated. Discovery accepts audited primitives only and enforces candidate-or-suppression liveness. Promotion enforces stage order, locked fingerprint, one-shot holdout, Shadow/Canary authority boundaries, explicit promotion approval and rollback.

## Public repository secret scanning

Before public backup/release scan for actual financial-authority secrets. If one was exposed publicly, revoke/rotate it; deletion alone is insufficient.

Evidence manifests also reject secret-shaped keys, but this does not replace repository scanning.

## CI versus controlled DEMO

Public CI runs credential-free software/replay/research/governance/security checks. Actual MT5 DEMO execution/cross-machine tests require a controlled environment with credentials outside the repository.

## Evidence reporting

Example:

```text
Unit                       PASS / count
Replay chronology           PASS / count
Confluence ablation         PASS / count
Bracket outcome model       PASS / count / coverage
Trade Manager replay        PASS / count / realism
Execution stress            PASS / scenarios / assumptions
Walk-forward chronology     PASS / windows / validation events
Dataset identity            PASS / dataset_sha256
Portable dataset bundle     PASS / manifest + file hashes
Evidence manifest integrity PASS / input + manifest hashes
Independent real-data run   PENDING/PASS
Execution gate              PASS / count
Controller/failover         PASS / count
Fresh-machine restore       PENDING/PASS
DEMO execution              PENDING/PASS
Long forward sample         PENDING/PASS
```

Do not mark pending evidence as PASS or convert unresolved modeled outcomes into resolved P/L.

Current deterministic checkpoint after portable research dataset bundles: **173 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Release-blocking failures

At minimum:

- future-data leakage;
- walk-forward development counted as validation or later-window leakage;
- validation/final-holdout governance bypass;
- dataset identity not changing when replay-relevant content changes;
- portable dataset import accepting tampered manifest/file/content identity;
- portable research export leaking broker endpoint identity or authority-bearing secrets;
- evidence manifest silently accepting authority-bearing secret-shaped fields;
- evidence/result reported without reproducible dataset/config/code identity when release evidence requires it;
- centralized execution/DEMO guard bypass;
- duplicate/wrong-account broker write;
- unknown exposure treated as zero;
- controller split-brain/stale epoch;
- daily-loss/original-R corruption;
- critical restart-state loss or false-flat PRE_CLOSE state;
- recovery restore failure;
- financial credential leakage;
- autonomous self-promotion/broker bypass;
- silent eligible-discovery loss;
- optional confluence acting as hidden hard gate;
- favorable same-bar guessing;
- retroactive management modification;
- stress model rewriting structural geometry/original R;
- hidden stress assumptions presented as broker fact.

## Explicit non-goals

Testing must not claim profitability from software correctness, mark docs VERIFIED because Markdown is complete, hide pending evidence, present synthetic fixtures as market proof, or replace required real historical/DEMO evidence with mocks.

## Open questions

- final CI coverage/static/security thresholds;
- authoritative real historical XAU acquisition/import test matrix;
- evidence package persistence/directory/publication tests;
- real-data walk-forward window/sample requirements;
- historical PRE_CLOSE/session integration;
- empirical execution-friction calibration;
- final controlled DEMO certification steps;
- long-duration forward-evidence requirement;
- optional-confluence evidence threshold.
