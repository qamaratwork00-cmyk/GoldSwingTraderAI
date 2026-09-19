# GoldSwingTraderAI — Complete File and Test Catalog

**Status:** CANDIDATE FOR ADOPTION  
**Version:** 0.1-file-catalog  
**Authority:** Exact repository navigation and proof ownership

## 1. Purpose

This is the navigation sheet for a developer who needs to find the real
implementation. It deliberately names files exactly as they exist in the
repository. Package summaries are useful, but an expert guide must also answer:

- where a feature is implemented;
- which document owns its behaviour;
- which tests prove it;
- whether the file is a boundary, authority or pure adapter.

When a source or test file is added, this catalog must be updated in the same
change packet.

## 2. Package map

~~~mermaid
flowchart TB
    FOUNDATION["config / domain / diagnostics / security"] --> READ["market_data"]
    READ --> INTEL["intelligence"]
    INTEL --> DECIDE["strategies / decisions"]
    DECIDE --> SAFETY["risk / execution"]
    SAFETY --> STATE["management / persistence"]
    STATE --> APP["app / operator"]
    RESEARCH["research / scripts"] -. evidence only .-> INTEL
    RESEARCH -. evidence only .-> DECIDE
    RESEARCH -. evidence only .-> STATE
~~~

## 3. Application and configuration

| File | Owns | Behaviour document | Main tests |
|---|---|---|---|
| src/goldswingtraderai/__init__.py | Package identity/version surface | Project Vision | Import smoke tests |
| src/goldswingtraderai/__main__.py | python -m entry point | Setup and Run Guide | test_app_readiness.py |
| src/goldswingtraderai/app/__init__.py | App package surface | Architecture | Import smoke tests |
| src/goldswingtraderai/app/main.py | Launcher, modes and readiness sink | Architecture; Setup and Run Guide | test_app_readiness.py; test_live_startup_runtime.py |
| src/goldswingtraderai/app/runtime.py | Live dependency composition | Architecture; Coder Guide | test_live_startup_runtime.py |
| src/goldswingtraderai/app/startup.py | Startup authority sequence | Architecture; Persistence and Recovery | test_startup_recovery.py; test_live_startup_runtime.py |
| src/goldswingtraderai/app/recovery.py | Startup and takeover recovery | Persistence and Recovery | test_startup_recovery.py |
| src/goldswingtraderai/app/recovery_mt5.py | MT5 recovery-truth adapter | Market Data; Execution Safety | test_recovery_mt5.py |
| src/goldswingtraderai/app/cycle.py | One governed entry/management cycle | Architecture; Coder Guide | test_runtime_loop.py |
| src/goldswingtraderai/app/loop.py | Persistent cadence, heartbeat and stop | Architecture; System Health | test_runtime_loop.py |
| src/goldswingtraderai/app/dashboard.py | Runtime facts to dashboard DTOs | Dashboard and UX | test_app_readiness.py; test_dashboard.py |
| src/goldswingtraderai/app/session_news.py | Session/news provider handoff | Session News Provider Contract | test_session_news_provider.py |
| src/goldswingtraderai/config/__init__.py | Config package surface | Setup and Run Guide | Import smoke tests |
| src/goldswingtraderai/config/settings.py | Validated settings and runtime modes | System Contract; Setup and Run Guide | test_settings.py |

## 4. Domain, diagnostics and security

| File | Owns | Behaviour document | Main tests |
|---|---|---|---|
| src/goldswingtraderai/domain/__init__.py | Domain package surface | System Contract | Import smoke tests |
| src/goldswingtraderai/domain/enums.py | Stable state vocabularies | Glossary; System Contract | test_models.py |
| src/goldswingtraderai/domain/ids.py | Typed identity values | System Contract | test_ids.py |
| src/goldswingtraderai/domain/market.py | Account, symbol, quote, candle and position facts | Market Data and History | test_models.py; test_market_data.py |
| src/goldswingtraderai/domain/models.py | Shared typed contracts | System Contract | test_models.py |
| src/goldswingtraderai/diagnostics/__init__.py | Diagnostics package surface | System Health and Diagnostics | Import smoke tests |
| src/goldswingtraderai/diagnostics/logging.py | Structured redacted logging | System Health and Diagnostics | test_logging.py |
| src/goldswingtraderai/diagnostics/reasons.py | Stable machine-readable reasons | System Health and Diagnostics | test_logging.py |
| src/goldswingtraderai/security/__init__.py | Security package surface | Coding Standard | Import smoke tests |
| src/goldswingtraderai/security/financial_secrets.py | Secret-shaped content detection | System Health; Release Checklist | test_secret_scanner.py |

