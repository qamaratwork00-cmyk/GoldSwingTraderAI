# GoldSwingTraderAI — Coder Guide

**Status:** DRAFT — IMPLEMENTATION MAP CURRENT  
**Version:** 2.3-implementation-map  
**Authority:** Feature-oriented developer navigation and implementation map. It does not redefine trading behaviour.

## Core rule

> **Behaviour comes from authoritative topic docs. Code implements it. This guide tells you where implementation lives and what has actually been verified.**

Use `CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` for sequencing/recovery and `60-engineering/CODING_STANDARD.md` for frozen engineering rules.

## Current checkpoint — 2026-09-18

Deterministic core implementation exists through current **Phase-10 research tooling including portable historical inputs, read-only MT5 acquisition, immutable evidence packages and verified historical PRE_CLOSE/session-policy replay integration**. The normal `goldswing` launcher remains read-only MT5 readiness; final persistent orchestration/live DEMO certification are not complete.

## Implemented phase map

### Phase 1 — Foundation
`config/`, `domain/`, diagnostics, launcher, CI and financial-secret scan.

### Phase 2 — MT5 read layer
`market_data/mt5_reader.py`, `snapshot.py`; completed candles only and read-only broker facts.

### Phase 3 — Market intelligence
`intelligence/` including causal Trendline/Fibonacci/POC confluence.

### Phase 4 — Strategies / Fusion / Opportunity / Timing
`strategies/` + `decisions/`; six parallel families; optional confluence bounded positive-only.

### Phase 5 — Trade Plan + Risk
`decisions/trade_plan.py`, `risk/engine.py`, `risk/state.py`; no `$100` floor; SMALL is any positive day-start equity below `$300`.

### Phase 6 — Session/News Permission + Persistence
`risk/permissions.py`, `persistence/`; hard permission + stdlib SQLite durable state.

### Phase 7 — Execution + Reconciliation
`execution/`; centralized gate, durable one-shot intents, raw writer boundary and broker reconciliation.

### Phase 8 — Trade Manager
`management/`; HOLD / PROTECT / TRAIL / RUNNER / EXIT and broker-verified state transition bridge.

### Phase 9 — Dashboard
`operator/dashboard.py`; read-only stdlib renderer. Runtime DTO/live refresh still integration work.

### Phase 10 — Research / Learning / Discovery

```text
research/replay.py
research/ablation.py
research/outcomes.py
research/management_replay.py
research/session_history.py
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

Current research data/evidence chain:

```text
existing MT5Reader or verified offline dataset
→ exact historical acquisition
→ portable dataset bundle
→ dataset_sha256
→ chronological production replay
→ optional verified historical session schedule
→ ablation / outcomes / manager / PRE_CLOSE / stress / walk-forward
→ ResearchEvidenceManifest
→ immutable EvidencePackage
→ metrics / learning / discovery / promotion evidence
```

### `research/datasets.py`
Portable public-safe bundle with `dataset_manifest.json` + timeframe CSVs. Hash/tamper verified, optional M1 preserved, login/server excluded, destination never overwritten.

### `research/acquisition.py`
Reuses `MT5Reader`; no duplicate raw MetaTrader5 client. Requires exact declared H4/H1/M15/M5 history counts, supports optional M1, rejects partial samples, derives median positive historical M5 spread or requires explicit override, and can export directly to portable bundle.

### `research/evidence.py`
Owns content-addressed dataset identity, input fingerprint and complete evidence-manifest hash. Secret-shaped result/config keys are rejected.

### `research/packages.py`
Owns immutable evidence persistence without copying large historical datasets into every result package.

Package:

```text
package_manifest.json
evidence_manifest.json
```

It binds `dataset_sha256`, optional verified dataset-bundle manifest hash, evidence input fingerprint, evidence manifest hash, evidence-file SHA and package SHA. Import recomputes/verifies all relevant identities. Existing destinations are never overwritten.

Do not add dataset path or mutable filename as authority. A dataset is paired by content hash.

### `research/session_history.py`
Owns explicit historical broker-session facts for replay. It does **not** guess session times.

Required inputs:

```text
source_label
source_version
coverage_start_utc
coverage_end_utc
chronological non-overlapping tradeable intervals
closure kind: DAILY or WEEKEND
```

`HistoricalSessionSchedule.market_permission_at()` delegates to production `risk.permissions.evaluate_market_permission()`, so frozen DAILY `T-20/T-10` and WEEKEND `T-60/T-30` rules stay single-source. Within verified coverage but outside an interval the market is CLOSED; outside verified coverage the module raises `HistoricalSessionCoverageError`.

`research/management_replay.py` accepts an optional `session_schedule`. When supplied, each completed M5 event obtains production session permission and passes mandatory flatten into the real Trade Manager. A schedule saying CLOSED while replay contains a normal completed event is treated as an explicit research-data/schedule mismatch, not silently ignored.

### Discovery / promotion
Eligible evidence must create a candidate or explicit suppression reason. Candidate recipes remain declarative, final holdout is one-shot, self-promotion/broker authority is prohibited.

## Deterministic test ownership

Major later suites:

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
tests/test_research_session_history.py
tests/test_discovery_invention.py
tests/test_discovery_journal.py
tests/test_promotion_governance.py
```

