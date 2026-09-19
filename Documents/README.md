# GoldSwingTraderAI — New Documentation Manual

**Status:** CANDIDATE FOR ADOPTION
**Version:** 0.1-information-architecture
**Authority:** Entry point and navigation for the new Documents manual

## What this folder is

This is a new, independent documentation manual for GoldSwingTraderAI. It is
being written as if the system were designed on paper before implementation.
The language is intentionally simple, but the contracts, boundaries, diagrams,
source maps and verification expectations are production-grade.

The existing docs/ folder is preserved as a separate reference set while this
manual is completed and reviewed. A document in this folder must never depend
on the reader opening an old file to understand its own subject.

## Reading order

~~~mermaid
flowchart TB
    START["Start Here"] --> VISION["Vision and glossary"]
    VISION --> CONTRACT["System contract"]
    CONTRACT --> ARCH["Runtime architecture"]
    ARCH --> FACTS["Market intelligence"]
    FACTS --> DECISIONS["Trading decisions"]
    DECISIONS --> SAFETY["Risk, execution and recovery"]
    SAFETY --> RESEARCH["Research and governed improvement"]
    SAFETY --> OPERATE["Setup, user manual and dashboard"]
    RESEARCH --> ENGINEERING["Coding, modules, tests and release"]
    OPERATE --> ENGINEERING
    ENGINEERING --> GOVERN["Decisions, open questions and documentation freeze"]
~~~

Read the documents in this order when learning the project:

1. This file.
2. [GLOSSARY.md](GLOSSARY.md).
3. [00-foundation/PROJECT_VISION.md](00-foundation/PROJECT_VISION.md).
4. [00-foundation/SYSTEM_CONTRACT.md](00-foundation/SYSTEM_CONTRACT.md).
5. [00-foundation/ARCHITECTURE.md](00-foundation/ARCHITECTURE.md).
6. 00-foundation/TRADING_FLOOR_ARCHITECTURE.md.
7. The 10, 20 and 30 folders in numerical order.
8. The 40 folder for replay, learning and promotion.
9. SETUP_AND_RUN_GUIDE.md, USER_MANUAL.md and 50-operator/DASHBOARD_AND_UX.md.
10. [CODER_GUIDE.md](CODER_GUIDE.md) and
    [60-engineering/MODULE_STRUCTURE.md](60-engineering/MODULE_STRUCTURE.md).
11. [60-engineering/CODING_STANDARD.md](60-engineering/CODING_STANDARD.md),
    [60-engineering/TESTING_AND_VERIFICATION.md](60-engineering/TESTING_AND_VERIFICATION.md),
    [60-engineering/FILE_AND_TEST_CATALOG.md](60-engineering/FILE_AND_TEST_CATALOG.md)
    and the release files.
12. [PROJECT_BUILD_AND_RECOVERY_GUIDE.md](PROJECT_BUILD_AND_RECOVERY_GUIDE.md)
    and [FINAL_BUILD_PROMPT.md](FINAL_BUILD_PROMPT.md).
13. [90-governance/OPEN_QUESTIONS.md](90-governance/OPEN_QUESTIONS.md) and
    [90-governance/DOCUMENTATION_STANDARD.md](90-governance/DOCUMENTATION_STANDARD.md).

This is a learning order. The authority order for resolving a contradiction is
defined in 90-governance/DOCUMENTATION_STANDARD.md.

## Status labels

| Label | Meaning |
|---|---|
| CANDIDATE FOR ADOPTION | New manual is complete enough for review but is not yet the repository's only canonical set |
| DRAFT | A section is still being designed |
| PROVISIONAL | Agreed design; thresholds or external proof may still change |
| FROZEN | The rule is approved for implementation and may change only through governance |
| IMPLEMENTED | The described software/process exists in the repository |
| VERIFIED | The exact required tests or environment evidence passed |
| PENDING EXTERNAL PROOF | Software exists, but broker/provider/machine evidence is not yet supplied |

Documentation status never upgrades code or trading safety by itself.

## Folder map

| Folder/file | Reader question answered |
|---|---|
| [00-foundation/](00-foundation/) | Why does the system exist and how does the whole runtime fit together? |
| [10-market-intelligence/](10-market-intelligence/) | What facts are measured from Gold and how are they kept causal? |
| [20-trading-decisions/](20-trading-decisions/) | How do facts become opportunities, plans and management actions? |
| [30-risk-execution/](30-risk-execution/) | What is allowed to touch the account and what happens after failure? |
| [40-research-learning/](40-research-learning/) | How are replay, learning, discovery and promotion governed? |
| [50-operator/](50-operator/) | What does the operator see and how is the system used? |
| [60-engineering/](60-engineering/) | Where is every module, how is it coded and how is it verified? |
| [90-governance/](90-governance/) | Which choices are frozen, unresolved or required for documentation quality? |
| [CODER_GUIDE.md](CODER_GUIDE.md) | How a developer finds the exact feature, source, entry point and tests |
| [PROJECT_BUILD_AND_RECOVERY_GUIDE.md](PROJECT_BUILD_AND_RECOVERY_GUIDE.md) | How an AI or developer builds, resumes and recovers the project |
| [FINAL_BUILD_PROMPT.md](FINAL_BUILD_PROMPT.md) | Compact implementation handoff that points to the detailed authorities |
| [SETUP_AND_RUN_GUIDE.md](SETUP_AND_RUN_GUIDE.md) | How to install, start, stop, restore and safely operate the runtime |
| [USER_MANUAL.md](USER_MANUAL.md) | What normal states mean to a human operator |
| [GLOSSARY.md](GLOSSARY.md) | Shared vocabulary so the same word has one meaning |