## 5. Market data and intelligence

| File | Owns | Behaviour document | Main tests |
|---|---|---|---|
| src/goldswingtraderai/market_data/__init__.py | Market-data package surface | Market Data and History | Import smoke tests |
| src/goldswingtraderai/market_data/mt5_reader.py | Single MT5 read boundary | Market Data and History | test_market_data.py |
| src/goldswingtraderai/market_data/snapshot.py | Normalized MarketSnapshot | Market Data and History | test_market_data.py |
| src/goldswingtraderai/intelligence/__init__.py | Intelligence package surface | Trading Floor Architecture | Import smoke tests |
| src/goldswingtraderai/intelligence/candle_structure.py | Causal candle and swing structure | Candle Structure | test_intelligence_core.py |
| src/goldswingtraderai/intelligence/technical.py | Zones, location and target room | Technical Structure and Levels | test_technical_liquidity.py |
| src/goldswingtraderai/intelligence/confluence.py | Trendline, Fibonacci and POC evidence | Technical Structure and Levels | test_technical_confluence.py |
| src/goldswingtraderai/intelligence/liquidity.py | Pools, sweeps, FVG, OB and path | Liquidity and SMC | test_technical_liquidity.py |
| src/goldswingtraderai/intelligence/indicators.py | EMA, RSI, ATR and volatility | Indicators and Volatility | test_intelligence_core.py |
| src/goldswingtraderai/intelligence/session.py | Session labels and ranges | Session Context | test_intelligence_snapshot.py |
| src/goldswingtraderai/intelligence/news.py | Event facts and safety tiers | Fundamental and News | test_session_news_permissions.py |
| src/goldswingtraderai/intelligence/snapshot.py | Shared intelligence composition | Trading Floor Architecture | test_intelligence_snapshot.py |

## 6. Strategies and decisions

| File | Owns | Behaviour document | Main tests |
|---|---|---|---|
| src/goldswingtraderai/strategies/__init__.py | Strategy package surface | Strategy Floor | Import smoke tests |
| src/goldswingtraderai/strategies/floor.py | Six family hypotheses | Strategy Floor | test_strategy_decisions.py |
| src/goldswingtraderai/strategies/confluence.py | Bounded optional bonus | Strategy Floor; Technical Structure and Levels | test_technical_confluence.py |
| src/goldswingtraderai/decisions/__init__.py | Decision package surface | Scoring and Decision Fusion | Import smoke tests |
| src/goldswingtraderai/decisions/fusion.py | Independent BUY/SELL fusion | Scoring and Decision Fusion | test_strategy_decisions.py |
| src/goldswingtraderai/decisions/snapshot.py | Analytical decision DTO | Scoring and Decision Fusion | test_strategy_decisions.py |
| src/goldswingtraderai/decisions/opportunity.py | Episode and opportunity lifecycle | Entry Timing; Persistence and Recovery | test_strategy_decisions.py; test_persistence_recovery.py |
| src/goldswingtraderai/decisions/timing.py | M5 entry timing | Entry Timing | test_strategy_decisions.py |
| src/goldswingtraderai/decisions/trade_plan.py | Structural plan and original R | Trade Plan | test_trade_plan_risk.py |

## 7. Risk and execution

| File | Owns | Behaviour document | Main tests |
|---|---|---|---|
| src/goldswingtraderai/risk/__init__.py | Risk package surface | Risk Contract | Import smoke tests |
| src/goldswingtraderai/risk/engine.py | Monetary sizing and affordability | Risk Contract | test_trade_plan_risk.py; test_margin_authority.py |
| src/goldswingtraderai/risk/state.py | Risk-day, loss lock and cooldown | Session and Risk State Machine | test_risk_state_regressions.py |
| src/goldswingtraderai/risk/permissions.py | Session/news hard permission | Session and Risk State Machine | test_session_news_permissions.py |
| src/goldswingtraderai/execution/__init__.py | Execution package surface | Execution and Broker Safety | Import smoke tests |
| src/goldswingtraderai/execution/models.py | Request and Intent contracts | Execution and Broker Safety | test_execution_safety.py |
| src/goldswingtraderai/execution/checks.py | Spread, drift, volume and safety checks | Execution and Broker Safety | test_execution_safety.py |
| src/goldswingtraderai/execution/gate.py | Final broker-write permission | Execution and Broker Safety | test_execution_safety.py |
| src/goldswingtraderai/execution/intent_store.py | One-shot Intent lifecycle | Execution and Broker Safety | test_execution_safety.py |
| src/goldswingtraderai/execution/service.py | Governed broker operation orchestration | Execution and Broker Safety | test_execution_safety.py |
| src/goldswingtraderai/execution/mt5_writer.py | Only raw MT5 write boundary | Execution and Broker Safety | test_execution_safety.py |
| src/goldswingtraderai/execution/reconcile.py | Broker verification and reconciliation | Execution and Broker Safety | test_execution_safety.py |
| src/goldswingtraderai/execution/controller.py | Lease, role and fencing | Execution and Broker Safety | test_sqlite_coordination.py |
| src/goldswingtraderai/execution/sqlite_coordination.py | Transactional coordination store | Persistence and Recovery | test_sqlite_coordination.py |

