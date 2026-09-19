# GoldSwingTraderAI — Coder Guide

**Status:** CANDIDATE FOR ADOPTION
**Version:** 0.1-developer-manual
**Authority:** Feature-oriented implementation navigation

## What this guide does

This is the developer’s map. It answers:

- which phase owns a feature;
- which document owns its behaviour;
- which source files implement it;
- which public entry point wires it;
- which tests prove it;
- which dashboard, persistence, research and release documents must be updated.

The detailed rule lives in the linked topic contract. This guide is a route
map, not a second risk or strategy specification.

## Before touching code

Read:

1. Documents/README.md.
2. Documents/90-governance/DOCUMENTATION_STANDARD.md.
3. Documents/00-foundation/SYSTEM_CONTRACT.md.
4. The feature’s topic contract.
5. Documents/90-governance/DESIGN_DECISIONS.md and OPEN_QUESTIONS.md.
6. Documents/60-engineering/CODING_STANDARD.md.
7. Documents/60-engineering/FILE_AND_TEST_CATALOG.md.
8. The exact source and tests named below.

Then write a small change packet:

~~~text
behavioural owner
→ inputs and chronology
→ output/state transition
→ source entry point
→ failure/UNKNOWN result
→ persistence/restart effect
→ dashboard/research effect
→ focused tests
→ affected documentation graph
~~~

## Runtime in one picture

~~~mermaid
flowchart TB
    READ["MT5Reader — account, symbol, quote, completed candles, positions"] --> SNAP["MarketSnapshot + IntelligenceSnapshot"]
    SNAP --> INTEL["Independent intelligence desks"]
    INTEL --> STRATEGY["Six strategy families"]
    STRATEGY --> DECISION["BUY/SELL fusion + Entry Timing"]
    DECISION --> PLAN["TradePlan"]
    PLAN --> RISK["Risk + session/news + capacity"]
    RISK --> GATE["DEMO Guard + Execution Permission Gate"]
    GATE --> INTENT["ExecutionIntent"]
    INTENT --> MT5["mt5_writer.py — one raw write"]
    MT5 --> VERIFY["reconcile.py + StateStore"]
    VERIFY --> DASH["Dashboard, Trade Manager and research"]
~~~

## Phase 1–9: production foundation

### Phase 1 — Foundation and contracts

**Behaviour:** typed settings, IDs, enums, models, reason codes, logging and
secret-safe boundaries.

**Read:** 00-foundation/SYSTEM_CONTRACT.md and
60-engineering/CODING_STANDARD.md.

**Code:** config/settings.py; domain/enums.py; domain/ids.py;
domain/market.py; domain/models.py; diagnostics/logging.py;
diagnostics/reasons.py; security/financial_secrets.py.

**Tests:** test_settings.py, test_ids.py, test_models.py, test_logging.py,
test_secret_scanner.py, test_coding_contract_regressions.py.

**Exit:** invalid settings fail clearly, domain identity is typed, logs redact
secrets, and source boundaries are tested.

### Phase 2 — MT5 reads and market snapshot

**Behaviour:** one read boundary, Gold symbol aliases, account/DEMO facts,
symbol specification, quote, completed candle windows, open positions and
DataQuality.

**Read:** 10-market-intelligence/MARKET_DATA_AND_HISTORY.md.

**Code:** market_data/mt5_reader.py; market_data/snapshot.py;
app/recovery_mt5.py.

**Entry points:** MT5Reader.account_facts, resolve_symbol, symbol_spec,
quote, completed_candles and open_positions; build_mt5_recovery_truth.

**Tests:** test_market_data.py, test_intelligence_snapshot.py,
test_recovery_mt5.py.

**Safety rule:** MT5Reader never calls order_send. A positive empty position
collection means known zero exposure; None or malformed positions mean
unavailable/corrupt exposure, never zero.

### Phase 3 — Intelligence desks

**Behaviour:** causal structure, technical location/confluence, liquidity/SMC,
EMA/RSI/ATR/volatility, session and news facts.

**Read:** the complete 10-market-intelligence/ folder.

**Code:** intelligence/candle_structure.py; technical.py; confluence.py;
liquidity.py; indicators.py; session.py; news.py; snapshot.py.

**Entry point:** build the shared IntelligenceSnapshot from one MarketSnapshot.

**Tests:** test_intelligence_core.py, test_intelligence_snapshot.py,
test_technical_liquidity.py, test_technical_confluence.py,
test_session_news_provider.py, test_session_news_permissions.py.

**Hard distinction:** Trendline, Fibonacci and POC are optional soft
confluence. Missing confluence does not subtract base strategy score.

### Phase 4 — Strategy floor, theses and timing

