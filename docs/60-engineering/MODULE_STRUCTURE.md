# GoldSwingTraderAI — Module Structure

**Status:** DRAFT  
**Version:** 2.1-implementation-map  
**Authority:** File/module ownership map and dependency direction. It does **not** redefine trading behaviour.  
**Depends on:** `CODING_STANDARD.md`, `../CODER_GUIDE.md`, `../00-foundation/ARCHITECTURE.md`

## Core engineering rule

> **One primary owner per responsibility; facts flow forward; irreversible broker authority stays narrow and last.**

## Current package shape — Phase 10 research foundation

```text
src/goldswingtraderai/
├── app/
├── config/
├── diagnostics/
├── domain/
├── market_data/
├── intelligence/
├── strategies/
├── decisions/
├── risk/
├── persistence/
├── execution/
├── management/
├── operator/
└── research/
    ├── replay.py
    ├── ablation.py
    ├── outcomes.py
    ├── management_replay.py
    ├── stress.py
    ├── validation.py
    ├── evidence.py
    ├── datasets.py
    ├── acquisition.py
    ├── packages.py
    ├── metrics.py
    ├── learning.py
    ├── episode_journal.py
    ├── discovery.py
    ├── invention.py
    └── promotion.py
```

## Dependency direction

```text
config/domain
→ market_data
→ intelligence
→ strategies
→ decisions
→ risk/persistence
→ execution
→ management
→ operator

read-only MT5 history or offline source
→ acquisition / portable dataset / dataset identity
→ replay / outcomes / management
→ stress / walk-forward
→ evidence manifest
→ immutable evidence package
→ metrics / learning / discovery / promotion
```

The execution package remains the only raw irreversible MT5-write owner.

## Key ownership

### `market_data/`
Read-only account/symbol/quote/completed-candle authority. Research acquisition reuses `MT5Reader.completed_candles()` and does not create another MetaTrader5 adapter.

### `intelligence/`
Shared causal structure/quant/technical/liquidity/session/news/confluence facts. No broker authority.

### `strategies/` + `decisions/`
Parallel strategy floor, BUY/SELL fusion, Opportunity/Timing and structural Trade Plan. Optional Trendline/Fib/POC remains bounded bonus-only.

### `risk/`, `persistence/`, `execution/`, `management/`
Risk/hard permissions, SQLite critical state, centralized one-shot execution/reconciliation and open-trade HOLD/PROTECT/TRAIL/RUNNER/EXIT respectively.

### `operator/`
Read-only presentation; no trading authority.

### `research/datasets.py`
Portable replay inputs. Hash-verifies manifest, CSVs, bar counts and reconstructed dataset identity. Does not export broker login/server.

### `research/acquisition.py`
Read-only MT5 history adapter built on `MT5Reader`. Exact declared counts, historical spread provenance, optional direct bundle export. No raw writes.

### `research/evidence.py`
Dataset/evidence content identity, canonical input fingerprint and evidence-manifest SHA.

### `research/packages.py`
Immutable evidence-package persistence.

```text
ResearchEvidenceManifest
+ optional verified DatasetBundle identity
→ evidence_manifest.json
→ package_manifest.json
→ package_sha256
```

Responsibilities:

- write-new destination only;
- persist canonical evidence JSON;
- hash the evidence file;
- bind evidence manifest/input/dataset hashes;
- optionally bind a verified dataset-bundle manifest hash;
- never copy large dataset bytes merely to package each result;
- recompute package, evidence, input and dataset identities on import;
- optionally verify a supplied external dataset bundle against the package.

Package identity is content-based; filesystem path is not authority. Module has no trading/risk/promotion authority.

### Other research modules
`replay.py` chronological decisions; `ablation.py` controlled variants; `outcomes.py` Trade Plan paths; `management_replay.py` production manager; `stress.py` declared friction; `validation.py` fixed-policy walk-forward; `metrics.py` actual/counterfactual metrics; learning/journal/discovery/invention/promotion own governed improvement lifecycle.

## Prohibited dependency directions

```text
intelligence → order_send                    NO
strategies   → order_send/risk reset         NO
decisions    → raw order_send                NO
management   → raw order_send                NO
operator     → trading authority             NO
research     → production broker write       NO
acquisition  → duplicate raw MT5 client      NO
packages     → trading/risk/promotion        NO
invention    → arbitrary Python/eval/exec    NO
candidate    → self-promotion                NO
stress       → production safety mutation    NO
validation   → hidden tuning/final holdout   NO
```

## Current deterministic tests

Later research suites include:

```text
tests/test_management_replay.py
tests/test_research_ablation.py
tests/test_research_outcomes.py
tests/test_research_stress.py
tests/test_research_validation.py
tests/test_research_evidence.py
tests/test_research_datasets.py
tests/test_research_acquisition.py
tests/test_research_packages.py
tests/test_discovery_invention.py
tests/test_discovery_journal.py
tests/test_promotion_governance.py
```

Current verified checkpoint: **183 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Remaining Phase-10 work

- controlled Windows/MT5 real-history acquisition evidence;
- broad regime-diverse real-XAU studies producing immutable evidence packages;
- historical PRE_CLOSE/session-policy integration;
- empirical execution-friction calibration;
- final untouched holdout evidence;
- replay-versus-DEMO attribution and operator visibility.

## Phase completion rule

Every coherent code checkpoint must update the authoritative topic doc, this map, `docs/CODER_GUIDE.md`, testing contract and open-question ledger before moving on.