## 8. Management and persistence

| File | Owns | Behaviour document | Main tests |
|---|---|---|---|
| src/goldswingtraderai/management/__init__.py | Management package surface | Trade Manager and Exit | Import smoke tests |
| src/goldswingtraderai/management/models.py | Management action and state types | Trade Manager and Exit | test_trade_manager.py |
| src/goldswingtraderai/management/manager.py | Hold/protect/trail/runner/exit decision | Trade Manager and Exit | test_trade_manager.py |
| src/goldswingtraderai/management/store.py | Managed-trade durable state | Persistence and Recovery | test_management_execution.py |
| src/goldswingtraderai/management/execution.py | Verified management writes | Execution and Broker Safety | test_management_execution.py |
| src/goldswingtraderai/persistence/__init__.py | Persistence package surface | Persistence and Recovery | Import smoke tests |
| src/goldswingtraderai/persistence/store.py | SQLite records and integrity | Persistence and Recovery | test_persistence_recovery.py |
| src/goldswingtraderai/persistence/runtime_state.py | Typed runtime state restore | Persistence and Recovery | test_persistence_recovery.py |
| src/goldswingtraderai/persistence/checkpoint.py | Portable checkpoint creation/restore | Persistence and Recovery | test_runtime_checkpoint.py |
| src/goldswingtraderai/persistence/backup.py | Backup catalog and artifact identity | Persistence and Recovery | test_backup_catalog.py |
| src/goldswingtraderai/persistence/publication.py | Secret-safe public staging | Persistence and Recovery | test_operator_scripts.py |

## 9. Operator and research

| File | Owns | Behaviour document | Main tests |
|---|---|---|---|
| src/goldswingtraderai/operator/__init__.py | Operator package surface | Dashboard and UX | test_dashboard.py |
| src/goldswingtraderai/operator/dashboard.py | Pure dashboard renderers | Dashboard and UX | test_dashboard.py |
| src/goldswingtraderai/research/ablation.py | Feature/strategy ablation | Research and Validation | test_research_ablation.py |
| src/goldswingtraderai/research/acquisition.py | Historical acquisition contract | Research and Validation | test_research_acquisition.py |
| src/goldswingtraderai/research/datasets.py | Portable dataset identity | Research and Validation | test_research_datasets.py |
| src/goldswingtraderai/research/discovery.py | Governed candidate discovery | Governed Strategy Discovery | test_discovery_invention.py |
| src/goldswingtraderai/research/episode_journal.py | Candidate/episode journal | Governed Strategy Discovery | test_discovery_journal.py |
| src/goldswingtraderai/research/evidence.py | Evidence identity and lineage | Research and Validation | test_research_evidence.py |
| src/goldswingtraderai/research/invention.py | Declarative candidate invention | Autonomous Strategy Invention | test_discovery_invention.py |
| src/goldswingtraderai/research/learning.py | StrategyMemory and learning feed | Learning and AI Boundaries | test_research_outcomes.py |
| src/goldswingtraderai/research/management_replay.py | Management replay | Trade Manager and Exit | test_management_replay.py |
| src/goldswingtraderai/research/metrics.py | Outcome and risk metrics | Research and Validation | test_research_outcomes.py |
| src/goldswingtraderai/research/outcomes.py | Replay outcome records | Research and Validation | test_research_outcomes.py |
| src/goldswingtraderai/research/packages.py | Evidence package assembly | Research and Validation | test_research_packages.py |
| src/goldswingtraderai/research/promotion.py | Stage, holdout, champion and rollback | Governed Experiments and Promotion | test_promotion_governance.py |
| src/goldswingtraderai/research/replay.py | Chronological replay engine | Research and Validation | test_research_validation.py |
| src/goldswingtraderai/research/session_history.py | Historical session facts | Research and Validation | test_research_session_history.py |
| src/goldswingtraderai/research/stress.py | Stress and sensitivity runs | Research and Validation | test_research_stress.py |
| src/goldswingtraderai/research/validation.py | Walk-forward and validation | Research and Validation | test_research_validation.py |