**Behaviour:** six independent families, optional bonus, independent BUY/SELL
theses, conflict, Opportunity IDs and M5 timing.

**Read:** STRATEGY_FLOOR.md, SCORING_AND_DECISION_FUSION.md and
ENTRY_TIMING.md.

**Code:** strategies/floor.py; strategies/confluence.py;
decisions/fusion.py; decisions/snapshot.py; decisions/opportunity.py;
decisions/timing.py.

**Tests:** test_strategy_decisions.py and
test_technical_confluence.py.

**Rule:** a strong family may lead; a poor current entry normally becomes WAIT;
BLOCK is supplied by hard authorities, not invented by scoring.

### Phase 5 — Trade Plan and risk

**Behaviour:** structural invalidation, initial SL, objective hierarchy,
immutable original R, RR guard, account profile, executable lot, daily lock,
reset, cooldown and capacity.

**Read:** TRADE_PLAN.md and RISK_CONTRACT.md.

**Code:** decisions/trade_plan.py; risk/engine.py; risk/state.py;
execution/checks.py; persistence/runtime_state.py.

**Tests:** test_trade_plan_risk.py, test_small_account_profile.py,
test_risk_state_regressions.py, test_margin_authority.py.

**Rule:** risk may block affordability but may not move structural SL to fit.
Positive equity below 300 is SMALL; there is no arbitrary 100-dollar floor.

### Phase 6 — Session/news and persistence

**Behaviour:** OPEN/PRE_CLOSE/CLOSED/REOPEN_WARMUP, news blackout/unknown/
warmup, SQLite StateStore, checksums and typed recovery.

**Read:** SESSION_AND_RISK_STATE_MACHINE.md,
SESSION_NEWS_PROVIDER_CONTRACT.md and
PERSISTENCE_RESTART_AND_RECOVERY.md.

**Code:** risk/permissions.py; app/session_news.py; persistence/store.py;
persistence/runtime_state.py.

**Tests:** test_session_news_permissions.py, test_session_news_provider.py,
test_persistence_recovery.py.

### Phase 7 — Execution and controller

**Behaviour:** positive DEMO Guard, central gate, Intent lifecycle, one-shot
writer, broker reconciliation and lease/fencing.

**Read:** EXECUTION_AND_BROKER_SAFETY.md.

**Code:** execution/models.py; checks.py; gate.py; intent_store.py;
service.py; mt5_writer.py; reconcile.py; controller.py;
sqlite_coordination.py.

**Tests:** test_execution_safety.py, test_sqlite_coordination.py,
test_live_startup_runtime.py.

**DEMO Guard trace:**

~~~text
MT5 account facts
→ account mode positively equals DEMO
→ DEMO_GUARD = PASS
→ central gate receives PASS
→ all other hard authorities pass
→ Intent may be approved
→ one writer call may occur
~~~

DEMO Guard is not a UI toggle, environment string or strategy score.

### Phase 8 — Trade Manager

**Behaviour:** post-entry continuation/reversal analysis,
HOLD/PROTECT/TRAIL/RUNNER/EXIT, structural protection, objectives and
PRE_CLOSE override.

**Read:** TRADE_MANAGER_AND_EXIT.md.

**Code:** management/models.py; manager.py; store.py; execution.py.

**Tests:** test_trade_manager.py, test_management_execution.py,
test_management_replay.py.

**Rule:** local SL/TP/objective state changes only after broker verification.
Profit alone cannot extend a TP or force a runner.

### Phase 9 — Dashboard and operator workflows

**Behaviour:** full-cycle DTO/rendering and separate read-only readiness frame.

**Read:** 50-operator/DASHBOARD_AND_UX.md, SETUP_AND_RUN_GUIDE.md and
USER_MANUAL.md.

**Code:** app/dashboard.py; operator/dashboard.py; operator/__init__.py.

**Tests:** test_dashboard.py and test_app_readiness.py.

**Rule:** rendering maps authoritative DTOs; it never recalculates risk,
strategy or execution and never creates a broker side effect.

## Phase 10 — Research, learning and governed improvement

**Behaviour:** chronological replay, outcomes, metrics, ablation, datasets,
evidence packages, learning, discovery, invention and promotion.

**Read:** the complete 40-research-learning/ folder.

**Code:** research/replay.py; management_replay.py; session_history.py;
outcomes.py; metrics.py; ablation.py; stress.py; validation.py; datasets.py;
acquisition.py; evidence.py; packages.py; learning.py; episode_journal.py;
discovery.py; invention.py; promotion.py.

**Scripts:** scripts/run_walk_forward.py and
scripts/acquire_mt5_dataset.py.

**Tests:** all test_research_*.py, test_discovery_*.py,
test_promotion_governance.py and test_walk_forward_script.py.

