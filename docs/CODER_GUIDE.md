# GoldSwingTraderAI — Coder Guide

**Status:** DRAFT — IMPLEMENTATION MAP CURRENT  
**Version:** 2.6-implementation-map  
**Authority:** Feature-oriented developer navigation and implementation map. It does not redefine trading behaviour.

## Core rule

> **Behaviour comes from authoritative topic docs. Code implements it. This guide tells you where implementation lives and what has actually been verified.**

Use `CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` for sequencing/recovery and `60-engineering/CODING_STANDARD.md` for frozen engineering rules.

## Current checkpoint — 2026-09-18

Deterministic core exists through Phase 10 plus Phase-11 **portable runtime checkpoints, verified automatic local backup cadence/retention/catalog, durable SQLite controller coordination and reconciliation-gated takeover**. The normal `goldswing` launcher remains read-only MT5 readiness; final persistent orchestration/live DEMO certification are not complete.

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
`execution/`; centralized gate, durable one-shot intents, raw writer boundary, controller fencing and broker reconciliation.

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

Current research chain:

```text
verified history
→ portable dataset identity
→ chronological production replay
→ optional verified historical session schedule
→ outcomes / manager / PRE_CLOSE / stress / walk-forward
→ ResearchEvidenceManifest
→ immutable EvidencePackage
→ governed learning/discovery/promotion evidence
```

### Phase 11 — Backup / Recovery / Controller — software foundation implemented

```text
persistence/store.py
persistence/runtime_state.py
persistence/checkpoint.py
persistence/backup.py
execution/controller.py
execution/sqlite_coordination.py
security/financial_secrets.py
```

Portable runtime checkpoint:

```text
checkpoint_manifest.json
records.jsonl
events.jsonl
```

`StateStore` exports integrity-checked `StoreSnapshot` objects containing current records + append-only events. Record/event timestamps, checksums and event IDs are preserved; event history is part of `integrity_check()`.

`persistence/checkpoint.py` owns public-safe immutable export/import/restore. Restore requires a NEW DB, verifies through a temporary store and always leaves `broker_reconciliation_required=True`.

`persistence/backup.py` owns the verified local rolling-backup layer:

```text
backup_catalog.json
checkpoints/runtime-YYYYMMDDTHHMMSSZ-<sha12>/...
```

Initial configurable engineering baseline:

```text
interval_minutes = 15
keep_latest      = 96
```

`create_backup_if_due()` verifies existing catalog/checkpoints, skips when not due, stages + verifies a new checkpoint, atomically installs it, writes the new hashed catalog and only then prunes old retention entries. `latest_verified_checkpoint()` returns a newest checkpoint only after full catalog + checkpoint verification.

Failed checkpoint creation, including a financial-secret block, leaves the previous known-good catalog/checkpoint unchanged. Catalog entries are chronological, hash-bound, basename-only and path-traversal-safe.

Remote GitHub publication is **not** owned by `backup.py`; authenticated publication must be external tooling so PAT/token material never enters repository/runtime checkpoint state.

### Durable controller coordination

`execution/sqlite_coordination.py` implements the existing `CoordinationStore` contract with transactional SQLite acquire/renew/release and a separate monotonic epoch ledger.

Deterministic guarantees:

```text
many independent store instances
→ exactly one lease winner
→ expired lease takeover gets a strictly newer epoch
→ stale holder cannot renew/release newer lease
→ epoch survives release/reopen
```

`shared_locking_verified=False` by default. Setting it true records a deployment assertion only; it does not make arbitrary network filesystems safe automatically.

`ControllerLeaseManager` now treats expired-lease takeover as:

```text
new epoch acquired
→ BLOCK / CONTROLLER_TAKEOVER_RECONCILIATION_REQUIRED
→ durable state + broker reconciliation outside manager
→ fresh same-holder/same-epoch verification
→ complete_takeover_reconciliation()
→ CONTROLLER_PRIMARY
```

A takeover cannot write merely because it obtained a newer epoch. Losing authority while reconciling prevents completion.

### Shared security owner

`security/financial_secrets.py` owns reusable financial-authority secret detection. Repository source scanning remains fixture-safe text scanning; exported structured state gets stricter recursive key/value inspection.

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
tests/test_persistence_recovery.py
tests/test_runtime_checkpoint.py
tests/test_backup_catalog.py
tests/test_execution_safety.py
tests/test_sqlite_coordination.py
tests/test_discovery_invention.py
tests/test_discovery_journal.py
tests/test_promotion_governance.py
```

Latest verified Phase-11 controller/backup checkpoint: **209 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Feature ownership index

| Feature | Authority | Owner |
|---|---|---|
| Market data/history | `10-market-intelligence/MARKET_DATA_AND_HISTORY.md` | `market_data/` |
| Technical/confluence | `10-market-intelligence/*` | `intelligence/` + `strategies/confluence.py` |
| Strategy/decision/Trade Plan | `20-trading-decisions/*` | `strategies/`, `decisions/` |
| Risk/session/news | `30-risk-execution/*` | `risk/` |
| Runtime persistence/backup | `30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md` | `persistence/store.py`, `runtime_state.py`, `checkpoint.py`, `backup.py` |
| Financial-secret detection | persistence/security policy | `security/financial_secrets.py` |
| Execution/controller | `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md` | `execution/`, including `controller.py`, `sqlite_coordination.py` |
| Trade Manager | `20-trading-decisions/TRADE_MANAGER_AND_EXIT.md` | `management/` |
| Dashboard | `50-operator/DASHBOARD_AND_UX.md` | `operator/` |
| Research validation/data/evidence/session | `40-research-learning/RESEARCH_AND_VALIDATION.md` | `research/` |
| Discovery/invention | `40-research-learning/GOVERNED_STRATEGY_DISCOVERY.md`, `AUTONOMOUS_STRATEGY_INVENTION.md` | `research/discovery.py`, `invention.py`, `episode_journal.py` |
| Promotion | `40-research-learning/GOVERNED_EXPERIMENTS_AND_PROMOTION.md` | `research/promotion.py` |

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
- historical broker session times are explicit/versioned;
- mutable filenames/paths never replace content identity;
- runtime checkpoints/catalogs are canonical and integrity checked;
- backup replacement must verify before old-retention prune;
- restore targets a new local DB; no stale-state merge into live DB;
- restored state never grants broker authority before reconciliation;
- controller takeover does not grant write authority before reconciliation completion;
- controller epoch must be monotonic and freshly verified before every write;
- authenticated remote backup credentials stay outside runtime/repository state;
- financial-authority credentials never enter tracked/public checkpoint state.

## Current integration gaps / next work

1. integrate restore/startup/broker reconciliation with `complete_takeover_reconciliation()` so takeover completion is reached only by the governed recovery orchestrator;
2. real fresh-machine restore + MT5 broker reconciliation drill;
3. controlled cross-laptop shared-locking/failover proof for the selected coordination deployment; replace backend if that environment cannot satisfy SQLite locking semantics;
4. public-safe **authenticated GitHub publication workflow** for already-verified backup artifacts, with credentials external;
5. controlled Windows/MT5 real-history acquisition + real broker-session evidence;
6. broad real-XAU walk-forward/holdout/DEMO evidence;
7. dashboard runtime DTO including backup/recovery/controller + research/discovery health;
8. Phase 12 final persistent runtime orchestrator + controlled Windows/MT5 DEMO certification;
9. final docs/release audit based on actual evidence.

The current `app/main.py` remains a read-only readiness launcher until final runtime orchestration.
