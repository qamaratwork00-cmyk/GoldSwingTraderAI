# GoldSwingTraderAI — Testing and Verification

**Status:** PROVISIONAL  
**Version:** 1.2-design  
**Authority:** Test taxonomy, executable proof requirements, replay/live parity, research-evidence/data integrity, crash/restart, migration, learning-governance and release verification.  
**Depends on:** `../90-governance/DOCUMENTATION_STANDARD.md`, `../40-research-learning/RESEARCH_AND_VALIDATION.md`, `../30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md`

## Purpose

Testing must prove documented invariants. `VERIFIED` is reserved for behaviour that actually passed required executable validation against the exact implementation.

> **Software verification and strategy validation are separate.**

## Test layers

```text
Unit / Contract Tests
→ Component Tests
→ Deterministic Replay Tests
→ Research Ablation / Outcome / Management / Stress / Walk-Forward / Evidence / Dataset / Acquisition Tests
→ Integration Tests
→ Fault / Crash Injection
→ Persistence / Migration Tests
→ Broker DEMO Tests
→ Learning / Discovery / Promotion Governance Tests
→ End-to-End DEMO Certification
```

## No-lookahead tests

Future candles/facts cannot leak into structure, confluence, decisions, Trade Plans, manager actions or earlier validation windows. MT5 research acquisition must use the existing completed-candle reader boundary and never include forming bar position 0 through a duplicate adapter.

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

Cover family fixtures, independent BUY/SELL theses, conflict, missing optional evidence, bounded correlation, one-strong-family opportunity creation, bonus-only Trendline/Fib/POC and entry WAIT/MISSED/INVALID lifecycle.

Trade Plan tests cover structural invalidation, volatility buffer, Stop Quality, RR guards, target roles, immutable original R and indivisible 0.01 management.

## Research replay / stress / validation tests

Initial outcomes preserve BUY/SELL symmetry and same-bar ambiguity. Trade Manager replay reuses production HOLD/PROTECT/TRAIL/RUNNER/EXIT, checks active barriers before new management and never applies a modification retroactively.

Execution stress proves immutable-R adverse fill, declared spread, modify delay/rejection and signed deltas without changing production policy.

Walk-forward proves non-overlapping validation slices, development-not-scored, validation-boundary clipping, no hidden tuning and no final-holdout consumption.

## Research dataset/evidence identity tests

`research/evidence.py` must prove stable content-addressed dataset identity, timeframe-order normalization, content-change sensitivity, replay assumption/symbol/economic-context representation, broker endpoint login/server exclusion, canonical evidence normalization, input/full-record hashing and financial-secret-shaped field rejection.

## Portable research dataset bundle tests

`research/datasets.py` must prove:

- export/import preserves dataset identity;
- H4/H1/M15/M5 are mandatory;
- optional supported M1 survives round-trip;
- login/server are absent from bundle research context;
- existing destination is never overwritten;
- manifest/CSV SHA-256 mismatch fails;
- bar count mismatch fails;
- unknown timeframe/canonical filename/symlink violations fail;
- recomputed dataset/symbol/account identity must match before exposure.

## Read-only MT5 historical acquisition tests

`research/acquisition.py` must prove:

- it consumes the existing `MT5Reader` interface rather than creating a second raw MetaTrader5 boundary;
- H4/H1/M15/M5 positive requested counts are mandatory;
- optional supported timeframes such as M1 can be requested;
- every requested timeframe is read through `completed_candles()`;
- returned history must match the exact requested count; partial history fails instead of silently reducing the sample;
- default replay spread is derived from median positive historical M5 `spread_points × SymbolSpec.point`;
- all-zero/missing M5 historical spread data fails unless an explicit spread override is supplied;
- explicit spread override is non-negative and its provenance is visible as `EXPLICIT_OVERRIDE`;
- current live quote spread is never silently substituted for historical spread;
- source label/version are required provenance;
- acquire → portable bundle → verified import preserves content identity;
- acquisition code has no broker-write/execution/promotion authority.