## 10. Scripts

| File | Boundary | Main tests |
|---|---|---|
| scripts/__init__.py | Script package surface | Import smoke tests |
| scripts/acquire_mt5_dataset.py | Read-only exact-count MT5 acquisition | test_research_acquisition.py |
| scripts/restore_runtime_checkpoint.py | New-database checkpoint restore | test_operator_scripts.py |
| scripts/run_walk_forward.py | Verified bundle to evidence package | test_walk_forward_script.py |
| scripts/scan_financial_secrets.py | Secret scan boundary | test_secret_scanner.py |
| scripts/stage_public_backup.py | Public-safe backup staging | test_operator_scripts.py |
| scripts/verify_documentation.py | Legacy docs contract verifier | test_documentation_contract.py |
| scripts/verify_documents_manual.py | New Documents manual structural verifier | test_documents_manual_contract.py |

## 11. Exact test catalog

| Test file | Primary proof area |
|---|---|
| tests/test_app_readiness.py | Readiness dashboard and stale-data keep-alive |
| tests/test_backup_catalog.py | Backup identity and catalog |
| tests/test_coding_contract_regressions.py | Frozen coding/safety regressions |
| tests/test_dashboard.py | Pure dashboard rendering and reasons |
| tests/test_discovery_invention.py | Discovery and invention liveness |
| tests/test_discovery_journal.py | Candidate journal |
| tests/test_documentation_contract.py | Legacy documentation gate |
| tests/test_documents_manual_contract.py | New Documents manual gate |
| tests/test_execution_safety.py | DEMO Guard, gate, Intent and reconciliation |
| tests/test_ids.py | Typed identifiers |
| tests/test_intelligence_core.py | Structure and indicator core |
| tests/test_intelligence_snapshot.py | Shared intelligence snapshot |
| tests/test_live_startup_runtime.py | Live composition and startup |
| tests/test_logging.py | Structured logging and reason codes |
| tests/test_management_execution.py | Verified management execution |
| tests/test_management_replay.py | Management replay |
| tests/test_margin_authority.py | Margin and affordability authority |
| tests/test_market_data.py | MT5 read boundary and freshness |
| tests/test_models.py | Domain models and enums |
| tests/test_operator_scripts.py | Restore and public staging scripts |
| tests/test_persistence_recovery.py | SQLite state and recovery |
| tests/test_promotion_governance.py | Promotion, holdout and rollback |
| tests/test_recovery_mt5.py | MT5 recovery truth |
| tests/test_research_ablation.py | Ablation evidence |
| tests/test_research_acquisition.py | Historical acquisition |
| tests/test_research_datasets.py | Portable dataset identity |
| tests/test_research_evidence.py | Evidence lineage |
| tests/test_research_outcomes.py | Outcomes and metrics |
| tests/test_research_packages.py | Evidence packages |
| tests/test_research_session_history.py | Historical sessions |
| tests/test_research_stress.py | Stress and sensitivity |
| tests/test_research_validation.py | Replay and walk-forward validation |
| tests/test_risk_state_regressions.py | Risk-day and cooldown regressions |
| tests/test_runtime_checkpoint.py | Runtime checkpoint portability |
| tests/test_runtime_loop.py | Persistent loop and cycle cadence |
| tests/test_secret_scanner.py | Financial secret scanning |
| tests/test_session_news_permissions.py | Session/news permission |
| tests/test_session_news_provider.py | Provider handoff |
| tests/test_settings.py | Settings validation |
| tests/test_small_account_profile.py | Small-account risk profile |
| tests/test_sqlite_coordination.py | Lease/fencing coordination |
| tests/test_startup_recovery.py | Startup recovery |
| tests/test_strategy_decisions.py | Strategy, fusion, opportunity and timing |
| tests/test_technical_confluence.py | Trendline, Fibonacci and POC confluence |
| tests/test_technical_liquidity.py | Technical/liquidity evidence |
| tests/test_trade_manager.py | Trade Manager policy |
| tests/test_trade_plan_risk.py | Trade Plan and risk geometry |
| tests/test_walk_forward_script.py | Walk-forward script boundary |

## 12. Catalog maintenance rule

The catalog is updated when any of these change:

- a source file is created, renamed or removed;
- a feature changes ownership;
- a test becomes the authoritative proof for a rule;
- a script changes its input/output boundary;
- a document changes the meaning of a module.

The catalog does not replace the topic contracts. It tells the reader where to
go next.
