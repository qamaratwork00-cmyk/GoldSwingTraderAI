# GoldSwingTraderAI — Module Structure and File Map

**Status:** PROVISIONAL
**Version:** 0.1-module-map
**Authority:** File ownership, dependency direction and placement

## Purpose

Use this file when deciding where new code belongs. Behavioural meaning remains
in the topic contracts; this file prevents duplicated ownership.

## Dependency direction

~~~mermaid
flowchart TB
    BASE["config + domain + diagnostics + security"] --> READ["market_data"]
    READ --> INTEL["intelligence"]
    INTEL --> STRAT["strategies"]
    STRAT --> DEC["decisions"]
    DEC --> RISK["risk + persistence"]
    RISK --> EXEC["execution"]
    EXEC --> MANAGE["management"]
    MANAGE --> APP["app + operator"]
    RESEARCH["research + scripts"] -.-> INTEL
    RESEARCH -.-> DEC
    RESEARCH -.-> MANAGE
~~~

Research may reuse typed semantics but cannot import production raw writer.

## Package ownership

| Package | Owns | Must not own |
|---|---|---|
| config | validated settings and modes | hidden policy overrides |
| domain | enums, IDs, normalized models | MT5 calls |
| diagnostics | logs and reason codes | trading decisions |
| security | financial-secret detection | credentials |
| market_data | single MT5 read boundary | order_send |
| intelligence | descriptive market evidence | money or writes |
| strategies | family hypotheses and bonus | risk or gate |
| decisions | fusion, timing, Trade Plan | MT5 or final permission |
| risk | monetary affordability and state | strategy rewrite or broker send |
| persistence | records, checkpoints, backups | broker truth |
| execution | gate, Intent, controller, writer, reconciliation | strategy invention |
| management | open-trade decision and state bridge | raw broker write |
| app | composition, startup, loop, dashboard mapping | duplicated policy |
| operator | pure rendering | side effects |
| research | replay, evidence and promotion | production authority |

## File-level ownership index

### Application and configuration

| File | Responsibility | Tests |
|---|---|---|
| app/main.py | launcher modes and readiness sink | test_app_readiness.py |
| app/runtime.py | live dependency composition | test_live_startup_runtime.py |
| app/startup.py | startup authorities | test_live_startup_runtime.py |
| app/recovery.py | startup/takeover recovery | test_startup_recovery.py |
| app/recovery_mt5.py | MT5RecoveryTruth adapter | test_recovery_mt5.py |
| app/cycle.py | one governed entry/management cycle | test_runtime_loop.py |
| app/loop.py | M5 cadence, heartbeat, backup and stop | test_runtime_loop.py |
| app/dashboard.py | authority facts to DTOs | test_dashboard.py, test_app_readiness.py |
| app/session_news.py | provider handoff | test_session_news_provider.py |
| config/settings.py | validated settings | test_settings.py |

### Domain, diagnostics and security

| File | Responsibility | Tests |
|---|---|---|
| domain/enums.py | stable states and vocabularies | test_models.py |
| domain/ids.py | typed identity | test_ids.py |
| domain/market.py | account/symbol/quote/candle/position facts | test_models.py |
| domain/models.py | shared typed contracts | test_models.py |
| diagnostics/logging.py | structured redacted logs | test_logging.py |
| diagnostics/reasons.py | stable reason codes | test_logging.py |
| security/financial_secrets.py | secret-shaped content scan | test_secret_scanner.py |

### Market data and intelligence

| File | Responsibility | Tests |
|---|---|---|
| market_data/mt5_reader.py | read boundary | test_market_data.py |
| market_data/snapshot.py | MarketSnapshot | test_market_data.py |
| intelligence/candle_structure.py | causal structure | test_intelligence_core.py |
| intelligence/technical.py | zones/location/target room | test_technical_liquidity.py |
| intelligence/confluence.py | Trendline/Fibonacci/POC | test_technical_confluence.py |
| intelligence/liquidity.py | pools/sweeps/FVG/OB/path | test_technical_liquidity.py |
| intelligence/indicators.py | EMA/RSI/ATR/volatility | test_intelligence_core.py |
| intelligence/session.py | session labels/ranges | test_intelligence_snapshot.py |
| intelligence/news.py | event facts/tiering | test_session_news_permissions.py |
| intelligence/snapshot.py | shared intelligence composition | test_intelligence_snapshot.py |

### Strategies, decisions, risk and execution

