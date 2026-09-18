# GoldSwingTraderAI — Coder Guide

**Status:** DRAFT — IMPLEMENTATION MAP CURRENT  
**Version:** 2.8-implementation-map  
**Authority:** Feature-oriented developer navigation and implementation map. It does not redefine trading behaviour.

## Core rule

> **Behaviour comes from authoritative topic docs. Code implements it. This guide tells you where implementation lives and what has actually been verified.**

Use `CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` for sequencing/recovery and `60-engineering/CODING_STANDARD.md` for frozen engineering rules.

## Current checkpoint — 2026-09-18

Deterministic core exists through Phase 10 plus Phase-11 **portable/local backup, durable controller fencing, governed startup recovery and live-read MT5 recovery truth**. `app/main.py` is still the read-only readiness launcher; final persistent runtime/DEMO certification are not complete.

## Phase map

### 1–9 production foundation
Foundation/config/domain → MT5 read layer → market intelligence → strategies/fusion/timing → Trade Plan/Risk → session/news/persistence → execution/reconciliation → Trade Manager → dashboard.

### Phase 10 research
`research/` owns chronological replay, historical PRE_CLOSE/session facts, stress/walk-forward, portable datasets, MT5 history acquisition, evidence packages, metrics/learning/discovery/invention/promotion.

### Phase 11 backup / recovery / controller

```text
persistence/store.py
persistence/runtime_state.py
persistence/checkpoint.py
persistence/backup.py
execution/controller.py
execution/sqlite_coordination.py
app/recovery.py
app/recovery_mt5.py
security/financial_secrets.py
```

#### Checkpoint / local backup
Portable records+events checkpoint is immutable, secret-scanned and fresh-DB-only on restore. Local rolling backup uses verified hashed catalog, configurable 15-minute / keep-96 baseline and last-known-good preservation.

#### Durable controller
SQLite coordination provides one-winner transactional lease semantics + durable monotonic fencing epochs. Cross-laptop deployment remains certification-dependent.

Expired-lease takeover gets a higher epoch but stays blocked until governed recovery completes.

#### Startup recovery
`app/recovery.py` composes persistence, Intent reconciliation, ManagedTrade reconciliation, hard authorities and controller completion. It has no raw broker-write authority.

#### Live MT5 recovery truth
`domain/market.py` now includes `OpenPositionFacts`.

`MT5Reader.open_positions(symbol)` is the **single read-only broker boundary** for current open-position facts. It distinguishes positive empty exposure from unknown/corrupt exposure and normalizes BUY/SELL, volume, open price, SL/TP, magic/comment.

`app/recovery_mt5.py` builds:

```text
MT5Reader account facts
+ resolved Gold symbol
+ verified SymbolSpec
+ normalized open positions
→ MT5RecoveryTruth
```

`MT5RecoveryTruth.price_tolerance` is one verified broker `tick_size`; no hard-coded Gold recovery tolerance.

## Test ownership

Important later suites:

```text
tests/test_market_data.py
tests/test_recovery_mt5.py
tests/test_persistence_recovery.py
tests/test_runtime_checkpoint.py
tests/test_backup_catalog.py
tests/test_execution_safety.py
tests/test_sqlite_coordination.py
tests/test_startup_recovery.py
tests/test_management_replay.py
tests/test_research_*.py
```

Latest verified checkpoint: **226 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Feature ownership index

| Feature | Authority | Owner |
|---|---|---|
| Market data/current broker reads | `10-market-intelligence/MARKET_DATA_AND_HISTORY.md` | `market_data/` |
| Live recovery snapshot adapter | Market Data + Recovery docs | `app/recovery_mt5.py` |
| Technical/confluence | `10-market-intelligence/*` | `intelligence/`, `strategies/confluence.py` |
| Strategy/Trade Plan | `20-trading-decisions/*` | `strategies/`, `decisions/` |
| Risk/session/news | `30-risk-execution/*` | `risk/` |
| Persistence/backup/recovery | `30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md` | `persistence/`, `app/recovery.py` |
| Execution/controller | `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md` | `execution/` |
| Trade Manager | `20-trading-decisions/TRADE_MANAGER_AND_EXIT.md` | `management/` |
| Dashboard | `50-operator/DASHBOARD_AND_UX.md` | `operator/` |
| Research/learning | `40-research-learning/*` | `research/` |

## Coding invariants

- Python 3.11+; standard-library first;
- no lookahead;
- analysis parallel, scoring centralized, safety binary, execution last;
- raw broker writes only in `execution/mt5_writer.py`;
- **all raw MT5 runtime reads reuse `MT5Reader` where its authority applies; no duplicate recovery read client**;
- `positions_get() is None` is UNKNOWN/unavailable, never zero exposure;
- positive empty positions is valid zero exposure;
- broker position facts do not automatically imply bot ownership;
- recovery price tolerance comes from verified symbol tick size;
- checkpoint restore is not broker truth;
- uncertain Intent is reconciled, never resent blindly;
- takeover requires governed recovery before PRIMARY write authority;
- remote credentials remain outside runtime/repository state.

## Current integration gaps / next work

1. wire live MT5 recovery truth into a startup runtime service;
2. construct `RecoveryAuthorities` from authoritative market/risk/session/execution owners rather than caller-made test traces;
3. integrate restored checkpoint selection + MT5 initialization + recovery into one explicit startup mode;
4. add operator recovery/controller DTO;
5. real fresh-machine MT5 reconciliation drill;
6. controlled cross-laptop failover proof;
7. authenticated external GitHub publication for verified backup artifacts;
8. controlled real-history/real-session/DEMO evidence;
9. final persistent runtime loop and release audit.

`app/main.py` remains read-only readiness until the new startup/runtime path is deliberately connected and certified.
