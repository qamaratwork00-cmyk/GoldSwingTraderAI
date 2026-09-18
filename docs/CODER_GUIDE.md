# GoldSwingTraderAI — Coder Guide

**Status:** DRAFT — IMPLEMENTATION MAP CURRENT  
**Version:** 2.7-implementation-map  
**Authority:** Feature-oriented developer navigation and implementation map. It does not redefine trading behaviour.

## Core rule

> **Behaviour comes from authoritative topic docs. Code implements it. This guide tells you where implementation lives and what has actually been verified.**

Use `CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` for sequencing/recovery and `60-engineering/CODING_STANDARD.md` for frozen engineering rules.

## Current checkpoint — 2026-09-18

Deterministic core exists through Phase 10 plus Phase-11 **portable checkpoints, automatic local backup/catalog, durable controller fencing and governed startup recovery**. The normal `goldswing` launcher is still read-only MT5 readiness; final persistent live orchestration/DEMO certification are not complete.

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
`decisions/trade_plan.py`, `risk/engine.py`, `risk/state.py`; SMALL is any positive day-start equity below `$300`.

### Phase 6 — Session/News Permission + Persistence
`risk/permissions.py`, `persistence/`; hard permission + stdlib SQLite durable state.

### Phase 7 — Execution + Reconciliation
`execution/`; centralized gate, durable one-shot intents, raw writer boundary, controller fencing and broker reconciliation.

### Phase 8 — Trade Manager
`management/`; HOLD / PROTECT / TRAIL / RUNNER / EXIT and broker-verified state transition bridge.

### Phase 9 — Dashboard
`operator/dashboard.py`; read-only stdlib renderer. Runtime DTO/live refresh still integration work.

### Phase 10 — Research / Learning / Discovery
`research/` owns chronological replay, historical PRE_CLOSE/session facts, stress/walk-forward, portable datasets, MT5 historical acquisition, evidence packages, metrics/learning/discovery/invention/promotion.

### Phase 11 — Backup / Recovery / Controller — deterministic software foundation

```text
persistence/store.py
persistence/runtime_state.py
persistence/checkpoint.py
persistence/backup.py
execution/controller.py
execution/sqlite_coordination.py
app/recovery.py
security/financial_secrets.py
```

#### Portable checkpoint

```text
checkpoint_manifest.json
records.jsonl
events.jsonl
```

Current records + append-only events are integrity-checked, secret-scanned, immutable/write-new and restorable only into a NEW local DB. Restore always requires broker reconciliation.

#### Local rolling backup

```text
backup_catalog.json
checkpoints/runtime-YYYYMMDDTHHMMSSZ-<sha12>/...
```

Initial configurable defaults are 15 minutes / keep 96. New checkpoint is staged + verified, catalog is atomically replaced, then old retention entries may be pruned. Failed creation preserves previous known-good state.

Remote GitHub publication stays outside `backup.py`; credentials must remain external.

#### Durable controller

`SQLiteCoordinationStore` implements atomic shared-DB acquire/renew/release + durable monotonic fencing epochs. Deterministic tests prove one winner, stale-holder denial and epoch persistence. Cross-laptop network/shared-filesystem safety still requires real deployment proof.

`ControllerLeaseManager` blocks expired-lease takeover with `CONTROLLER_TAKEOVER_RECONCILIATION_REQUIRED`; a higher epoch alone is not write authority.

#### Governed startup recovery

`app/recovery.py` now binds persistence + broker-recovery facts + controller takeover into one fail-closed sequence.

```text
StateStore integrity
→ RuntimeState recovery bundle
→ ExecutionIntent load/reconcile
→ ManagedTrade load/reconcile
→ DEMO/account/server/symbol checks
→ hard RecoveryAuthorities PASS
→ fresh controller holder/epoch verify
→ complete takeover reconciliation if required
→ READY
```

`StartupRecoveryCoordinator` never sends an order. It may safely cancel an `APPROVED` pre-submit Intent with zero send attempts, but `SUBMITTING/ACCEPTED_UNKNOWN` always use the existing reconciler. Verified OPEN without ManagedTrade context cannot become READY.

## Deterministic test ownership

Important later suites:

```text
tests/test_persistence_recovery.py
tests/test_runtime_checkpoint.py
tests/test_backup_catalog.py
tests/test_execution_safety.py
tests/test_sqlite_coordination.py
tests/test_startup_recovery.py
tests/test_management_replay.py
tests/test_research_*.py
tests/test_discovery_invention.py
tests/test_discovery_journal.py
tests/test_promotion_governance.py
```

Latest verified checkpoint: **219 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Feature ownership index

| Feature | Authority | Owner |
|---|---|---|
| Market data/history | `10-market-intelligence/MARKET_DATA_AND_HISTORY.md` | `market_data/` |
| Technical/confluence | `10-market-intelligence/*` | `intelligence/`, `strategies/confluence.py` |
| Strategy/decision/Trade Plan | `20-trading-decisions/*` | `strategies/`, `decisions/` |
| Risk/session/news | `30-risk-execution/*` | `risk/` |
| Persistence/backup/recovery | `30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md` | `persistence/`, `app/recovery.py` |
| Execution/controller | `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md` | `execution/` |
| Financial-secret detection | persistence/security policy | `security/financial_secrets.py` |
| Trade Manager | `20-trading-decisions/TRADE_MANAGER_AND_EXIT.md` | `management/` |
| Dashboard | `50-operator/DASHBOARD_AND_UX.md` | `operator/` |
| Research / evidence / learning | `40-research-learning/*` | `research/` |

## Coding invariants

- Python 3.11+; standard-library first for production runtime;
- no lookahead;
- analysis parallel, scoring centralized, safety binary, execution last;
- raw broker writes only in `execution/mt5_writer.py`;
- reuse `MT5Reader`; do not create duplicate raw MT5 read clients;
- optional confluence cannot become hidden hard filter;
- any positive day-start equity below `$300` is SMALL;
- historical data/session facts are explicit, never guessed;
- checkpoints/catalogs use content integrity, not mutable path as authority;
- restore never merges stale state into a live DB;
- restored state is not broker truth;
- uncertain Intent is reconciled, never resent blindly;
- ManagedTrade must reconcile with current broker position before READY;
- controller fencing epoch is monotonic and freshly checked before every write;
- takeover requires governed recovery before PRIMARY write authority;
- remote backup credentials stay outside runtime/repository state;
- financial-authority credentials never enter tracked/public backup state.

## Current integration gaps / next work

1. add read-only live MT5 recovery-snapshot adapter through existing `MT5Reader` boundary;
2. wire final startup runtime so authoritative risk/session/data facts feed `RecoveryAuthorities`;
3. real fresh-machine restore + MT5 broker reconciliation drill;
4. controlled cross-laptop shared-locking/failover proof; replace backend if deployment cannot satisfy SQLite semantics;
5. authenticated GitHub publication workflow for already-verified public-safe backup artifacts;
6. controlled Windows/MT5 real-history + broker-session evidence;
7. broad real-XAU walk-forward/holdout/DEMO evidence;
8. dashboard runtime DTO with backup/recovery/controller/research health;
9. final persistent runtime orchestrator + DEMO certification;
10. final docs/release audit.

`app/main.py` remains a read-only readiness launcher until final runtime orchestration is deliberately wired and certified.