| File | Responsibility | Tests |
|---|---|---|
| strategies/floor.py | six family cases | test_strategy_decisions.py |
| strategies/confluence.py | bounded bonus | test_technical_confluence.py |
| decisions/fusion.py | BUY/SELL fusion | test_strategy_decisions.py |
| decisions/snapshot.py | analytical DTO | test_strategy_decisions.py |
| decisions/opportunity.py | episode/opportunity lifecycle | test_strategy_decisions.py |
| decisions/timing.py | M5 timing | test_strategy_decisions.py |
| decisions/trade_plan.py | structural plan/original R | test_trade_plan_risk.py |
| risk/engine.py | monetary sizing/affordability | test_trade_plan_risk.py |
| risk/state.py | day/lock/cooldown | test_risk_state_regressions.py |
| risk/permissions.py | hard session/news states | test_session_news_permissions.py |
| execution/models.py | request/Intent models | test_execution_safety.py |
| execution/checks.py | fresh spread/drift/volume checks | test_execution_safety.py |
| execution/gate.py | final permission | test_execution_safety.py |
| execution/intent_store.py | one-shot lifecycle | test_execution_safety.py |
| execution/service.py | governed broker operation | test_execution_safety.py |
| execution/mt5_writer.py | only raw order_send | test_execution_safety.py |
| execution/reconcile.py | broker verification | test_execution_safety.py |
| execution/controller.py | lease/fencing | test_sqlite_coordination.py |
| execution/sqlite_coordination.py | transactional coordination | test_sqlite_coordination.py |

### Management, persistence, operator and research

| File group | Responsibility | Tests |
|---|---|---|
| management/models.py, manager.py, store.py, execution.py | action and verified state | test_trade_manager.py, test_management_execution.py |
| persistence/store.py, runtime_state.py | SQLite state and typed restore | test_persistence_recovery.py |
| persistence/checkpoint.py | portable restore | test_runtime_checkpoint.py |
| persistence/backup.py, publication.py | backup catalog and safe staging | test_backup_catalog.py, test_operator_scripts.py |
| operator/dashboard.py, operator/__init__.py | pure renderers | test_dashboard.py |
| research/replay.py, management_replay.py | replay | test_research_validation.py, test_management_replay.py |
| research/session_history.py | historical sessions | test_research_session_history.py |
| research/outcomes.py, metrics.py, ablation.py | metrics | test_research_outcomes.py, test_research_ablation.py |
| research/stress.py, validation.py | stress/WFA | test_research_stress.py, test_research_validation.py |
| research/datasets.py, acquisition.py | data bundles/acquisition | test_research_datasets.py, test_research_acquisition.py |
| research/evidence.py, packages.py | evidence identity/package | test_research_evidence.py, test_research_packages.py |
| research/learning.py, episode_journal.py | memory and feed | test_research_outcomes.py, test_discovery_journal.py |
| research/discovery.py, invention.py | candidate liveness | test_discovery_invention.py |
| research/promotion.py | stage/holdout/rollback | test_promotion_governance.py |

## Scripts

| Script | Boundary | Tests |
|---|---|---|
| scripts/run_walk_forward.py | verified bundle to evidence package | test_walk_forward_script.py |
| scripts/acquire_mt5_dataset.py | read-only exact-count acquisition | test_research_acquisition.py |
| scripts/stage_public_backup.py | public-safe local staging | test_operator_scripts.py |
| scripts/restore_runtime_checkpoint.py | new-DB restore | test_operator_scripts.py |
| scripts/scan_financial_secrets.py | secret scan | test_secret_scanner.py |
| scripts/verify_documentation.py | legacy docs contract; new-manual verifier is pending | test_documentation_contract.py |

## Placement decision tree

Raw external fact → market_data/app boundary.
Descriptive evidence → intelligence.
Family hypothesis → strategies.
Fusion/timing/structural geometry → decisions.
Affordability/permission → risk/execution.
Durable state/recovery → persistence/app.
Open-trade decision → management.
Presentation → app/dashboard and operator.
Offline evidence → research/scripts.

## Forbidden directions

~~~text
strategy → MetaTrader5                         NO
market_data → order_send                       NO
dashboard → risk recalculation                 NO
backup → embedded credentials                  NO
new fencing epoch → immediate write            NO
unknown positions → empty exposure             NO
checkpoint restore → broker permission         NO
research candidate → raw broker authority      NO
~~~