The governance folder also contains
[DOCUMENTATION_AUDIT.md](90-governance/DOCUMENTATION_AUDIT.md), the executable
and human review protocol for adopting this manual.

## System map in one screen

~~~mermaid
flowchart TB
    BROKER["MT5 account, symbol, quote and completed candles"] --> SNAP["One immutable normalized snapshot"]
    SNAP --> INTEL["Independent intelligence desks"]
    INTEL --> STRAT["Six strategy families — BUY and SELL cases"]
    STRAT --> FUSE["Fusion, Red Team and Entry Timing"]
    FUSE --> PLAN["Structural Trade Plan"]
    PLAN --> HARD["Risk, session/news, position and controller authorities"]
    HARD --> GATE["Central Execution Permission Gate — DEMO Guard included"]
    GATE --> WRITE["One durable intent and one governed MT5 write"]
    WRITE --> RECON["Broker verification and durable state"]
    RECON --> MANAGE["Trade Manager, dashboard and research"]
~~~

The intelligence and strategy boxes may be evaluated independently from the
same snapshot. Fusion, Trade Plan, risk, gate, intent, write and reconciliation
are ordered authorities. The diagram does not authorize a shortcut.

## Repository implementation coverage

| Source area | Primary new manual | Main proof |
|---|---|---|
| config, domain, diagnostics, security | 00-foundation/SYSTEM_CONTRACT.md and 60-engineering/CODING_STANDARD.md | tests/test_settings.py, tests/test_models.py, tests/test_ids.py, tests/test_logging.py, tests/test_secret_scanner.py |
| market_data | 10-market-intelligence/MARKET_DATA_AND_HISTORY.md | tests/test_market_data.py, tests/test_intelligence_snapshot.py, tests/test_recovery_mt5.py |
| intelligence | 10-market-intelligence/ folder | tests/test_intelligence_core.py, tests/test_intelligence_snapshot.py, tests/test_technical_liquidity.py, tests/test_technical_confluence.py |
| strategies and decisions | 20-trading-decisions/ folder | tests/test_strategy_decisions.py, tests/test_trade_plan_risk.py |
| risk and permissions | 30-risk-execution/RISK_CONTRACT.md and SESSION_AND_RISK_STATE_MACHINE.md | tests/test_trade_plan_risk.py, tests/test_risk_state_regressions.py, tests/test_small_account_profile.py, tests/test_session_news_permissions.py |
| execution and controller | 30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md | tests/test_execution_safety.py, tests/test_sqlite_coordination.py, tests/test_live_startup_runtime.py |
| persistence and recovery | 30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md | tests/test_persistence_recovery.py, tests/test_runtime_checkpoint.py, tests/test_backup_catalog.py, tests/test_startup_recovery.py |
| management | 20-trading-decisions/TRADE_MANAGER_AND_EXIT.md | tests/test_trade_manager.py, tests/test_management_execution.py |
| app and runtime | 00-foundation/ARCHITECTURE.md and 60-engineering/MODULE_STRUCTURE.md | tests/test_runtime_loop.py, tests/test_live_startup_runtime.py, tests/test_app_readiness.py |
| operator | 50-operator/DASHBOARD_AND_UX.md and USER_MANUAL.md | tests/test_dashboard.py, tests/test_app_readiness.py |
| research and scripts | 40-research-learning/ and PROJECT_BUILD_AND_RECOVERY_GUIDE.md | tests/test_research_*.py, tests/test_discovery_*.py, tests/test_promotion_governance.py, tests/test_walk_forward_script.py |

The package-level map is in
[60-engineering/MODULE_STRUCTURE.md](60-engineering/MODULE_STRUCTURE.md). The
exact file/test map is in
[60-engineering/FILE_AND_TEST_CATALOG.md](60-engineering/FILE_AND_TEST_CATALOG.md).
The feature-level map is in [CODER_GUIDE.md](CODER_GUIDE.md). The old docs/ set
is intentionally not counted as a dependency of this new manual.

## Authority rule

When two new Documents disagree:

1. 00-foundation/SYSTEM_CONTRACT.md for system-wide invariants.
2. The specific topic contract for the behaviour.
3. [90-governance/DESIGN_DECISIONS.md](90-governance/DESIGN_DECISIONS.md) for
   cross-cutting accepted choices.
4. [90-governance/OPEN_QUESTIONS.md](90-governance/OPEN_QUESTIONS.md) for
   unresolved classification.
5. [60-engineering/CODING_STANDARD.md](60-engineering/CODING_STANDARD.md) for
   code quality.
6. [90-governance/DOCUMENTATION_STANDARD.md](90-governance/DOCUMENTATION_STANDARD.md)
   for placement, preservation and synchronization.
7. Coder, setup, dashboard, testing and release documents as navigation/evidence.
8. FINAL_BUILD_PROMPT.md only as a compact handoff summary.

If the conflict can change money, broker exposure, chronology, recovery or
controller ownership, stop implementation until the authority is repaired.

## New-manual adoption rule

This folder is a candidate manual until:

- every subject in CONTENT_COVERAGE_MATRIX.md has a complete destination;
- every source module and test module is named;
- every local link resolves;
- diagrams use real code/state names;
- old useful meaning is retained or explicitly relocated;
- the new manual agrees with the current implementation and release boundary;
- a human review accepts the new reading experience.
- scripts/verify_documents_manual.py passes on the same revision.

Only after those gates may the project decide whether to replace the old docs/
set, keep both with a clear relationship, or merge selected content.
