# GoldSwingTraderAI — Documentation Content Coverage Matrix

**Status:** CANDIDATE FOR ADOPTION
**Version:** 0.1-inventory
**Authority:** Proof that the new manual covers the previous design surface

## How to read this matrix

This is not a history log. It is a loss-prevention map. Every previous
substantive subject has a new destination, an implementation owner and a proof
route. A row is complete only when the destination document explains the
subject from purpose through evidence.

| Previous subject | New destination | Main implementation | Main proof |
|---|---|---|---|
| project vision | 00-foundation/PROJECT_VISION.md | app/, domain/ | system and integration suites |
| system-wide contract | 00-foundation/SYSTEM_CONTRACT.md | all packages | all contract suites |
| runtime architecture | 00-foundation/ARCHITECTURE.md | app/runtime.py, app/loop.py | test_runtime_loop.py, test_live_startup_runtime.py |
| trading-floor desks | 00-foundation/TRADING_FLOOR_ARCHITECTURE.md | intelligence/, strategies/, decisions/, risk/, execution/ | intelligence and strategy suites |
| market facts/history | 10-market-intelligence/MARKET_DATA_AND_HISTORY.md | market_data/mt5_reader.py, market_data/snapshot.py | test_market_data.py, test_recovery_mt5.py |
| candle/structure | 10-market-intelligence/CANDLE_STRUCTURE.md | intelligence/candle_structure.py | test_intelligence_core.py, test_intelligence_snapshot.py |
| technical zones and confluence | 10-market-intelligence/TECHNICAL_STRUCTURE_AND_LEVELS.md | intelligence/technical.py, intelligence/confluence.py | test_technical_liquidity.py, test_technical_confluence.py |
| liquidity and SMC | 10-market-intelligence/LIQUIDITY_AND_SMC.md | intelligence/liquidity.py | test_technical_liquidity.py |
| indicators/volatility | 10-market-intelligence/INDICATORS_AND_VOLATILITY.md | intelligence/indicators.py | test_intelligence_core.py |
| fundamental/news facts | 10-market-intelligence/FUNDAMENTAL_AND_NEWS.md | intelligence/news.py, app/session_news.py | test_session_news_provider.py, test_session_news_permissions.py |
| session context | 10-market-intelligence/SESSION_CONTEXT.md | intelligence/session.py | test_intelligence_snapshot.py |
| strategy families | 20-trading-decisions/STRATEGY_FLOOR.md | strategies/floor.py, strategies/confluence.py | test_strategy_decisions.py |
| BUY/SELL fusion | 20-trading-decisions/SCORING_AND_DECISION_FUSION.md | decisions/fusion.py, decisions/snapshot.py | test_strategy_decisions.py |
| entry timing/opportunity | 20-trading-decisions/ENTRY_TIMING.md | decisions/opportunity.py, decisions/timing.py | test_strategy_decisions.py |
| structural Trade Plan | 20-trading-decisions/TRADE_PLAN.md | decisions/trade_plan.py | test_trade_plan_risk.py |
| Trade Manager/exit | 20-trading-decisions/TRADE_MANAGER_AND_EXIT.md | management/manager.py, management/execution.py | test_trade_manager.py, test_management_execution.py |
| monetary risk | 30-risk-execution/RISK_CONTRACT.md | risk/engine.py, risk/state.py | test_trade_plan_risk.py, test_small_account_profile.py |
| session/news permission | 30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md | risk/permissions.py | test_session_news_permissions.py |
| external provider handoff | 30-risk-execution/SESSION_NEWS_PROVIDER_CONTRACT.md | app/session_news.py | test_session_news_provider.py |
| DEMO Guard and broker writes | 30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md | execution/gate.py, service.py, mt5_writer.py | test_execution_safety.py |
| persistence/restart/recovery | 30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md | persistence/, app/recovery.py | test_persistence_recovery.py, test_startup_recovery.py |
| chronological replay/validation | 40-research-learning/RESEARCH_AND_VALIDATION.md | research/replay.py, validation.py, stress.py | test_research_validation.py, test_research_stress.py |
| learning/AI boundary | 40-research-learning/LEARNING_AND_AI_BOUNDARIES.md | research/learning.py, metrics.py | test_research_outcomes.py |
| governed discovery | 40-research-learning/GOVERNED_STRATEGY_DISCOVERY.md | research/discovery.py, episode_journal.py | test_discovery_journal.py, test_discovery_invention.py |
| autonomous invention | 40-research-learning/AUTONOMOUS_STRATEGY_INVENTION.md | research/invention.py | test_discovery_invention.py |
| promotion/rollback | 40-research-learning/GOVERNED_EXPERIMENTS_AND_PROMOTION.md | research/promotion.py | test_promotion_governance.py |
| dashboard/UX | 50-operator/DASHBOARD_AND_UX.md | app/dashboard.py, operator/dashboard.py | test_dashboard.py, test_app_readiness.py |
| coding quality | 60-engineering/CODING_STANDARD.md | all maintained code | test_coding_contract_regressions.py, Ruff |
| module/file placement | 60-engineering/MODULE_STRUCTURE.md | all source packages | import/source-boundary tests |
| system health | 60-engineering/SYSTEM_HEALTH_AND_DIAGNOSTICS.md | diagnostics/, app/, operator/ | logging and integration tests |
| testing strategy | 60-engineering/TESTING_AND_VERIFICATION.md | tests/, CI | pytest, Ruff, compile, secret scan |
| release gate | 60-engineering/RELEASE_CHECKLIST.md | CI and operator evidence | release audit |
| final evidence record | 60-engineering/FINAL_RELEASE_AUDIT.md | exact build/environment | audit artifacts |
| design decisions | 90-governance/DESIGN_DECISIONS.md | docs governance | decision review |
| open questions/freeze | 90-governance/OPEN_QUESTIONS.md | docs governance | release review |
| documentation process | 90-governance/DOCUMENTATION_STANDARD.md and DOCUMENTATION_AUDIT.md | all documentation | documentation audit |
| AI build/recovery method | PROJECT_BUILD_AND_RECOVERY_GUIDE.md | app/, all packages | phase and recovery tests |
| implementation handoff prompt | FINAL_BUILD_PROMPT.md | all packages | source/test/doc audit |
| setup/run | SETUP_AND_RUN_GUIDE.md | app/main.py, config/settings.py, scripts/ | test_settings.py, test_app_readiness.py |
| user operation | USER_MANUAL.md | operator/ and runtime | dashboard/runtime suites |
| feature/source navigation | CODER_GUIDE.md | all packages | documentation coverage audit |

## Coverage invariants

- The six strategy families remain individually documented.
- DEMO Guard is a named feature, not a hidden line in execution prose.
- Phase 1–9, Phase 10, Phase 11 and Phase 12 remain distinct.
- Every maintained source module, script and test module is named in the new manual.
- Every state with financial or broker impact has owner, failure behaviour and proof.
- Dashboard, persistence, research and release effects are never omitted from a feature change.

## Completion fields for review

~~~text
Inventory checked: yes
New destination exists for every row: yes
Source filename coverage: PASS — scripts/verify_documents_manual.py
Test filename coverage: PASS — scripts/verify_documents_manual.py
Cross-links: PASS — scripts/verify_documents_manual.py
Diagram structure: PASS — required architecture and lifecycle diagrams are present
Human adoption review: pending
~~~
