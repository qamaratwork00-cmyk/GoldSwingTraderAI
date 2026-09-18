# GoldSwingTraderAI — Testing and Verification

**Status:** PROVISIONAL  
**Version:** 1.4-design  
**Authority:** Test taxonomy, executable proof requirements, replay/live parity, research data/evidence integrity, historical session-policy replay, crash/restart, migration, learning-governance and release verification.  
**Depends on:** `../90-governance/DOCUMENTATION_STANDARD.md`, `../40-research-learning/RESEARCH_AND_VALIDATION.md`, `../30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md`

## Purpose

Testing must prove documented invariants. `VERIFIED` is reserved for behaviour that actually passed required executable validation against the exact implementation.

> **Software verification and strategy validation are separate.**

## Test layers

```text
Unit / Contract
→ Component
→ Deterministic Replay
→ Research Ablation / Outcomes / Manager / Historical Session / Stress / Walk-Forward
→ Dataset / Acquisition / Evidence / Package Integrity
→ Integration / Fault Injection / Persistence
→ Controlled Windows MT5 / DEMO
→ Learning / Discovery / Promotion Governance
→ End-to-End DEMO Certification
```

## No-lookahead / strategy / lifecycle

Future data cannot leak into structure, confluence, decisions, Trade Plans, manager actions or earlier validation windows. Optional Trendline/Fib/POC remains bonus-only. WAIT/MISSED/INVALID, re-entry limits and immutable original-R semantics remain regression protected.

## Research replay / stress / validation

Tests preserve same-bar ambiguity, production Trade Manager reuse, non-retroactive modifications, explicit friction assumptions, fixed-policy walk-forward boundaries, development-not-scored and final-holdout separation.

## Historical session / PRE_CLOSE replay

`research/session_history.py` and session-aware `research/management_replay.py` must prove:

- historical schedules require explicit source label/version and UTC verified coverage;
- trading intervals are chronological, non-overlapping and inside coverage;
- no default/guessed broker close time exists;
- DAILY no-entry/flatten behaviour comes from production `evaluate_market_permission()` and remains `T-20/T-10`;
- WEEKEND behaviour remains `T-60/T-30` through the same production authority;
- time inside verified coverage but outside a tradeable interval is CLOSED;
- time outside verified coverage raises `HistoricalSessionCoverageError` rather than assuming OPEN/CLOSED;
- close instant belongs to the closed side;
- session-aware manager replay passes production mandatory PRE_CLOSE flatten into `evaluate_trade_manager()`;
- a verified T-5 DAILY replay event can produce manager `PRE_CLOSE_FLATTEN` exit;
- replay candle/session schedule contradictions fail explicitly instead of silently treating CLOSED time as normal trading;
- replay without a schedule preserves baseline behaviour but cannot be reported as historical PRE_CLOSE parity.

Synthetic schedules prove software semantics only. They are not evidence that a real broker used those times historically.

## Dataset / evidence identity

`research/evidence.py` tests stable content-addressed identities, timeframe-order normalization, content-change sensitivity, source/spread/symbol/economic-context representation, login/server exclusion, canonical mapping normalization, input/full-record hashes and secret-shaped-field rejection.

## Portable dataset bundles

`research/datasets.py` tests round-trip identity, required H4/H1/M15/M5, optional M1 preservation, no endpoint identity, no overwrite, manifest/CSV/bar-count/recomputed-identity verification, canonical filenames and symlink rejection.

## Historical acquisition

`research/acquisition.py` tests reuse of the read-only `MT5Reader` contract, exact requested counts, partial-history rejection, median positive M5 historical spread derivation, explicit spread override and acquisition → bundle → verified import. Synthetic/FakeReader evidence is not real broker proof.

## Immutable evidence-package tests

`research/packages.py` must prove:

- canonical `ResearchEvidenceManifest` persists and round-trips through package integrity checks;
- package binds `dataset_sha256`, evidence input fingerprint and evidence manifest SHA;
- when a dataset bundle is supplied, it is verified before export and its dataset identity must equal the evidence dataset;
- package may reference dataset identity without copying dataset bytes;
- optional dataset-bundle manifest hash is preserved and checked when the bundle is supplied again;
- evidence file SHA-256 is verified before evidence contents are trusted;
- evidence manifest's internal `manifest_sha256` is recomputed;
- evidence input fingerprint is recomputed from experiment-input fields;
- package-manifest SHA-256 is recomputed;
- mismatched dataset bundle fails;
- tampered evidence file fails;
- tampered package manifest fails;
- existing destination is never overwritten;
- evidence package code has no trading/risk/execution/promotion authority.

A package path is not evidence identity; hashes are authority.

## Risk / execution / session / persistence

Risk tests cover all frozen bands, no `$100` floor, min-lot actual risk, daily lock/reset/cooldown and 0/1 capacity. Execution tests cover positive DEMO guard, central gate, exactly-one-send, reconciliation and controller fencing. Runtime session/news tests cover frozen blackout/PRE_CLOSE/reopen rules. Persistence/fault tests protect restart and corruption handling.

## Discovery / promotion

Discovery accepts audited declarative primitives and enforces candidate-or-suppression liveness. Promotion enforces stage order, locked fingerprint, one-shot final holdout, explicit approval and rollback. Neither gets raw broker authority.

## CI versus controlled broker evidence

Public CI is credential-free software evidence. Windows MT5 acquisition, real historical broker-session schedule evidence, cross-machine coordination and DEMO execution need controlled environment evidence with secrets outside the repository.

## Evidence reporting

```text
Unit / deterministic CI       PASS / count
Replay chronology              PASS
Historical PRE_CLOSE software  PASS / verified synthetic schedule semantics
Stress / walk-forward          PASS / declared assumptions/windows
Dataset identity               PASS / dataset_sha256
Portable dataset bundle        PASS / bundle manifest SHA
MT5 acquisition software       PASS / exact-count + spread provenance
Evidence manifest              PASS / input + manifest SHA
Immutable evidence package     PASS / package SHA
Real historical session source PENDING/PASS
Windows MT5 real history       PENDING/PASS
Fresh-machine restore          PENDING/PASS
DEMO execution                 PENDING/PASS
```

Current deterministic checkpoint after historical-session/PRE_CLOSE integration: **189 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Release-blocking failures

At minimum:

- future-data leakage;
- optional confluence becoming hidden hard gate;
- favorable ambiguity guessing;
- stress rewriting structural geometry/original R;
- hidden walk-forward tuning or holdout bypass;
- historical session times guessed/defaulted when PRE_CLOSE parity is claimed;
- session-aware replay treating out-of-coverage or verified CLOSED time as normal OPEN data;
- dataset/evidence/package hash inconsistency accepted;
- evidence package accepting a mismatched dataset bundle;
- historical acquisition silently shrinking sample or inventing spread;
- credential/financial-secret leakage;
- centralized execution/DEMO guard bypass;
- duplicate/wrong-account broker write;
- split-brain controller write;
- critical restart-state loss;
- autonomous self-promotion/broker bypass.

## Explicit non-goals

Software correctness is not profitability proof. Synthetic fixtures/schedules are not real-market validation. Evidence packages are not broker statements and do not turn modeled P/L into realized P/L.

## Open questions

- final CI coverage/static/security thresholds;
- controlled Windows/MT5 historical acquisition matrix;
- trustworthy historical broker-session source/version/coverage matrix;
- higher-level evidence catalog/publication convention;
- real-data walk-forward sample requirements;
- empirical execution-friction calibration;
- final DEMO certification/forward-evidence requirement;
- optional-confluence retention threshold.