Deterministic FakeReader tests prove software contracts only. Controlled Windows/MT5 evidence is separately required to verify broker history availability and source/version assumptions.

## Risk / execution / controller / session tests

Risk covers SMALL/MEDIUM/NORMAL, any positive equity below $300 as SMALL, min-lot actual-risk evaluation, 0/1 capacity, external ownership, margin authority, UTC risk day, cash-flow-adjusted AccountSafetyPL, daily lock/reset/cooldown and unknown-state fail-closed behaviour.

Execution covers positive DEMO guard, centralized gate, spread/drift, exactly-one-send Intent semantics and reconciliation. Cross-machine controller certification requires a real shared atomic backend.

Session/news tests cover Tier windows, required truth failure, PRE_CLOSE/reopen rules and ambiguous-close reconciliation.

## Crash / persistence / restore tests

Fault injection covers intent/send/fill/modify/close/PRE_CLOSE/daily-lock/controller/atomic-write boundaries. Persistence covers checksum/schema failure and all critical runtime/research state. Fresh-machine restore must exclude financial-authority secrets and reconcile broker truth.

## Dashboard / learning / discovery / promotion tests

Dashboard is presentation-only. Learning is bounded/context-isolated. Discovery accepts audited primitives and enforces candidate-or-suppression liveness. Promotion enforces stage order, locked fingerprint, one-shot holdout, explicit approval and rollback.

## Public repository secret scanning

Repository financial-secret scan remains mandatory. Evidence/bundle sanitization does not replace it.

## CI versus controlled broker evidence

Public CI runs credential-free software/replay/research/governance/security checks. Actual Windows MT5 acquisition and broker execution require controlled environment evidence with credentials outside the repository.

## Evidence reporting

```text
Unit                       PASS / count
Replay chronology           PASS / count
Trade Manager replay        PASS / count / realism
Execution stress            PASS / scenarios
Walk-forward chronology     PASS / windows
Dataset identity            PASS / dataset_sha256
Portable dataset bundle     PASS / manifest + file hashes
MT5 acquisition software    PASS / exact-count + spread provenance
Windows MT5 real-history    PENDING/PASS
Evidence manifest integrity PASS / hashes
Fresh-machine restore       PENDING/PASS
DEMO execution              PENDING/PASS
```

Do not mark pending evidence as PASS.

Current deterministic checkpoint after historical acquisition adapter: **178 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Release-blocking failures

At minimum:

- future-data leakage;
- hidden validation tuning/final-holdout bypass;
- dataset identity/tamper verification failure;
- historical acquisition silently accepting fewer bars than declared;
- historical acquisition inventing zero/current-live spread when historical spread is unavailable;
- duplicate raw MT5 acquisition client that bypasses completed-candle semantics;
- evidence/bundle leaking authority-bearing secrets;
- centralized execution/DEMO guard bypass;
- duplicate/wrong-account broker write;
- unknown exposure treated as zero;
- controller split-brain/stale epoch;
- daily-loss/original-R corruption;
- critical restart-state loss;
- autonomous self-promotion/broker bypass;
- optional confluence acting as hidden hard gate;
- favorable same-bar guessing;
- stress model rewriting structural geometry/original R.

## Explicit non-goals

Testing must not claim profitability from software correctness, mark docs VERIFIED because Markdown is complete, present FakeReader/synthetic fixtures as real broker-history proof, or replace required real historical/DEMO evidence with mocks.

## Open questions

- final CI coverage/static/security thresholds;
- controlled Windows/MT5 historical acquisition test matrix/source-version convention;
- evidence-package persistence/directory/publication tests;
- real-data walk-forward window/sample requirements;
- historical PRE_CLOSE/session integration;
- empirical execution-friction calibration;
- final controlled DEMO certification steps;
- long-duration forward-evidence requirement;
- optional-confluence evidence threshold.