**Liveness rule:** eligible recurring evidence must create a durable candidate
or a machine-readable suppression reason. Silent disappearance is degraded
health.

## Phase 11 — Backup, migration and recovery proof

**Behaviour:** portable checkpoint, fresh-database restore, verified backup
catalog, public-safe staging, controller takeover and startup reconciliation.

**Read:** PERSISTENCE_RESTART_AND_RECOVERY.md and
EXECUTION_AND_BROKER_SAFETY.md.

**Code:** persistence/checkpoint.py; backup.py; publication.py;
app/recovery.py; app/recovery_mt5.py; execution/controller.py;
execution/sqlite_coordination.py.

**Scripts:** scripts/restore_runtime_checkpoint.py and
scripts/stage_public_backup.py.

**Tests:** test_runtime_checkpoint.py, test_backup_catalog.py,
test_operator_scripts.py, test_startup_recovery.py,
test_persistence_recovery.py and test_sqlite_coordination.py.

**Rule:** restore is context only. Current MT5 truth and reconciliation are
required before READY or any new write.

## Phase 12 — Integrated runtime and final DEMO proof

**Behaviour:** startup service, RecoveryAuthorities, persistent M5 loop,
controller renewal, governed entry/management cycle, backup cadence, live
dashboard DTO and final release evidence.

**Code:** app/main.py; app/runtime.py; app/startup.py; app/cycle.py;
app/loop.py; app/dashboard.py.

**Tests:** test_live_startup_runtime.py, test_runtime_loop.py,
test_runtime_checkpoint.py, test_app_readiness.py.

**External proof still required:** fresh broker data, real DEMO
OPEN/MODIFY/CLOSE/restart, fresh-machine restore, two-machine failover,
provider operation, real-XAU walk-forward/calibration and final audit.

## Feature-to-code traceability

| Feature | Authority | Source/entry point | Tests |
|---|---|---|---|
| DEMO Guard | EXECUTION_AND_BROKER_SAFETY.md | market_data/mt5_reader.py; execution/gate.py; app/startup.py | test_market_data.py, test_execution_safety.py, test_live_startup_runtime.py |
| readiness monitor | ARCHITECTURE.md, DASHBOARD_AND_UX.md | app/main.py; app/dashboard.py; operator/dashboard.py | test_app_readiness.py, test_dashboard.py |
| stale-data keep-alive | ARCHITECTURE.md | app/main.py; app/loop.py | test_app_readiness.py, test_runtime_loop.py |
| one-shot Intent | EXECUTION_AND_BROKER_SAFETY.md | execution/intent_store.py; execution/service.py | test_execution_safety.py |
| position truth | MARKET_DATA_AND_HISTORY.md | market_data/mt5_reader.py; app/recovery_mt5.py | test_market_data.py, test_recovery_mt5.py |
| controller fencing | EXECUTION_AND_BROKER_SAFETY.md | execution/controller.py; sqlite_coordination.py | test_sqlite_coordination.py |
| Trade Manager | TRADE_MANAGER_AND_EXIT.md | management/manager.py; management/execution.py | test_trade_manager.py, test_management_execution.py |
| public backup staging | PERSISTENCE_RESTART_AND_RECOVERY.md | persistence/publication.py; scripts/stage_public_backup.py | test_backup_catalog.py, test_operator_scripts.py |
| research CLI | RESEARCH_AND_VALIDATION.md | scripts/run_walk_forward.py | test_walk_forward_script.py |

## Code-placement decision tree

1. Raw MT5 row or external JSON? Normalize at market_data/app boundary.
2. Immutable normalized fact? Use domain.
3. Descriptive market evidence? Use intelligence.
4. Directional family hypothesis? Use strategies.
5. Fusion, lifecycle, timing or structural geometry? Use decisions.
6. Affordability or hard permission? Use risk/execution.
7. Durable state or recovery? Use persistence/app.
8. Post-entry decision? Use management.
9. Presentation? Use app/dashboard and operator.
10. Historical evidence? Use research/scripts.

Never import app/runtime into a pure calculator, MetaTrader5 into strategy code,
or execution policy into the dashboard.

## Documentation change gate

Before merging any material code:

~~~text
authority updated
→ architecture/dataflow checked
→ source/module map updated
→ tests added or named
→ persistence/restart checked
→ dashboard/operator checked
→ research/replay checked
→ setup/prompt/release docs checked
→ old useful meaning retained
→ links and coverage verified
→ python scripts/verify_documents_manual.py . passes
~~~

## Completion definition

The code is not complete when the primary function exists. It is complete when
the behaviour, failure cases, tests, docs, operator view and evidence boundary
all agree.