Latest verified historical-session checkpoint: **189 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Feature ownership index

| Feature | Authority | Owner |
|---|---|---|
| Market data/history | `10-market-intelligence/MARKET_DATA_AND_HISTORY.md` | `market_data/` |
| Technical/confluence | `10-market-intelligence/*` | `intelligence/` + `strategies/confluence.py` |
| Strategy/decision/Trade Plan | `20-trading-decisions/*` | `strategies/`, `decisions/` |
| Risk/session/news | `30-risk-execution/*` | `risk/` |
| Runtime persistence | `30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md` | `persistence/` |
| Execution | `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md` | `execution/` |
| Trade Manager | `20-trading-decisions/TRADE_MANAGER_AND_EXIT.md` | `management/` |
| Dashboard | `50-operator/DASHBOARD_AND_UX.md` | `operator/` |
| Research validation/data/evidence/session | `40-research-learning/RESEARCH_AND_VALIDATION.md` | `research/replay.py`, `ablation.py`, `outcomes.py`, `management_replay.py`, `session_history.py`, `stress.py`, `validation.py`, `evidence.py`, `datasets.py`, `acquisition.py`, `packages.py`, `metrics.py` |
| Discovery/invention | `40-research-learning/GOVERNED_STRATEGY_DISCOVERY.md`, `AUTONOMOUS_STRATEGY_INVENTION.md` | `episode_journal.py`, `discovery.py`, `invention.py` |
| Promotion | `40-research-learning/GOVERNED_EXPERIMENTS_AND_PROMOTION.md` | `promotion.py` |

## Coding invariants

- Python 3.11+; standard-library first for production runtime;
- no lookahead;
- analysis parallel, scoring centralized, safety binary, execution last;
- raw broker writes only in `execution/mt5_writer.py`;
- no duplicate MT5 research client; reuse `MT5Reader`;
- optional confluence cannot become hidden hard filter;
- any positive day-start equity below `$300` is SMALL;
- partial historical samples are not silently accepted;
- missing historical spread is explicit, never hidden zero/live fallback;
- historical broker session times are explicit/versioned; never inferred from convenience defaults;
- session-aware replay reuses production session permission rather than duplicating thresholds;
- mutable filenames/paths never replace content identity;
- dataset/evidence packages are write-new and integrity checked;
- evidence packaging does not grant trading or promotion authority;
- financial-authority credentials never enter tracked/public state.

## Current integration gaps / next work

1. controlled Windows/MT5 real-history acquisition and source/version evidence;
2. trustworthy versioned real broker-session history covering research periods;
3. broad real-XAU walk-forward/independent-validation evidence using immutable evidence packages;
4. dashboard runtime DTO including research/discovery health;
5. Phase 11 runtime-state backup/checkpoint + fresh-machine recovery + shared cross-laptop controller proof;
6. Phase 12 final persistent runtime orchestrator + controlled Windows/MT5 DEMO certification;
7. final docs/release audit based on actual evidence.

The current `app/main.py` remains a read-only readiness launcher until final runtime orchestration.
